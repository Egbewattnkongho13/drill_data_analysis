#!/bin/bash
set -eu

# take lambda dir as arg
lambda_dir="$1"

if [ -z "$lambda_dir" ]; then
    echo "Usage: $0 <lambda_dir>"
    exit 1
fi

LAMBDA_ROOT_DIR="lambdas"
LAMBDA_PATH="$LAMBDA_ROOT_DIR/$lambda_dir"

# check presence of changelog & pyproject.toml
if [ ! -f "$LAMBDA_PATH/changelog.md" ]; then
    echo "Error: changelog.md not found in $LAMBDA_PATH"
    exit 1
fi

if [ ! -f "$LAMBDA_PATH/pyproject.toml" ]; then
    echo "Error: pyproject.toml not found in $LAMBDA_PATH"
    exit 1
fi

# Function to get version from pyproject.toml
get_pyproject_version() {
    if git show main:"$LAMBDA_PATH/pyproject.toml" &> /dev/null; then
        # File exists in main, get version from diff
        git diff main -- "$LAMBDA_PATH/pyproject.toml" | grep '^\+version' | sed -E 's/.*= "(.*)"/\1/'
    else
        # File is new, get version directly
        grep 'version = ' "$LAMBDA_PATH/pyproject.toml" | sed -E 's/.*= "(.*)"/\1/'
    fi
}

# Function to get version from changelog.md
get_changelog_version() {
    if git show main:"$LAMBDA_PATH/changelog.md" &> /dev/null; then
        # File exists in main, get version from diff
        git diff main -- "$LAMBDA_PATH/changelog.md" | grep '^\+## \[' | head -n 1 | sed -E 's/\+## \[(v*)(.*)\].*/\2/'
    else
        # File is new, get version directly
        grep '## \[' "$LAMBDA_PATH/changelog.md" | head -n 1 | sed -E 's/## \[(v*)(.*)\].*/\2/'
    fi
}

pyproject_version=$(get_pyproject_version)
changelog_version=$(get_changelog_version)

if [ -z "$pyproject_version" ]; then
    echo "Error: No version line found in pyproject.toml or no changes detected."
    exit 1
fi

if [ -z "$changelog_version" ]; then
    echo "Error: No version line found in changelog.md or no changes detected."
    exit 1
fi

if [ "$pyproject_version" != "$changelog_version" ]; then
    echo "Error: Version mismatch between pyproject.toml ($pyproject_version) and changelog.md ($changelog_version)."
    exit 1
fi

echo "$pyproject_version"