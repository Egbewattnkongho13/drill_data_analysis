"""
3W Dataset Transform Job for AWS Glue.

This job processes ZIP files containing Parquet data from the bronze layer
and writes transformed data to the silver layer using the GlueJob framework.
"""

import os
import sys
from pathlib import Path

from awsglue.context import GlueContext #type: ignore
from awsglue.utils import getResolvedOptions #type: ignore
from pyspark.context import SparkContext

# Import from glue-core
from core import GlueJob, BronzeSource, LocalSink, S3Sink, load_config

# Import transformation components
from transformation import SilverTransformJobConfig, ThreedWDataHandler


class SilverTransformJob(GlueJob):
    """Glue job that transforms 3W data from Bronze to Silver layer."""

    def __init__(self, config: SilverTransformJobConfig) -> None:
        super().__init__(config)
        self.config: SilverTransformJobConfig = config
        self.spark = None
        self.bronze_source = None
        self.sink = None
        self.handler = None

    def setup(self) -> None:
        """Initialize Spark context, sources, sinks, and transformation handler."""
        # Initialize Spark
        sc = SparkContext()
        glue_context = GlueContext(sc)
        self.spark = glue_context.spark_session
        self.logger.info("Spark context initialized.")

        # Initialize Bronze source
        if self.config.source.type == "s3":
            self.bronze_source = BronzeSource(bucket_name=self.config.source.bucket_name)
            self.logger.info(f"Bronze source initialized: s3://{self.config.source.bucket_name}")
        else:
            raise ValueError(f"Unsupported source type: {self.config.source.type}")

        # Initialize sink
        if self.config.sink.type == "s3":
            self.sink = S3Sink(bucket_name=self.config.sink.bucket_name)
        else:
            self.sink = LocalSink()
        self.logger.info(f"Sink initialized: {self.config.sink.type}")

        # Initialize transformation handler
        self.handler = ThreedWDataHandler()
        self.logger.info("ThreedWDataHandler initialized.")

    def run(self) -> None:
        """Execute the silver transformation job logic."""
        # STEP 1: SOURCE - Read ZIP archive from Bronze
        if self.config.source.key:
            # Specific file
            self.logger.info(f"Reading ZIP archive from Bronze: {self.config.source.key}")
            files_iterator = self.bronze_source.load_archive(key=self.config.source.key)
        else:
            # Use prefix + file_pattern (future enhancement)
            raise NotImplementedError(
                "Prefix-based source loading not yet implemented. Use 'key' for specific file."
            )

        # STEP 2: TRANSFORM - Process files with handler
        self.logger.info("Transforming data with ThreedWDataHandler")
        combined_df = self.handler.process_archive(files_iterator)

        if combined_df.empty:
            self.logger.warning("No data to process. Exiting.")
            return

        # STEP 3: Convert pandas DataFrame to Spark DataFrame
        self.logger.info(f"Converting pandas DataFrame to Spark (shape: {combined_df.shape})")
        spark_df = self.spark.createDataFrame(combined_df)

        # STEP 4: SINK - Write partitioned Parquet to silver layer
        if self.config.sink.type == "s3":
            output_path = f"s3://{self.config.sink.bucket_name}/{self.config.destination}"
        else:
            output_path = f"{self.config.sink.path}/{self.config.destination}"

        self.logger.info(f"Writing partitioned Parquet to silver layer at {output_path}")
        spark_df.write.mode("overwrite").partitionBy("source_type").parquet(output_path)

        self.logger.info(f"Successfully wrote {combined_df.shape[0]} rows to silver layer")


if __name__ == "__main__":
    # Get job arguments from Glue
    args = getResolvedOptions(sys.argv, ["JOB_NAME", "ENVIRONMENT", "BRONZE_BUCKET", "SILVER_BUCKET"])
    os.environ["ENVIRONMENT"] = args.get("ENVIRONMENT", "dev")

    # Load configuration
    env = os.environ["ENVIRONMENT"]
    config_path = Path(__file__).parent / "transformation" / "envs" / f"{env}.yml"
    config = load_config(SilverTransformJobConfig, str(config_path))

    # Override config with Terraform-provided values
    config.job_name = args["JOB_NAME"]
    config.source.bucket_name = args["BRONZE_BUCKET"]
    config.sink.bucket_name = args["SILVER_BUCKET"]

    # Execute job
    SilverTransformJob(config).execute()