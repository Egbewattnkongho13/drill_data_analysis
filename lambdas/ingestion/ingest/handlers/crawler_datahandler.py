import logging
from .base.data import DataSource
from ..sinks.base.sink import Sink
from typing import List
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import time
from requests.exceptions import ConnectionError, Timeout, RequestException

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

MAX_RETRIES = 5
RETRY_DELAY_SECONDS = 5

class CrawlerDataHandler(DataSource):
    """
    A data handler for crawling and downloading raw files from web pages.
    """

    def __init__(self, urls: List[str]):
        """
        Initializes the CrawlerDataHandler with a list of URLs to crawl.

        Args:
            urls: A list of URLs to be crawled.
        """
        self.urls = urls
        logger.info(f"Initialized CrawlerDataHandler with {len(self.urls)} URLs.")

    def _retry_get_request(self, url: str, retry_count: int = 0) -> requests.Response:
        """
        Attempts to perform a GET request with retries.
        """
        try:
            logger.info(f"Attempting to GET '{url}' (Attempt {retry_count + 1}/{MAX_RETRIES})...")
            response = requests.get(url)
            response.raise_for_status()
            return response
        except (ConnectionError, Timeout, RequestException) as e:
            if retry_count < MAX_RETRIES - 1:
                logger.warning(f"Request failed for '{url}': {e}. Retrying in {RETRY_DELAY_SECONDS} seconds...")
                time.sleep(RETRY_DELAY_SECONDS)
                return self._retry_get_request(url, retry_count + 1)
            else:
                logger.error(f"Could not get {url} after {MAX_RETRIES} attempts. Reason: {e}")
                raise

    def download(self, sink: Sink, destination: str) -> None:
        """
        Crawls the configured URLs and saves the discovered files to the provided sink.

        Args:
            sink: The sink to use for saving the data.
            destination: The base destination path or key for the sink.
        """
        logger.info(f"Crawling for raw data from URLs: {self.urls}")

        for url in self.urls:
            try:
                response = self._retry_get_request(url)
                soup = BeautifulSoup(response.content, "html.parser")

                # Find all links ending with .csv
                for link in soup.find_all("a", href=lambda href: href and href.endswith(".csv")):
                    file_url = urljoin(url, link["href"])
                    try:
                        # Download the raw content
                        file_response = self._retry_get_request(file_url)

                        # Define a unique name for the output file
                        output_filename = os.path.basename(file_url)
                        output_destination = os.path.join(destination, output_filename)

                        logger.info(f"Saving raw file to {output_destination}...")
                        sink.save(file_response.content, output_destination)
                        logger.info(f"Successfully saved {output_filename}.")

                    except requests.RequestException as e:
                        logger.error(f"Failed to download linked file {file_url} from page {url}. Final error: {e}")
                    except Exception as e:
                        logger.error(f"An unexpected error occurred while downloading {file_url}: {e}")

            except requests.RequestException as e:
                logger.error(f"Failed to crawl page {url} after multiple retries. Final error: {e}")
            except Exception as e:
                logger.error(f"An unexpected error occurred while crawling {url}: {e}")

        logger.info("Crawling and saving complete.")
