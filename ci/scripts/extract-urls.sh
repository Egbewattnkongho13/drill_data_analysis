#!/bin/bash

set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 [--kaggle | --crawler]"
    exit 1
fi

YAML_FILE="$(dirname "$0")/../configs/data_sources.yaml"
YAML_KEY=""

case "$1" in
    --kaggle)
        YAML_KEY="KAGGLE_URLS"
        ;;
    --crawler)
        YAML_KEY="CRAWLER_URLS"
        ;;
    *)
        echo "Invalid argument: $1"
        echo "Usage: $0 [--kaggle | --crawler]"
        exit 1
        ;;
esac

# Use yq to dynamically select the key and format the URLs.
# We use strenv to read the YAML_KEY environment variable
export YAML_KEY
yq -r '.[strenv('YAML_KEY')] | join(",")' "$YAML_FILE"
