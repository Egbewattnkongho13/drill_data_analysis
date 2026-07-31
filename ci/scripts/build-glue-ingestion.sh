#!/bin/bash
# Build script for glue-ingestion job with glue-core dependency
# This creates TWO wheels: glue-core and glue-ingestion

set -euo pipefail

echo "--- Building Glue Ingestion Job ---"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/../.."
GLUE_CORE_DIR="$PROJECT_ROOT/glue-jobs/glue-core"
GLUE_INGESTION_DIR="$PROJECT_ROOT/glue-jobs/glue-ingestion"
DIST_DIR="$GLUE_INGESTION_DIR/dist"

# Clean up previous builds
echo "Cleaning previous build artifacts..."
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

# Step 1: Build glue-core wheel
echo ""
echo "=== Building glue-core wheel ==="
pushd "$GLUE_CORE_DIR" > /dev/null
rm -rf dist build *.egg-info

# Extract version
CORE_VERSION=$(grep -m1 '^version = ' pyproject.toml | cut -d '"' -f2 | tr -d '\r\n')
CORE_WHEEL_NAME="glue_core-${CORE_VERSION}-py3-none-any.whl"

poetry install --only main --sync
poetry build -f wheel

# Copy core wheel to ingestion dist
echo "Copying dist/$CORE_WHEEL_NAME to $DIST_DIR/"
cp -v "dist/$CORE_WHEEL_NAME" "$DIST_DIR/"
ls -l "$DIST_DIR/$CORE_WHEEL_NAME"
echo "✓ Built and copied: $CORE_WHEEL_NAME"
popd > /dev/null

# Step 2: Build glue-ingestion wheel
echo ""
echo "=== Building glue-ingestion wheel ==="
pushd "$GLUE_INGESTION_DIR" > /dev/null
rm -rf build *.egg-info  # Don't delete dist - glue_core wheel is already there!

# Extract version
INGESTION_VERSION=$(grep -m1 '^version = ' pyproject.toml | cut -d '"' -f2 | tr -d '\r\n')
INGESTION_WHEEL_NAME="ingestion-${INGESTION_VERSION}-py3-none-any.whl"

# Install dependencies and build
poetry install --only main --sync
poetry build -f wheel

# Copy ingestion wheel to dist (it's already there, but let's be explicit)
echo "✓ Built: $INGESTION_WHEEL_NAME"
popd > /dev/null

echo ""
echo "=== Build Complete! ==="
echo ""
echo "Built wheels:"
echo "  1. $CORE_WHEEL_NAME (core library)"
echo "  2. $INGESTION_WHEEL_NAME (ingestion job)"
echo ""
echo "Location: glue-jobs/glue-ingestion/dist/"
echo ""
echo "Note: Terraform will automatically upload both wheels to S3 and configure the Glue job."
echo ""
