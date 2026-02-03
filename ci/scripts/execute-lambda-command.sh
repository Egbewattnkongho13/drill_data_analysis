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

clean_up(){
    # Ensure we return to the original directory
    popd || exit 1
}

trap clean_up EXIT

execute(){
    # Execute the command in the lambda directory
    if [ -d "$LAMBDAS_DIR/$BUILD_LAMBDA" ]; then
        echo "Executing command in $LAMBDAS_DIR/$BUILD_LAMBDA"

        pushd "$LAMBDAS_DIR/$BUILD_LAMBDA" || {
            echo "Error: Could not change directory to $LAMBDAS_DIR/$BUILD_LAMBDA"
            exit 1
        }

        $CMD || {
                echo "Error: Command failed in $LAMBDAS_DIR/$BUILD_LAMBDA"
                exit 1
            }
    fi
    
}
execute