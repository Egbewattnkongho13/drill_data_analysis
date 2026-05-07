#!/bin/bash
# Build script for silver-transform job with glue-core dependency
# This creates TWO wheels: glue-core and silver-transform

set -euo pipefail

echo "--- Building Silver Transform Job ---"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/../.."
GLUE_CORE_DIR="$PROJECT_ROOT/glue-jobs/glue-core"
SILVER_TRANSFORM_DIR="$PROJECT_ROOT/glue-jobs/silver-transform"
DIST_DIR="$SILVER_TRANSFORM_DIR/dist"

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

# Copy core wheel to silver-transform dist
echo "Copying dist/$CORE_WHEEL_NAME to $DIST_DIR/"
cp -v "dist/$CORE_WHEEL_NAME" "$DIST_DIR/"
ls -l "$DIST_DIR/$CORE_WHEEL_NAME"
echo "✓ Built and copied: $CORE_WHEEL_NAME"
popd > /dev/null

# Step 2: Build silver-transform wheel
echo ""
echo "=== Building silver-transform wheel ==="
pushd "$SILVER_TRANSFORM_DIR" > /dev/null
rm -rf build *.egg-info  # Don't delete dist - glue_core wheel is already there!

# Extract version
TRANSFORM_VERSION=$(grep -m1 '^version = ' pyproject.toml | cut -d '"' -f2 | tr -d '\r\n')
TRANSFORM_WHEEL_NAME="silver_transform-${TRANSFORM_VERSION}-py3-none-any.whl"

# Install dependencies and build
poetry install --only main --sync
poetry build -f wheel

echo "✓ Built: $TRANSFORM_WHEEL_NAME"
popd > /dev/null

echo ""
echo "=== Build Complete! ==="
echo ""
echo "Built wheels:"
echo "  1. $CORE_WHEEL_NAME (core library)"
echo "  2. $TRANSFORM_WHEEL_NAME (silver-transform job)"
echo ""
echo "Location: glue-jobs/silver-transform/dist/"
echo ""
echo "Note: Terraform will automatically upload both wheels to S3 and configure the Glue job."
echo ""
