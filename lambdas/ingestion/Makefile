# Makefile for the ingestion lambda

.PHONY: build test

# Build the Docker image
build:
	poetry install --no-root
	docker build -t ingestion .

# Run tests
test:
	poetry install --no-root --with dev
	poetry run pytest
