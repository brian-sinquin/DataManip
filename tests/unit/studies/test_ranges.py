"""
Tests for range column functionality in DataTableStudy.
"""

import numpy as np
import pytest

from studies.data_table_study import DataTableStudy, ColumnType


class TestRangeColumns:
    """Test range column generation."""
    
    def test_linspace_basic(self):
        """Test linspace range generation."""
        study = DataTableStudy("test")
        
        study.add_column(
            "x",
            ColumnType.RANGE,
            range_type="linspace",
            range_start=0,
            range_stop=10,
            range_count=11,
            unit="m"
        )
        
        x = study.table.get_column("x").values
        expected = np.linspace(0, 10, 11)
        
        assert len(x) == 11
        assert np.allclose(x, expected)
        assert study.get_column_unit("x") == "m"
    
    def test_arange_basic(self):
        """Test arange range generation."""
        study = DataTableStudy("test")
        
        study.add_column(
            "t",
            ColumnType.RANGE,
            range_type="arange",
            range_start=0,
            range_stop=5,
            range_step=0.5,
            unit="s"
        )
        
        t = study.table.get_column("t").values
        expected = np.arange(0, 5, 0.5)
        
        assert len(t) == len(expected)
        assert np.allclose(t, expected)
    
    def test_arange_default_step(self):
        """Test arange with default step=1."""
        study = DataTableStudy("test")
        
        study.add_column(
            "n",
            ColumnType.RANGE,
            range_type="arange",
            range_start=1,
            range_stop=6
        )
        
        n = study.table.get_column("n").values
        expected = np.arange(1, 6, 1)
        
        assert np.array_equal(n, expected)
    
    def test_logspace_basic(self):
        """Test logspace range generation."""
        study = DataTableStudy("test")
        
        study.add_column(
            "freq",
            ColumnType.RANGE,
            range_type="logspace",
            range_start=0,  # 10^0 = 1
            range_stop=3,   # 10^3 = 1000
            range_count=4,
            unit="Hz"
        )
        
        freq = study.table.get_column("freq").values
        expected = np.logspace(0, 3, 4)  # [1, 10, 100, 1000]
        
        assert len(freq) == 4
        assert np.allclose(freq, expected)
    
    def test_range_sets_table_size(self):
        """Test that range column establishes table size."""
        study = DataTableStudy("test")
        
        # Add range column to empty table
        study.add_column(
            "x",
            ColumnType.RANGE,
            range_type="linspace",
            range_start=0,
            range_stop=1,
            range_count=21
        )
        
        # Table should now have 21 rows
        assert len(study.table.data) == 21
    
    def test_range_column_with_calculated(self):
        """Test using range column in calculations."""
        study = DataTableStudy("test")
        
        # Add range column
        study.add_column(
            "x",
            ColumnType.RANGE,
            range_type="linspace",
            range_start=0,
            range_stop=10,
            range_count=11
        )
        
        # Add calculated column
        study.add_column(
            "y",
            ColumnType.CALCULATED,
            formula="{x} ** 2"
        )
        
        x = study.table.get_column("x").values
        y = study.table.get_column("y").values
        
        assert np.allclose(y, x ** 2)
    
    def test_multiple_range_columns(self):
        """Test adding multiple range columns of different lengths."""
        study = DataTableStudy("test")
        
        study.add_column(
            "t",
            ColumnType.RANGE,
            range_type="arange",
            range_start=0,
            range_stop=5,
            range_step=1,
            unit="s"
        )
        
        study.add_column(
            "freq",
            ColumnType.RANGE,
            range_type="logspace",
            range_start=0,
            range_stop=2,
            range_count=3,
            unit="Hz"
        )
        
        # Both should exist
        assert "t" in study.table.columns
        assert "freq" in study.table.columns
        
        # Table size is determined by longest column
        assert len(study.table.data) == 5
        
        # t column has 5 values
        t = study.table.get_column("t").values
        assert len(t) == 5
        assert not np.isnan(t).any()
        
        # freq column has 3 values, then NaN for remaining rows
        freq = study.table.get_column("freq").values
        assert len(freq) == 5
        assert not np.isnan(freq[:3]).any()  # First 3 are valid
        assert np.isnan(freq[3:]).all()  # Last 2 are NaN
    
    def test_range_metadata_preserved(self):
        """Test that range metadata is stored correctly."""
        study = DataTableStudy("test")
        
        study.add_column(
            "x",
            ColumnType.RANGE,
            range_type="linspace",
            range_start=1.5,
            range_stop=5.5,
            range_count=5
        )
        
        meta = study.column_metadata["x"]
        assert meta["type"] == ColumnType.RANGE
        assert meta["range_type"] == "linspace"
        assert meta["range_start"] == 1.5
        assert meta["range_stop"] == 5.5
        assert meta["range_count"] == 5
    
    def test_time_series_example(self):
        """Test creating a time series with range column."""
        study = DataTableStudy("test")
        
        # Time column
        study.add_column(
            "t",
            ColumnType.RANGE,
            range_type="linspace",
            range_start=0,
            range_stop=2*np.pi,
            range_count=100,
            unit="s"
        )
        
        # Signal column
        study.add_column(
            "signal",
            ColumnType.CALCULATED,
            formula="np.sin({t})",
            unit="V"
        )
        
        t = study.table.get_column("t").values
        signal = study.table.get_column("signal").values
        
        assert len(signal) == 100
        assert np.allclose(signal, np.sin(t))
