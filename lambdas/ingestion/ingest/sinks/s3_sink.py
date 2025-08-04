from .base.sink import Sink
from typing import Any, List
import boto3
import json


class S3Sink(Sink):
    """
    A sink that saves data to an Amazon S3 bucket.
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

    def save(self, data: List[Any], destination: str) -> None:
        """
        Saves the given data to a file in the S3 bucket.

        Args:
            data: A list of data records to save.
            destination: The key (file path) within the S3 bucket.
        """
        print(f"Using S3Sink to save data to s3://{self.bucket_name}/{destination}")

        try:
            # Convert the data to a JSON string
            json_data = json.dumps(data, ensure_ascii=False, indent=4)

            # Upload the data to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=destination,
                Body=json_data,
                ContentType="data/json",
            )

            print(
                f"Successfully saved {len(data)} records to s3://{self.bucket_name}/{destination}"
            )

        except Exception as e:
            print(f"Error saving data to S3: {e}")
            # Depending on requirements, you might want to raise the exception
            # raise
