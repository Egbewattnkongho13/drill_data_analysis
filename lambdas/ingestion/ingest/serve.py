import os
import logging
from .config.config import settings
from .sinks.s3_sink import S3Sink
from .sinks.local_sink import LocalSink
from .handlers.kaggle_datahandler import KaggleDataHandler
from .handlers.crawler_datahandler import CrawlerDataHandler

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def serve(event=None, context=None):
    """
    Main function to orchestrate the data ingestion process.

    This function initializes the necessary sink and data handlers based on the
    loaded configuration, then triggers the data download and storage.
    """
    if not settings:
        logger.error("Configuration not loaded. Exiting.")
        return

    sink = None
    destination_path = None

    if settings.sink.type == "s3":
        if hasattr(settings.sink, "bucket_name") and settings.sink.bucket_name:
            sink = S3Sink(bucket_name=settings.sink.bucket_name)
            destination_path = settings.destination
        else:
            logger.error("S3 sink is configured but bucket_name is missing.")
            return
            
            
    elif settings.sink.type == "local":
        sink = LocalSink()
        if hasattr(settings.sink, "path") and settings.sink.path:
            destination_path = settings.sink.path # Simply use the sink path as the base
        else:
            logger.error("Local sink is configured but path is missing.")
            return

    else:
        logger.error(f"Unknown or unsupported sink type: {settings.sink.type}")
        return

    if not sink:
        logger.error("Sink could not be initialized. Aborting.")
        return

    # Initialize and run Kaggle data handler
    if settings.kaggle_data_source and settings.kaggle_data_source.urls:
        kaggle_username = os.environ.get("KAGGLE_USERNAME")
        kaggle_api_key = os.environ.get("KAGGLE_KEY")

        if kaggle_username and kaggle_api_key:
            logger.info("Initializing KaggleDataHandler...")
            kaggle_handler = KaggleDataHandler(
                urls=[str(url) for url in settings.kaggle_data_source.urls],
                username=kaggle_username,
                api_key=kaggle_api_key,
            )
            kaggle_handler.download(sink, destination_path)
        else:
            logger.warning("KAGGLE_USERNAME or KAGGLE_KEY environment variables not set. Skipping Kaggle download.")
    else:
        logger.info("Kaggle data source is not configured in settings. Skipping.")

    # Initialize and run Crawler data handler
    if settings.crawler_data_source and settings.crawler_data_source.urls:
        logger.info("Initializing CrawlerDataHandler...")
        crawler_handler = CrawlerDataHandler(
            urls=[str(url) for url in settings.crawler_data_source.urls]
        )
        crawler_handler.download(sink, destination_path)
    else:
        logger.info("Crawler data source is not configured in settings. Skipping.")

    logger.info("Ingestion process finished.")
