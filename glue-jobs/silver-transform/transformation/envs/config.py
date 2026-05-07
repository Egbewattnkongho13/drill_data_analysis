"""
Silver-transform job configuration.

Composes glue-core building blocks into the config for the silver-transform Glue job.
The YAML file provides the full config structure and local dev defaults.
In cloud, SSM parameters are merged on top via OmegaConf to override values.
"""

from typing import Dict

from core.config.config import BaseJobConfig, S3SourceConfig, SinkConfig


class SilverTransformJobConfig(BaseJobConfig):
    """Settings for the 3W silver-transform Glue job."""

    source: S3SourceConfig  # Bronze layer source
    sink: SinkConfig  # Silver layer destination
    destination: str  # Silver layer prefix/path

    @classmethod
    def ssm_param_map(cls, env: str) -> Dict[str, str]:
        """Map dotted config keys to SSM parameter paths.

        Keys mirror the YAML structure — OmegaConf merges them in place.
        Keys prefixed with '_' are secrets handled by inject_secrets(), not merged.
        Note: Bucket names come from --BRONZE_BUCKET and --SILVER_BUCKET job arguments, not SSM
        """
        return {
            "source.type":        f"/drill-data-analysis/{env}/bronze/type",
            "source.prefix":      f"/drill-data-analysis/{env}/bronze/prefix",
            "sink.type":          f"/drill-data-analysis/{env}/silver/sink_type",
            "destination":        f"/drill-data-analysis/{env}/silver/destination",
        }

    def validate(self) -> None:
        """Validate silver-transform specific config rules."""
        # Validate that source has either key or prefix
        if self.source.type == "s3":
            if not self.source.key and not self.source.prefix:
                raise ValueError(
                    "S3 source must have either 'key' (specific file) or 'prefix' (folder) defined"
                )

        # Validate S3 sink has bucket_name
        if self.sink.type == "s3" and not self.sink.bucket_name:
            raise ValueError("S3 sink must have a non-empty bucket_name")
