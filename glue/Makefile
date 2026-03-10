# Makefile for Glue Job Development

# Variables
DOCKER_IMAGE_NAME := glue-ingestion-job
DOCKERFILE := Dockerfile
BUILD_SCRIPT := ./ci/scripts/build-glue-package.sh

# Help target
.PHONY: help
help: ## Show this help message
	@echo "Glue Job Development Commands:"
	@echo ""
	@echo "Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Build the Docker image
.PHONY: build
build: ## Build the Docker image for local development
	cd .. && docker build -t $(DOCKER_IMAGE_NAME) -f glue/$(DOCKERFILE) .

# Run the Glue job locally
.PHONY: run
run: ## Run the Glue job locally using Docker
	docker run --rm -v $(PWD)/data:/app/data $(DOCKER_IMAGE_NAME)

# Build the wheel package
.PHONY: build-wheel
build-wheel: ## Build the wheel package for deployment
	cd .. && $(BUILD_SCRIPT)

# Install dependencies locally
.PHONY: install
install: ## Install dependencies locally using Poetry
	poetry install

# Run tests
.PHONY: test
test: ## Run tests
	poetry run pytest

# Clean build artifacts
.PHONY: clean
clean: ## Clean build artifacts
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf build/

# Lint the code
.PHONY: lint
lint: ## Run code linting
	poetry run ruff check --fix .

.PHONY: glue-lint-check
lint-check: ## Check code linting without fixing
	poetry run ruff check .
	
# Format the code
.PHONY: format
format: ## Format the code
	poetry run ruff check --select I --fix .
	poetry run ruff format .

# Validate configuration
.PHONY: validate-config
validate-config: ## Validate the configuration file
	python ingestion/config/config.py

# Show Docker image details
.PHONY: image-details
image-details: ## Show details of the built Docker image
	docker image inspect $(DOCKER_IMAGE_NAME)

# Remove Docker image
.PHONY: remove-image
remove-image: ## Remove the Docker image
	docker rmi $(DOCKER_IMAGE_NAME) || true