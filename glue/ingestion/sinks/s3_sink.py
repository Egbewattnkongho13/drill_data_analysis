import logging
import mimetypes

import boto3
from botocore.exceptions import ClientError

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
        self.s3_client = boto3.client("s3")
        logger.info(f"Initialized S3Sink for bucket: {self.bucket_name}")

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
                # Some other error occurred
                logger.error(f"Error checking for object existence: {e}")
                return  # Do not proceed if we can't verify existence

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

            logger.info(
                f"Successfully saved raw data to s3://{self.bucket_name}/{destination}"
            )

        except Exception as e:
            logger.error(f"Error saving data to S3: {e}")


# import hashlib
# import logging
# import mimetypes
# from typing import Dict, Optional

# import boto3
# from botocore.exceptions import ClientError

# from .base.sink import Sink

# # Configure logging
# logger = logging.getLogger(__name__)


# class DataValidationError(Exception):
#     """Raised when data validation fails."""

#     pass


# class S3Sink(Sink):
#     """
#     A sink that saves raw data to an Amazon S3 bucket with integrity checks.
#     """

#     def __init__(
#         self,
#         bucket_name: str,
#         min_file_size: int = 1,  # Minimum file size in bytes
#         max_file_size: Optional[int] = None,  # Maximum file size in bytes
#         validate_content: bool = True,
#         enable_checksum: bool = True,
#         overwrite_on_corruption: bool = True,
#     ):
#         """
#         Initializes the S3Sink with the target bucket name and validation options.

#         Args:
#             bucket_name: The name of the S3 bucket.
#             min_file_size: Minimum acceptable file size in bytes (default: 1).
#             max_file_size: Maximum acceptable file size in bytes (optional).
#             validate_content: Whether to perform content validation (default: True).
#             enable_checksum: Whether to store and verify checksums (default: True).
#             overwrite_on_corruption: Whether to overwrite corrupted files (default: True).
#         """
#         self.bucket_name = bucket_name
#         self.s3_client = boto3.client("s3")
#         self.min_file_size = min_file_size
#         self.max_file_size = max_file_size
#         self.validate_content = validate_content
#         self.enable_checksum = enable_checksum
#         self.overwrite_on_corruption = overwrite_on_corruption
#         logger.info(f"Initialized S3Sink for bucket: {self.bucket_name}")

#     def _validate_data(self, data: bytes, destination: str) -> None:
#         """
#         Validates the data before upload.

#         Args:
#             data: The raw binary data to validate.
#             destination: The destination key for context in error messages.

#         Raises:
#             DataValidationError: If validation fails.
#         """
#         # Check if data is empty or None
#         if data is None:
#             raise DataValidationError(f"Data is None for destination: {destination}")

#         if len(data) == 0:
#             raise DataValidationError(f"Data is empty for destination: {destination}")

#         # Check minimum file size
#         if len(data) < self.min_file_size:
#             raise DataValidationError(
#                 f"Data size ({len(data)} bytes) is below minimum ({self.min_file_size} bytes) "
#                 f"for destination: {destination}"
#             )

#         # Check maximum file size if specified
#         if self.max_file_size and len(data) > self.max_file_size:
#             raise DataValidationError(
#                 f"Data size ({len(data)} bytes) exceeds maximum ({self.max_file_size} bytes) "
#                 f"for destination: {destination}"
#             )

#         # Validate content based on file type
#         if self.validate_content:
#             self._validate_content_type(data, destination)

#         logger.debug(f"Data validation passed for {destination} ({len(data)} bytes)")

#     def _validate_content_type(self, data: bytes, destination: str) -> None:
#         """
#         Validates data content based on file type signatures.

#         Args:
#             data: The raw binary data to validate.
#             destination: The destination key to determine expected type.

#         Raises:
#             DataValidationError: If content validation fails.
#         """
#         # Get file extension
#         extension = destination.lower().split(".")[-1] if "." in destination else None

#         # Define magic bytes for common file types
#         magic_bytes_map = {
#             "pdf": [b"%PDF"],
#             "jpg": [b"\xff\xd8\xff"],
#             "jpeg": [b"\xff\xd8\xff"],
#             "png": [b"\x89PNG\r\n\x1a\n"],
#             "gif": [b"GIF87a", b"GIF89a"],
#             "zip": [b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"],
#             "json": [b"{", b"["],
#             "xml": [b"<?xml", b"<"],
#             "csv": [],  # CSV has no magic bytes, will skip
#             "txt": [],  # Text files have no magic bytes
#         }

#         if extension in magic_bytes_map and magic_bytes_map[extension]:
#             expected_signatures = magic_bytes_map[extension]
#             is_valid = any(
#                 data.startswith(signature) for signature in expected_signatures
#             )

#             if not is_valid:
#                 raise DataValidationError(
#                     f"Content validation failed for {destination}: "
#                     f"Data does not match expected {extension.upper()} format"
#                 )

#             logger.debug(f"Content type validation passed for {destination}")

#     def _compute_checksum(self, data: bytes) -> str:
#         """
#         Computes MD5 checksum of the data.

#         Args:
#             data: The raw binary data.

#         Returns:
#             The MD5 checksum as a hexadecimal string.
#         """
#         return hashlib.md5(data).hexdigest()

#     def _verify_existing_file(self, destination: str, expected_checksum: str) -> bool:
#         """
#         Verifies if an existing file in S3 is corrupted.

#         Args:
#             destination: The S3 key to check.
#             expected_checksum: The expected MD5 checksum.

#         Returns:
#             True if file exists and is valid, False if corrupted or doesn't exist.
#         """
#         try:
#             # Get object metadata
#             response = self.s3_client.head_object(
#                 Bucket=self.bucket_name, Key=destination
#             )

#             # Check if ETag (which is MD5 for simple uploads) matches
#             existing_etag = response.get("ETag", "").strip('"')

#             if existing_etag == expected_checksum:
#                 logger.info(
#                     f"Object s3://{self.bucket_name}/{destination} exists and is valid. "
#                     f"Checksum matches: {expected_checksum}"
#                 )
#                 return True
#             else:
#                 logger.warning(
#                     f"Object s3://{self.bucket_name}/{destination} exists but checksum mismatch. "
#                     f"Expected: {expected_checksum}, Found: {existing_etag}"
#                 )
#                 return False

#         except ClientError as e:
#             if e.response["Error"]["Code"] == "404":
#                 logger.info(
#                     f"Object not found at s3://{self.bucket_name}/{destination}"
#                 )
#                 return False
#             else:
#                 logger.error(f"Error checking object existence: {e}")
#                 raise

#     def _download_and_verify(self, destination: str, expected_size: int) -> bool:
#         """
#         Downloads existing file and verifies it's complete and not corrupted.

#         Args:
#             destination: The S3 key to verify.
#             expected_size: The expected file size in bytes.

#         Returns:
#             True if file is valid, False otherwise.
#         """
#         try:
#             # Get the object
#             response = self.s3_client.get_object(
#                 Bucket=self.bucket_name, Key=destination
#             )

#             # Read the content
#             existing_data = response["Body"].read()

#             # Verify size
#             if len(existing_data) != expected_size:
#                 logger.warning(
#                     f"Size mismatch for s3://{self.bucket_name}/{destination}. "
#                     f"Expected: {expected_size}, Found: {len(existing_data)}"
#                 )
#                 return False

#             # Verify it's not truncated/corrupted by checking content
#             try:
#                 self._validate_data(existing_data, destination)
#                 logger.info(
#                     f"Existing file at s3://{self.bucket_name}/{destination} is valid"
#                 )
#                 return True
#             except DataValidationError as e:
#                 logger.warning(f"Existing file validation failed: {e}")
#                 return False

#         except ClientError as e:
#             logger.error(f"Error downloading file for verification: {e}")
#             return False
#         except Exception as e:
#             logger.error(f"Unexpected error during verification: {e}")
#             return False

#     def save(
#         self, data: bytes, destination: str, metadata: Optional[Dict[str, str]] = None
#     ) -> None:
#         """
#         Saves the given raw data to a file in the S3 bucket with integrity checks.

#         Args:
#             data: The raw binary data to save.
#             destination: The key (file path) within the S3 bucket.
#             metadata: Optional metadata to attach to the S3 object.

#         Raises:
#             DataValidationError: If data validation fails.
#         """
#         logger.info(f"Preparing to save data to s3://{self.bucket_name}/{destination}")

#         # Step 1: Validate the incoming data
#         try:
#             self._validate_data(data, destination)
#         except DataValidationError as e:
#             logger.error(f"Data validation failed: {e}")
#             raise

#         # Step 2: Compute checksum if enabled
#         checksum = None
#         if self.enable_checksum:
#             checksum = self._compute_checksum(data)
#             logger.debug(f"Computed checksum for {destination}: {checksum}")

#         # Step 3: Check if file exists and verify integrity
#         should_upload = True
#         try:
#             if self.enable_checksum and checksum:
#                 # Quick check using ETag/checksum
#                 if self._verify_existing_file(destination, checksum):
#                     logger.info(
#                         f"Valid file already exists at s3://{self.bucket_name}/{destination}. Skipping upload."
#                     )
#                     should_upload = False
#             else:
#                 # Fallback: check existence and verify by downloading
#                 self.s3_client.head_object(Bucket=self.bucket_name, Key=destination)
#                 logger.info(
#                     f"Object exists at s3://{self.bucket_name}/{destination}. Verifying integrity..."
#                 )

#                 if self._download_and_verify(destination, len(data)):
#                     logger.info("Existing file is valid. Skipping upload.")
#                     should_upload = False
#                 elif self.overwrite_on_corruption:
#                     logger.warning("Existing file is corrupted. Will overwrite.")
#                     should_upload = True
#                 else:
#                     logger.error(
#                         "Existing file is corrupted but overwrite is disabled."
#                     )
#                     raise DataValidationError(f"Corrupted file exists at {destination}")

#         except ClientError as e:
#             if e.response["Error"]["Code"] == "404":
#                 logger.info("Object not found. Proceeding with upload.")
#                 should_upload = True
#             else:
#                 logger.error(f"Error checking for object existence: {e}")
#                 raise

#         # Step 4: Upload if needed
#         if should_upload:
#             try:
#                 # Guess the content type from the filename
#                 content_type, _ = mimetypes.guess_type(destination)
#                 if content_type is None:
#                     content_type = "application/octet-stream"

#                 # Prepare metadata
#                 s3_metadata = metadata or {}
#                 if self.enable_checksum and checksum:
#                     s3_metadata["data-checksum"] = checksum
#                 s3_metadata["data-size"] = str(len(data))

#                 # Upload the data to S3
#                 put_params = {
#                     "Bucket": self.bucket_name,
#                     "Key": destination,
#                     "Body": data,
#                     "ContentType": content_type,
#                 }

#                 if s3_metadata:
#                     put_params["Metadata"] = s3_metadata

#                 self.s3_client.put_object(**put_params)

#                 logger.info(
#                     f"Successfully saved data to s3://{self.bucket_name}/{destination} "
#                     f"({len(data)} bytes, checksum: {checksum})"
#                 )

#                 # Step 5: Verify the upload
#                 if self.enable_checksum and checksum:
#                     if not self._verify_existing_file(destination, checksum):
#                         logger.error(f"Upload verification failed for {destination}")
#                         raise DataValidationError("Uploaded file verification failed")
#                     logger.info(f"Upload verified successfully for {destination}")

#             except ClientError as e:
#                 logger.error(f"S3 client error saving data: {e}")
#                 raise
#             except Exception as e:
#                 logger.error(f"Unexpected error saving data to S3: {e}")
#                 raise
