# Makefile for building and testing Lambda functions and Glue jobs

# Get the list of lambdas from the directory names under lambdas/
LAMBDAS := $(patsubst lambdas/%/,%,$(wildcard lambdas/*/))

# Default target
all: help

# Build all lambdas
build-all: $(addprefix build-,$(LAMBDAS))

# Build a specific lambda
build-%:
	@echo "Building lambda: $*"
	@$(MAKE) -C lambdas/$* build

# Run tests for all lambdas
test-all: $(addprefix test-,$(LAMBDAS))

# Run tests for a specific lambda
test-%:
	@echo "Testing lambda: $*"
	@$(MAKE) -C lambdas/$* test

# Glue Job targets
glue-build:
	@echo "Building Glue job package"
	@$(MAKE) -C glue build-wheel

glue-test:
	@echo "Running Glue job tests"
	@$(MAKE) -C glue test

glue-lint:
	@echo "Linting Glue job code"
	@$(MAKE) -C glue lint

glue-lint-check:
	@echo "Checking Glue job code linting"
	@$(MAKE) -C glue lint-check

glue-format:
	@echo "Formatting Glue job code"
	@$(MAKE) -C glue format

glue-run:
	@echo "Running Glue job locally"
	@$(MAKE) -C glue run

glue-clean:
	@echo "Cleaning Glue job build artifacts"
	@$(MAKE) -C glue clean

glue-install:
	@echo "Installing Glue job dependencies"
	@$(MAKE) -C glue install

# Help message
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Lambda Targets:"
	@echo "  build-all             Build all lambdas"
	@echo "  build-<lambda>        Build a specific lambda (e.g., make build-ingestion)"
	@echo "  test-all              Run tests for all lambdas"
	@echo "  test-<lambda>         Run tests for a specific lambda (e.g., make test-ingestion)"
	@echo ""
	@echo "Glue Job Targets:"
	@echo "  glue-build            Build the Glue job package"
	@echo "  glue-test             Run Glue job tests"
	@echo "  glue-lint             Run code linting"
	@echo "  glue-lint-check       Check code linting without fixing"
	@echo "  glue-format           Format the code"
	@echo "  glue-run              Run the Glue job locally"
	@echo "  glue-clean            Clean build artifacts"
	@echo "  glue-install          Install dependencies"
	@echo ""
	@echo "General Targets:"
	@echo "  help                  Show this help message"

.PHONY: all build-all build-% test-all test-% help glue-build glue-test glue-lint glue-lint-check glue-format glue-run glue-clean glue-install
