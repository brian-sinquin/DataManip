"""
Tests for range column functionality in DataTableV2.

This module tests the creation of evenly-spaced and logarithmically-spaced
data columns for independent variables.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

import pytest
import numpy as np
import pandas as pd

from widgets.DataTable.model import DataTableModel, ColumnExistsError
from widgets.DataTable.column_metadata import ColumnType, DataType


@pytest.fixture
def model():
    """Create a fresh DataTableModel instance."""
    return DataTableModel()


# ============================================================================
# Linspace Mode Tests
# ============================================================================

def test_add_range_column_linspace_basic(model):
    """Test basic linspace range column."""
    model.add_range_column("time", start=0, end=10, points=11, unit="s")
    
    # Verify metadata
    assert "time" in model.get_column_names()
    metadata = model.get_column_metadata("time")
    assert metadata.column_type == ColumnType.RANGE
    assert metadata.dtype == DataType.FLOAT
    assert metadata.unit == "s"
    assert metadata.range_start == 0
    assert metadata.range_end == 10
    assert metadata.range_points == 11
    
    # Verify data
    data = model.get_column_data("time")
    expected = np.linspace(0, 10, 11)
    np.testing.assert_array_almost_equal(data, expected)


def test_add_range_column_linspace_float_endpoints(model):
    """Test linspace with float endpoints."""
    model.add_range_column("x", start=0.5, end=2.5, points=5)
    
    data = model.get_column_data("x")
    expected = np.linspace(0.5, 2.5, 5)  # [0.5, 1.0, 1.5, 2.0, 2.5]
    np.testing.assert_array_almost_equal(data, expected)


def test_add_range_column_linspace_negative_range(model):
    """Test linspace with negative values."""
    model.add_range_column("y", start=-5, end=5, points=11)
    
    data = model.get_column_data("y")
    expected = np.linspace(-5, 5, 11)
    np.testing.assert_array_almost_equal(data, expected)


def test_add_range_column_linspace_descending(model):
    """Test linspace with descending values (end < start)."""
    model.add_range_column("z", start=10, end=0, points=6)
    
    data = model.get_column_data("z")
    expected = np.linspace(10, 0, 6)  # [10, 8, 6, 4, 2, 0]
    np.testing.assert_array_almost_equal(data, expected)


def test_add_range_column_linspace_two_points(model):
    """Test linspace with minimum 2 points."""
    model.add_range_column("x", start=0, end=1, points=2)
    
    data = model.get_column_data("x")
    expected = np.array([0.0, 1.0])
    np.testing.assert_array_almost_equal(data, expected)


# ============================================================================
# Logspace Mode Tests
# ============================================================================

def test_add_range_column_logspace_basic(model):
    """Test basic logspace range column."""
    model.add_range_column("freq", start=1, end=1000, points=4, 
                          mode="logspace", unit="Hz")
    
    # Verify metadata
    metadata = model.get_column_metadata("freq")
    assert metadata.column_type == ColumnType.RANGE
    assert metadata.unit == "Hz"
    
    # Verify data (1, 10, 100, 1000)
    data = model.get_column_data("freq")
    expected = np.logspace(0, 3, 4)  # 10^0 to 10^3 in 4 points
    np.testing.assert_array_almost_equal(data, expected)


def test_add_range_column_logspace_decades(model):
    """Test logspace spanning multiple decades."""
    model.add_range_column("f", start=1, end=1e6, points=7, mode="logspace")
    
    data = model.get_column_data("f")
    expected = np.logspace(0, 6, 7)  # 10^0 to 10^6 in 7 points
    np.testing.assert_array_almost_equal(data, expected)


def test_add_range_column_logspace_fractional(model):
    """Test logspace with fractional endpoints."""
    model.add_range_column("x", start=0.1, end=100, points=5, mode="logspace")
    
    data = model.get_column_data("x")
    expected = np.logspace(np.log10(0.1), np.log10(100), 5)
    np.testing.assert_array_almost_equal(data, expected)


# ============================================================================
# Arange Mode Tests
# ============================================================================

def test_add_range_column_arange_basic(model):
    """Test basic arange range column with integer step."""
    model.add_range_column("n", start=0, end=10, step=1, mode="arange")
    
    # Verify data
    data = model.get_column_data("n")
    expected = np.arange(0, 10.5, 1)  # [0, 1, 2, ..., 10]
    np.testing.assert_array_almost_equal(data, expected)


def test_add_range_column_arange_float_step(model):
    """Test arange with float step."""
    model.add_range_column("x", start=0, end=2, step=0.5, mode="arange")
    
    data = model.get_column_data("x")
    expected = np.arange(0, 2.25, 0.5)  # [0, 0.5, 1.0, 1.5, 2.0]
    np.testing.assert_array_almost_equal(data, expected)


def test_add_range_column_arange_negative_step(model):
    """Test arange with negative step (descending)."""
    model.add_range_column("y", start=10, end=0, step=-2, mode="arange")
    
    data = model.get_column_data("y")
    expected = np.arange(10, -1, -2)  # [10, 8, 6, 4, 2, 0]
    np.testing.assert_array_almost_equal(data, expected)


def test_add_range_column_arange_non_integer_division(model):
    """Test arange when range is not evenly divisible by step."""
    model.add_range_column("x", start=0, end=1, step=0.3, mode="arange")
    
    data = model.get_column_data("x")
    # Should have: 0, 0.3, 0.6, 0.9 (1.2 would exceed end)
    # But we add step/2 to include endpoint if close
    expected = np.arange(0, 1.15, 0.3)
    np.testing.assert_array_almost_equal(data, expected)


# ============================================================================
# Error Handling Tests
# ============================================================================

def test_add_range_column_duplicate_name_raises_error(model):
    """Test that duplicate column name raises error."""
    model.add_range_column("x", start=0, end=1, points=2)
    
    with pytest.raises(ColumnExistsError):
        model.add_range_column("x", start=0, end=10, points=5)


def test_add_range_column_linspace_missing_points_raises_error(model):
    """Test that linspace without points raises error."""
    with pytest.raises(ValueError, match="requires 'points'"):
        model.add_range_column("x", start=0, end=10, mode="linspace")


def test_add_range_column_linspace_too_few_points_raises_error(model):
    """Test that linspace with <2 points raises error."""
    with pytest.raises(ValueError, match="at least 2 points"):
        model.add_range_column("x", start=0, end=10, points=1, mode="linspace")


def test_add_range_column_logspace_missing_points_raises_error(model):
    """Test that logspace without points raises error."""
    with pytest.raises(ValueError, match="requires 'points'"):
        model.add_range_column("x", start=1, end=100, mode="logspace")


def test_add_range_column_logspace_negative_start_raises_error(model):
    """Test that logspace with negative start raises error."""
    with pytest.raises(ValueError, match="positive start and end"):
        model.add_range_column("x", start=-10, end=100, points=5, mode="logspace")


def test_add_range_column_logspace_zero_start_raises_error(model):
    """Test that logspace with zero start raises error."""
    with pytest.raises(ValueError, match="positive start and end"):
        model.add_range_column("x", start=0, end=100, points=5, mode="logspace")


def test_add_range_column_arange_missing_step_raises_error(model):
    """Test that arange without step raises error."""
    with pytest.raises(ValueError, match="requires 'step'"):
        model.add_range_column("x", start=0, end=10, mode="arange")


def test_add_range_column_arange_zero_step_raises_error(model):
    """Test that arange with zero step raises error."""
    with pytest.raises(ValueError, match="step cannot be zero"):
        model.add_range_column("x", start=0, end=10, step=0, mode="arange")


def test_add_range_column_arange_wrong_step_sign_raises_error(model):
    """Test that arange with wrong step sign raises error."""
    # Ascending range with negative step
    with pytest.raises(ValueError, match="step sign must match"):
        model.add_range_column("x", start=0, end=10, step=-1, mode="arange")
    
    # Descending range with positive step
    with pytest.raises(ValueError, match="step sign must match"):
        model.add_range_column("y", start=10, end=0, step=1, mode="arange")


def test_add_range_column_invalid_mode_raises_error(model):
    """Test that invalid mode raises error."""
    with pytest.raises(ValueError, match="Invalid mode"):
        model.add_range_column("x", start=0, end=10, points=5, mode="invalid")


# ============================================================================
# Integration Tests
# ============================================================================

def test_range_column_with_calculated_column(model):
    """Test using range column in calculated column formula."""
    # Create range column
    model.add_range_column("x", start=0, end=4, points=5)
    
    # Create calculated column using range column
    model.add_calculated_column("y", "{x}**2")
    
    # Verify calculated values
    y_data = model.get_column_data("y")
    expected = np.array([0, 1, 4, 9, 16], dtype=float)
    np.testing.assert_array_almost_equal(y_data, expected)


def test_multiple_range_columns(model):
    """Test creating multiple range columns."""
    model.add_range_column("time", start=0, end=1, points=11, unit="s")
    model.add_range_column("freq", start=1, end=1000, points=4, 
                          mode="logspace", unit="Hz")
    model.add_range_column("index", start=0, end=10, step=1, mode="arange")
    
    # All should have same row count (extended to max)
    assert len(model.get_column_data("time")) == 11
    assert len(model.get_column_data("freq")) == 11  # Extended from 4
    assert len(model.get_column_data("index")) == 11  # Extended from 11


def test_range_column_row_synchronization(model):
    """Test that range columns synchronize with existing data columns."""
    # Add data column with 5 rows
    model.add_data_column("existing", data=[1, 2, 3, 4, 5])
    
    # Add range column with 10 points
    model.add_range_column("time", start=0, end=9, points=10)
    
    # Both should now have 10 rows
    assert len(model.get_column_data("existing")) == 10
    assert len(model.get_column_data("time")) == 10
    
    # Existing column should have been extended with NaN
    existing_data = model.get_column_data("existing")
    assert not np.isnan(existing_data[0])  # Original data
    assert np.isnan(existing_data[5])  # Extended with NaN


def test_range_column_not_editable(model):
    """Test that range columns are read-only (not editable)."""
    from PySide6.QtCore import Qt
    
    model.add_range_column("x", start=0, end=4, points=5)
    
    # Check metadata
    metadata = model.get_column_metadata("x")
    assert metadata.editable is False
    
    # Try to edit - should return False
    x_col = model._column_order.index("x")
    idx = model.index(0, x_col)
    result = model.setData(idx, 999.0, Qt.ItemDataRole.EditRole)
    assert result is False
    
    # Value should remain unchanged
    x_data = model.get_column_data("x")
    assert x_data[0] == 0.0  # Original value


# ============================================================================
# Display and Formatting Tests
# ============================================================================

def test_range_column_custom_precision(model):
    """Test range column with custom precision."""
    model.add_range_column("x", start=0, end=1, points=5, precision=4)
    
    metadata = model.get_column_metadata("x")
    assert metadata.precision == 4


def test_range_column_with_description(model):
    """Test range column with description."""
    model.add_range_column("time", start=0, end=10, points=11, 
                          description="Measurement time points")
    
    metadata = model.get_column_metadata("time")
    assert metadata.description == "Measurement time points"


# ============================================================================
# Edge Cases
# ============================================================================

def test_range_column_single_point_linspace(model):
    """Test that linspace rejects single point."""
    with pytest.raises(ValueError, match="at least 2 points"):
        model.add_range_column("x", start=0, end=10, points=1)


def test_range_column_large_number_of_points(model):
    """Test range column with large number of points."""
    model.add_range_column("x", start=0, end=1, points=1000)
    
    data = model.get_column_data("x")
    assert len(data) == 1000
    assert data[0] == 0.0
    assert abs(data[999] - 1.0) < 1e-10


def test_range_column_very_small_step(model):
    """Test arange with very small step."""
    model.add_range_column("x", start=0, end=0.01, step=0.001, mode="arange")
    
    data = model.get_column_data("x")
    assert len(data) == 11  # 0.000, 0.001, ..., 0.010
    np.testing.assert_array_almost_equal(data[0], 0.0)
    np.testing.assert_array_almost_equal(data[10], 0.01)


def test_range_column_empty_model(model):
    """Test adding range column to empty model."""
    # Should work fine - creates first column
    model.add_range_column("x", start=0, end=5, points=6)
    
    assert model.rowCount() == 6
    assert model.columnCount() == 1
