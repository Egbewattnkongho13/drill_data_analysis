"""
Silver-transform job configuration.

Composes glue-core building blocks into the config for the silver-transform Glue job.
The YAML file provides the full config structure and local dev defaults.
In cloud, SSM parameters are merged on top via OmegaConf to override values.
"""

from typing import Dict, Optional

from core.config.config import BaseJobConfig, S3SourceConfig, SinkConfig


class SilverTransformJobConfig(BaseJobConfig):
    """Settings for the 3W silver-transform Glue job."""

    source: S3SourceConfig  # Bronze layer source
    sink: SinkConfig  # Silver layer destination
    destination: str  # Silver layer prefix/path

    # Data Catalog configuration
    enable_catalog: bool = False  # Whether to register output in Glue Data Catalog
    catalog_database: Optional[str] = None  # Glue database name
    catalog_table: Optional[str] = None  # Glue table name

    @classmethod
    def ssm_param_map(cls, env: str) -> Dict[str, str]:
        """Map dotted config keys to SSM parameter paths.

        Keys mirror the YAML structure — OmegaConf merges them in place.
        Keys prefixed with '_' are secrets handled by inject_secrets(), not merged.
        Note: Bucket names come from --BRONZE_BUCKET and --SILVER_BUCKET job arguments, not SSM
        Note: Both source.key and source.prefix are available - use key for specific files, prefix for pattern matching
        """
        return {
            "source.type":        f"/drill-data-analysis/{env}/bronze/type",
            "source.key":         f"/drill-data-analysis/{env}/bronze/key",
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

        # Validate Data Catalog configuration
        if self.enable_catalog:
            if not self.catalog_database:
                raise ValueError(
                    "catalog_database is required when enable_catalog is True"
                )
            if not self.catalog_table:
                raise ValueError(
                    "catalog_table is required when enable_catalog is True"
                )

            # Validate naming conventions
            if not self.catalog_database.replace("_", "").isalnum():
                raise ValueError(
                    f"Invalid catalog_database name: '{self.catalog_database}'. "
                    "Must contain only alphanumeric characters and underscores."
                )
            if not self.catalog_table.replace("_", "").isalnum():
                raise ValueError(
                    f"Invalid catalog_table name: '{self.catalog_table}'. "
                    "Must contain only alphanumeric characters and underscores."
                )
