#!/usr/bin/env bash

set -eu

USAGE="Usage: 
$0 <lambda_name> < cmd ... >"

if [[ $# < 2 ]]; then
    echo $USAGE
    exit 1
fi

LAMBDAS_DIR="lambdas"
BUILD_LAMBDA=$1
CMD="${@:2}"

echo "PWD: $(pwd)"

clean_up(){
    # Ensure we return to the original directory
    popd >/dev/null 2>&1 || true
}

trap clean_up EXIT

execute(){
    # Execute the command in the lambda directory
       echo "Executing command in $(pwd)"
    $CMD
            
}
execute