"""
Unit tests for the 3W Dataset handler.

These cover the staging helpers, which are pure Python and run without a Spark
context. The Spark-side transform() is exercised by integration tests.
"""

import pytest

from transformation.handlers.threed_w_handler import (
    HIVE_NULL_PARTITION,
    ThreedWDataHandler,
)

STAGING = "_unzipped/dev/3w_dataset"


class TestNormalise:
    """Paths inside a ZIP may use either separator regardless of the host OS."""

    def test_backslashes_become_forward_slashes(self):
        assert (
            ThreedWDataHandler.normalise(r"2.0.0\3\WELL-00001_20170201.parquet")
            == "2.0.0/3/WELL-00001_20170201.parquet"
        )

    def test_posix_paths_are_unchanged(self):
        path = "2.0.0/3/WELL-00001_20170201.parquet"
        assert ThreedWDataHandler.normalise(path) == path


class TestIsDataFile:
    @pytest.mark.parametrize(
        "path",
        [
            "2.0.0/0/WELL-00001_20170201010207.parquet",
            "2.0.0/5/SIMULATED_00072.parquet",
            r"2.0.0\5\DRAWN_00007.parquet",
            "2.0.0/1/WELL-00002_20170301.PARQUET",
        ],
    )
    def test_accepts_parquet_entries(self, path):
        assert ThreedWDataHandler.is_data_file(path) is True

    @pytest.mark.parametrize(
        "path",
        [
            "2.0.0/0/",  # directory entry
            "2.0.0/README.md",
            "2.0.0/0/dataset.csv",
            "__MACOSX/2.0.0/0/._WELL-00001.parquet",
            "2.0.0/0/.DS_Store",
        ],
    )
    def test_rejects_everything_else(self, path):
        assert ThreedWDataHandler.is_data_file(path) is False


class TestFolderClass:
    def test_parses_the_immediate_parent_folder(self):
        assert (
            ThreedWDataHandler.folder_class("2.0.0/3/WELL-00001_20170201.parquet") == 3
        )

    def test_parses_class_zero(self):
        assert (
            ThreedWDataHandler.folder_class("2.0.0/0/WELL-00001_20170201.parquet") == 0
        )

    def test_handles_windows_separators(self):
        assert ThreedWDataHandler.folder_class(r"2.0.0\7\SIMULATED_00072.parquet") == 7

    def test_returns_none_for_a_non_numeric_folder(self):
        """No magic number: an unparseable folder is genuinely unknown."""
        assert ThreedWDataHandler.folder_class("2.0.0/misc/WELL-00001.parquet") is None

    def test_returns_none_when_there_is_no_folder(self):
        assert ThreedWDataHandler.folder_class("WELL-00001.parquet") is None


class TestStagingKey:
    def test_maps_class_folder_to_a_hive_partition(self):
        assert (
            ThreedWDataHandler.staging_key(
                "2.0.0/3/WELL-00001_20170201010207.parquet", STAGING
            )
            == f"{STAGING}/folder_class=3/WELL-00001_20170201010207.parquet"
        )

    def test_tolerates_a_trailing_slash_on_the_prefix(self):
        assert (
            ThreedWDataHandler.staging_key("2.0.0/0/SIMULATED_00072.parquet", STAGING + "/")
            == f"{STAGING}/folder_class=0/SIMULATED_00072.parquet"
        )

    def test_unknown_class_uses_sparks_null_partition(self):
        """Spark reads this literal back as NULL, so the row is not falsely labelled."""
        key = ThreedWDataHandler.staging_key("2.0.0/misc/WELL-00001.parquet", STAGING)
        assert key == f"{STAGING}/folder_class={HIVE_NULL_PARTITION}/WELL-00001.parquet"

    def test_windows_entries_produce_posix_keys(self):
        key = ThreedWDataHandler.staging_key(r"2.0.0\8\DRAWN_00007.parquet", STAGING)
        assert key == f"{STAGING}/folder_class=8/DRAWN_00007.parquet"
        assert "\\" not in key

    def test_distinct_classes_do_not_collide(self):
        """Same file name under different class folders must stay distinct."""
        a = ThreedWDataHandler.staging_key("2.0.0/0/WELL-00001_1.parquet", STAGING)
        b = ThreedWDataHandler.staging_key("2.0.0/1/WELL-00001_1.parquet", STAGING)
        assert a != b


class TestSchemaConstants:
    def test_expects_the_full_v2_sensor_set(self):
        assert len(ThreedWDataHandler.EXPECTED_SENSORS) == 27
        assert len(set(ThreedWDataHandler.EXPECTED_SENSORS)) == 27
