# Makefile for the gold-transform lambda

.PHONY: build test

# Build the Docker image
build:
	poetry install --no-root
	docker build -t gold-transform .

# Run tests
test:
	poetry install --no-root --with dev
	poetry run pytest
