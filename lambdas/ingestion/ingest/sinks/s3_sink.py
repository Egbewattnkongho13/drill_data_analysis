from .base.sink import Sink
import boto3
import mimetypes

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
        print(f"Initialized S3Sink for bucket: {self.bucket_name}")

    def save(self, data: bytes, destination: str) -> None:
        """
        Saves the given raw data to a file in the S3 bucket.

        Args:
            data: The raw binary data to save.
            destination: The key (file path) within the S3 bucket.
        """
        print(f"Using S3Sink to save raw data to s3://{self.bucket_name}/{destination}")

        try:
            # Guess the content type from the filename
            content_type, _ = mimetypes.guess_type(destination)
            if content_type is None:
                content_type = "application/octet-stream" # Default for unknown binary

            # Upload the data to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=destination,
                Body=data,
                ContentType=content_type,
            )

            print(
                f"Successfully saved raw data to s3://{self.bucket_name}/{destination}"
            )

        except Exception as e:
            print(f"Error saving data to S3: {e}")

