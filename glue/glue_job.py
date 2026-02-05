import zipfile
import tempfile
import shutil
import sys
import os
import logging

# Configure logging for early script execution
# Ensure this logger is not re-configured later if it's already set up
# from the current module's logger setup.
_early_logger = logging.getLogger(__name__)
if not _early_logger.handlers:
    _early_logger.setLevel(logging.INFO)
    _early_handler = logging.StreamHandler()
    _early_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    _early_handler.setFormatter(_early_formatter)
    _early_logger.addHandler(_early_handler)

# --- Workaround for Pydantic C-extension in AWS Glue ---
# Detect if running in AWS Glue environment
is_glue_env = os.environ.get("GLUE_JOB_NAME") is not None or \
              os.environ.get("AWS_REGION") is not None

if is_glue_env:
    _early_logger.info("Detected AWS Glue environment. Attempting to unpack C-extensions.")
    temp_dir = None
    try:
        # Find the job bundle zip in sys.path
        found_bundle_zip = None
        for path_entry in sys.path:
            if zipfile.is_zipfile(path_entry) and "ingestion-bundle" in path_entry:
                found_bundle_zip = path_entry
                break
        
        if found_bundle_zip:
            _early_logger.info(f"Found job bundle zip: {found_bundle_zip}")
            # Create a temporary directory in /tmp (the only writable location in Glue)
            temp_dir = tempfile.mkdtemp(dir="/tmp")
            with zipfile.ZipFile(found_bundle_zip, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Insert this temporary directory at the beginning of sys.path
            sys.path.insert(0, temp_dir)
            _early_logger.info(f"Unpacked {found_bundle_zip} to {temp_dir} and added to sys.path.")

            # It's good practice to also update LD_LIBRARY_PATH for native libs
            current_ld_library_path = os.environ.get("LD_LIBRARY_PATH", "")
            if temp_dir not in current_ld_library_path:
                os.environ["LD_LIBRARY_PATH"] = f"{temp_dir}:{current_ld_library_path}"
                _early_logger.info(f"Updated LD_LIBRARY_PATH to include {temp_dir}")
        else:
            _early_logger.warning("Could not find 'ingestion-bundle' zip in sys.path. C-extensions might not be unpacked.")
    except Exception as e:
        _early_logger.error(f"Error during C-extension unpacking in Glue: {e}")
        # Clean up temp_dir if an error occurred during unpacking, to avoid leaving junk
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        # Re-raise to prevent job from continuing with a broken environment
        raise

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

# Configure logging (main logger, separate from early_logger if needed, or unify)
logger = logging.getLogger(__name__) # Re-using __name__ for the main script logger
logger.setLevel(logging.INFO)
# Ensure the main logger has a handler if the early logger didn't set one for __main__
if not logger.handlers:
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
