#!/bin/bash
set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: 
    $0 <lambda_dir>" >&2
    exit 1
fi

lambda_dir="$1"

LAMBDA_ROOT_DIR="lambdas"
LAMBDA_PATH="$LAMBDA_ROOT_DIR/$lambda_dir"

# Check for required files before doing anything else
if [ ! -f "$LAMBDA_PATH/pyproject.toml" ]; then
    echo "Error: pyproject.toml not found in $LAMBDA_PATH" >&2
    exit 1
fi

if [ ! -f "$LAMBDA_PATH/changelog.md" ]; then
    echo "Error: changelog.md not found in $LAMBDA_PATH" >&2
    exit 1
fi

# Determine the current branch name
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# --- Main Logic ---

# If on the main branch, just print the current version and exit.
if [ "$CURRENT_BRANCH" == "main" ]; then
    grep 'version = ' "$LAMBDA_PATH/pyproject.toml" | sed -E 's/.*= "(.*)"/\1/'
    exit 0
fi

# --- Feature Branch Logic ---

# On a feature branch, first check if a version change has been made compared to main.

# Use '|| true' to prevent the script from exiting if grep finds no match.
pyproject_version_new=$(git diff main -- "$LAMBDA_PATH/pyproject.toml" | grep '^+version' | sed -E 's/.*= "(.*)"/\1/' || true)
changelog_version_new=$(git diff main -- "$LAMBDA_PATH/changelog.md" | grep '^+## \[' | head -n 1 | sed -E 's/\+## \[(v?)(.*)\].*/\2/' || true)

# If a new version is found in BOTH files, check if they match.
if [ -n "$pyproject_version_new" ] && [ -n "$changelog_version_new" ]; then
    if [ "$pyproject_version_new" == "$changelog_version_new" ]; then
        # New, matching version found. Output it.
        echo "$pyproject_version_new"
        exit 0
    else
        # Mismatch in the new versions. This is a critical error.
        echo "Error: New version in pyproject.toml ('$pyproject_version_new') does not match new version in changelog.md ('$changelog_version_new')." >&2
        exit 1
    fi
fi

# If a new version is in one file but not the other, that's also an error.
if [ -n "$pyproject_version_new" ] && [ -z "$changelog_version_new" ]; then
    echo "Error: A new version was found in pyproject.toml, but no corresponding new version was found in changelog.md." >&2
    exit 1
fi
if [ -z "$pyproject_version_new" ] && [ -n "$changelog_version_new" ]; then
    echo "Error: A new version was found in changelog.md, but no corresponding new version was found in pyproject.toml." >&2
    exit 1
fi

# If no new version change was detected, just print the existing version on the branch.
# This allows commits without version changes to pass CI without error.
grep 'version = ' "$LAMBDA_PATH/pyproject.toml" | sed -E 's/.*= "(.*)"/\1/'
