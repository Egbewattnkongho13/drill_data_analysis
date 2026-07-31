import logging
from typing import Any, Optional

from .base.source import Source

logger = logging.getLogger(__name__)


class SilverSource(Source):
    """
    Source for reading data from the Silver layer in S3.

    The Silver layer contains cleaned and conformed data, typically stored
    as partitioned Parquet files optimized for analytical queries.
    """

    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        """
        Initialize the SilverSource with the S3 bucket name.

        Args:
            bucket_name: The name of the Silver layer S3 bucket.
            region: AWS region where the bucket is located.
        """
        self.bucket_name = bucket_name
        self.region = region
        logger.info(f"Initialized SilverSource for bucket: {self.bucket_name}")

    def load(
        self,
        path: str,
        spark_session: Any,
        file_format: str = "parquet",
        partition_filters: Optional[dict] = None,
        **kwargs
    ) -> Any:
        """
        Load data from the Silver layer.

        Args:
            path: The S3 key/prefix to read from (e.g., 'cleaned-data/dataset/').
            spark_session: The active Spark session.
            file_format: The file format to read (defaults to 'parquet').
            partition_filters: Optional dict of partition column filters
                              (e.g., {'source_type': 'SIMULATED'}).
            **kwargs: Additional Spark read options.

        Returns:
            A Spark DataFrame containing the loaded data.
        """
        s3_path = f"s3://{self.bucket_name}/{path}"
        logger.info(f"Loading {file_format} data from Silver layer: {s3_path}")

        try:
            # Load the data using Spark
            df = spark_session.read.format(file_format).options(**kwargs).load(s3_path)

            # Apply partition filters if provided
            if partition_filters:
                logger.info(f"Applying partition filters: {partition_filters}")
                for column, value in partition_filters.items():
                    df = df.filter(df[column] == value)

            record_count = df.count()
            logger.info(f"Successfully loaded {record_count} records from {s3_path}")

            return df

        except Exception as e:
            logger.error(f"Error loading data from Silver layer at {s3_path}: {e}")
            raise

    def load_partitioned(
        self,
        path: str,
        spark_session: Any,
        partitions: list[str],
        **kwargs
    ) -> Any:
        """
        Load partitioned data from the Silver layer with partition pruning.

        Args:
            path: The S3 key/prefix to read from.
            spark_session: The active Spark session.
            partitions: List of partition columns to maintain.
            **kwargs: Additional Spark read options.

        Returns:
            A Spark DataFrame with partitioned data.
        """
        s3_path = f"s3://{self.bucket_name}/{path}"
        logger.info(
            f"Loading partitioned data from Silver layer: {s3_path} "
            f"(partitions: {partitions})"
        )

        try:
            df = (
                spark_session.read
                .format("parquet")
                .options(**kwargs)
                .load(s3_path)
            )

            logger.info(f"Successfully loaded partitioned data from {s3_path}")
            return df

        except Exception as e:
            logger.error(
                f"Error loading partitioned data from Silver layer at {s3_path}: {e}"
            )
            raise
