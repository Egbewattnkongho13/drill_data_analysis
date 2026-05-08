"""
Configuration management for AWS Glue jobs.

This module provides the base config model and reusable source/sink building
blocks for glue-core. Each individual Glue job defines its own Settings
subclass by composing these building blocks and adding job-specific fields.
"""

import logging
import os
from typing import Annotated, Dict, List, Literal, Type, TypeVar, Union

import boto3
import yaml
from botocore.exceptions import ClientError, EndpointConnectionError, NoCredentialsError
from omegaconf import OmegaConf
from pydantic import BaseModel, Field, HttpUrl, ValidationError, field_validator

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# Base config — fields common to every Glue job
# ---------------------------------------------------------------------------

class BaseJobConfig(BaseModel):
    """Base model with common settings inherited by every Glue job config."""

    environment: Literal["dev", "qc", "prod"] = "dev"
    job_name: str = "glue-job"
    region: str = "us-east-1"
    logging_level: str = "INFO"
    timeout_seconds: int = 3600
    retry_attempts: int = 3

    @classmethod
    def ssm_param_map(cls, env: str) -> Dict[str, str]:
        """Return a mapping of dotted-config-key → SSM parameter path.

        Keys mirror the YAML structure using dot notation (e.g. 'sink.bucket_name').
        Keys prefixed with '_' are treated as secrets: fetched from SSM and passed
        to inject_secrets(), but NOT merged into the config object.
        Return an empty dict to skip SSM loading entirely.
        """
        return {}

    @classmethod
    def inject_secrets(cls, fetched: Dict[str, str]) -> None:
        """Inject sensitive SSM values (e.g. credentials) as environment variables.

        Override in job configs that need credentials. The base implementation
        does nothing. Called with the full fetched dict (including _ prefixed keys).
        """
        pass

    def validate(self) -> None:
        """Perform semantic validation beyond Pydantic type checks.

        Override in each job config to add job-specific rules, e.g.:
          - S3 sink must have a non-empty bucket_name
          - Source URLs must be reachable
        Raise ValueError with a clear message if validation fails.
        """
        pass


# ---------------------------------------------------------------------------
# Sink building blocks
# ---------------------------------------------------------------------------

class S3SinkConfig(BaseModel):
    """Configuration for writing data to an S3 bucket."""

    type: Literal["s3"]
    bucket_name: str = ""  # Optional - can be overridden by job arguments


class LocalSinkConfig(BaseModel):
    """Configuration for writing data to the local filesystem."""

    type: Literal["local"]
    path: str


SinkConfig = Annotated[Union[S3SinkConfig, LocalSinkConfig], Field(discriminator="type")]


# ---------------------------------------------------------------------------
# Source building blocks
# ---------------------------------------------------------------------------

class KaggleSourceConfig(BaseModel):
    """Configuration for reading data from Kaggle."""

    type: Literal["kaggle"] = "kaggle"
    urls: List[HttpUrl]

    @field_validator("urls", mode="before")
    @classmethod
    def parse_urls(cls, v):
        if isinstance(v, str):
            return [url.strip() for url in v.split(",") if url.strip()]
        return v


class WebSourceConfig(BaseModel):
    """Configuration for reading data from web URLs."""

    type: Literal["web"] = "web"
    urls: List[HttpUrl]
    headers: dict = {}
    auth_required: bool = False

    @field_validator("urls", mode="before")
    @classmethod
    def parse_urls(cls, v):
        if isinstance(v, str):
            return [url.strip() for url in v.split(",") if url.strip()]
        return v


class S3SourceConfig(BaseModel):
    """Configuration for reading data from S3."""

    type: Literal["s3"] = "s3"
    bucket_name: str = ""  # Optional - can be overridden by job arguments
    prefix: str = ""
    file_pattern: str = "*"
    key: str | None = None  # specific file key; overrides prefix+file_pattern when set


# ---------------------------------------------------------------------------
# Generic config loader — SSM first, YAML fallback
# ---------------------------------------------------------------------------

T = TypeVar("T", bound=BaseJobConfig)


def _fetch_ssm_params(param_map: Dict[str, str], region: str) -> Dict[str, str]:
    """Fetch a batch of SSM parameters. Missing params are skipped."""
    ssm = boto3.client("ssm", region_name=region)
    fetched: Dict[str, str] = {}
    for dotted_key, path in param_map.items():
        try:
            result = ssm.get_parameter(Name=path, WithDecryption=True)
            fetched[dotted_key] = result["Parameter"]["Value"]
        except ClientError as e:
            if e.response["Error"]["Code"] == "ParameterNotFound":
                logger.warning(f"SSM parameter not found: {path}")
            else:
                raise
    return fetched


def load_config(config_cls: Type[T], config_path: str) -> T:
    """Load and validate a job config — cloud (SSM) first, local (YAML) fallback.

    Cloud path (AWS credentials present + ssm_param_map non-empty):
        1. Fetch SSM parameters using the dotted-key map defined by the job.
        2. Call inject_secrets() so credentials become env vars (never stored in config).
        3. Build an OmegaConf dict from the fetched values using dot notation.
        4. Validate with Pydantic → return typed config.

    Local path (no credentials or empty ssm_param_map):
        1. Load config_path (YAML) via OmegaConf.
        2. Validate with Pydantic → return typed config.

    Args:
        config_cls: A BaseJobConfig subclass with ssm_param_map / inject_secrets / validate.
        config_path: Path to the YAML fallback config file (used in local dev only).

    Returns:
        A validated instance of config_cls.
    """
    env = os.environ.get("ENVIRONMENT", "dev")
    region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

    param_map = config_cls.ssm_param_map(env)

    # --- Cloud path: SSM first ---
    if param_map:
        try:
            boto3.client("sts", region_name=region).get_caller_identity()
            logger.info("AWS credentials found. Loading config from SSM Parameter Store.")

            fetched = _fetch_ssm_params(param_map, region)

            # Inject secrets (credentials etc.) as environment variables
            config_cls.inject_secrets(fetched)

            # Build OmegaConf dict from dotted SSM keys (skipping secret keys)
            conf = OmegaConf.create({"environment": env})
            for dotted_key, value in fetched.items():
                if not dotted_key.startswith("_"):
                    OmegaConf.update(conf, dotted_key, value, merge=True)

            config = config_cls(**OmegaConf.to_container(conf, resolve=True))
            config.validate()
            logger.info(f"Config loaded and validated from SSM for {config_cls.__name__}.")
            return config

        except (NoCredentialsError, EndpointConnectionError):
            logger.warning("No AWS credentials. Falling back to local YAML config.")
        except ClientError as e:
            logger.warning(f"SSM error ({e}). Falling back to local YAML config.")

    # --- Local path: YAML fallback ---
    logger.info(f"Loading config from YAML: {config_path}")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    conf = OmegaConf.load(config_path)

    try:
        config = config_cls(**OmegaConf.to_container(conf, resolve=True))
        config.validate()
        logger.info(f"Config loaded and validated from YAML for {config_cls.__name__}.")
        return config
    except ValidationError as e:
        logger.error(f"Config validation failed for {config_cls.__name__}: {e}")
        raise
