import logging
import mimetypes
import time
import ssl

import boto3
from botocore.exceptions import ClientError, ConnectionClosedError, SSLError
from botocore.config import Config

from .base.sink import Sink

# Configure logging
logger = logging.getLogger(__name__)


class S3Sink(Sink):
    """
    A sink that saves raw data to an Amazon S3 bucket.
    """

    def __init__(self, bucket_name: str):
        """
        Initializes the S3Sink with the target bucket name.

        Args:
            bucket_name: The name of the S3 bucket.
        """
        self.bucket_name = bucket_name

        # Configure S3 client with enhanced retry settings and timeouts
        config = Config(
            retries={'max_attempts': 5, 'mode': 'adaptive'},
            connect_timeout=60,
            read_timeout=60,
            # Add connection pool settings for better connection management
            max_pool_connections=50,
        )

        self.s3_client = boto3.client("s3", config=config, region_name="us-east-1")  # Specify region if needed
        logger.info(f"Initialized S3Sink for bucket: {self.bucket_name}")

    def _upload_with_retry(self, data: bytes, destination: str, max_retries: int = 5) -> bool:
        """
        Upload data to S3 with enhanced retry logic for transient network issues.

        Args:
            data: The raw binary data to save.
            destination: The key (file path) within the S3 bucket.
            max_retries: Maximum number of retry attempts.

        Returns:
            bool: True if upload succeeded, False otherwise.
        """
        for attempt in range(max_retries):
            try:
                # Guess the content type from the filename
                content_type, _ = mimetypes.guess_type(destination)
                if content_type is None:
                    content_type = "application/octet-stream"  # Default for unknown binary

                # Upload the data to S3
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=destination,
                    Body=data,
                    ContentType=content_type,
                )
                return True

            except (SSLError, ConnectionClosedError, ssl.SSLEOFError) as e:
                logger.warning(f"S3 upload attempt {attempt + 1} failed with SSL/connection error: {e}")
                if attempt < max_retries - 1:
                    # Enhanced exponential backoff with jitter for SSL errors
                    sleep_time = (2 ** attempt) * 2 + (attempt * 0.5)
                    logger.info(f"Retrying in {sleep_time:.1f} seconds...")
                    time.sleep(sleep_time)

                    # For SSL protocol errors, recreate the client to get fresh connections
                    if isinstance(e, (SSLError, ssl.SSLEOFError)):
                        logger.info("Recreating S3 client due to SSL error")
                        config = Config(
                            retries={'max_attempts': 5, 'mode': 'adaptive'},
                            connect_timeout=60,
                            read_timeout=60,
                            max_pool_connections=50,
                        )
                        self.s3_client = boto3.client("s3", config=config)
                else:
                    logger.error(f"All retry attempts exhausted for S3 upload: {e}")
                    return False

            except Exception as e:
                logger.error(f"Unexpected error during S3 upload: {e}")
                return False

        return False

    def save(self, data: bytes, destination: str) -> None:
        """
        Saves the given raw data to a file in the S3 bucket if it does not already exist.

        Args:
            data: The raw binary data to save.
            destination: The key (file path) within the S3 bucket.
        """
        logger.info(
            f"Checking for existing object at s3://{self.bucket_name}/{destination}"
        )

        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=destination)
            logger.info(
                f"Object s3://{self.bucket_name}/{destination} already exists. Skipping."
            )
            return
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                # Object does not exist, so we can proceed with the upload
                logger.info(
                    f"Object not found. Proceeding with upload to s3://{self.bucket_name}/{destination}"
                )
            else:
                # Some other error occurred (like 403 Forbidden)
                error_msg = f"Error checking for object existence: {e}"
                logger.error(error_msg)
                raise  # Re-raise the exception so the job fails properly

        try:
            # Upload with retry logic
            success = self._upload_with_retry(data, destination)

            if success:
                logger.info(
                    f"Successfully saved raw data to s3://{self.bucket_name}/{destination}"
                )
            else:
                logger.error(
                    f"Failed to save raw data to s3://{self.bucket_name}/{destination} after retries. "
                    f"This may be due to network connectivity issues, SSL/TLS configuration problems, "
                    f"or AWS S3 service availability issues. Check network connectivity and try again."
                )

        except Exception as e:
            logger.error(f"Error saving data to S3: {e}")
            raise  # Re-raise the exception so the job fails properly

