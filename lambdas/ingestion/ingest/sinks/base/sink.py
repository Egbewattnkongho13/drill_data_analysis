from abc import ABC, abstractmethod
from typing import Any


class Sink(ABC):
    """
    Abstract base class for data sinks. It defines the contract for saving data
    to a specific destination, such as a local file or an S3 bucket.
    """

    @abstractmethod
    def save(self, data: bytes, destination: str) -> None:
        """
        Saves the given data to the specified destination.

        Args:
            data: A list of data records to save.
            destination: A string representing the destination, e.g., a file path or S3 key.
        """
        pass
