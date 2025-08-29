# Makefile for the gold-transform lambda


# Build the Docker image
.PHONY: build
build:
	poetry install --no-root
	docker build -t gold-transform .

# Run tests
.PHONY: test
test:
	poetry install --no-root --with dev
	poetry run pytest
