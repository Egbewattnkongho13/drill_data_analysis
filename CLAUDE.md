# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a serverless data ingestion and transformation pipeline on AWS for drill data analysis. It uses AWS Lambda functions for event-driven processing, AWS Glue jobs for batch ingestion, Amazon S3 for data lake storage (Bronze, Silver, Gold layers), and Amazon ECR for Docker image management. The pipeline ingests raw data through multiple channels, transforms it through multiple layers, and stores it in a structured format for analysis.

## Architecture

The system follows a three-tier data lake architecture:
- **Bronze Layer**: Raw data storage
- **Silver Layer**: Cleaned and conformed data
- **Gold Layer**: Curated data for analysis

Components:
- AWS Lambda functions for ingestion and transformation
- AWS S3 buckets for the data lake
- AWS ECR for Docker image storage
- AWS Glue jobs for data processing
- AWS Parameter Store for configuration management

## Common Development Commands

### Building and Testing

**Build all lambdas:**
```bash
make build-all
```

**Test all lambdas:**
```bash
make test-all
```

**Build a specific lambda:**
```bash
make build-ingestion
make build-silver-transform
make build-gold-transform
```

**Test a specific lambda:**
```bash
make test-ingestion
make test-silver-transform
make test-gold-transform
```

**Run tests with pytest directly:**
```bash
cd lambdas/ingestion # or silver-transform, gold-transform
poetry run pytest
```

### Glue Job Development

**Build the Glue job package:**
```bash
make glue-build
```

**Run Glue job tests:**
```bash
make glue-test
```

**Run the Glue job locally:**
```bash
make glue-run
```

### Infrastructure Management

**Deploy infrastructure with Terraform:**
```bash
cd infrastructure/envs/dev
terraform init
terraform plan
terraform apply
```

## Code Structure

- `lambdas/`: Contains three Lambda functions (ingestion, silver-transform, gold-transform) each with their own Dockerfile and dependencies
- `glue/`: Contains the Glue job implementation with data processing logic
- `infrastructure/`: Terraform modules and environment configurations
- `ci/`: CI/CD scripts and workflows
- `ingestion/`: Shared ingestion package used by both Lambda functions and Glue jobs

## Key Components

1. **Lambda Functions**: Docker-based AWS Lambda functions that process data through the pipeline layers
2. **Glue Jobs**: AWS Glue jobs for batch data ingestion using Spark (part of the ingestion pipeline)
3. **Configuration Management**: Uses AWS Parameter Store in cloud environments and YAML files locally with Pydantic for validation
4. **Data Handlers**: Modular components for different data sources (Kaggle, web crawlers)
5. **Sinks**: Pluggable storage mechanisms (S3, local filesystem)

## Development Workflow

1. Make changes to the relevant component (Lambda function, Glue job, or infrastructure)
2. Run tests locally using `make test-*` commands
3. Build Docker images using `make build-*` commands
4. Deploy infrastructure changes using Terraform
5. Push Docker images to ECR for deployment

## Testing

Tests are implemented with pytest and can be run individually for each Lambda function or collectively using the Makefile targets. CI/CD pipelines automatically run tests on pull requests.