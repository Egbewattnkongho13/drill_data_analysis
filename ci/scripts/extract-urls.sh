#!/bin/bash

set -euo pipefail

if [ "$#" -ne 1 ]; then 
    echo "Usage: $0 [--kaggle | --crawler]"
    exit 1
fi

YAML_FILE="$(dirname "$0")/../configs/data_sources.yaml"
KEY=""

case "$1" in
    --kaggle)
        KEY="KAGGLE_URLS:"
        ;;
    --crawler)
        KEY="CRAWLER_URLS:"
        ;;
    *)
        echo "Invalid argument: $1"
        echo "Usage: $0 [--kaggle | --crawler]"
        exit 1
        ;;
esac 

# Extract the value of the specified key from the
awk -v key="$KEY" ' { gsub(/\r$/, ""); } \
    $0 == key {found=1; next} \
    found && NF == 0 {found=0} \
    found && !/^[[:space:]]*-/ {found=0} \
 \
   found { \
   gsub(/^[[:space:]]*- ?/, ""); \
    urls = urls (urls ? "," : "") $0 \
    } \
    END { \
    if (urls) { \
        print "\"" urls "\"" \
     } else { \
        print "\"\"" \
    } \
   }' "$YAML_FILE"
