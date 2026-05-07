# Glue 3W Transform Job

This package contains the AWS Glue job for transforming 3W drill data from ZIP files.

## Overview

The 3W transform job processes ZIP files containing Parquet data from the bronze layer and writes the transformed data to the silver layer. The job:

1. Streams ZIP files from S3 into memory
2. Processes Parquet files within the ZIP without writing to disk
3. Extracts metadata from filenames (source_type, class, well_id)
4. Transforms and enriches data
5. Writes partitioned Parquet files to the silver layer

## Package Structure

```
glue-threedw-job/
├── threed_w_transform_job.py    # Main Glue job script
├── ingestion/
│   └── handlers/
│       └── threed_w_handler.py  # 3W data processing logic
├── tests/                       # Unit tests
│   └── test_threed_w_handler.py
├── pyproject.toml              # Package definition
└── README.md                   # This file
```

## Dependencies

This package depends on:
- `glue-core`: Shared components for all Glue jobs
- `pandas`: Data processing
- `pyarrow`: Parquet file handling

## Building

To build the wheel package:

```bash
poetry install
poetry build
```

## Testing

To run tests:

```bash
poetry run pytest
```