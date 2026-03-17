# Makefile for the ingestion lambda

.PHONY: build test install ingestion-test ingestion-install ingestion-build

# Install dependencies
ingestion-install: ## Install dependencies for ingestion lambda
	@echo "Dependencies installed for ingestion lambda"
	poetry install --no-root --with dev

# Build the Docker image
ingestion-build: ## Build the ingestion lambda Docker image
	@echo "Docker image built for ingestion lambda"
	poetry install --no-root
	docker build -t ingestion .

# Run tests
ingestion-test: ## Run tests for ingestion lambda
	@echo "Running tests for ingestion lambda"
	poetry install --no-root --with dev
	poetry run pytest tests/

ingestion-ci-test: ## Run CI-style test for ingestion lambda (matches GitHub Actions)
	@echo "Running CI-style test for ingestion lambda"
	@chmod +x ../../ci/scripts/execute-lambda-command.sh
	@../../ci/scripts/execute-lambda-command.sh ingestion make ingestion-install
	@../../ci/scripts/execute-lambda-command.sh ingestion make ingestion-test

ingestion-ci-install: ## Run CI-style install for ingestion lambda (matches GitHub Actions)
	@echo "Running CI-style install for ingestion lambda"
	@chmod +x ../../ci/scripts/execute-lambda-command.sh
	@../../ci/scripts/execute-lambda-command.sh ingestion make ingestion-install
