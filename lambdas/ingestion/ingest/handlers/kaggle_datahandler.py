from .base.data import DataSource
from ..sinks.base.sink import Sink
from typing import List
import os
import subprocess
import tempfile
import csv
import pandas as pd  # type: ignore


class KaggleDataHandler(DataSource):
    """
    A data handler for downloading datasets from Kaggle.
    """

    def __init__(self, urls: List[str]):
        """
        Initializes the KaggleDataHandler with a list of Kaggle dataset URLs.

        Args:
            urls: A list of URLs pointing to Kaggle datasets.
        """
        self.urls = urls
        print(f"Initialized KaggleDataHandler with {len(self.urls)} URLs.")

    def download(self, sink: Sink, destination: str) -> None:
        """
        Downloads data from the configured Kaggle URLs and saves it using the provided sink.

        Args:
            sink: The sink to use for saving the data.
            destination: The destination path or key for the sink.
        """
        print(f"Downloading data from Kaggle URLs: {self.urls}")

        all_data = []
        for url in self.urls:
            try:
                slug = "/".join(url.split("/")[-2:])

                with tempfile.TemporaryDirectory() as tmpdir:
                    print(f"Downloading dataset '{slug}' to '{tmpdir}'...")
                    subprocess.run(
                        [
                            "kaggle",
                            "datasets",
                            "download",
                            "-d",
                            slug,
                            "-p",
                            tmpdir,
                            "--unzip",
                        ],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    print(f"Successfully downloaded and unzipped '{slug}'.")

                    # --- Smart File Processing Logic ---
                    for filename in os.listdir(tmpdir):
                        file_path = os.path.join(tmpdir, filename)
                        if filename.endswith(".xlsx"):
                            xls = pd.ExcelFile(file_path)
                            for sheet_name in xls.sheet_names:
                                df = pd.read_excel(xls, sheet_name=sheet_name)
                                df["source_sheet"] = (
                                    sheet_name  # Add sheet name as context
                                )
                                all_data.extend(df.to_dict("records"))
                            print(f"Processed Excel file: {filename}")

                        elif filename.endswith(".csv"):
                            with open(
                                file_path, "r", encoding="utf-8", errors="ignore"
                            ) as f:
                                reader = csv.DictReader(f)
                                for row in reader:
                                    row["source_file"] = (
                                        filename  # Add filename as context
                                    )
                                    all_data.append(row)
                            print(f"Processed CSV file: {filename}")

            except subprocess.CalledProcessError as e:
                print(
                    f"ERROR: Failed to download dataset from {url}. Kaggle CLI error: {e.stderr}"
                )
            except Exception as e:
                print(f"An unexpected error occurred while processing {url}: {e}")

        if all_data:
            print(
                f"Saving {len(all_data)} records to {destination} using {sink.__class__.__name__}."
            )
            sink.save(all_data, destination)
        else:
            print("No data was downloaded, nothing to save.")
        print("Kaggle data download and save complete.")
