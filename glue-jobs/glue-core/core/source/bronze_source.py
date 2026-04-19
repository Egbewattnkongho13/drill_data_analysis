import logging
from typing import Any, Optional

from .base.source import Source

logger = logging.getLogger(__name__)


class BronzeSource(Source):
    """
    Source for reading data from the Bronze layer in S3.

    The Bronze layer contains raw ingested data, which may be in various formats
    (Parquet, CSV, JSON, etc.) depending on the ingestion source.
    """

    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        """
        Initialize the BronzeSource with the S3 bucket name.

        Args:
            bucket_name: The name of the Bronze layer S3 bucket.
            region: AWS region where the bucket is located.
        """
        self.bucket_name = bucket_name
        self.region = region
        logger.info(f"Initialized BronzeSource for bucket: {self.bucket_name}")

    def load(
        self,
        path: str,
        spark_session: Any,
        file_format: str = "parquet",
        **kwargs
    ) -> Any:
        """
        Load data from the Bronze layer.

        Args:
            path: The S3 key/prefix to read from (e.g., 'raw-data/dataset/').
            spark_session: The active Spark session.
            file_format: The file format to read ('parquet', 'csv', 'json', etc.).
            **kwargs: Additional Spark read options (e.g., schema, header, inferSchema).

        Returns:
            A Spark DataFrame containing the loaded data.
        """
        s3_path = f"s3://{self.bucket_name}/{path}"
        logger.info(f"Loading {file_format} data from Bronze layer: {s3_path}")

        try:
            # Use Spark's DataFrameReader with the specified format and options
            df = spark_session.read.format(file_format).options(**kwargs).load(s3_path)

            record_count = df.count()
            logger.info(f"Successfully loaded {record_count} records from {s3_path}")

            return df

        except Exception as e:
            logger.error(f"Error loading data from Bronze layer at {s3_path}: {e}")
            raise

    def list_files(self, prefix: str) -> list[str]:
        """
        List all files in the Bronze layer with the given prefix.

        Args:
            prefix: The S3 prefix to search under.

        Returns:
            A list of S3 keys matching the prefix.
        """
        import boto3

        s3_client = boto3.client("s3", region_name=self.region)

        try:
            response = s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )

            if 'Contents' not in response:
                logger.warning(f"No files found in {self.bucket_name}/{prefix}")
                return []

            files = [obj['Key'] for obj in response['Contents']]
            logger.info(f"Found {len(files)} files in {self.bucket_name}/{prefix}")

            return files

        except Exception as e:
            logger.error(f"Error listing files from Bronze layer: {e}")
            raise
