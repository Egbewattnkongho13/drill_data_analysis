"""
3W Dataset handler (Petrobras 3W v2.0.0).

The archive layout is ``<version>/<class>/<WELL-ID>_<timestamp>.parquet``, so the
handler has two distinct jobs:

1. Staging (driver-side, pure Python): map each entry inside the ZIP to a
   Hive-style key under a staging prefix, e.g.
   ``2.0.0/3/WELL-00001_20170201010207.parquet``
     -> ``<staging_prefix>/folder_class=3/WELL-00001_20170201010207.parquet``
   Spark then discovers ``folder_class`` as a partition column for free.

2. Transformation (executor-side, Spark): validate the sensor schema, cast
   types, and derive the metadata that only exists in the file name.

Nothing here loads the dataset into a single pandas DataFrame — Spark reads the
staged Parquet files in parallel.
"""

import io
import logging
import posixpath
from typing import List, Optional

import pyarrow.parquet as pq
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import LongType

logger = logging.getLogger(__name__)

# Spark writes NULL partition values under this literal and reads them back as
# NULL, so unparseable class folders round-trip correctly instead of needing a
# magic number like -1.
HIVE_NULL_PARTITION = "__HIVE_DEFAULT_PARTITION__"

# 'WELL-00001_20170201010207.parquet' -> 'WELL-00001_20170201010207'
_FILE_STEM_PATTERN = r"([^/]+)\.parquet$"


class ThreedWDataHandler:
    """Stateless handler for 3W Dataset v2.0.0."""

    # The 27 sensor columns in 3W v2.0.0. Any of these that are present are
    # cast to float; absent ones are tolerated and reported.
    EXPECTED_SENSORS: List[str] = [
        "ABER-CKGL", "ABER-CKP", "ESTADO-DHSV", "ESTADO-M1", "ESTADO-M2",
        "ESTADO-PXO", "ESTADO-SDV-GL", "ESTADO-SDV-P", "ESTADO-W1", "ESTADO-W2",
        "ESTADO-XO", "P-ANULAR", "P-JUS-BS", "P-JUS-CKGL", "P-JUS-CKP",
        "P-MON-CKGL", "P-MON-CKP", "P-MON-SDV-P", "P-PDG", "PT-P", "P-TPT",
        "QBS", "QGL", "T-JUS-CKP", "T-MON-CKP", "T-PDG", "T-TPT",
    ]

    # Warn (do not fail) if fewer than this many known sensors are present —
    # it usually means the archive is a different 3W version.
    MIN_EXPECTED_SENSORS = 15

    PARQUET_SUFFIX = ".parquet"

    # ------------------------------------------------------------------
    # Stage 1: staging helpers — pure Python, no Spark, unit-testable
    # ------------------------------------------------------------------

    @staticmethod
    def normalise(entry_path: str) -> str:
        """Normalise a ZIP entry path to POSIX separators.

        ZIP archives may be written with backslashes on Windows; Glue runs on
        Linux, so ``os.path`` would treat the whole string as one file name.
        """
        return entry_path.replace("\\", "/")

    @classmethod
    def is_data_file(cls, entry_path: str) -> bool:
        """True if this ZIP entry is a 3W Parquet data file."""
        normalised = cls.normalise(entry_path)
        if normalised.endswith("/"):
            return False
        if "__MACOSX" in normalised:
            return False
        name = posixpath.basename(normalised)
        # Skip resource forks and other dotfiles bundled into archives.
        if name.startswith("."):
            return False
        return name.lower().endswith(cls.PARQUET_SUFFIX)

    @classmethod
    def folder_class(cls, entry_path: str) -> Optional[int]:
        """Return the class label encoded in the parent folder, or None.

        This is the *instance-level* label (the fault type the whole file is an
        example of). It is deliberately kept separate from the per-row ``class``
        column inside the Parquet, which also encodes transient periods.
        """
        folder = posixpath.basename(posixpath.dirname(cls.normalise(entry_path)))
        try:
            return int(folder)
        except ValueError:
            logger.warning(
                f"Could not parse a class from the parent folder of '{entry_path}'; "
                "staging it under a NULL partition."
            )
            return None

    @classmethod
    def staging_key(cls, entry_path: str, staging_prefix: str) -> str:
        """Map a ZIP entry to its Hive-partitioned key under the staging prefix."""
        normalised = cls.normalise(entry_path)
        filename = posixpath.basename(normalised)
        label = cls.folder_class(normalised)
        partition = HIVE_NULL_PARTITION if label is None else str(label)
        return f"{staging_prefix.rstrip('/')}/folder_class={partition}/{filename}"

    @staticmethod
    def conform_parquet_bytes(data: bytes) -> bytes:
        """Re-encode a 3W Parquet file with microsecond timestamps.

        The files are written by pandas, whose datetime64[ns] becomes Parquet
        TIMESTAMP(NANOS). Spark cannot read that physical type and fails the
        whole read with:

            Illegal Parquet type: INT64 (TIMESTAMP(NANOS,false))

        Coercing to microseconds here means the staged data is readable by any
        engine, rather than depending on spark.sql.legacy.parquet.nanosAsLong,
        which only exists from Spark 3.3.2 onward. Truncation is nanoseconds to
        microseconds on sensor readings sampled per second, so it loses nothing
        real.
        """
        table = pq.read_table(io.BytesIO(data))
        buffer = io.BytesIO()
        pq.write_table(
            table,
            buffer,
            coerce_timestamps="us",
            allow_truncated_timestamps=True,
            compression="snappy",
        )
        return buffer.getvalue()

    # ------------------------------------------------------------------
    # Stage 2: Spark transformation
    # ------------------------------------------------------------------

    def transform(self, df: DataFrame) -> DataFrame:
        """Validate and conform a Spark DataFrame of staged 3W Parquet files.

        Expects ``folder_class`` to be present as a discovered partition column.

        Args:
            df: Raw Spark DataFrame read from the staging prefix.

        Returns:
            The conformed silver-layer DataFrame.
        """
        columns = set(df.columns)

        present_sensors = [c for c in self.EXPECTED_SENSORS if c in columns]
        missing_sensors = [c for c in self.EXPECTED_SENSORS if c not in columns]
        if len(present_sensors) < self.MIN_EXPECTED_SENSORS:
            logger.warning(
                f"Only {len(present_sensors)}/{len(self.EXPECTED_SENSORS)} known 3W "
                f"sensors present — is this a different dataset version? "
                f"Missing: {missing_sensors}"
            )
        elif missing_sensors:
            logger.info(f"Sensors absent from this archive: {missing_sensors}")

        # Sensors to float (half the width of the default double).
        for sensor in present_sensors:
            df = df.withColumn(sensor, F.col(sensor).cast("float"))

        # Metadata that only exists in the file name. input_file_name() is
        # evaluated per row on the executor that read the file.
        file_stem = F.regexp_extract(F.input_file_name(), _FILE_STEM_PATTERN, 1)

        df = df.withColumn("instance_id", file_stem)
        df = df.withColumn("well_id", F.split(F.col("instance_id"), "_").getItem(0))
        df = df.withColumn(
            "source_type",
            F.when(F.col("well_id") == "SIMULATED", F.lit("simulated"))
            .when(F.col("well_id") == "DRAWN", F.lit("hand_drawn"))
            .otherwise(F.lit("real")),
        )

        # 'well' and 'id' may already exist inside the Parquet. Prefer the
        # recorded value and fall back to what the file name tells us.
        if "well" in columns:
            df = df.withColumn(
                "well", F.coalesce(F.col("well").cast("string"), F.col("well_id"))
            )
        else:
            df = df.withColumn("well", F.col("well_id"))

        if "id" in columns:
            df = df.withColumn(
                "id", F.coalesce(F.col("id").cast("string"), F.col("instance_id"))
            )
        else:
            df = df.withColumn("id", F.col("instance_id"))

        # Per-row labels are left exactly as recorded — including NULLs and
        # transient labels (fault class + 100). They are observations, not
        # metadata to be repaired from the folder name.
        for label_column in ("class", "state"):
            if label_column in columns:
                df = df.withColumn(label_column, F.col(label_column).cast("int"))
            else:
                logger.warning(f"No '{label_column}' column in the staged data.")
                df = df.withColumn(label_column, F.lit(None).cast("int"))

        return self._normalise_timestamp(df)

    @staticmethod
    def _normalise_timestamp(df: DataFrame) -> DataFrame:
        """Convert an epoch-millisecond ``timestamp`` column to a real timestamp."""
        if "timestamp" not in df.columns:
            logger.warning("No 'timestamp' column found in the staged 3W data.")
            return df

        dtype = df.schema["timestamp"].dataType
        if isinstance(dtype, LongType):
            return df.withColumn(
                "timestamp", F.timestamp_seconds(F.col("timestamp") / 1000)
            )

        logger.info(
            f"Leaving 'timestamp' as {dtype.simpleString()} — not epoch milliseconds."
        )
        return df

    # ------------------------------------------------------------------
    # Observability
    # ------------------------------------------------------------------

    @staticmethod
    def label_distribution(df: DataFrame) -> List[dict]:
        """Return the row count per (folder_class, class) pair, for logging.

        Surfaces transient labels (e.g. 101-109) and NULL classes rather than
        letting them be silently dropped or overwritten.
        """
        rows = (
            df.groupBy("folder_class", "class")
            .count()
            .orderBy("folder_class", "class")
            .collect()
        )
        return [row.asDict() for row in rows]
