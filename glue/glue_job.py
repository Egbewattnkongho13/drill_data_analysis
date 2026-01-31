import sys
import os
import logging
from pyspark.context import SparkContext
from awsglue.context import GlueContext  # type: ignore
from awsglue.utils import getResolvedOptions # type: ignore

# Since this script is run after the 'ingestion_package' has been installed
# in the Glue environment (via --extra-py-files), we can use fully
import pip # type: ignore
pip.main(['list'])  # type: ignore
# qualified imports from the package.
from ingestion.config import load_config, Settings
from ingestion.sinks import S3Sink, LocalSink
from ingestion.handlers import KaggleDataHandler

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def run_job():
    # Initialize GlueContext
    args = getResolvedOptions(sys.argv, ['JOB_NAME', 'ENVIRONMENT'])
    
    sc = SparkContext()
    glueContext = GlueContext(sc)
    spark = glueContext.spark_session
    logger.info(f"Initialized Glue job '{args['JOB_NAME']}' in environment '{args['ENVIRONMENT']}'")

    # Set environment variable for config loading
    os.environ["ENVIRONMENT"] = args.get("ENVIRONMENT", "dev")

    # Load configuration
    settings: Settings = load_config()

    if not settings:
        logger.error("Configuration not loaded. Exiting Glue job.")
        sys.exit(1)

    sink = None
    destination_path = None

    if settings.sink.type == "s3":
        if hasattr(settings.sink, "bucket_name") and settings.sink.bucket_name:
            sink = S3Sink(bucket_name=settings.sink.bucket_name)
            destination_path = settings.destination
        else:
            logger.error("S3 sink is configured but bucket_name is missing. Exiting.")
            sys.exit(1)
            
    elif settings.sink.type == "local":
        sink = LocalSink()
        if hasattr(settings.sink, "path") and settings.sink.path:
            destination_path = settings.sink.path
        else:
            logger.error("Local sink is configured but path is missing. Exiting.")
            sys.exit(1)
    else:
        logger.error(f"Unknown or unsupported sink type: {settings.sink.type}. Exiting.")
        sys.exit(1)

    if not sink:
        logger.error("Sink could not be initialized. Aborting.")
        sys.exit(1)

    # Initialize and run Kaggle data handler
    if settings.kaggle_data_source and settings.kaggle_data_source.urls:
        kaggle_username = os.environ.get("KAGGLE_USERNAME")
        kaggle_api_key = os.environ.get("KAGGLE_KEY")

        if kaggle_username and kaggle_api_key:
            logger.info("Initializing KaggleDataHandler...")
            
            all_urls = settings.kaggle_data_source.urls
            target_urls = []
            if len(all_urls) >= 2:
                logger.info(f"Found {len(all_urls)} URLs. Selecting the second URL for processing.")
                target_urls = [str(all_urls[1])] # Get the second URL (index 1)
            elif all_urls:
                logger.warning(f"Only one URL found: {all_urls[0]}. Processing the first URL as a fallback.")
                target_urls = [str(all_urls[0])]
            else:
                logger.warning("No Kaggle URLs found in the configuration.")

            if target_urls:
                kaggle_handler = KaggleDataHandler(
                    urls=target_urls,
                    username=kaggle_username,
                    api_key=kaggle_api_key,
                )
                kaggle_handler.download(sink, destination_path)
        else:
            logger.warning("KAGGLE_USERNAME or KAGGLE_KEY environment variables not set. Skipping Kaggle download.")
    else:
        logger.info("Kaggle data source is not configured in settings. Skipping.")

    logger.info("Glue ingestion job finished.")

if __name__ == '__main__':
    run_job()
