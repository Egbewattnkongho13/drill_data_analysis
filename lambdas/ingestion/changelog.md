# changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v1.0.0] - 2025-09-02

### Added
- Implemented a new configuration system in `ingest/config/config.py`.
- The system now attempts to load configuration from AWS Parameter Store in a cloud environment.
- Added fallback to a local `dev.yml` file for local development.
- Introduced `boto3`, `omegaconf`, and `pydantic` to manage AWS services and type-safe settings.

### Removed
- Deleted the placeholder `tests/random_test.py`.

## [v0.1.0] - 2025-07-08    

### Added

- This CHANGELOG file to hopefully serve as an evolving example of a standardized open source project CHANGELOG
-  Initial setup for ingestion lambda function.
-  Dockerfile for building the ingestion lambda image.  
-  ingest directory for lambda function handler and base code implementation.
-  pyproject.toml and poetry lock files for dependency management and versioning.
