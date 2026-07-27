"""
3W Dataset Transform Job for AWS Glue.

Bronze -> Silver in three stages:

  1. STAGE   Unzip each Bronze archive on the driver and write the individual
             Parquet files back to S3 under a Hive-partitioned staging prefix.
             ZIP is not a splittable format, so this step is unavoidably
             single-node — but it only moves bytes, it never parses them.
  2. READ    Point Spark at the staging prefix. Every executor reads its own
             slice of the files in parallel, and ``folder_class`` comes back
             for free as a discovered partition column.
  3. WRITE   Conform the schema and write partitioned Parquet to Silver.

Staging is idempotent: S3Sink skips objects that already exist, so a re-run
after a failure resumes rather than re-uploading the whole archive.
"""

import os 
import sys
from pathlib import Path
from typing import List, Optional

from awsglue.context import GlueContext  # type: ignore
from awsglue.utils import getResolvedOptions  # type: ignore
from pyspark.context import SparkContext
from pyspark.sql import DataFrame, SparkSession

# Import from glue-core
from core import BronzeSource, GlueJob, S3Sink, configure_logging, load_config

# Import transformation components
from transformation import SilverTransformJobConfig, ThreedWDataHandler

PARTITION_COLUMN = "folder_class"


def local_config_path(env: str) -> str:
    """Path to the YAML config. Local and Docker runs only.

    This file does not exist in Glue: dev.yml is gitignored so it is never built
    into the wheel, and the job script is staged alone in /tmp. In Glue the
    config comes from SSM and load_config() returns before it reads any YAML.

    So a FileNotFoundError on this path in Glue does not mean the file is
    missing. It means SSM failed - check the SSM error logged just above it.
    """
    return str(
        Path(__file__).resolve().parent / "transformation" / "envs" / f"{env}.yml"
    )


class SilverTransformJob(GlueJob):
    """Glue job that transforms 3W data from Bronze to Silver layer."""

    def __init__(self, config: SilverTransformJobConfig) -> None:
        super().__init__(config)
        self.config: SilverTransformJobConfig = config
        self.spark: Optional[SparkSession] = None
        self.bronze_source: Optional[BronzeSource] = None
        self.staging_sink: Optional[S3Sink] = None
        self.handler: Optional[ThreedWDataHandler] = None

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def setup(self) -> None:
        """Initialize Spark context, sources, sinks, and transformation handler."""
        sc = SparkContext()
        glue_context = GlueContext(sc)
        self.spark = glue_context.spark_session
        self.logger.info("Spark context initialized.")

        if self.config.source.type != "s3":
            raise ValueError(f"Unsupported source type: {self.config.source.type}")

        self.bronze_source = BronzeSource(
            bucket_name=self.config.source.bucket_name,
            region=self.config.region,
        )
        self.logger.info(
            f"Bronze source initialized: s3://{self.config.source.bucket_name}"
        )

        # Unzipping is decompression, not transformation, so the extracted
        # Parquet files stay in the Bronze bucket alongside the archive.
        self.staging_sink = S3Sink(bucket_name=self.config.source.bucket_name)
        self.logger.info(
            f"Staging sink initialized: "
            f"s3://{self.config.source.bucket_name}/{self.config.staging_prefix}"
        )

        self.handler = ThreedWDataHandler()
        self.logger.info("ThreedWDataHandler initialized.")

    # ------------------------------------------------------------------
    # Stage 1 — resolve and unzip archives
    # ------------------------------------------------------------------

    def _resolve_archive_keys(self) -> List[str]:
        """Resolve the Bronze archives to process from config.key or config.prefix."""
        assert self.bronze_source is not None

        if self.config.source.key:
            self.logger.info(f"Using single archive key: {self.config.source.key}")
            return [self.config.source.key]

        if self.config.source.prefix:
            self.logger.info(
                f"Listing archives under prefix: {self.config.source.prefix}"
            )
            keys = [
                key
                for key in self.bronze_source.list_files(self.config.source.prefix)
                if key.lower().endswith(".zip")
            ]
            self.logger.info(f"Found {len(keys)} archive(s) to process.")
            return keys

        # pre_validate() enforces this, but the job should not silently no-op.
        raise ValueError("Config must define either 'source.key' or 'source.prefix'.")

    def _stage_archive(self, archive_key: str) -> int:
        """Unzip one Bronze archive into the staging prefix. Returns files staged."""
        assert self.bronze_source is not None
        assert self.staging_sink is not None
        assert self.handler is not None

        self.logger.info(f"Staging archive: {archive_key}")
        staged = 0
        skipped = 0

        for entry_path, entry_bytes in self.bronze_source.load_archive(archive_key):
            if not self.handler.is_data_file(entry_path):
                skipped += 1
                continue

            destination = self.handler.staging_key(
                entry_path, self.config.staging_prefix
            )
            # Re-encode timestamps to microseconds; Spark cannot read the
            # nanosecond timestamps pandas wrote into these files.
            conformed = self.handler.conform_parquet_bytes(entry_bytes)
            # S3Sink.save() is a no-op when the object already exists, which
            # makes re-running the job after a failure cheap.
            self.staging_sink.save(conformed, destination)
            staged += 1

            if staged % 500 == 0:
                self.logger.info(f"  ...{staged} files staged from {archive_key}")

        self.logger.info(
            f"Staged {staged} Parquet file(s) from {archive_key} "
            f"({skipped} non-data entries skipped)."
        )
        return staged

    # ------------------------------------------------------------------
    # Stage 2 — read staged Parquet with Spark
    # ------------------------------------------------------------------

    def _staging_root(self) -> str:
        return (
            f"s3://{self.config.source.bucket_name}/"
            f"{self.config.staging_prefix.strip('/')}/"
        )

    def _read_staged(self) -> DataFrame:
        """Read the staging prefix in parallel, discovering folder_class."""
        assert self.spark is not None

        staging_root = self._staging_root()
        self.logger.info(f"Reading staged Parquet from {staging_root}")

        # basePath tells Spark where partition discovery starts, so
        # 'folder_class=3' becomes a column rather than part of the path.
        return (
            self.spark.read.option("basePath", staging_root)
            .option("mergeSchema", "true")
            .parquet(staging_root)
        )

    # ------------------------------------------------------------------
    # Stage 3 — write to Silver
    # ------------------------------------------------------------------

    def _output_path(self) -> str:
        if self.config.sink.type == "s3":
            return f"s3://{self.config.sink.bucket_name}/{self.config.destination}"
        return f"{self.config.sink.path}/{self.config.destination}"

    def _write(self, df: DataFrame, output_path: str) -> None:
        writer = df.write.mode("overwrite").partitionBy(PARTITION_COLUMN)

        if (
            self.config.enable_catalog
            and self.config.catalog_database
            and self.config.catalog_table
        ):
            catalog_name = f"{self.config.catalog_database}.{self.config.catalog_table}"
            self.logger.info(f"Writing to Glue Data Catalog: {catalog_name}")
            writer.format("parquet").option("path", output_path).saveAsTable(
                catalog_name
            )
            self.logger.info(f"Successfully wrote to catalog table: {catalog_name}")
        else:
            writer.parquet(output_path)
            self.logger.info("Data Catalog not enabled - wrote Parquet files only")

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Execute the silver transformation job logic."""
        assert self.spark is not None, "Spark session not initialized. Call setup() first."
        assert self.handler is not None, "Handler not initialized. Call setup() first."

        # STAGE 1: unzip Bronze archives into the staging prefix
        archive_keys = self._resolve_archive_keys()
        if not archive_keys:
            self.logger.warning("No archives found to process. Exiting.")
            return

        total_staged = sum(self._stage_archive(key) for key in archive_keys)
        if total_staged == 0:
            self.logger.warning("No Parquet files were staged from any archive. Exiting.")
            return

        # STAGE 2: distributed read
        raw_df = self._read_staged()
        self.logger.info(f"Staged schema: {raw_df.schema.simpleString()}")

        # STAGE 3: conform and write
        silver_df = self.handler.transform(raw_df)

        if self.config.log_label_distribution:
            # An extra pass over the data — informative during bring-up, but
            # worth disabling once the label semantics are settled.
            for row in self.handler.label_distribution(silver_df):
                self.logger.info(f"Label distribution: {row}")

        output_path = self._output_path()
        self.logger.info(f"Writing partitioned Parquet to silver layer at {output_path}")
        self._write(silver_df, output_path)
        self.logger.info("Silver transform complete.")


if __name__ == "__main__":
    # Set up logging first, so anything load_config() reports about SSM is
    # actually visible in CloudWatch.
    configure_logging()

    # Get job arguments from Glue (catalog args are optional)
    required_args = ["JOB_NAME", "ENVIRONMENT", "BRONZE_BUCKET", "SILVER_BUCKET"]
    args = getResolvedOptions(sys.argv, required_args)

    # Try to get optional catalog arguments
    optional_args = {}
    try:
        optional_args = getResolvedOptions(
            sys.argv,
            ["ENABLE_CATALOG", "CATALOG_DATABASE", "CATALOG_TABLE"]
        )
    except Exception:
        pass  # Optional args not provided, skip

    os.environ["ENVIRONMENT"] = args.get("ENVIRONMENT", "dev")

    # Load configuration. In Glue this resolves entirely from SSM; the YAML path
    # is only the local/Docker fallback and is not expected to exist in cloud.
    env = os.environ["ENVIRONMENT"]
    config = load_config(SilverTransformJobConfig, local_config_path(env))

    # Override config with Terraform-provided values
    config.job_name = args["JOB_NAME"]
    config.source.bucket_name = args["BRONZE_BUCKET"]

    # Override sink bucket name if it's an S3 sink (cloud deployment)
    if config.sink.type == "s3":
        config.sink.bucket_name = args["SILVER_BUCKET"]

    # Override catalog settings if provided
    if optional_args.get("ENABLE_CATALOG", "").lower() == "true":
        config.enable_catalog = True
        config.catalog_database = optional_args.get("CATALOG_DATABASE", "")
        config.catalog_table = optional_args.get("CATALOG_TABLE", "")

    # Execute job
    SilverTransformJob(config).execute()
