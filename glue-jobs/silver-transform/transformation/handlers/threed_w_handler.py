"""
3W Dataset handler (Petrobras 3W v2.0.0).

The archive layout is ``<version>/<class>/<WELL-ID>_<timestamp>.parquet``, so the
handler has two distinct jobs:

1. Staging (driver-side, pure Python): map each entry inside the ZIP to a
   Hive-style key under a staging prefix, e.g.
   ``2.0.0/3/WELL-00001_20170201010207.parquet``
     -> ``<staging_prefix>/folder_class=3/WELL-00001_20170201010207.parquet``
   Spark then discovers ``folder_class`` as a partition column for free.
   Per-file checks that need the file name (source family, sensor count) belong
   here, where they are free and can fail before 2,228 objects are written.

2. Transformation (executor-side, Spark): quality-control the sensor values,
   cast types, and derive the metadata that only exists in the file name.

Silver is lossless: no row is ever filtered. Values that fail a QC rule are set
to NULL (or clamped) and the reason is recorded in a parallel ``qc_<sensor>``
column, so a reviewer can see what changed without going back to Bronze.

Nothing here loads the dataset into a single pandas DataFrame — Spark reads the
staged Parquet files in parallel.
"""

import io
import logging
import posixpath
import re
from typing import Dict, List, Optional, Tuple

import pyarrow.parquet as pq
from pyspark.sql import Column, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, FloatType, TimestampType

logger = logging.getLogger(__name__)

# Spark writes NULL partition values under this literal and reads them back as
# NULL, so unparseable class folders round-trip correctly instead of needing a
# magic number like -1.
HIVE_NULL_PARTITION = "__HIVE_DEFAULT_PARTITION__"

# 'WELL-00001_20170201010207.parquet' -> 'WELL-00001_20170201010207'
_FILE_STEM_PATTERN = r"([^/]+)\.parquet$"

# Source families. Real instances are 'WELL-<digits>'; the two synthetic
# families use a fixed stem. Anything else is unrecognised and must fail loudly
# rather than default to 'real': every headline metric in this experiment is
# real-instances-only, so one synthetic file silently classified as real
# contaminates the primary result with no visible symptom.
REAL_WELL_PATTERN = r"^WELL-\d+$"
SIMULATED_WELL_ID = "SIMULATED"
HAND_DRAWN_WELL_ID = "DRAWN"

SOURCE_REAL = "real"
SOURCE_SIMULATED = "simulated"
SOURCE_HAND_DRAWN = "hand_drawn"

# QC flag vocabulary. NULL means the value passed through untouched.
QC_NOT_A_NUMBER = "NOT_A_NUMBER"  # NaN in the source -> NULL
QC_SENTINEL = "SENTINEL"  # instrument error code -> NULL
QC_OUT_OF_RANGE = "OUT_OF_RANGE"  # outside physical bounds -> NULL
QC_CLAMPED = "CLAMPED"  # outside bounds but bounded by definition -> clamped


class ThreedWDataHandler:
    """Stateless handler for 3W Dataset v2.0.0."""

    # The 27 sensor columns in 3W v2.0.0. Any of these that are present are
    # quality-controlled and cast to float; absent ones are tolerated.
    EXPECTED_SENSORS: List[str] = [
        "ABER-CKGL", "ABER-CKP", "ESTADO-DHSV", "ESTADO-M1", "ESTADO-M2",
        "ESTADO-PXO", "ESTADO-SDV-GL", "ESTADO-SDV-P", "ESTADO-W1", "ESTADO-W2",
        "ESTADO-XO", "P-ANULAR", "P-JUS-BS", "P-JUS-CKGL", "P-JUS-CKP",
        "P-MON-CKGL", "P-MON-CKP", "P-MON-SDV-P", "P-PDG", "PT-P", "P-TPT",
        "QBS", "QGL", "T-JUS-CKP", "T-MON-CKP", "T-PDG", "T-TPT",
    ]

    # 100% NULL across all 2,228 files in v2.0.0. Kept in EXPECTED_SENSORS so
    # the per-file schema check can still use them for version detection, but
    # dropped from the Silver projection — carrying four empty columns through
    # the whole pipeline costs metadata on every downstream read.
    ALL_NULL_SENSORS = frozenset(
        {"P-JUS-BS", "P-MON-SDV-P", "PT-P", "QBS"}
    )

    # Which physical range rule applies to which sensor.
    PRESSURE_SENSORS = frozenset(
        {
            "P-ANULAR", "P-JUS-BS", "P-JUS-CKGL", "P-JUS-CKP", "P-MON-CKGL",
            "P-MON-CKP", "P-MON-SDV-P", "P-PDG", "P-TPT", "PT-P",
        }
    )
    TEMPERATURE_SENSORS = frozenset({"T-JUS-CKP", "T-MON-CKP", "T-PDG", "T-TPT"})
    OPENING_SENSORS = frozenset({"ABER-CKGL", "ABER-CKP"})

    # Default QC bounds. These are a defensible starting proposal, not physics —
    # the temperature floor in particular is a judgement call. Override them from
    # config so they can be varied without a code change.
    DEFAULT_SENTINEL_THRESHOLD = 1e10
    DEFAULT_PRESSURE_BOUNDS = (0.0, 6e7)  # Pa
    DEFAULT_TEMPERATURE_BOUNDS = (0.0, 200.0)  # degrees C
    DEFAULT_OPENING_BOUNDS = (0.0, 100.0)  # percent

    # Minimum known sensors expected in a single file, by source family. Real
    # instances carry 17-22 channels; simulated carry 5-7 and hand-drawn 5, so a
    # single global threshold either misses a truncated real file or warns on
    # every synthetic one. Checked per file at staging, where the file name says
    # which family applies — the Spark-side schema is the *union* across all
    # files and so can never answer this question.
    MIN_SENSORS_BY_SOURCE: Dict[str, int] = {
        SOURCE_REAL: 15,
        SOURCE_SIMULATED: 4,
        SOURCE_HAND_DRAWN: 4,
    }

    PARQUET_SUFFIX = ".parquet"

    def __init__(
        self,
        sentinel_threshold: float = DEFAULT_SENTINEL_THRESHOLD,
        pressure_bounds: Tuple[float, float] = DEFAULT_PRESSURE_BOUNDS,
        temperature_bounds: Tuple[float, float] = DEFAULT_TEMPERATURE_BOUNDS,
        opening_bounds: Tuple[float, float] = DEFAULT_OPENING_BOUNDS,
    ) -> None:
        self.sentinel_threshold = sentinel_threshold
        self.pressure_bounds = pressure_bounds
        self.temperature_bounds = temperature_bounds
        self.opening_bounds = opening_bounds

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
    def instance_id(cls, entry_path: str) -> str:
        """'2.0.0/3/WELL-00001_2017.parquet' -> 'WELL-00001_2017'."""
        name = posixpath.basename(cls.normalise(entry_path))
        return name[: -len(cls.PARQUET_SUFFIX)]

    @classmethod
    def well_id(cls, entry_path: str) -> str:
        """'WELL-00001_20170201010207' -> 'WELL-00001'."""
        return cls.instance_id(entry_path).split("_")[0]

    @classmethod
    def source_type(cls, entry_path: str) -> str:
        """Classify a file into its source family, or raise.

        Raises:
            ValueError: the well ID matches no known family. Deliberately fatal:
                the alternative — defaulting to 'real' — silently poisons every
                real-only metric, and that failure is invisible downstream.
        """
        well = cls.well_id(entry_path)
        if re.match(REAL_WELL_PATTERN, well):
            return SOURCE_REAL
        if well == SIMULATED_WELL_ID:
            return SOURCE_SIMULATED
        if well == HAND_DRAWN_WELL_ID:
            return SOURCE_HAND_DRAWN
        raise ValueError(
            f"Unrecognised 3W well ID '{well}' in '{entry_path}'. Expected "
            f"'WELL-<digits>', '{SIMULATED_WELL_ID}' or '{HAND_DRAWN_WELL_ID}'. "
            "Refusing to guess a source family: mislabelling a synthetic file as "
            "real would contaminate every real-only metric with no visible symptom."
        )

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

    @classmethod
    def conform_entry(cls, entry_path: str, data: bytes) -> bytes:
        """Validate and re-encode one ZIP entry on its way to the staging prefix.

        Does the per-file work that only the file name makes possible: rejects
        unrecognised source families, and warns when a file carries too few known
        sensors for its family (usually a different 3W version).

        Raises:
            ValueError: the well ID matches no known source family.
        """
        source = cls.source_type(entry_path)

        table = pq.read_table(io.BytesIO(data))
        present = [c for c in cls.EXPECTED_SENSORS if c in table.column_names]
        minimum = cls.MIN_SENSORS_BY_SOURCE[source]
        if len(present) < minimum:
            missing = [c for c in cls.EXPECTED_SENSORS if c not in table.column_names]
            logger.warning(
                f"'{entry_path}' ({source}) carries {len(present)} known 3W sensors, "
                f"fewer than the {minimum} expected for its source family — is this a "
                f"different dataset version? Missing: {missing}"
            )

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

    def _bounds_for(self, sensor: str) -> Optional[Tuple[float, float]]:
        """Physical bounds for a sensor, or None if no range rule applies."""
        if sensor in self.PRESSURE_SENSORS:
            return self.pressure_bounds
        if sensor in self.TEMPERATURE_SENSORS:
            return self.temperature_bounds
        if sensor in self.OPENING_SENSORS:
            return self.opening_bounds
        # ESTADO-* are discrete state codes and QGL/QBS are flow rates; neither
        # has a bound we can defend, so only the sentinel rule applies.
        return None

    def _qc_expressions(self, sensor: str) -> Tuple[Column, Column]:
        """Build the (cleaned value, QC flag) pair for one sensor.

        The two expressions are built from the *same* source column and applied
        in one projection, so the flag always describes the value beside it.

        Rule order matters: the sentinel test runs before the range test so that
        -1.18e42 is reported as SENTINEL rather than the less specific
        OUT_OF_RANGE, even though it fails both.
        """
        # Read as double. The source is float64 and the sentinels do not fit in
        # float32 — casting first would turn -1.18e42 into -Infinity, which no
        # comparison can then recognise, and which poisons every mean, stddev
        # and scaler that later touches the partition.
        raw = F.col(sensor).cast("double")

        is_sentinel = F.abs(raw) > F.lit(self.sentinel_threshold)

        value = F.when(raw.isNull(), F.lit(None).cast("double"))
        flag = F.when(raw.isNull(), F.lit(None).cast("string"))

        # isnan() is only meaningful once nulls are already handled above.
        value = value.when(F.isnan(raw), F.lit(None).cast("double"))
        flag = flag.when(F.isnan(raw), F.lit(QC_NOT_A_NUMBER))

        value = value.when(is_sentinel, F.lit(None).cast("double"))
        flag = flag.when(is_sentinel, F.lit(QC_SENTINEL))

        bounds = self._bounds_for(sensor)
        if bounds is not None:
            low, high = bounds
            out_of_range = (raw < F.lit(low)) | (raw > F.lit(high))
            if sensor in self.OPENING_SENSORS:
                # A valve opening is a percentage by definition, so a reading of
                # 100.4 is an calibration offset rather than a broken sensor:
                # clamping keeps the observation, nulling would discard it.
                value = value.when(raw < F.lit(low), F.lit(low)).when(
                    raw > F.lit(high), F.lit(high)
                )
                flag = flag.when(out_of_range, F.lit(QC_CLAMPED))
            else:
                value = value.when(out_of_range, F.lit(None).cast("double"))
                flag = flag.when(out_of_range, F.lit(QC_OUT_OF_RANGE))

        value = value.otherwise(raw)
        flag = flag.otherwise(F.lit(None).cast("string"))

        # float32 is safe now that sentinels are gone: round-trip error on a
        # 1.01e7 Pa P-TPT sample is 0.000 Pa, at half the width of a double.
        return value.cast("float").alias(sensor), flag.alias(f"qc_{sensor}")

    @staticmethod
    def _label_expression(df: DataFrame, name: str) -> Column:
        """Cast a label column to int without turning NaN into a valid label.

        Spark casts a floating-point NaN to 0 for an integral target, and 0 is a
        *meaningful* value in both label columns — class 0 is Normal and state 0
        is a real valve configuration. So an Unknown state or an unlabelled
        observation would silently become a confident reading. Null it first.
        """
        column = F.col(name)
        dtype = df.schema[name].dataType
        if isinstance(dtype, (FloatType, DoubleType)):
            column = F.when(F.isnan(column), F.lit(None)).otherwise(column)
        return column.cast("int").alias(name)

    @staticmethod
    def _timestamp_expression(df: DataFrame) -> Column:
        """Return the timestamp column, asserting staging already conformed it.

        conform_parquet_bytes() coerces every staged file to TIMESTAMP(us), so
        Spark always reads this back as TimestampType. Anything else means the
        staging prefix holds files this job did not write, and silently carrying
        on would produce a Silver table whose time axis is not comparable across
        instances.
        """
        dtype = df.schema["timestamp"].dataType
        if not isinstance(dtype, TimestampType):
            raise TypeError(
                f"Staged 'timestamp' is {dtype.simpleString()}, expected timestamp. "
                "Every file this job stages is coerced to TIMESTAMP(us), so this "
                "means the staging prefix contains foreign files — clear it and "
                "re-stage rather than trusting the result."
            )
        return F.col("timestamp")

    def transform(self, df: DataFrame) -> DataFrame:
        """Quality-control and conform a Spark DataFrame of staged 3W files.

        Expects ``folder_class`` to be present as a discovered partition column.
        One row in, one row out — nothing is ever filtered.

        Args:
            df: Raw Spark DataFrame read from the staging prefix.

        Returns:
            The conformed silver-layer DataFrame.
        """
        columns = list(df.columns)
        present = set(columns)

        # The DataFrame schema here is the *union* across every staged file, so
        # it says which sensors exist somewhere in the archive — not which exist
        # in any one file. Per-file completeness is checked at staging.
        known_sensors = [c for c in self.EXPECTED_SENSORS if c in present]
        output_sensors = [c for c in known_sensors if c not in self.ALL_NULL_SENSORS]
        dropped = [c for c in known_sensors if c in self.ALL_NULL_SENSORS]
        if dropped:
            logger.info(f"Dropping all-NULL sensors from the Silver projection: {dropped}")
        absent = [c for c in self.EXPECTED_SENSORS if c not in present]
        if absent:
            logger.info(f"Sensors absent from this archive: {absent}")

        projection: List[Column] = []

        # Metadata that only exists in the file name. input_file_name() is
        # resolved against the file scan, so it MUST be materialised in this
        # projection, before any shuffle. Evaluated after one — which is exactly
        # what adding a window function over instance_id would introduce — it
        # returns the empty string and silently blanks every identity column.
        file_stem = F.regexp_extract(F.input_file_name(), _FILE_STEM_PATTERN, 1)
        instance_id = file_stem
        well_id = F.split(file_stem, "_").getItem(0)

        projection.append(instance_id.alias("instance_id"))
        projection.append(well_id.alias("well_id"))

        # Staging already rejects unrecognised well IDs, so the fall-through is a
        # backstop for foreign files in the staging prefix. NULL, never 'real'.
        projection.append(
            F.when(well_id.rlike(REAL_WELL_PATTERN), F.lit(SOURCE_REAL))
            .when(well_id == F.lit(SIMULATED_WELL_ID), F.lit(SOURCE_SIMULATED))
            .when(well_id == F.lit(HAND_DRAWN_WELL_ID), F.lit(SOURCE_HAND_DRAWN))
            .otherwise(F.lit(None).cast("string"))
            .alias("source_type")
        )

        if "timestamp" in present:
            projection.append(self._timestamp_expression(df))
        else:
            logger.warning("No 'timestamp' column found in the staged 3W data.")

        # Cleaned values and their QC flags, built as one projection so the plan
        # stays shallow — 23 sensors via chained withColumn() calls would nest 46
        # levels deep before Spark ever sees the query.
        for sensor in output_sensors:
            value, flag = self._qc_expressions(sensor)
            projection.append(value)
            projection.append(flag)

        # Per-row labels keep their recorded semantics — including NULLs and
        # transient labels (fault class + 100). They are observations, not
        # metadata to be repaired from the folder name.
        for label in ("class", "state"):
            if label in present:
                projection.append(self._label_expression(df, label))
            else:
                logger.warning(f"No '{label}' column in the staged data.")
                projection.append(F.lit(None).cast("int").alias(label))

        # 'well' and 'id' may already exist inside the Parquet. Prefer the
        # recorded value and fall back to what the file name tells us.
        if "well" in present:
            projection.append(
                F.coalesce(F.col("well").cast("string"), well_id).alias("well")
            )
        else:
            projection.append(well_id.alias("well"))

        if "id" in present:
            projection.append(
                F.coalesce(F.col("id").cast("string"), instance_id).alias("id")
            )
        else:
            projection.append(instance_id.alias("id"))

        # Anything else the archive carried, including folder_class.
        handled = (
            set(self.EXPECTED_SENSORS)
            | {"timestamp", "class", "state", "well", "id"}
        )
        for column in columns:
            if column not in handled:
                projection.append(F.col(column))

        return df.select(*projection)

    # ------------------------------------------------------------------
    # Observability
    # ------------------------------------------------------------------

    @staticmethod
    def label_distribution(df: DataFrame) -> List[dict]:
        """Return the row count per (source_type, folder_class, class) triple.

        Surfaces transient labels (e.g. 101-109) and NULL classes rather than
        letting them be silently dropped or overwritten. Split by source_type
        because real and simulated label timings differ by an order of magnitude
        and a pooled count hides that.
        """
        rows = (
            df.groupBy("source_type", "folder_class", "class")
            .count()
            .orderBy("source_type", "folder_class", "class")
            .collect()
        )
        return [row.asDict() for row in rows]

    @classmethod
    def qc_summary(cls, df: DataFrame) -> List[dict]:
        """Return the count of each QC flag per sensor, for the run log.

        A sudden change in these counts between runs is a data-quality alarm:
        the same archive should always yield the same rejections.
        """
        qc_columns = [c for c in df.columns if c.startswith("qc_")]
        if not qc_columns:
            return []

        # One pass, one row out: count each flag value per sensor via a stack.
        pairs = ", ".join(f"'{c[len('qc_'):]}', `{c}`" for c in qc_columns)
        exploded = df.selectExpr(f"stack({len(qc_columns)}, {pairs}) as (sensor, flag)")
        rows = (
            exploded.filter(F.col("flag").isNotNull())
            .groupBy("sensor", "flag")
            .count()
            .orderBy("sensor", "flag")
            .collect()
        )
        return [row.asDict() for row in rows]
