from .base.data import DataSource
from ..sinks.base.sink import Sink
from typing import List
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv
import io


class CrawlerDataHandler(DataSource):
    """
    A data handler for crawling and downloading data from web pages.
    """

    def __init__(self, urls: List[str]):
        """
        Initializes the CrawlerDataHandler with a list of URLs to crawl.

        Args:
            urls: A list of URLs to be crawled.
        """
        self.urls = urls
        print(f"Initialized CrawlerDataHandler with {len(self.urls)} URLs.")

    def download(self, sink: Sink, destination: str) -> None:
        """
        Crawls the configured URLs and saves the extracted data using the provided sink.

        Args:
            sink: The sink to use for saving the data.
            destination: The destination path or key for the sink.
        """
        print(f"Crawling data from URLs: {self.urls}")

        all_csv_data = []
        for url in self.urls:
            try:
                response = requests.get(url)
                response.raise_for_status()  # Raise an exception for bad status codes

                soup = BeautifulSoup(response.content, "html.parser")

                # Find all links ending with .csv
                for link in soup.find_all(
                    "a", href=lambda href: href and href.endswith(".csv")
                ):
                    file_url = urljoin(url, link["href"])
                    try:
                        # Download the content and process it in memory
                        file_response = requests.get(file_url)
                        file_response.raise_for_status()

                        # Use io.StringIO to treat the string content as a file
                        csv_file = io.StringIO(file_response.text)
                        reader = csv.DictReader(csv_file)
                        for row in reader:
                            all_csv_data.append(row)

                        print(f"Successfully downloaded and parsed: {file_url}")
                    except requests.RequestException as e:
                        print(f"ERROR: Could not download file {file_url}. Reason: {e}")
                    except csv.Error as e:
                        print(
                            f"ERROR: Could not parse CSV file {file_url}. Reason: {e}"
                        )

            except requests.RequestException as e:
                print(f"ERROR: Could not crawl {url}. Reason: {e}")

        if all_csv_data:
            print(
                f"Saving {len(all_csv_data)} records to {destination} using {sink.__class__.__name__}."
            )
            sink.save(all_csv_data, destination)
        else:
            print("No CSV files were downloaded, nothing to save.")
        print("Crawling and saving complete.")
