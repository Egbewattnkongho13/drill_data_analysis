#!/bin/bash

# Execute script from project root
PROJ_ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." &> /dev/null && pwd)"
LAMBDA_ROOT_DIR="$PROJ_ROOT_DIR/lambdas"
pushd "$PROJ_ROOT_DIR" &> /dev/null

GOLD_TRANSFORM="gold-transform"
INGESTION="ingestion"
SILVER_TRANSFORM="silver-transform"

# Check if running in GitHub Actions
IS_GHA=false
if [ -n "$GITHUB_ACTIONS" ]; then
    IS_GHA=true
fi

# Function to run black
run_black_poetry() {
    if $IS_GHA; then
        echo "Running black in check mode..."
        poetry run python -m black --check .
    else
        echo "Running black to format code..."
        poetry run python -m black .
    fi
}

run_black() {
    if $IS_GHA; then
        echo "Running black in check mode..."
        python3 -m black --check .
    else
        echo "Running black to format code..."
        python3 -m black .
    fi
}

# Function to run isort
run_isort_poetry() {
    if $IS_GHA; then
        echo "Running isort in check mode..."
        poetry run python -m isort --check-only .
    else
        echo "Running isort to format code..."
        poetry run python -m isort .
    fi
}

run_isort() {
    if $IS_GHA; then
        echo "Running isort in check mode..."
        python3 -m isort --check-only .
    else
        echo "Running isort to format code..."
        python3 -m isort .
    fi
}

lint_lambda() {
    local lambda_dir="$1"
    pushd $LAMBDA_ROOT_DIR/"$lambda_dir" || exit 1
    echo "Linting lambda in $LAMBDA_ROOT_DIR/$lambda_dir"

    # Install dependencies & Lint
    if [ -f "requirements-lint.txt" ]; then
        echo "Install lint requirements."
        pip install -r requirements-lint.txt --break-system-packages

        run_black 
        run_isort
    else
        poetry install

        run_black_poetry
        run_isort_poetry
    fi
    popd || exit 1

}

# Lint all lambdas
lint_lambda "$GOLD_TRANSFORM"
lint_lambda "$INGESTION"
lint_lambda "$SILVER_TRANSFORM"
