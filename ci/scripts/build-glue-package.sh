#!/bin/bash
# This script packages the 'ingestion' module and its external dependencies
# into a single, self-contained zip artifact for production Glue jobs.

# Exit immediately if a command exits with a non-zero status.
set -euo pipefail

echo "--- Starting 'gold standard' build process for Glue package ---"

# --- Setup ---
# Get the directory where this script is located to run commands from the correct context.
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Define build directories
GLUE_DIR="../../glue"
cd "$GLUE_DIR" # Glue directory as working directory
DIST_DIR="dist"

# extract version from pyproject.toml
VERSION=$(grep -m1 '^version = ' pyproject.toml | cut -d '"' -f2)
PACKAGE_NAME="ingestion-bundle-$VERSION"
FINAL_PACKAGE_NAME="$PACKAGE_NAME.zip"

# Clean up previous build artifacts to ensure a fresh build
echo "Cleaning up previous build artifacts..."
rm -rf "$DIST_DIR" *.egg-info

# --- Local Package Build ---
echo "Building wheel for local 'ingestion' package..."
rm -rf dist

poetry install --only main --sync
echo "Dependencies installed."

poetry build -f wheel
echo "Local package built."

# poetry run pip install --upgrade -t $PACKAGE_NAME dist/*.whl

echo "Packaging final package into zip artifact..."
INGESTION_WHEEL_PATH=$(ls "$DIST_DIR"/glue_ingestion-*.whl | head -n 1)
mv $INGESTION_WHEEL_PATH dist/$FINAL_PACKAGE_NAME
zip dist/$FINAL_PACKAGE_NAME pyproject.toml
zip -r dist/$FINAL_PACKAGE_NAME README.md
echo "Final package packaged."
# rm -rf ./$PACKAGE_NAME
# rm -rf dist/*.whl

INGESTION_ZIP_PATH=$(ls "$DIST_DIR"/ingestion-bundle-*.zip | head -n 1)
if [ -z "$INGESTION_ZIP_PATH" ]; then
    echo "Error: Ingestion zip not found in $DIST_DIR"
    exit 1
fi
echo "Ingestion zip built at: $DIST_DIR/$FINAL_PACKAGE_NAME"

# Write the wheel name to a file for Terraform to read
echo -n "$FINAL_PACKAGE_NAME" > "$DIST_DIR/package_name.txt"

# --- Final Artifact Creation ---
echo "Checking final package artifact: $FINAL_PACKAGE_NAME..."

echo ""
echo "--- Build successful! ---"
echo "Package created at: glue/$DIST_DIR/$FINAL_PACKAGE_NAME"
echo ""
echo "Next Steps:"
echo "1. Upload 'glue/$DIST_DIR/$FINAL_PACKAGE_NAME' to an S3 bucket."
echo "2. For Glue Ray jobs (like the one configured in Terraform), use:"
echo "   --pip-install s3://<your-bucket>/path/to/$FINAL_PACKAGE_NAME"
echo "3. For standard PySpark jobs, use:"
echo "   --extra-py-files s3://<your-bucket>/path/to/$FINAL_PACKAGE_NAME"