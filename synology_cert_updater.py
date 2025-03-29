#!/usr/bin/env python3

__version__ = "1.0.0"

import os
import sys
import json
import time
import logging
import tempfile
import requests
from urllib.parse import urlencode
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Enable debug mode for detailed logging (set to False for production)
DEBUG_MODE = False

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('synology-cert-updater')

# Disable SSL warnings - useful if Synology uses self-signed cert
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class SynologyClient:
    def __init__(self, host, username, password, verify_ssl=False):
        self.host = host
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.verify = verify_ssl
        self.sid = None
        self.base_url = f"https://{self.host}/webapi"
    
    def _build_url(self, path, api, version, method, params=None):
        url = f"{self.base_url}/{path}"
        query_params = {
            'api': api,
            'version': version,
            'method': method
        }
        if params:
            query_params.update(params)
        return f"{url}?{urlencode(query_params)}"
    
    def login(self):
        """Authenticate with Synology DSM and obtain session ID"""
        logger.info(f"Logging in to Synology DSM at {self.host}")
        url = self._build_url(
            'auth.cgi', 'SYNO.API.Auth', 6, 'login',
            {'account': self.username, 'passwd': self.password, 'format': 'sid'}
        )
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data.get('success'):
                self.sid = data['data']['sid']
                logger.info("Login successful")
                return True
            else:
                error_code = data.get('error', {}).get('code', 'unknown')
                logger.error(f"Login failed with error code: {error_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Login request failed: {str(e)}")
            return False
    
    def _api_request(self, path, api, version, method, params=None, use_post=False):
        """Make an authenticated API request to Synology DSM"""
        if not self.sid:
            logger.error("Not authenticated. Call login() first.")
            return None
        
        base_params = {
            'api': api,
            'version': version,
            'method': method,
            '_sid': self.sid
        }
        
        url = f"{self.base_url}/{path}"
        
        if DEBUG_MODE:
            logger.debug(f"API request: {api} v{version}, method={method}")
        
        try:
            if use_post:
                # For POST requests, send API parameters in URL and data in request body
                url_with_params = f"{url}?{urlencode(base_params)}"
                
                if DEBUG_MODE:
                    logger.debug(f"POST request to: {url_with_params}")
                    if params:
                        logger.debug(f"POST data keys: {list(params.keys())}")
                
                response = self.session.post(url_with_params, data=params)
            else:
                # For GET requests, send all parameters in URL
                if params:
                    base_params.update(params)
                
                url_with_params = f"{url}?{urlencode(base_params)}"
                
                if DEBUG_MODE:
                    logger.debug(f"GET request to: {url_with_params}")
                
                response = self.session.get(url_with_params)
            
            response.raise_for_status()
            json_response = response.json()
            
            if not json_response.get('success', False):
                error = json_response.get('error', {})
                if DEBUG_MODE:
                    logger.debug(f"API error details: {json.dumps(error, indent=2)}")
                error_code = error.get('code', 'unknown')
                error_msg = error.get('message', 'No error message')
                logger.error(f"API request failed: Error code: {error_code}, Message: {error_msg}")
            
            return json_response
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            if DEBUG_MODE and hasattr(e, 'response') and e.response:
                try:
                    logger.debug(f"Error response content: {e.response.text}")
                except:
                    pass
            return None
    
    def list_certificates(self):
        """List all certificates in Synology DSM
        
        Uses the SYNO.Core.Certificate.CRT API to retrieve all certificates.
        
        Returns:
            list: List of certificate dictionaries, each containing id, subject, etc.
        """
        logger.info("Retrieving list of certificates")
        
        # Synology DSM 7.x uses SYNO.Core.Certificate.CRT for certificate listing
        request_path = 'entry.cgi'
        request_api = 'SYNO.Core.Certificate.CRT'
        request_version = 1
        request_method = 'list'
        
        result = self._api_request(
            request_path, request_api, request_version, request_method
        )
        
        if result:
            if result.get('success'):
                certificates = result.get('data', {}).get('certificates', [])
                logger.info(f"Successfully retrieved {len(certificates)} certificates")
                
                if DEBUG_MODE:
                    logger.debug(f"Certificates: {json.dumps(certificates, indent=2)}")
                
                return certificates
        
        logger.error("Failed to retrieve certificates")
        return []
    
    def find_certificate_by_name(self, name_pattern):
        """Find certificate by common name or subject alternative name"""
        logger.info(f"Looking for certificate matching pattern: {name_pattern}")
        certificates = self.list_certificates()
        
        for cert in certificates:
            # Check subject common name
            if name_pattern in cert.get('subject', {}).get('common_name', ''):
                logger.info(f"Found matching certificate: {cert['id']} (matched common name)")
                return cert
            
            # Check subject alternative names
            alt_names = cert.get('subject', {}).get('sub_alt_name', [])
            if any(name_pattern in alt_name for alt_name in alt_names):
                logger.info(f"Found matching certificate: {cert['id']} (matched alternative name)")
                return cert
        
        logger.error(f"No certificate found matching pattern: {name_pattern}")
        return None
    
    def update_certificate(self, cert_id, cert_data, key_data, dry_run=False):
        """Update an existing certificate with new data
        
        Note: Unlike certificate listing which uses SYNO.Core.Certificate.CRT,
        certificate updates must use SYNO.Core.Certificate API with multipart/form-data.
        
        Args:
            cert_id (str): ID of the certificate to update
            cert_data (str): Certificate data in PEM format
            key_data (str): Private key data in PEM format
            dry_run (bool, optional): If True, don't actually update. Defaults to False.
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Updating certificate with ID: {cert_id}")
        
        if dry_run:
            logger.info(f"DRY RUN: Would update certificate with ID: {cert_id}")
            logger.info(f"DRY RUN: Certificate data length: {len(cert_data)} bytes")
            logger.info(f"DRY RUN: Key data length: {len(key_data)} bytes")
            return True
        
        cert_file_path = None
        key_file_path = None
        cert_file = None
        key_file = None
        
        try:
            # Create temporary files for the certificate and key
            cert_file_path = tempfile.mktemp(suffix='.crt')
            key_file_path = tempfile.mktemp(suffix='.key')
            
            with open(cert_file_path, 'w') as f:
                f.write(cert_data)
            
            with open(key_file_path, 'w') as f:
                f.write(key_data)
            
            # Prepare the URL with query parameters
            api_name = 'SYNO.Core.Certificate'  # Note: Different API than list_certificates
            api_version = 1
            api_method = 'import'
            
            url = f"{self.base_url}/entry.cgi?api={api_name}&version={api_version}&method={api_method}&_sid={self.sid}"
            
            # Prepare form data
            form_data = {
                'id': cert_id,
                'desc': f"Updated via automation on {time.strftime('%Y-%m-%d')}",
                'as_default': 'false'
            }
            
            # Open files for multipart/form-data upload
            cert_file = open(cert_file_path, 'rb')
            key_file = open(key_file_path, 'rb')
            
            # Prepare files for multipart/form-data
            files = {
                'cert': ('cert.crt', cert_file, 'application/x-x509-ca-cert'),
                'key': ('key.key', key_file, 'application/x-x509-ca-cert')
            }
            
            if DEBUG_MODE:
                logger.debug(f"Sending certificate update request to: {url}")
            
            # Make the request
            response = self.session.post(url, files=files, data=form_data)
            
            # Process the response
            if response.status_code == 200:
                result = response.json()
                
                if DEBUG_MODE:
                    logger.debug(f"API response: {json.dumps(result, indent=2)}")
                
                if result.get('success'):
                    logger.info("Certificate updated successfully")
                    return True
                else:
                    error_code = result.get('error', {}).get('code', 'unknown')
                    error_msg = result.get('error', {}).get('message', 'No error message')
                    logger.error(f"Failed to update certificate. Error code: {error_code}, Message: {error_msg}")
            else:
                logger.error(f"API request failed with status code: {response.status_code}")
                if DEBUG_MODE:
                    logger.debug(f"Response content: {response.text}")
            
            return False
                
        except Exception as e:
            logger.error(f"Exception during certificate update: {str(e)}")
            return False
        finally:
            # Close file handles
            if cert_file:
                cert_file.close()
            if key_file:
                key_file.close()
                
            # Clean up temporary files
            for path in [cert_file_path, key_file_path]:
                if path and os.path.exists(path):
                    try:
                        os.unlink(path)
                    except Exception as e:
                        if DEBUG_MODE:
                            logger.warning(f"Failed to clean up temporary file {path}: {str(e)}")
    
    def logout(self):
        """End the DSM session"""
        if self.sid:
            logger.info("Logging out from Synology DSM")
            self._api_request('auth.cgi', 'SYNO.API.Auth', 6, 'logout')
            self.sid = None


def read_file(file_path):
    """Read file contents"""
    try:
        with open(file_path, 'r') as f:
            return f.read().strip()
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {str(e)}")
        return None


def main():
    """Main function to update Synology certificate
    
    Reads configuration from environment variables, connects to the Synology DSM,
    finds the certificate matching the domain pattern, and updates it with the
    provided certificate and key data.
    """
    # Get configuration from environment variables
    synology_host = os.environ.get('SYNOLOGY_HOST')
    synology_user = os.environ.get('SYNOLOGY_USER')
    synology_pass = os.environ.get('SYNOLOGY_PASS')
    cert_path = os.environ.get('CERT_PATH', '/certs/tls.crt')
    key_path = os.environ.get('KEY_PATH', '/certs/tls.key')
    domain_pattern = os.environ.get('DOMAIN_PATTERN', '*.liofal.net')
    verify_ssl = os.environ.get('VERIFY_SSL', 'false').lower() == 'true'
    dry_run = os.environ.get('DRY_RUN', 'false').lower() == 'true'
    
    # Enable debug mode if requested
    global DEBUG_MODE
    DEBUG_MODE = os.environ.get('DEBUG', 'false').lower() == 'true'
    
    if dry_run:
        logger.info("DRY RUN MODE ENABLED - No changes will be made")
    
    if DEBUG_MODE:
        logger.info("DEBUG MODE ENABLED - Detailed logging is active")
    
    # Check required parameters
    if not all([synology_host, synology_user, synology_pass]):
        logger.error("Missing required environment variables. Please set SYNOLOGY_HOST, SYNOLOGY_USER, and SYNOLOGY_PASS.")
        sys.exit(1)
    
    # Read certificate and key
    logger.info("Reading certificate and key files")
    cert_data = read_file(cert_path)
    key_data = read_file(key_path)
    
    if not cert_data or not key_data:
        logger.error(f"Failed to read certificate or key data from {cert_path} and {key_path}")
        sys.exit(1)
    
    # Initialize Synology client
    client = SynologyClient(synology_host, synology_user, synology_pass, verify_ssl)
    
    # Login to DSM
    if not client.login():
        logger.error("Failed to login to Synology DSM")
        sys.exit(1)
    
    try:
        # Find certificate by pattern
        certificate = client.find_certificate_by_name(domain_pattern)
        if not certificate:
            logger.error(f"No certificate found matching pattern: {domain_pattern}")
            sys.exit(1)
        
        # Update certificate (services will be restarted automatically)
        if not client.update_certificate(certificate['id'], cert_data, key_data, dry_run):
            logger.error("Failed to update certificate")
            sys.exit(1)
        
        logger.info("Certificate update completed successfully")
    finally:
        # Always logout
        client.logout()


if __name__ == "__main__":
    main()
