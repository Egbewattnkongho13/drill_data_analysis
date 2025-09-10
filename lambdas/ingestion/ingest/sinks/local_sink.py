import logging
from .base.sink import Sink
import os

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class LocalSink(Sink):
    """
    A sink that saves raw data to the local filesystem.
    """

    def save(self, data: bytes, destination: str) -> None:
        """
        Saves the given raw data to a local file.

        Args:
            data: The raw binary data to save.
            destination: The full path to the output file.
        """
        logger.info(f"Using LocalSink to save data to {destination}")

        try:
            # Ensure the directory exists
            dir_name = os.path.dirname(destination)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)

            with open(destination, "wb") as f:
                f.write(data)

            logger.info(f"Successfully saved data to {destination}")

        except (IOError, OSError) as e:
            logger.error(f"Error saving data to local file: {e}")
