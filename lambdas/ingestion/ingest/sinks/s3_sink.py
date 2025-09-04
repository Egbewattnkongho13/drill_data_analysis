from .base.sink import Sink
import boto3
from botocore.exceptions import ClientError
import mimetypes
import logging

logger = logging.getLogger(__name__)
class S3Sink(Sink):
    """
    A sink that saves raw data to an Amazon S3 bucket.
    """

    def __init__(self, bucket_name: str, assume_role_arn: str):
        """
        Initializes the S3Sink with the target bucket name.

        Args:
            bucket_name: The name of the S3 bucket.
        """
        self.bucket_name = bucket_name
        self.s3_client = self._get_s3_client(assume_role_arn)
        logger.info(f"Initialized S3Sink for bucket: {self.bucket_name}")
    
    def _get_s3_client(self, assume_role_arn: str):
        if assume_role_arn:
            logger.info("Assuming role for S3 client")
            sts_client = boto3.client('sts')
            try:
                assumed_role_object=sts_client.assume_role(
                    RoleArn=assume_role_arn,
                    RoleSessionName="LambdaAssumeRoleSession"
                )
                credentials = assumed_role_object['Credentials']
                return boto3.client(
                    's3',
                    aws_access_key_id=credentials['AccessKeyId'],
                    aws_secret_access_key=credentials['SecretAccessKey'],
                    aws_session_token=credentials['SessionToken']
                )
            except ClientError as e:
                logger.error(f"Error assuming role {assume_role_arn}: {e}")
                raise 
        else:
            logger.info("Using default Lambda execution role for s3 operations.")
            return boto3.client('s3')

                

    def save(self, data: bytes, destination: str) -> None:
        """
        Saves the given raw data to a file in the S3 bucket.

        Args:
            data: The raw binary data to save.
            destination: The key (file path) within the S3 bucket.
        """
        logger.info(f"Using S3Sink to save raw data to s3://{self.bucket_name}/{destination}")

        try:
            logger.info(f"Saving data to s3://{self.bucket_name}/{destination}")
            # Guess the content type from the filename
            content_type = mimetypes.guess_type(destination)
            if content_type is None:
                content_type = "application/octet-stream" # Default for unknown binary

            # Upload the data to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=destination,
                Body=data,
                ContentType=content_type,
            )

            logger.info(f"Successfully saved raw data to s3://{self.bucket_name}/{destination}")

        except Exception as e:
            logger.error(f"Error saving data to S3: {e}")
            raise

