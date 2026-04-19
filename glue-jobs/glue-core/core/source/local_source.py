import logging
from pathlib import Path
from typing import Any, Optional

from .base.source import Source

logger = logging.getLogger(__name__)


class LocalSource(Source):
    """
    Source for reading data from the local filesystem.

    Primarily used for local development and testing before deploying
    transformation jobs to AWS Glue.
    """

    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize the LocalSource with an optional base path.

        Args:
            base_path: The base directory path for local data storage.
                      If not provided, paths must be absolute.
        """
        self.base_path = Path(base_path) if base_path else None
        logger.info(
            f"Initialized LocalSource"
            f"{f' with base path: {self.base_path}' if self.base_path else ''}"
        )

    def load(
        self,
        path: str,
        spark_session: Any,
        file_format: str = "parquet",
        **kwargs
    ) -> Any:
        """
        Load data from the local filesystem.

        Args:
            path: The relative path (if base_path is set) or absolute path to read from.
            spark_session: The active Spark session.
            file_format: The file format to read ('parquet', 'csv', 'json', etc.).
            **kwargs: Additional Spark read options.

        Returns:
            A Spark DataFrame containing the loaded data.
        """
        # Construct the full path
        if self.base_path:
            full_path = self.base_path / path
        else:
            full_path = Path(path)

        local_path = f"file://{full_path.absolute()}"
        logger.info(f"Loading {file_format} data from local filesystem: {local_path}")

        try:
            # Verify the path exists
            if not full_path.exists():
                raise FileNotFoundError(f"Path does not exist: {full_path}")

            # Use Spark's DataFrameReader with the specified format and options
            df = spark_session.read.format(file_format).options(**kwargs).load(str(full_path))

            record_count = df.count()
            logger.info(f"Successfully loaded {record_count} records from {local_path}")

            return df

        except Exception as e:
            logger.error(f"Error loading data from local filesystem at {local_path}: {e}")
            raise

    def list_files(self, path: str, pattern: str = "*") -> list[Path]:
        """
        List all files in the local directory matching the pattern.

        Args:
            path: The directory path to search.
            pattern: Glob pattern to match files (default: '*').

        Returns:
            A list of Path objects matching the pattern.
        """
        if self.base_path:
            full_path = self.base_path / path
        else:
            full_path = Path(path)

        try:
            if not full_path.exists():
                logger.warning(f"Path does not exist: {full_path}")
                return []

            files = list(full_path.glob(pattern))
            logger.info(f"Found {len(files)} files in {full_path}")

            return files

        except Exception as e:
            logger.error(f"Error listing files from local filesystem: {e}")
            raise
