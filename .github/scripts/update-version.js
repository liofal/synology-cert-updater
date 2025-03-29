#!/usr/bin/env node

/**
 * This script updates the version in the Python file
 * It's used by semantic-release to keep versions in sync
 */

const fs = require('fs');
const path = require('path');

// Get the new version from the command line arguments
const newVersion = process.argv[2];

if (!newVersion) {
  console.error('Error: No version provided');
  process.exit(1);
}

// Path to the Python file
const pythonFilePath = path.join(process.cwd(), 'synology_cert_updater.py');

try {
  // Read the Python file
  let content = fs.readFileSync(pythonFilePath, 'utf8');
  
  // Replace the version
  content = content.replace(
    /^__version__ = ["'](.+)["']$/m,
    `__version__ = "${newVersion}"`
  );
  
  // Write the updated content back to the file
  fs.writeFileSync(pythonFilePath, content);

  // Write the version to VERSION.txt for subsequent workflow steps
  fs.writeFileSync('VERSION.txt', newVersion);
  
  console.log(`Updated version in ${pythonFilePath} to ${newVersion}`);
} catch (error) {
  console.error(`Error updating version: ${error.message}`);
  process.exit(1);
}
