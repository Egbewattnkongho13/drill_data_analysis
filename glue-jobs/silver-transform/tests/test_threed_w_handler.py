"""
Unit tests for 3W Dataset Handler.

These tests cover the helper functions in isolation without requiring Spark context.
"""

import pandas as pd
import pytest

from transformation.handlers.threed_w_handler import ThreedWDataHandler


class TestThreedWDataHandler:
    """Test suite for ThreedWDataHandler."""

    def test_parse_source_type_simulated(self):
        """Test parsing simulated source type from filename."""
        handler = ThreedWDataHandler()
        assert handler.parse_source_type("SIMULATED_1_001.parquet") == "simulated"

    def test_parse_source_type_hand_drawn(self):
        """Test parsing hand drawn source type from filename."""
        handler = ThreedWDataHandler()
        assert handler.parse_source_type("DRAWN_2_001.parquet") == "hand_drawn"

    def test_parse_source_type_real(self):
        """Test parsing real source type from filename."""
        handler = ThreedWDataHandler()
        assert handler.parse_source_type("3_001.parquet") == "real"

    def test_parse_class_from_folder(self):
        """Test parsing class from folder path."""
        handler = ThreedWDataHandler()
        assert handler.parse_class_from_folder("path/to/5") == 5
        assert handler.parse_class_from_folder("5") == 5

    def test_parse_class_from_folder_invalid(self):
        """Test parsing class from invalid folder path."""
        handler = ThreedWDataHandler()
        assert handler.parse_class_from_folder("path/to/invalid") == -1

    def test_parse_well_id(self):
        """Test parsing well ID from filename."""
        handler = ThreedWDataHandler()
        assert handler.parse_well_id("SIMULATED_1_001.parquet") == "SIMULATED_1_001"
        assert handler.parse_well_id("DRAWN_2_002.parquet") == "DRAWN_2_002"
        assert handler.parse_well_id("3_003.parquet") == "3_003"

    def test_transform_dataframe(self):
        """Test transforming a DataFrame with metadata."""
        handler = ThreedWDataHandler()

        # Create a sample DataFrame
        data = {
            'col1': [1, 2, 3],
            'col2': [4, 5, 6],
            'col3': [7, 8, 9],
            'col4': [10, 11, 12],
            'col5': [13, 14, 15],
            'col6': [16, 17, 18],
            'col7': [19, 20, 21]
        }
        df = pd.DataFrame(data)

        # Transform the DataFrame
        transformed_df = handler.transform_dataframe(df, "simulated", "well_001", 3)

        # Check that metadata columns were added
        assert "source_type" in transformed_df.columns
        assert "well_id" in transformed_df.columns
        assert "class" in transformed_df.columns

        # Check that values are correct
        assert transformed_df["source_type"].iloc[0] == "simulated"
        assert transformed_df["well_id"].iloc[0] == "well_001"
        assert transformed_df["class"].iloc[0] == 3

        # Check that sensor columns are float32
        for col in ['col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7']:
            assert transformed_df[col].dtype == "float32"

        # Check that class column is Int64
        assert transformed_df["class"].dtype == "Int64"