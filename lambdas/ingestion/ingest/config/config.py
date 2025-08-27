"""
Configuration management for the ingestion lambda.

This module uses Pydantic for data validation and python-dotenv to load settings
from a .env file, allowing for a flexible and type-safe configuration system.
"""

import os
from pathlib import Path
from typing import Literal, Union, List
import yaml # Add this import

from omegaconf import OmegaConf 
from pydantic import BaseModel, Field, DirectoryPath, HttpUrl, ValidationError, field_validator

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

  

class CrawlerDataSource(BaseModel):
    """Configuration for crawling and downloading data from web URLs."""

    type: Literal["crawler"] = "crawler"
    urls: List[HttpUrl]

    @field_validator("urls", mode="before")
    def parse_urls(cls, v):
        if isinstance(v, str):
            return [HttpUrl(url.strip()) for url in v.split(",") if url.strip()]
        return v

   




class Settings(BaseConfig):
    """The main settings object for the application."""

    sink: SinkConfig = Field(..., discriminator="type")
    kaggle_data_source: KaggleDataSource = Field(..., discriminator="type")
    crawler_data_source: CrawlerDataSource = Field(..., discriminator="type")
    destination: str


# --- Load Config from environment ---
def load_config(config_path: str = None) -> Settings:
    if config_path is None:
        env = os.environ.get("ENVIRONMENT", "dev")
        config_path = f"ingest/config/{env}.yml"

    try:
        conf = OmegaConf.load(config_path)
        # OmegaConf automatically resolves ${oc.env:VAR_NAME} expressions
        # when the config is loaded.
        # Environment variables set in template.yaml will override values
        # in dev.yml if they have the same key.

        return Settings(**conf)
    except Exception as e:
        print(f"ERROR: Could not load or validate configuration. {e}")
        return None


# --- Global Configuration Object ---

try:
    settings = load_config()
except (FileNotFoundError, ValidationError) as e:
    print(f"ERROR: Could not load or validate configuration. {e}")
    settings = None


if __name__ == "__main__":
    if settings:
        print(settings.model_dump_json(indent=4))

# kaggle | crawler types should always be setup by default to kaggle and crawler
# they should resolve if the urls are there