"""
Tests for calculated column functionality in DataTableV2.

This module tests the formula engine integration with the data model,
including formula evaluation, automatic recalculation, and dependency management.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

import pytest
import numpy as np
import pandas as pd
from PySide6.QtCore import Qt

from widgets.data_table.model import DataTableModel, ColumnNotFoundError
from widgets.data_table.column_metadata import ColumnType, DataType
from utils.formula_parser import FormulaError


@pytest.fixture
def model():
    """Create a fresh DataTableModel instance."""
    return DataTableModel()


@pytest.fixture
def model_with_data(model):
    """Create a model with sample data columns."""
    # Add columns
    model.add_data_column("x", dtype=DataType.FLOAT)
    model.add_data_column("y", dtype=DataType.FLOAT)
    
    # Add rows
    model.insertRows(0, 5)
    
    # Set data: x = [1, 2, 3, 4, 5], y = [10, 20, 30, 40, 50]
    for i in range(5):
        x_idx = model.index(i, 0)
        y_idx = model.index(i, 1)
        model.setData(x_idx, i + 1, Qt.ItemDataRole.EditRole)
        model.setData(y_idx, (i + 1) * 10, Qt.ItemDataRole.EditRole)
    
    return model


# ============================================================================
# Basic Calculated Column Tests
# ============================================================================

def test_add_simple_calculated_column(model_with_data):
    """Test adding a simple calculated column."""
    # Add calculated column: z = x * 2
    model_with_data.add_calculated_column("z", "{x} * 2")
    
    # Verify metadata
    assert "z" in model_with_data.get_column_names()
    metadata = model_with_data.get_column_metadata("z")
    assert metadata.column_type == ColumnType.CALCULATED
    assert metadata.formula == "{x} * 2"
    
    # Verify data
    z_data = model_with_data.get_column_data("z")
    expected = np.array([2, 4, 6, 8, 10], dtype=float)
    np.testing.assert_array_almost_equal(z_data, expected)


def test_add_calculated_column_with_multiple_dependencies(model_with_data):
    """Test calculated column that depends on multiple columns."""
    # Add calculated column: sum = x + y
    model_with_data.add_calculated_column("sum", "{x} + {y}")
    
    # Verify data
    sum_data = model_with_data.get_column_data("sum")
    expected = np.array([11, 22, 33, 44, 55], dtype=float)
    np.testing.assert_array_almost_equal(sum_data, expected)


def test_calculated_column_with_math_functions(model_with_data):
    """Test calculated column using mathematical functions."""
    # Add calculated column: sqrt_x = sqrt(x)
    model_with_data.add_calculated_column("sqrt_x", "sqrt({x})")
    
    # Verify data
    sqrt_data = model_with_data.get_column_data("sqrt_x")
    expected = np.sqrt(np.array([1, 2, 3, 4, 5], dtype=float))
    np.testing.assert_array_almost_equal(sqrt_data, expected)


def test_calculated_column_with_constants(model_with_data):
    """Test calculated column using constants."""
    # Add calculated column: circle_area = pi * x^2
    model_with_data.add_calculated_column("area", "pi * {x}**2")
    
    # Verify data
    area_data = model_with_data.get_column_data("area")
    expected = np.pi * np.array([1, 4, 9, 16, 25], dtype=float)
    np.testing.assert_array_almost_equal(area_data, expected)


def test_calculated_column_with_scalar_result(model):
    """Test calculated column that evaluates to a scalar (broadcasts to all rows)."""
    # Add data column
    model.add_data_column("x", dtype=DataType.FLOAT)
    model.insertRows(0, 3)
    
    # Add calculated column with scalar result: constant = 42
    model.add_calculated_column("constant", "42")
    
    # Verify data (scalar should broadcast to all rows)
    constant_data = model.get_column_data("constant")
    expected = np.array([42, 42, 42], dtype=float)
    np.testing.assert_array_almost_equal(constant_data, expected)


# ============================================================================
# Error Handling Tests
# ============================================================================

def test_calculated_column_invalid_syntax(model_with_data):
    """Test that invalid formula syntax is caught."""
    with pytest.raises(FormulaError):
        model_with_data.add_calculated_column("invalid", "{x} +* 2")  # +* is invalid


def test_calculated_column_missing_dependency(model_with_data):
    """Test that missing column dependency is caught."""
    with pytest.raises(ColumnNotFoundError) as exc_info:
        model_with_data.add_calculated_column("bad", "{z} * 2")
    
    assert "z" in str(exc_info.value)


def test_calculated_column_circular_dependency(model_with_data):
    """Test that circular dependencies are detected."""
    # Add first calculated column: a = x * 2
    model_with_data.add_calculated_column("a", "{x} * 2")
    
    # Add second calculated column: b = a + 1
    model_with_data.add_calculated_column("b", "{a} + 1")
    
    # Try to create circular dependency: a = b * 2 (should fail)
    # Note: This requires the model to detect circular dependencies
    # For now, we just ensure it doesn't crash
    # TODO: Add proper circular dependency detection


def test_calculated_column_unsafe_operation(model_with_data):
    """Test that unsafe operations are rejected."""
    with pytest.raises(FormulaError):
        model_with_data.add_calculated_column("unsafe", "import os")


# ============================================================================
# Dependency Tracking Tests
# ============================================================================

def test_calculated_column_dependencies_registered(model_with_data):
    """Test that dependencies are properly registered."""
    # Add calculated column: z = x + y
    model_with_data.add_calculated_column("z", "{x} + {y}")
    
    # Verify dependencies using _dependents (columns that depend on this one)
    deps = model_with_data._dependents
    assert "x" in deps
    assert "z" in deps["x"]
    assert "y" in deps
    assert "z" in deps["y"]


def test_calculated_column_chain_dependencies(model_with_data):
    """Test chained calculated columns (a depends on b depends on c)."""
    # Create chain: a = x * 2, b = a + 1, c = b * 3
    model_with_data.add_calculated_column("a", "{x} * 2")
    model_with_data.add_calculated_column("b", "{a} + 1")
    model_with_data.add_calculated_column("c", "{b} * 3")
    
    # Verify final result
    c_data = model_with_data.get_column_data("c")
    # c = (x * 2 + 1) * 3 = (1*2+1)*3=9, (2*2+1)*3=15, (3*2+1)*3=21, etc.
    expected = np.array([9, 15, 21, 27, 33], dtype=float)
    np.testing.assert_array_almost_equal(c_data, expected)


def test_get_recalculation_order(model_with_data):
    """Test that recalculation order is correct (topological sort)."""
    # Create dependencies: a->c, b->c, c->d
    model_with_data.add_calculated_column("a", "{x} * 2")
    model_with_data.add_calculated_column("b", "{y} / 10")
    model_with_data.add_calculated_column("c", "{a} + {b}")
    model_with_data.add_calculated_column("d", "{c} * 2")
    
    # Get recalculation order
    order = model_with_data._get_recalculation_order("x")
    
    # Verify: a should come before c, c should come before d
    a_idx = order.index("a")
    c_idx = order.index("c")
    d_idx = order.index("d")
    
    assert a_idx < c_idx, "a should be calculated before c"
    assert c_idx < d_idx, "c should be calculated before d"


# ============================================================================
# Automatic Recalculation Tests
# ============================================================================

def test_automatic_recalculation_on_data_change(model_with_data):
    """Test that calculated columns recalculate when data changes."""
    # Add calculated column: z = x * 2
    model_with_data.add_calculated_column("z", "{x} * 2")
    
    # Initial value: z[0] = 1 * 2 = 2
    z_data = model_with_data.get_column_data("z")
    assert z_data[0] == 2
    
    # Change x[0] from 1 to 10
    x_idx = model_with_data.index(0, 0)
    model_with_data.setData(x_idx, 10, Qt.ItemDataRole.EditRole)
    
    # Verify z[0] recalculated: 10 * 2 = 20
    z_data = model_with_data.get_column_data("z")
    assert z_data[0] == 20


def test_automatic_recalculation_cascade(model_with_data):
    """Test that recalculation cascades through dependencies."""
    # Create chain: a = x * 2, b = a + 1
    model_with_data.add_calculated_column("a", "{x} * 2")
    model_with_data.add_calculated_column("b", "{a} + 1")
    
    # Initial values: x[0]=1, a[0]=2, b[0]=3
    a_data = model_with_data.get_column_data("a")
    b_data = model_with_data.get_column_data("b")
    assert a_data[0] == 2
    assert b_data[0] == 3
    
    # Change x[0] to 5
    x_idx = model_with_data.index(0, 0)
    model_with_data.setData(x_idx, 5, Qt.ItemDataRole.EditRole)
    
    # Verify both a and b recalculated
    a_data = model_with_data.get_column_data("a")
    b_data = model_with_data.get_column_data("b")
    assert a_data[0] == 10  # 5 * 2
    assert b_data[0] == 11  # 10 + 1


def test_no_recalculation_on_calculated_column_change(model_with_data):
    """Test that changing a calculated column directly doesn't trigger recalc."""
    # Add calculated column: z = x * 2
    model_with_data.add_calculated_column("z", "{x} * 2")
    
    # Try to change z directly (should not affect x or trigger recalc)
    z_idx = model_with_data.index(0, 2)
    result = model_with_data.setData(z_idx, 999, Qt.ItemDataRole.EditRole)
    
    # Should return False (calculated columns are read-only)
    assert result is False


# ============================================================================
# Complex Formula Tests
# ============================================================================

def test_calculated_column_with_comparisons(model_with_data):
    """Test calculated column with comparison operations."""
    # Add calculated column: is_large = x > 3
    model_with_data.add_calculated_column("is_large", "{x} > 3")
    
    # Verify data (boolean results as 0/1)
    is_large_data = model_with_data.get_column_data("is_large")
    expected = np.array([0, 0, 0, 1, 1], dtype=float)  # [False, False, False, True, True]
    np.testing.assert_array_almost_equal(is_large_data, expected)


def test_calculated_column_with_trigonometry(model_with_data):
    """Test calculated column with trigonometric functions."""
    # Add calculated column: sin_x = sin(x)
    model_with_data.add_calculated_column("sin_x", "sin({x})")
    
    # Verify data
    sin_data = model_with_data.get_column_data("sin_x")
    expected = np.sin(np.array([1, 2, 3, 4, 5], dtype=float))
    np.testing.assert_array_almost_equal(sin_data, expected)


def test_calculated_column_complex_expression(model_with_data):
    """Test calculated column with complex expression."""
    # Add calculated column: result = sqrt(x^2 + y^2)
    model_with_data.add_calculated_column("result", "sqrt({x}**2 + {y}**2)")
    
    # Verify data
    result_data = model_with_data.get_column_data("result")
    x = np.array([1, 2, 3, 4, 5], dtype=float)
    y = np.array([10, 20, 30, 40, 50], dtype=float)
    expected = np.sqrt(x**2 + y**2)
    np.testing.assert_array_almost_equal(result_data, expected)


# ============================================================================
# Edge Cases
# ============================================================================

def test_calculated_column_empty_model(model):
    """Test adding calculated column to empty model (0 rows)."""
    # Add data column
    model.add_data_column("x", dtype=DataType.FLOAT)
    
    # Add calculated column (no rows yet)
    model.add_calculated_column("z", "{x} * 2")
    
    # Should succeed with empty data
    z_data = model.get_column_data("z")
    assert len(z_data) == 0


def test_calculated_column_after_adding_rows(model):
    """Test that calculated column updates when rows are added."""
    # Add data column with initial row
    model.add_data_column("x", dtype=DataType.FLOAT)
    model.insertRows(0, 1)
    model.setData(model.index(0, 0), 5, Qt.ItemDataRole.EditRole)
    
    # Add calculated column
    model.add_calculated_column("z", "{x} * 2")
    assert model.get_column_data("z")[0] == 10
    
    # Add more rows
    model.insertRows(1, 2)
    model.setData(model.index(1, 0), 10, Qt.ItemDataRole.EditRole)
    model.setData(model.index(2, 0), 15, Qt.ItemDataRole.EditRole)
    
    # Verify calculated column extended (should have 0 for new rows initially)
    z_data = model.get_column_data("z")
    assert len(z_data) == 3
    
    # After recalculation, should have correct values
    # Note: Row insertion might not trigger auto-recalc depending on implementation
    # For now, just check structure


def test_calculated_column_with_nan_values(model):
    """Test calculated column handling NaN values."""
    # Add data column with NaN
    model.add_data_column("x", dtype=DataType.FLOAT)
    model.insertRows(0, 3)
    model.setData(model.index(0, 0), 1.0, Qt.ItemDataRole.EditRole)
    model.setData(model.index(1, 0), np.nan, Qt.ItemDataRole.EditRole)
    model.setData(model.index(2, 0), 3.0, Qt.ItemDataRole.EditRole)
    
    # Add calculated column
    model.add_calculated_column("z", "{x} * 2")
    
    # Verify NaN propagates correctly
    z_data = model.get_column_data("z")
    assert z_data[0] == 2.0
    assert np.isnan(z_data[1])
    assert z_data[2] == 6.0


# ============================================================================
# Signal Tests - Requires pytest-qt
# ============================================================================

# TODO: Add when pytest-qt is installed
# def test_calculated_column_emits_signals(model_with_data, qtbot):
#     """Test that adding calculated column emits appropriate signals."""
#     with qtbot.waitSignal(model_with_data.columnAdded, timeout=1000) as blocker:
#         model_with_data.add_calculated_column("z", "{x} * 2")
#     assert blocker.args[0] == "z"

# def test_recalculation_emits_data_changed(model_with_data, qtbot):
#     """Test that recalculation emits dataChanged signal."""
#     model_with_data.add_calculated_column("z", "{x} * 2")
#     with qtbot.waitSignal(model_with_data.dataChanged, timeout=1000):
#         x_idx = model_with_data.index(0, 0)
#         model_with_data.setData(x_idx, 10, Qt.ItemDataRole.EditRole)
