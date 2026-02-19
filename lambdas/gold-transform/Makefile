# Makefile for the gold-transform lambda

.PHONY: build test install

# Install dependencies
install: ## Install dependencies using Poetry
	poetry install --no-root --with dev

# Build the Docker image
build:
	poetry install --no-root
	docker build -t gold-transform .

# Run tests
test:
	poetry install --no-root --with dev
	poetry run pytest tests/
