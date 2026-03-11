# Changelog

All notable changes to the Glue Ingestion Job will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Professional documentation and developer experience improvements
- Example configuration file for local development
- Makefile with common development commands
- Detailed comments in Dockerfile explaining each stage

### Changed
- Enhanced README with comprehensive documentation
- Improved Dockerfile with explanatory comments

## [0.1.0] - 2026-02-15

### Added
- Initial implementation of Glue ingestion job
- Configuration management with Pydantic and YAML
- Support for Kaggle dataset downloads
- Dual sink support (local filesystem and S3)
- Multi-stage Docker build process
- Automated wheel packaging for Glue deployment
- Integration with AWS Parameter Store for production configuration

### Changed
- Refined Glue job script for better error handling
- Simplified package deployment to use wheel instead of source code
- Ensured pydantic_core is found in AWS Glue environment

### Fixed
- Missing dependencies in Glue job configuration
- Environment argument handling in Glue job
- Dependency resolution issues with pydantic_core in AWS Glue

## [0.0.1] - 2026-01-15

### Added
- Basic project structure
- Initial Glue job implementation
- Configuration loading from YAML files
- Docker setup for local development
- CI/CD integration scripts