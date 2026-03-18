# Ingestion Lambda

A modular AWS Lambda function for data ingestion and transformation, packaged with Docker and managed via Terraform. This lambda is responsible for ingesting data from various sources (Kaggle, web crawlers) and storing it in configurable sinks (S3 or local filesystem).

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [Development](#development)
  - [Building](#building)
  - [Testing](#testing)
  - [Running Locally](#running-locally)
- [Deployment](#deployment)
- [Directory Structure](#directory-structure)

## Overview

The ingestion lambda is part of a serverless data pipeline that ingests raw data from multiple sources and stores it in a data lake architecture. It supports ingestion from Kaggle datasets and web scraping, with pluggable storage mechanisms for S3 and local filesystem.

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Kaggle    │    │              │    │             │
│  Datasets   │───▶│  Ingestion   │───▶│    S3       │
└─────────────┘    │    Lambda    │    │ Data Lake   │
                   │              │    │             │
┌─────────────┐    └──────────────┘    └─────────────┘
│ Web Crawlers│           │
│    (HTML)   │───────────┘
└─────────────┘
```

## Features

- **Multi-source ingestion**: Supports Kaggle datasets and web crawling
- **Pluggable storage**: Configurable sinks for S3 or local filesystem
- **Environment-based configuration**: Uses OmegaConf for flexible configuration
- **Docker packaging**: Containerized for consistent deployment
- **Terraform integration**: Infrastructure as code deployment
- **Logging**: Comprehensive logging for monitoring and debugging

## Prerequisites

- AWS CLI configured with appropriate permissions
- Docker installed and running
- Poetry for Python dependency management
- Python 3.12+
- Kaggle account and API credentials (for Kaggle data sources)

## Configuration

The lambda uses environment-based configuration with the following key settings:

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Deployment environment | `dev` |
| `LOCAL_SINK_PATH` | Path for local storage | N/A |
| `KAGGLE_URLS` | Comma-separated Kaggle dataset URLs | N/A |
| `CRAWLER_URLS` | Comma-separated URLs for web crawling | N/A |
| `S3_DESTINATION` | S3 destination path | `raw/dev/` |
| `KAGGLE_USERNAME` | Kaggle username | N/A |
| `KAGGLE_KEY` | Kaggle API key | N/A |

See `ingest/config/env.yml.example` for a complete configuration example.

## Development

### Building

To build the ingestion lambda Docker image:

```bash
make ingestion-build
```

Or using Docker directly:

```bash
docker build -t ingestionlambda:ingestion-lambda-v1 .
```

### Testing

To run tests for the ingestion lambda:

```bash
make ingestion-test
```

Or using pytest directly:

```bash
poetry run pytest tests/
```

### Running Locally

To run the lambda locally:

```bash
make ingestion-install
poetry run serve
```

## Deployment

The lambda is deployed using Terraform as part of the infrastructure-as-code approach. The Docker image is pushed to Amazon ECR and deployed as an AWS Lambda function.

To deploy the entire infrastructure:

```bash
cd infrastructure/envs/dev
terraform init
terraform plan
terraform apply
```

## Directory Structure

```
lambdas/ingestion/
├── Dockerfile              # Docker configuration
├── Makefile                # Build and test commands
├── README.md               # This file
├── pyproject.toml          # Python dependencies and metadata
├── poetry.lock             # Locked dependencies
├── template.yaml           # AWS SAM template
├── tests/                  # Unit and integration tests
└── ingest/                 # Main lambda code
    ├── __init__.py
    ├── serve.py            # Entry point
    ├── config/             # Configuration management
    ├── handlers/           # Data source handlers
    └── sinks/              # Storage mechanisms
```

## Dependencies

Key Python dependencies include:

- `requests`: HTTP library for web requests
- `beautifulsoup4`: HTML parsing for web crawling
- `boto3`: AWS SDK for Python
- `omegaconf`: Configuration management
- `pydantic`: Data validation
- `kaggle`: Kaggle API client

For development:
- `black`: Code formatting
- `pytest`: Testing framework