from .base.data import DataSource
from ..sinks.base.sink import Sink
from typing import List
import os
import json
import time
import re
from pathlib import Path

# In AWS Lambda, only the /tmp directory is writable.
# Set KAGGLE_CONFIG_DIR to a writable directory before importing the Kaggle API.
kaggle_dir = Path("/tmp/.kaggle")
kaggle_dir.mkdir(parents=True, exist_ok=True)
os.environ["KAGGLE_CONFIG_DIR"] = str(kaggle_dir)

import tempfile
from requests.exceptions import ConnectionError, Timeout, RequestException

MAX_RETRIES = 5
RETRY_DELAY_SECONDS = 5

class KaggleDataHandler(DataSource):
    """
    A data handler for downloading raw dataset archives from Kaggle using the official Kaggle API library.
    """

    def __init__(self, urls: List[str], username: str, api_key: str):
        """
        Initializes the KaggleDataHandler and sets up authentication.

        Args:
            urls: A list of URLs pointing to Kaggle datasets.
            username: Your Kaggle username.
            api_key: Your Kaggle API key.
        """
        self.urls = urls
        self._setup_kaggle_credentials(username, api_key)
        from kaggle.api.kaggle_api_extended import KaggleApi
        self.api = KaggleApi()
        # The authentication is now handled by environment variables,
        # and the API is authenticated on import.
        print(f"Initialized KaggleDataHandler with {len(self.urls)} URLs.")

    def _setup_kaggle_credentials(self, username: str, api_key: str):
        """
        Sets the Kaggle API credentials as environment variables.
        """
        os.environ["KAGGLE_USERNAME"] = username
        os.environ["KAGGLE_KEY"] = api_key

    def _retry_download(self, slug: str, path: str, retry_count: int = 0):
        """
        Attempts to download a Kaggle dataset with retries.
        """
        try:
            print(f"Attempting to download '{slug}' (Attempt {retry_count + 1}/{MAX_RETRIES})...")
            # dataset_status = self.api.dataset_status(dataset=slug)
            # print(f"Dataset Status: {dataset_status}")
            self.api.dataset_download_files(slug, path=path, unzip=False)
        except (ConnectionError, Timeout, RequestException) as e:
            if retry_count < MAX_RETRIES - 1:
                print(f"Download failed for '{slug}': {e}. Retrying in {RETRY_DELAY_SECONDS} seconds...")
                time.sleep(RETRY_DELAY_SECONDS)
                self._retry_download(slug, path, retry_count + 1)
            else:
                raise # Re-raise the exception if max retries reached
        except Exception as e:
            raise # Re-raise any other unexpected exceptions

    def download(self, sink: Sink, destination: str) -> None:
        """
        Downloads raw dataset archives from Kaggle and saves them to the provided sink.

        Args:
            sink: The sink to use for saving the data.
            destination: The base destination path/key for the sink.
        """
        print(f"Downloading raw data from Kaggle URLs: {self.urls}")

        for url in self.urls:
            try:
                match = re.search(r"kaggle\.com/datasets/([^/]+/[^/]+)", url)
                if not match:
                    print(f"Could not extract a valid dataset slug from URL: '{url}'. Skipping.")
                    continue
                
                slug = match.group(1)
                output_filename = f"{slug.replace('/', '_')}.zip"
                output_destination = os.path.join(destination, output_filename)

                with tempfile.TemporaryDirectory() as tmpdir:
                    print(f"Downloading dataset '{slug}' to temporary directory...")
                    self._retry_download(slug, tmpdir)
                    
                    # The library downloads as 'dataset-slug.zip', find the actual file
                    downloaded_file_path = os.path.join(tmpdir, f"{slug.split('/')[-1]}.zip")

                    print(f"Saving raw zip file to {output_destination}...")
                    with open(downloaded_file_path, "rb") as f:
                        raw_data = f.read()
                    
                    sink.save(raw_data, output_destination)
                    print(f"Successfully saved {output_filename}.")

            except (ConnectionError, Timeout, RequestException) as e:
                print(f"ERROR: Failed to download from {url} after multiple retries. Final error: {e}")
            except Exception as e:
                print(f"An unexpected error occurred while processing {url}: {e}")

        print("Kaggle raw data download complete.")