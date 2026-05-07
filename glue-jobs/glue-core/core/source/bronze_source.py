import io
import logging
import zipfile
from typing import Any, Iterator, Optional, Tuple

import boto3

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
        self.s3_client = boto3.client("s3", region_name=region)
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
        try:
            response = self.s3_client.list_objects_v2(
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

    def load_archive(self, key: str) -> Iterator[Tuple[str, bytes]]:
        """
        Load and decompress a ZIP archive from the Bronze layer.

        This method is used when bronze data is stored as ZIP files containing
        multiple data files (common for Kaggle datasets).

        Args:
            key: The S3 key for the ZIP file (e.g., 'drill-data/dataset.zip').

        Yields:
            Tuples of (filepath_in_zip, file_bytes) for each file in the archive.

        Example:
            >>> source = BronzeSource('my-bronze-bucket')
            >>> for filepath, data in source.load_archive('data/3w.zip'):
            ...     if filepath.endswith('.parquet'):
            ...         df = pd.read_parquet(io.BytesIO(data))
        """
        s3_path = f"s3://{self.bucket_name}/{key}"
        logger.info(f"Loading ZIP archive from Bronze layer: {s3_path}")

        try:
            # Download ZIP from S3
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            zip_bytes = response['Body'].read()

            archive_size_mb = len(zip_bytes) / (1024**2)
            logger.info(f"Downloaded archive size: {archive_size_mb:.2f} MB")

            # Iterate through files in the ZIP
            with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zip_ref:
                file_list = [f for f in zip_ref.namelist() if not f.endswith('/')]
                logger.info(f"Found {len(file_list)} files in archive")

                for file_info in zip_ref.infolist():
                    # Skip directories
                    if file_info.is_dir():
                        continue

                    # Get full path within ZIP (includes folder structure)
                    filepath = file_info.filename

                    # Read file bytes
                    file_bytes = zip_ref.read(file_info)

                    logger.debug(f"Extracted {filepath} ({len(file_bytes)} bytes)")

                    yield (filepath, file_bytes)

        except Exception as e:
            logger.error(f"Error loading archive from Bronze layer at {s3_path}: {e}")
            raise
