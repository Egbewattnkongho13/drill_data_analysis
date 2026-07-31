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

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def configure_logging(level: str = "INFO") -> None:
    """Attach a handler to the ROOT logger. Idempotent.

    Every module in glue-core and in the job packages logs through
    logging.getLogger(__name__). Those loggers have no handler of their own, so
    without a root handler Python falls back to logging.lastResort, which drops
    everything below WARNING - all the INFO diagnostics vanish.

    Call this at the very start of a job's __main__, before load_config(), so
    that config-loading errors are visible too.
    """
    root = logging.getLogger()
    if not any(getattr(h, "_glue_core", False) for h in root.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        handler._glue_core = True  # type: ignore[attr-defined]
        root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))


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
        """Return the job logger, ensuring root logging is set up.

        The handler lives on the root logger, not here: a handler on both would
        print every job message twice, since this logger propagates.
        """
        configure_logging(self.config.logging_level)
        logger = logging.getLogger(self.config.job_name)
        logger.setLevel(
            getattr(logging, self.config.logging_level.upper(), logging.INFO)
        )
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
