"""
Core library for AWS Glue jobs in the drill data analysis pipeline.

This module provides the foundational components for building and running
AWS Glue jobs, including configuration management, data sources, and sinks.
"""

from .config import (
    BaseJobConfig,
    KaggleSourceConfig,
    LocalSinkConfig,
    S3SinkConfig,
    S3SourceConfig,
    SinkConfig,
    WebSourceConfig,
    load_config,
)
from .handlers.data import DataSource
from .job import GlueJob
from .sinks.base.sink import Sink
from .sinks.local_sink import LocalSink
from .sinks.s3_sink import S3Sink
from .source.base.source import Source
from .source.bronze_source import BronzeSource
from .source.local_source import LocalSource
from .source.silver_source import SilverSource

__all__ = [
    "BaseJobConfig",
    "KaggleSourceConfig",
    "LocalSinkConfig",
    "S3SinkConfig",
    "S3SourceConfig",
    "SinkConfig",
    "WebSourceConfig",
    "load_config",
    "GlueJob",
    "DataSource",
    "Sink",
    "LocalSink",
    "S3Sink",
    "Source",
    "BronzeSource",
    "SilverSource",
    "LocalSource",
]

__version__ = "0.1.0"