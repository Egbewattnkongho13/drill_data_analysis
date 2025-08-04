from .base.sink import Sink
from typing import Any, List
import os
import json


class LocalSink(Sink):
    """
    A sink that saves data to the local filesystem.
    """

    def save(self, data: List[Any], destination: str) -> None:
        """
        Saves the given data to a local file.

        The destination is treated as a directory, and a file named 'data.json'
        will be created inside it.

        Args:
            data: A list of data records to save.
            destination: The path to the directory where the data will be saved.
        """
        print(f"Using LocalSink to save data to directory: {destination}")

        try:
            os.makedirs(destination, exist_ok=True)

            file_path = os.path.join(destination, "data.json")

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            print(f"Successfully saved {len(data)} records to {file_path}")

        except (IOError, OSError) as e:
            print(f"Error saving data to local file: {e}")
