"""
Configuration management for the ingestion lambda.

This module uses Pydantic for data validation and python-dotenv to load settings
from a .env file, allowing for a flexible and type-safe configuration system.
"""

import logging
import os
from typing import List, Literal, Union

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError, NoCredentialsError
from omegaconf import OmegaConf
from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    ValidationError,
    field_validator,
)

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- Pydantic Models for Type-Safe Configuration ---


class BaseConfig(BaseModel):
    """Base model with common settings."""

    environment: Literal["dev", "qc", "prod"]


class S3SinkConfig(BaseModel):
    """Configuration for storing data in an S3 bucket."""

    type: Literal["s3"]
    bucket_name: str


class LocalSinkConfig(BaseModel):
    """Configuration for storing data on the local filesystem."""

    type: Literal["local"]
    path: str


SinkConfig = Union[S3SinkConfig, LocalSinkConfig]


class KaggleDataSource(BaseModel):
    """Configuration for downloading data from Kaggle."""

    type: Literal["kaggle"] = "kaggle"
    urls: List[HttpUrl]

    @field_validator("urls", mode="before")
    def parse_urls(cls, v):
        if isinstance(v, str):
            return [HttpUrl(url.strip()) for url in v.split(",") if url.strip()]
        return v


class Settings(BaseConfig):
    """The main settings object for the application."""

    sink: SinkConfig = Field(..., discriminator="type")
    kaggle_data_source: KaggleDataSource
    destination: str


# --- Load Config from environment ---
def load_config(config_path: str = None) -> Settings:
    env = os.environ.get("ENVIRONMENT", "dev")

    # --- Cloud Environment: Attempt to load from AWS Parameter Store ---
    try:
        # Check for AWS credentials with a short timeout to fail fast
        boto3.client("sts", region_name="us-east-1").get_caller_identity()

        logger.info(
            "AWS credentials detected. Attempting to load config from AWS Parameter Store..."
        )
        ssm_client = boto3.client("ssm")

        param_names = {
            "sink_type": f"/drill-data-analysis/{env}/sink/type",
            "sink_bucket": f"/drill-data-analysis/{env}/sink/bucket_name",
            "kaggle_urls": f"/drill-data-analysis/{env}/kaggle/data_source_urls",
            "kaggle_username": f"/drill-data-analysis/{env}/kaggle/username",
            "kaggle_key": f"/drill-data-analysis/{env}/kaggle/key",
        }

        fetched_params = {}
        for key, name in param_names.items():
            try:
                parameter = ssm_client.get_parameter(Name=name, WithDecryption=True)
                fetched_params[key] = parameter["Parameter"]["Value"]
            except ClientError as e:
                if e.response["Error"]["Code"] == "ParameterNotFound":
                    logger.warning(f"SSM Parameter '{name}' not found.")
                    continue
                else:
                    raise

        # Set Kaggle credentials as environment variables for the Kaggle API client
        if fetched_params.get("kaggle_username"):
            os.environ["KAGGLE_USERNAME"] = fetched_params["kaggle_username"]
        if fetched_params.get("kaggle_key"):
            os.environ["KAGGLE_KEY"] = fetched_params["kaggle_key"]

        config_dict = {
            "environment": env,
            "sink": {
                "type": fetched_params.get("sink_type"),
                "bucket_name": fetched_params.get("sink_bucket"),
            },
            "kaggle_data_source": {
                "type": "kaggle",
                "urls": fetched_params.get("kaggle_urls"),
            },
            "destination": "drill-data",  # Default destination in Lambda
        }

        if config_dict["sink"]["type"] is None:
            del config_dict["sink"]

        conf = OmegaConf.create(config_dict)
        logger.info("Successfully loaded configuration from AWS Parameter Store.")
        return Settings(**conf)

    except (NoCredentialsError, EndpointConnectionError, ClientError) as e:
        logger.warning(
            f"Could not connect to AWS. Assuming local environment. Error: {e}"
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred loading from Parameter Store: {e}")

    # --- Local Environment: Fallback to local YAML file ---
    logger.info("Loading config from local YAML file...")
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), f"{env}.yml")

    try:
        conf = OmegaConf.load(config_path)

        # Extract Kaggle credentials from raw YAML BEFORE creating Settings object
        if conf.get("kaggle_username"):
            os.environ["KAGGLE_USERNAME"] = conf.get("kaggle_username")
            logger.info("Set KAGGLE_USERNAME from config file")
        if conf.get("kaggle_key"):
            os.environ["KAGGLE_KEY"] = conf.get("kaggle_key")
            logger.info("Set KAGGLE_KEY from config file")

        # Now create Settings without those fields
        settings = Settings(**conf)
        return settings
    except Exception as e:
        logger.error(
            f"ERROR: Could not load or validate configuration from {config_path}. {e}"
        )
        return None


# --- Global Configuration Object ---
try:
    settings = load_config()
except (FileNotFoundError, ValidationError) as e:
    logger.error(f"ERROR: Could not load or validate configuration. {e}")
    settings = None

if __name__ == "__main__":
    if settings:
        print(settings.model_dump_json(indent=4))
