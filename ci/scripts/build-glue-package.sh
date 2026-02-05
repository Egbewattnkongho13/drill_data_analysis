#!/bin/bash
# This script builds the ingestion wheel for AWS Glue.
# Glue will handle dependency resolution via --pip-install argument.

# Exit immediately if a command exits with a non-zero status.
set -euo pipefail

echo "--- Building Glue Ingestion Wheel ---"

# Setup
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Define build directories
GLUE_DIR="../../glue"
cd "$GLUE_DIR" # Glue directory as working directory
DIST_DIR="dist"

# Extract version from pyproject.toml
VERSION=$(grep -m1 '^version = ' pyproject.toml | cut -d '"' -f2 | tr -d '\r\n')
WHEEL_NAME="glue_ingestion-${VERSION}-py3-none-any.whl"

# Clean up previous build artifacts
echo "Cleaning up previous build artifacts..."
rm -rf "$DIST_DIR" *.egg-info build/

# --- Local Package Build ---
echo "Building wheel for local 'ingestion' package..."
rm -rf dist

poetry install --only main --sync

echo "Building wheel..."
poetry build -f wheel -o "$DIST_DIR"
echo "Wheel built successfully."

# Verify wheel was created
if [ ! -f "$DIST_DIR/$WHEEL_NAME" ]; then
    echo "Error: Wheel not found at $DIST_DIR/$WHEEL_NAME"
    exit 1
fi

# Write the wheel name to a file for Terraform to read
echo -n "$WHEEL_NAME" > "$DIST_DIR/wheel_name.txt"


echo ""
echo "=== Build successful! ==="
echo "Wheel created at: glue/$DIST_DIR/$WHEEL_NAME"
echo ""
echo "Next step:"
echo "Upload to S3 and configure Glue job with:"
echo "  --pip-install s3://<your-bucket>/path/to/$WHEEL_NAME"
echo ""
echo "Next Steps:"
echo "1. Upload 'glue/$DIST_DIR/$WHEEL_NAME' to an S3 bucket."
echo "2. For Glue Ray jobs (like the one configured in Terraform), use:"
echo "   --pip-install s3://<your-bucket>/path/to/$WHEEL_NAME"
echo "3. For standard PySpark jobs, use:"
echo "   --extra-py-files s3://<your-bucket>/path/to/$WHEEL_NAME"