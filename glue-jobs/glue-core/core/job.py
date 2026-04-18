"""
Abstract base class for all AWS Glue jobs in the pipeline.

Every concrete Glue job (ingestion, silver-transform, gold-transform, ...)
must subclass GlueJob and implement setup() and run().

Lifecycle:
    job = MyGlueJob(config)
    job.setup()   # initialise Spark, sinks, sources, etc.
    job.run()     # execute the job logic
"""

import logging
from abc import ABC, abstractmethod

from .config.config import BaseJobConfig


class GlueJob(ABC):
    """Abstract base class that every Glue job must extend."""

    def __init__(self, config: BaseJobConfig) -> None:
        """
        Initialise the job with a validated config.

        Args:
            config: A validated BaseJobConfig (or subclass) instance.
        """
        self.config = config
        self.logger = self._configure_logging()

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _configure_logging(self) -> logging.Logger:
        """Configure a logger for the job using the level set in config."""
        logger = logging.getLogger(self.config.job_name)
        level = getattr(logging, self.config.logging_level.upper(), logging.INFO)
        logger.setLevel(level)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def setup(self) -> None:
        """
        Initialise job resources: Spark context, sinks, sources, clients, etc.
        Called once before run().
        """
        ...

    @abstractmethod
    def run(self) -> None:
        """
        Execute the job logic.
        Called after setup() completes successfully.
        """
        ...

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def execute(self) -> None:
        """
        Convenience method that calls setup() then run() in order.
        Concrete jobs can call this from their __main__ block.
        """
        self.logger.info(
            f"Starting job '{self.config.job_name}' "
            f"[env={self.config.environment}, region={self.config.region}]"
        )
        self.setup()
        self.run()
        self.logger.info(f"Job '{self.config.job_name}' completed successfully.")
