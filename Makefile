# Makefile for building and testing Lambda functions

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

# Help message
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  build-all          Build all lambdas"
	@echo "  build-<lambda>     Build a specific lambda (e.g., make build-ingestion)"
	@echo "  test-all           Run tests for all lambdas"
	@echo "  test-<lambda>      Run tests for a specific lambda (e.g., make test-ingestion)"
	@echo "  help               Show this help message"

.PHONY: all build-all build-% test-all test-% help
