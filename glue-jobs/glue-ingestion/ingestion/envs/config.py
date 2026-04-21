"""
Ingestion job configuration.

Composes glue-core building blocks into the config for the ingestion Glue job.
The YAML file provides the full config structure and local dev defaults.
In cloud, SSM parameters are merged on top via OmegaConf to override values.
Kaggle credentials are injected as environment variables via inject_secrets()
and are never stored in the config object.
"""

import os
from typing import Dict

from core.config.config import BaseJobConfig, KaggleSourceConfig, SinkConfig


class IngestionJobConfig(BaseJobConfig):
    """Settings for the Kaggle ingestion Glue job."""

    source: KaggleSourceConfig
    sink: SinkConfig
    destination: str

    @classmethod
    def ssm_param_map(cls, env: str) -> Dict[str, str]:
        # Dotted keys mirror the YAML structure — OmegaConf merges them in place.
        # Keys prefixed with '_' are secrets handled by inject_secrets(), not merged.
        return {
            "sink.type":          f"/drill-data-analysis/{env}/sink/type",
            "sink.bucket_name":   f"/drill-data-analysis/{env}/sink/bucket_name",
            "source.urls":        f"/drill-data-analysis/{env}/kaggle/data_source_urls",
            "destination":        f"/drill-data-analysis/{env}/kaggle/destination",
            "_kaggle_username":   f"/drill-data-analysis/{env}/kaggle/username",
            "_kaggle_key":        f"/drill-data-analysis/{env}/kaggle/key",
        }

    @classmethod
    def inject_secrets(cls, fetched: Dict[str, str]) -> None:
        if fetched.get("_kaggle_username"):
            os.environ["KAGGLE_USERNAME"] = fetched["_kaggle_username"]
        if fetched.get("_kaggle_key"):
            os.environ["KAGGLE_KEY"] = fetched["_kaggle_key"]
