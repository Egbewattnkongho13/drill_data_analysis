"""
3W Dataset Handler for processing ZIP files containing Parquet data.

This handler processes ZIP files from S3 containing Parquet files,
extracts metadata from filenames, and prepares data for the silver layer.
"""

import io
import logging
import os
from typing import Iterator, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


class ThreedWDataHandler:
    """Handler for 3W dataset transformation from Bronze to Silver layer."""

    def __init__(self):
        """Initialize the 3W data handler."""
        pass

    def parse_source_type(self, filename: str) -> str:
        """
        Derive source_type from filename prefix.

        Args:
            filename: Name of the parquet file

        Returns:
            Source type: 'simulated', 'hand_drawn', or 'real'
        """
        if filename.startswith("SIMULATED_"):
            return "simulated"
        elif filename.startswith("DRAWN_"):
            return "hand_drawn"
        else:
            return "real"

    def parse_class_from_folder(self, folder_path: str) -> int:
        """
        Derive class from parent folder name.

        Args:
            folder_path: Path to the folder containing the file

        Returns:
            Class as integer (0-8)
        """
        # Get the last folder name from path
        folder_name = os.path.basename(os.path.normpath(folder_path))
        try:
            return int(folder_name)
        except ValueError:
            logger.warning(f"Could not parse class from folder: {folder_path}")
            return -1

    def parse_well_id(self, filename: str) -> str:
        """
        Extract well_id from filename stem.

        Args:
            filename: Name of the parquet file

        Returns:
            Well ID extracted from filename
        """
        # Remove .parquet extension and return stem
        if filename.endswith(".parquet"):
            return filename[:-8]  # Remove '.parquet'
        return filename

    def transform_dataframe(self, df: pd.DataFrame, source_type: str, well_id: str, class_label: int) -> pd.DataFrame:
        """
        Transform a single pandas DataFrame by adding metadata columns and casting types.

        Args:
            df: Input pandas DataFrame
            source_type: Source type derived from filename
            well_id: Well ID derived from filename
            class_label: Class derived from folder name

        Returns:
            Transformed DataFrame with metadata columns and proper types
        """
        # Add metadata columns
        df["source_type"] = source_type
        df["well_id"] = well_id
        df["class"] = class_label

        # Cast sensor columns to float32 (assuming columns 0-6 are sensor data)
        sensor_columns = df.columns[:7]  # First 7 columns assumed to be sensors
        for col_name in sensor_columns:
            df[col_name] = df[col_name].astype("float32")

        # Cast class to Int64
        df["class"] = df["class"].astype("Int64")

        return df

    def process_archive(self, files_iterator: Iterator[Tuple[str, bytes]]) -> pd.DataFrame:
        """
        Process files from a ZIP archive and return combined DataFrame.

        This method uses the BronzeSource.load_archive() iterator to process
        files one at a time without loading the entire archive into memory.

        Args:
            files_iterator: Iterator from BronzeSource.load_archive() yielding
                          (filepath, file_bytes) tuples

        Returns:
            Combined pandas DataFrame with all processed data in silver schema
        """
        logger.info("Processing archive files for 3W transformation")

        dataframes = []
        file_count = 0

        for filepath, file_bytes in files_iterator:
            # Only process Parquet files
            if not filepath.endswith(".parquet"):
                continue

            file_count += 1

            # Extract folder path and filename
            folder_path = os.path.dirname(filepath)
            filename = os.path.basename(filepath)

            # Parse metadata from filename and folder
            source_type = self.parse_source_type(filename)
            class_label = self.parse_class_from_folder(folder_path)
            well_id = self.parse_well_id(filename)

            logger.debug(
                f"Processing file: {filename}, source_type: {source_type}, "
                f"class: {class_label}, well_id: {well_id}"
            )

            # Read parquet bytes into pandas DataFrame
            df = pd.read_parquet(io.BytesIO(file_bytes))

            # Transform the DataFrame
            transformed_df = self.transform_dataframe(df, source_type, well_id, class_label)
            dataframes.append(transformed_df)

        # Combine all DataFrames
        if dataframes:
            combined_df = pd.concat(dataframes, ignore_index=True)
            logger.info(
                f"Successfully processed {file_count} parquet files. "
                f"Combined DataFrame shape: {combined_df.shape}"
            )
            return combined_df
        else:
            logger.warning("No parquet files found in archive")
            return pd.DataFrame()