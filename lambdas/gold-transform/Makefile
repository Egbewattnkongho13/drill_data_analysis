# Makefile for the gold-transform lambda

.PHONY: build test install gold-transform-test gold-transform-install gold-transform-build

# Install dependencies
gold-transform-install: ## Install dependencies for gold-transform lambda
	@echo "Dependencies installed for gold-transform lambda"
	poetry install --no-root --with dev

# Build the Docker image
gold-transform-build: ## Build the gold-transform lambda Docker image
	@echo "Docker image built for gold-transform lambda"
	poetry install --no-root
	docker build -t gold-transform .

# Run tests
gold-transform-test: ## Run tests for gold-transform lambda
	@echo "Running tests for gold-transform lambda"
	poetry install --no-root --with dev
	poetry run pytest tests/

gold-transform-ci-test: ## Run CI-style test for gold-transform lambda (matches GitHub Actions)
	@echo "Running CI-style test for gold-transform lambda"
	@chmod +x ../../ci/scripts/execute-lambda-command.sh
	@../../ci/scripts/execute-lambda-command.sh gold-transform make gold-transform-install
	@../../ci/scripts/execute-lambda-command.sh gold-transform make gold-transform-test

gold-transform-ci-install: ## Run CI-style install for gold-transform lambda (matches GitHub Actions)
	@echo "Running CI-style install for gold-transform lambda"
	@chmod +x ../../ci/scripts/execute-lambda-command.sh
	@../../ci/scripts/execute-lambda-command.sh gold-transform make gold-transform-install
