# Makefile for the silver-transform lambda

.PHONY: build test install silver-transform-test silver-transform-install silver-transform-build

# Install dependencies
silver-transform-install: install ## Install dependencies for silver-transform lambda
	@echo "Dependencies installed for silver-transform lambda"
	poetry install --no-root --with dev

# Build the Docker image
silver-transform-build: build ## Build the silver-transform lambda Docker image
	@echo "Docker image built for silver-transform lambda"
	poetry install --no-root
	docker build -t silver-transform .

# Run tests
silver-transform-test: test ## Run tests for silver-transform lambda
	@echo "Running tests for silver-transform lambda"
	poetry install --no-root --with dev
	poetry run pytest tests/

silver-transform-ci-test: ## Run CI-style test for silver-transform lambda (matches GitHub Actions)
	@echo "Running CI-style test for silver-transform lambda"
	@chmod +x ../../ci/scripts/execute-lambda-command.sh
	@../../ci/scripts/execute-lambda-command.sh silver-transform make silver-transform-install
	@../../ci/scripts/execute-lambda-command.sh silver-transform make silver-transform-test

silver-transform-ci-install: ## Run CI-style install for silver-transform lambda (matches GitHub Actions)
	@echo "Running CI-style install for silver-transform lambda"
	@chmod +x ../../ci/scripts/execute-lambda-command.sh
	@../../ci/scripts/execute-lambda-command.sh silver-transform make silver-transform-install
