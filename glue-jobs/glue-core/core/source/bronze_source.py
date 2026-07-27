import logging
import os
import tempfile
import zipfile
from typing import Any, Iterator, Tuple

import boto3
from botocore.exceptions import ClientError

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

            logger.info(f"Successfully loaded Spark DataFrame from {s3_path}")

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
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)

            files = []
            for page in pages:
                if 'Contents' in page:
                    files.extend([obj['Key'] for obj in page['Contents']])

            if not files:
                logger.warning(f"No files found in {self.bucket_name}/{prefix}")
                return []
                
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

        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
            tmp_path = tmp_file.name
            logger.debug(f"Temporary file created at {tmp_path}")

        try:
            # Download the ZIP directly to the local disk instead of RAM 
            logger.info(f"Downloading {s3_path} ZIP archive from S3 to {tmp_path}")
            self.s3_client.download_file(self.bucket_name, key, tmp_path)

            # Open the local ZIP file and yield its contents
            with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                file_list = [f for f in zip_ref.namelist() if not f.endswith('/')]
                logger.info(f"Found {len(file_list)} files in archive")

                for file_info in zip_ref.infolist():
                    # Skip directories
                    if file_info.is_dir():
                        continue

                    # Get full path within ZIP (includes folder structure)
                    filepath = file_info.filename

                    # Read file bytes from local disk into memory one file at a time
                    file_bytes = zip_ref.read(file_info)
                    logger.debug(f"Extracted {filepath} ({len(file_bytes)} bytes)")
                    yield (filepath, file_bytes)

        except ClientError as e:
            # download_file surfaces a missing key as a bare 'HeadObject 404 Not
            # Found' that never names the object. Say which one.
            if e.response.get("Error", {}).get("Code") in ("404", "NoSuchKey"):
                raise FileNotFoundError(
                    f"No such object in the Bronze layer: {s3_path}"
                ) from e
            logger.error(f"Error loading archive from Bronze layer at {s3_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading archive from Bronze layer at {s3_path}: {e}")
            raise
        finally:
            # Clean up the temporary file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                logger.debug(f"Temporary file {tmp_path} deleted")
