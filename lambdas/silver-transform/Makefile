# Makefile for the silver-transform lambda

.PHONY: build test

# Build the Docker image
build:
	poetry install --no-root
	docker build -t silver-transform .

# Run tests
test:
	poetry install --no-root --with dev
	poetry run pytest
