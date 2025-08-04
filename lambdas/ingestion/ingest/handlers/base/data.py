from abc import ABC, abstractmethod
from ...sinks.base.sink import Sink

class DataSource(ABC):
    """
    Abstract base class for data sources. It defines the contract for downloading
    data from a specific source, such as Kaggle or a web crawler.
    """

    @abstractmethod
    def download(self, sink: Sink, destination: str) -> None:
        """
        Downloads data from the source and saves it using the provided sink.

        Args:
            sink: An instance of a Sink implementation (e.g., S3Sink, LocalSink).
            destination: The destination path or key to be used by the sink.
        """
        pass