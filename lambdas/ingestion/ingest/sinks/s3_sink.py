from .base.sink import Sink
import boto3
import mimetypes
from botocore.exceptions import ClientError
import logging
from typing import Any, IO, Union
import os
import requests

# Configure logging
logger = logging.getLogger(__name__)

class S3Sink(Sink):
    """
    A sink that saves raw data to an Amazon S3 bucket.
    It can handle both small in-memory data (bytes) and large file streams.
    """

    def __init__(self, bucket_name: str, multipart_threshold_mb: int = 50, chunk_size_mb: int = 10):
        """
        Initializes the S3Sink.

        Args:
            bucket_name: The name of the S3 bucket.
            multipart_threshold_mb: The file size in MB above which multipart upload is used.
            chunk_size_mb: The chunk size in MB for multipart uploads.
        """
        self.bucket_name = bucket_name
        self.s3_client = boto3.client("s3")
        self.multipart_threshold = multipart_threshold_mb * 1024 * 1024
        self.chunk_size = chunk_size_mb * 1024 * 1024
        logger.info(f"Initialized S3Sink for bucket: {self.bucket_name}")

    def _get_stream_details(self, stream: Union[requests.Response, IO]) -> tuple[object, int]:
        """Determines the iterator and size from a stream object."""
        file_size = None
        if isinstance(stream, requests.Response):
            file_size = int(stream.headers.get('content-length', 0))
            iterator = stream.iter_content(chunk_size=self.chunk_size)
        elif hasattr(stream, 'read'): # File-like object
            # Get file size if available
            if hasattr(stream, 'seekable') and stream.seekable():
                original_pos = stream.tell()
                stream.seek(0, os.SEEK_END)
                file_size = stream.tell()
                stream.seek(original_pos, os.SEEK_SET)

            def file_chunk_iterator(f, c_size):
                while True:
                    chunk = f.read(c_size)
                    if not chunk:
                        break
                    yield chunk
            iterator = file_chunk_iterator(stream, self.chunk_size)
        else:
            raise TypeError(f"Unsupported stream type: {type(stream)}")
        
        return iterator, file_size

    def _upload_multipart(self, iterator: object, destination: str, content_type: str):
        """Handles the S3 multipart upload."""
        mpu = self.s3_client.create_multipart_upload(Bucket=self.bucket_name, Key=destination, ContentType=content_type)
        upload_id = mpu['UploadId']
        
        parts = []
        part_number = 1
        
        try:
            for chunk in iterator:
                if chunk:
                    logger.debug(f"Uploading part {part_number} for {destination} with {len(chunk)} bytes.")
                    part = self.s3_client.upload_part(
                        Bucket=self.bucket_name,
                        Key=destination,
                        PartNumber=part_number,
                        UploadId=upload_id,
                        Body=chunk
                    )
                    parts.append({'ETag': part['ETag'], 'PartNumber': part_number})
                    part_number += 1
            
            logger.info(f"Completing multipart upload for {destination}...")
            self.s3_client.complete_multipart_upload(
                Bucket=self.bucket_name,
                Key=destination,
                UploadId=upload_id,
                MultipartUpload={'Parts': parts}
            )
            logger.info(f"Successfully uploaded {destination} using multipart upload.")

        except Exception as e:
            logger.error(f"Error during multipart upload for {destination}. Aborting. Error: {e}")
            self.s3_client.abort_multipart_upload(
                Bucket=self.bucket_name,
                Key=destination,
                UploadId=upload_id
            )
            raise

    def save(self, data: Any, destination: str) -> None:
        """
        Saves data to S3. Handles bytes for small files and streams for large files.

        Args:
            data: The data to save. Can be bytes, a requests.Response object, or a file-like object.
            destination: The key (file path) within the S3 bucket.
        """
        logger.info(f"Checking for existing object at s3://{self.bucket_name}/{destination}")
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=destination)
            logger.info(f"Object s3://{self.bucket_name}/{destination} already exists. Skipping.")
            return
        except ClientError as e:
            if e.response["Error"]["Code"] != "404":
                logger.error(f"Error checking for object existence: {e}")
                raise

        content_type, _ = mimetypes.guess_type(destination)
        if content_type is None:
            content_type = "application/octet-stream"

        try:
            is_stream = isinstance(data, requests.Response) or hasattr(data, 'read')

            if is_stream:
                iterator, file_size = self._get_stream_details(data)
                
                if file_size is None or file_size > self.multipart_threshold:
                    logger.info(f"File size is {file_size} bytes. Using multipart upload for {destination}.")
                    self._upload_multipart(iterator, destination, content_type)
                else:
                    logger.info(f"File size is {file_size} bytes. Using direct upload for {destination}.")
                    # Read the entire stream content for direct upload
                    if isinstance(data, requests.Response):
                         body = data.content
                    else: # File-like object
                        body = data.read()
                    self.s3_client.put_object(
                        Bucket=self.bucket_name,
                        Key=destination,
                        Body=body,
                        ContentType=content_type,
                    )

            elif isinstance(data, bytes):
                logger.info(f"Data is bytes. Using direct upload for {destination}.")
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=destination,
                    Body=data,
                    ContentType=content_type,
                )
            else:
                raise TypeError(f"Unsupported data type for S3 sink: {type(data)}")

            logger.info(
                f"Successfully saved raw data to s3://{self.bucket_name}/{destination}"
            )

        except Exception as e:
            logger.error(f"Error saving data to S3: {e}")
            # The multipart upload helper already aborts, but we might need to
            # handle errors from direct uploads or pre-flight checks.
            raise

