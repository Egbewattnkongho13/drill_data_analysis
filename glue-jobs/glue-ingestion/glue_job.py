"""
Ingestion Glue job — downloads raw data from Kaggle into the Bronze S3 layer.
"""

import os
import sys
from pathlib import Path

from awsglue.context import GlueContext  # type: ignore
from awsglue.utils import getResolvedOptions  # type: ignore
from pyspark.context import SparkContext # type: ignore

from core import GlueJob, LocalSink, S3Sink, load_config
from ingestion.envs.config import IngestionJobConfig
from ingestion.handlers import KaggleDataHandler


class IngestionJob(GlueJob):
    """Glue job that downloads Kaggle datasets and writes them to the Bronze layer."""

    def __init__(self, config: IngestionJobConfig) -> None:
        super().__init__(config)
        self.config: IngestionJobConfig = config
        self.spark = None
        self.handler = None
        self.sink = None

    def setup(self) -> None:
        sc = SparkContext()
        glue_context = GlueContext(sc)
        self.spark = glue_context.spark_session
        self.logger.info("Spark context initialised.")

        if self.config.sink.type == "s3":
            self.sink = S3Sink(bucket_name=self.config.sink.bucket_name)
        else:
            self.sink = LocalSink()
        self.logger.info(f"Sink initialised: {self.config.sink.type}")

        # Validate Kaggle credentials are present
        username = os.environ.get("KAGGLE_USERNAME")
        api_key = os.environ.get("KAGGLE_KEY")

        if not username or not api_key:
            raise ValueError(
                "Missing Kaggle credentials. Set KAGGLE_USERNAME and KAGGLE_KEY environment variables."
            )

        urls = [str(u) for u in self.config.source.urls]
        self.handler = KaggleDataHandler(urls=urls, username=username, api_key=api_key)

    def run(self) -> None:
        destination = (
            self.config.sink.path
            if self.config.sink.type == "local"
            else self.config.destination
        )
        self.handler.download(self.sink, destination)


if __name__ == "__main__":
    args = getResolvedOptions(sys.argv, ["JOB_NAME", "ENVIRONMENT", "BRONZE_BUCKET"])
    os.environ["ENVIRONMENT"] = args.get("ENVIRONMENT", "dev")

    env = os.environ["ENVIRONMENT"]
    config_path = Path(__file__).parent / "ingestion" / "envs" / f"{env}.yml"
    config = load_config(IngestionJobConfig, str(config_path))

    # Override config with Terraform-provided values
    config.job_name = args["JOB_NAME"]
    config.sink.bucket_name = args["BRONZE_BUCKET"]

    IngestionJob(config).execute()
