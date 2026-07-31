"""
Ingestion module for the Kaggle data ingestion Glue job.

Exports only the Kaggle-specific data handler. All base classes,
sinks, and sources are provided by glue-core.
"""

from .handlers import KaggleDataHandler

__all__ = ["KaggleDataHandler"]
