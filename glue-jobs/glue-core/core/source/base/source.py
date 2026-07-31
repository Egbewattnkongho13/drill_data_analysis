from abc import ABC, abstractmethod
from typing import Any


class Source(ABC):
    """
    Abstract base class for data sources in transformation jobs.

    Sources are responsible for reading data from data lake layers
    (Bronze, Silver) and returning it in a format suitable for processing.
    """

    @abstractmethod
    def load(self, path: str, spark_session: Any, **kwargs) -> Any:
        """
        Load data from the specified path and return a Spark DataFrame.

        Args:
            path: The S3 path or local path to read from (e.g., 's3://bucket/prefix/').
            spark_session: The active Spark session to use for reading data.
            **kwargs: Additional keyword arguments specific to the source implementation
                     (e.g., file format, schema, read options).

        Returns:
            A Spark DataFrame containing the loaded data.
        """
        pass
