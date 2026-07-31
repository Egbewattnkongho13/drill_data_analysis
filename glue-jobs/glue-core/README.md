# glue-core

Core library for AWS Glue jobs in the drill data analysis pipeline.

## Overview

Provides foundational components for building AWS Glue jobs:

- **`GlueJob`**: Abstract base class with lifecycle methods (`setup()`, `run()`, `execute()`)
- **Configuration**: Type-safe config management with Pydantic + OmegaConf (SSM + YAML)
- **Sinks**: S3 and local filesystem storage abstractions
- **Sources**: S3, local, and web data source abstractions
- **Handlers**: Base classes for data processing

## Usage

```python
from core import GlueJob, load_config, BaseJobConfig

class MyJob(GlueJob):
    def setup(self):
        # Initialize Spark, sinks, sources
        pass
    
    def run(self):
        # Execute job logic
        pass

config = load_config(MyJobConfig, "config.yml")
MyJob(config).execute()
```

## Installation

Installed as a path dependency in glue job modules:

```toml
[tool.poetry.dependencies]
glue-core = { path = "../glue-core", develop = true }
```
