# Makefile for Silver Transform Glue Job Development

# Variables
DOCKER_IMAGE_NAME := silver-transform-job
DOCKERFILE := Dockerfile
BUILD_SCRIPT := ../../ci/scripts/build-silver-transform.sh

# Help target
.PHONY: help
help: ## Show this help message
	@echo "Silver Transform Glue Job Development Commands:"
	@echo ""
	@echo "Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Build the Docker image
.PHONY: build
build: ## Build the Docker image for local development
	cd ../.. && docker build -t $(DOCKER_IMAGE_NAME) -f glue-jobs/silver-transform/$(DOCKERFILE) .

# Run the Glue job locally
.PHONY: run
run: ## Run the Glue job locally using Docker
	docker run --rm \
		-v $(PWD)/data:/app/data \
		$(DOCKER_IMAGE_NAME)

# Build the wheel package
.PHONY: build-wheel
build-wheel: ## Build the wheel package for deployment
	cd ../.. && $(BUILD_SCRIPT)

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

.PHONY: lint-check
lint-check: ## Check code linting without fixing
	poetry run ruff check .

# Format the code
.PHONY: format
format: ## Format the code
	poetry run ruff check --select I --fix .
	poetry run ruff format .

# Remove Docker image
.PHONY: remove-image
remove-image: ## Remove the Docker image
	docker rmi $(DOCKER_IMAGE_NAME) || true
