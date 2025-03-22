# Synology Certificate Updater

A Python application that automatically updates Synology DSM certificates from Kubernetes secrets.

## Overview

This application is designed to run as a Kubernetes job or cronjob. It:

1. Reads a TLS certificate and key from a Kubernetes secret
2. Connects to a Synology DSM server via its API
3. Finds a certificate matching a specified domain pattern (e.g., `*.liofal.net`)
4. Updates the certificate with the new one from the Kubernetes secret
5. Restarts the necessary services to apply the new certificate

## Prerequisites

- A Kubernetes cluster with access to the certificate secret
- A Synology DSM server with API access
- Docker for building the container image

## Configuration

### Environment Variables

The application is configured using environment variables:

- `SYNOLOGY_HOST`: Hostname or IP address of your Synology NAS
- `SYNOLOGY_USER`: Username for Synology DSM
- `SYNOLOGY_PASS`: Password for Synology DSM
- `CERT_PATH`: Path to the certificate file (default: `/certs/tls.crt`)
- `KEY_PATH`: Path to the key file (default: `/certs/tls.key`)
- `DOMAIN_PATTERN`: Domain pattern to match (default: `*.liofal.net`)
- `VERIFY_SSL`: Whether to verify SSL certificates (default: `false`)
- `DRY_RUN`: Run without making changes (default: `false`)
- `DEBUG`: Enable detailed debug logging (default: `false`)

### Kubernetes Secret

Create a secret for Synology credentials:

```bash
kubectl create secret generic synology-credentials \
  --from-literal=host=your-synology-ip-or-hostname \
  --from-literal=username=your-synology-username \
  --from-literal=password=your-synology-password
```

## Testing with Docker Compose

For easy testing before deploying to Kubernetes, you can use Docker Compose:

1. Copy the example environment file:

```bash
cp .env.example .env
```

2. Edit the `.env` file with your Synology credentials:

```
SYNOLOGY_HOST=your-synology-ip-or-hostname
SYNOLOGY_USER=your-synology-username
SYNOLOGY_PASS=your-synology-password
DOMAIN_PATTERN=*.liofal.net
VERIFY_SSL=false
DRY_RUN=true  # Set to true for testing without making changes
DEBUG=false   # Set to true for detailed debug logging
```

3. Extract certificates from Kubernetes (if available):

```bash
./scripts/extract-k8s-cert.sh
```

Or manually place your certificate and key files in `test/certs/tls.crt` and `test/certs/tls.key`.

4. Run with Docker Compose:

```bash
docker-compose up --build
```

## Building and Deployment

### Build the Docker Image

```bash
docker build -t synology-cert-updater:latest .
```

If you're using a private registry, tag and push the image:

```bash
docker tag synology-cert-updater:latest your-registry/synology-cert-updater:latest
docker push your-registry/synology-cert-updater:latest
```

### Deploy to Kubernetes

1. Update the image reference in `k8s/job.yaml` and `k8s/cronjob.yaml` if you're using a private registry.

2. Deploy the CronJob for monthly execution:

```bash
kubectl apply -f k8s/cronjob.yaml
```

3. For a one-time execution:

```bash
kubectl apply -f k8s/job.yaml
```

## Monitoring

Check the status of the job:

```bash
kubectl get jobs
```

View the logs:

```bash
kubectl logs job/synology-cert-update
```

## Development

### Synology DSM API Details

This application interacts with the Synology DSM API using two different endpoints:

1. **SYNO.Core.Certificate.CRT** (API version 1) - Used for listing certificates
2. **SYNO.Core.Certificate** (API version 1) - Used for updating certificates

The certificate update operation requires sending the certificate and key files as multipart/form-data, which is different from most other Synology API endpoints that accept JSON or URL parameters.

### Debugging

If you encounter issues, enable debug mode by setting the `DEBUG` environment variable to `true`. This will provide detailed logs of:

- API requests and responses
- Certificate data (truncated for security)
- Error details and troubleshooting information

For local development and testing:

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set environment variables:

```bash
export SYNOLOGY_HOST=your-synology-ip-or-hostname
export SYNOLOGY_USER=your-synology-username
export SYNOLOGY_PASS=your-synology-password
export CERT_PATH=/path/to/certificate.crt
export KEY_PATH=/path/to/private.key
export DOMAIN_PATTERN="*.liofal.net"
export DRY_RUN=true  # Optional: for testing without making changes
export DEBUG=false   # Optional: for detailed debug logging
```

3. Run the script:

```bash
python synology_cert_updater.py
```
