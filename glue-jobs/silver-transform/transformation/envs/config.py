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

    # Where the job unzips Bronze archives before Spark reads them. Lives in the
    # Bronze bucket: unzipping is decompression, not transformation.
    staging_prefix: str = "_unzipped/dev/3w_dataset"

    # Log the row count per (folder_class, class) pair before writing. Costs an
    # extra pass over the data; useful while the label semantics are unsettled.
    log_label_distribution: bool = False

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
            "staging_prefix":     f"/drill-data-analysis/{env}/bronze/staging_prefix",
            "sink.type":          f"/drill-data-analysis/{env}/silver/sink_type",
            "destination":        f"/drill-data-analysis/{env}/silver/destination",
        }

    def pre_validate(self) -> None:
        """Validate silver-transform specific config rules."""
        # Validate that source has either key or prefix
        if self.source.type == "s3":
            if not self.source.key and not self.source.prefix:
                raise ValueError(
                    "S3 source must have either 'key' (specific file) or 'prefix' (folder) defined"
                )

        # The staging prefix must not sit inside the archive prefix the job
        # scans, or a re-run would try to unzip its own extracted Parquet files.
        staging = self.staging_prefix.strip("/")
        if not staging:
            raise ValueError("staging_prefix must be a non-empty S3 prefix")
        source_prefix = self.source.prefix.strip("/")
        if source_prefix and staging.startswith(f"{source_prefix}/"):
            raise ValueError(
                f"staging_prefix ('{self.staging_prefix}') must not live under "
                f"source.prefix ('{self.source.prefix}') — the job would re-scan its "
                "own extracted output."
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
