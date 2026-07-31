# Glue Ingestion Job

This project implements an AWS Glue job for data ingestion, designed to download datasets from Kaggle and store them in either local storage or S3. The job is packaged as a Python wheel for easy deployment to AWS Glue.

## Overview

The Glue ingestion job is responsible for:
- Downloading datasets from Kaggle
- Processing and validating the data
- Storing the data in either local filesystem or S3
- Running in both local development and production environments

## Project Structure

```
glue/
├── Dockerfile              # Multi-stage Docker build for local development
├── Makefile                # Common development commands
├── CHANGELOG.md            # Project changelog
├── README.md               # This file
├── glue_job.py             # Main Glue job script
├── pyproject.toml          # Project metadata and dependencies
├── poetry.lock             # Locked dependency versions
└── ingestion/              # Core ingestion package
    ├── config/             # Configuration management
    │   ├── config.py       # Configuration loading and validation
    │   ├── dev.yml         # Development configuration
    │   └── example.dev.yml # Example configuration template
    ├── handlers/           # Data source handlers
    │   └── kaggle_datahandler.py # Kaggle dataset downloader
    └── sinks/              # Data storage implementations
        ├── local_sink.py   # Local filesystem storage
        └── s3_sink.py      # AWS S3 storage
```

## Local Development Setup

### Prerequisites

- Docker
- Python 3.9+
- Poetry (for dependency management)
- Kaggle account and API credentials

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd drill_data_analysis
   ```

2. **Install dependencies:**
   ```bash
   make install
   ```

3. **Configure Kaggle credentials:**
   - Create a Kaggle API token at https://www.kaggle.com/settings/account
   - Update the `glue/ingestion/config/dev.yml` file with your credentials

4. **Build and run locally with Docker:**
   ```bash
   make build
   make run
   ```

## Configuration

The job uses YAML configuration files located in `glue/ingestion/config/`.

### Development Configuration (`dev.yml`)

```yaml
# Environment identifier
environment: "dev"

# Sink configuration (where to store data)
sink:
  type: "local"  # or "s3"
  path: "/app/data/output/glue_ingestion"  # for local sink
  bucket_name: "your-s3-bucket"  # for s3 sink

# Data source configuration
kaggle_data_source:
  type: "kaggle"
  urls:
    - "https://www.kaggle.com/datasets/example/dataset"

# Destination path within the sink
destination: "raw/dev/glue_ingestion/"

# Kaggle API credentials
kaggle_username: "your-kaggle-username"
kaggle_key: "your-kaggle-api-key"
```

See `glue/ingestion/config/example.dev.yml` for a complete example with comments.

## Development Commands

The project includes a Makefile with common development commands:

```bash
# Show all available commands
make help

# Build the Docker image
make build

# Run the Glue job locally
make run

# Build the wheel package for deployment
make build-wheel

# Install dependencies
make install

# Run tests
make test

# Clean build artifacts
make clean

# Lint the code
make lint

# Format the code
make format

# Validate configuration
make validate-config
```

## Docker Usage

The Dockerfile implements a multi-stage build:

1. **Stage 1**: Builds the Python wheel package using Poetry
2. **Stage 2**: Creates a runtime environment with the installed wheel

To build and run manually:

```bash
# Build the image
docker build -t glue-ingestion-job .

# Run the job
docker run --rm -v $(pwd)/data:/app/data glue-ingestion-job
```

## Deployment to AWS Glue

1. **Build the wheel package:**
   ```bash
   make build-wheel
   ```

2. **Upload to S3:**
   ```bash
   aws s3 cp glue/dist/glue_ingestion-*.whl s3://your-bucket/path/
   ```

3. **Configure Glue Job:**
   - Set the script location to `glue/glue_job.py`
   - Add `--pip-install s3://your-bucket/path/glue_ingestion-*.whl` to job parameters
   - Add `--ENVIRONMENT prod` to job parameters

## Testing

Run tests with:

```bash
make test
```

Or directly with Poetry:

```bash
poetry run pytest
```

## Configuration Management

The job supports two configuration sources:

1. **Local Development**: YAML files in `glue/ingestion/config/`
2. **Production**: AWS Parameter Store (when deployed to AWS)

The configuration system uses Pydantic for validation and type safety.

## Troubleshooting

### Common Issues

1. **Missing Kaggle credentials**: Ensure `kaggle_username` and `kaggle_key` are set in your configuration
2. **Docker volume permissions**: Make sure the data directory has appropriate permissions
3. **Dependency conflicts**: Run `poetry install` to resolve dependency issues

### Logs

Logs are output to stdout and can be viewed in:
- Docker logs for local runs
- CloudWatch Logs for AWS Glue jobs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make test`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.