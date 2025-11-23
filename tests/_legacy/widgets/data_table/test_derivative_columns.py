"""
Tests for derivative column functionality in DataTableV2.

Tests cover:
- Forward, backward, and central difference methods
- Unit propagation
- Dependency tracking and recalculation
- Integration with calculated columns
- Edge cases and error handling
"""

import pytest
import numpy as np
import pandas as pd

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from widgets.data_table.model import DataTableModel, ColumnExistsError, ColumnNotFoundError
from widgets.data_table.column_metadata import ColumnType, DataType


class TestDerivativeBasics:
    """Test basic derivative column functionality."""
    
    def test_forward_difference_linear(self):
        """Test forward difference on linear data."""
        model = DataTableModel()
        
        # Create linear data: y = 2x + 1
        model.add_data_column("x", data=[0, 1, 2, 3, 4])
        model.add_data_column("y", data=[1, 3, 5, 7, 9])
        
        # Add derivative (should be constant = 2)
        model.add_derivative_column("dydx", "y", "x")
        
        result = model.get_column_data("dydx")
        
        # Forward difference: (y[i+1] - y[i]) / (x[i+1] - x[i])
        # All differences should be 2, except last (NaN)
        assert result[0] == pytest.approx(2.0)
        assert result[1] == pytest.approx(2.0)
        assert result[2] == pytest.approx(2.0)
        assert result[3] == pytest.approx(2.0)
        assert pd.isna(result[4])  # Last point has no forward difference
    
    def test_backward_difference_linear(self):
        """Test backward difference on linear data."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0, 1, 2, 3, 4])
        model.add_data_column("y", data=[1, 3, 5, 7, 9])
        
        model.add_derivative_column("dydx", "y", "x", method="backward")
        
        result = model.get_column_data("dydx")
        
        # Backward difference: (y[i] - y[i-1]) / (x[i] - x[i-1])
        # First point has no backward difference
        assert pd.isna(result[0])
        assert result[1] == pytest.approx(2.0)
        assert result[2] == pytest.approx(2.0)
        assert result[3] == pytest.approx(2.0)
        assert result[4] == pytest.approx(2.0)
    
    def test_central_difference_linear(self):
        """Test central difference on linear data."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0, 1, 2, 3, 4])
        model.add_data_column("y", data=[1, 3, 5, 7, 9])
        
        model.add_derivative_column("dydx", "y", "x", method="central")
        
        result = model.get_column_data("dydx")
        
        # Central difference: (y[i+1] - y[i-1]) / (x[i+1] - x[i-1])
        # Endpoints have NaN
        assert pd.isna(result[0])
        assert result[1] == pytest.approx(2.0)
        assert result[2] == pytest.approx(2.0)
        assert result[3] == pytest.approx(2.0)
        assert pd.isna(result[4])
    
    def test_forward_difference_quadratic(self):
        """Test forward difference on quadratic data (y = x^2)."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0, 1, 2, 3, 4])
        model.add_data_column("y", data=[0, 1, 4, 9, 16])
        
        model.add_derivative_column("dydx", "y", "x")
        
        result = model.get_column_data("dydx")
        
        # dy/dx of x^2 is 2x, but discrete derivative gives secant slopes
        # (0,1): (1-0)/(1-0) = 1
        # (1,2): (4-1)/(2-1) = 3
        # (2,3): (9-4)/(3-2) = 5
        # (3,4): (16-9)/(4-3) = 7
        assert result[0] == pytest.approx(1.0)
        assert result[1] == pytest.approx(3.0)
        assert result[2] == pytest.approx(5.0)
        assert result[3] == pytest.approx(7.0)
        assert pd.isna(result[4])
    
    def test_floating_point_data(self):
        """Test derivative with floating point data."""
        model = DataTableModel()
        
        model.add_data_column("t", data=[0.0, 0.5, 1.0, 1.5, 2.0])
        model.add_data_column("s", data=[0.0, 1.25, 5.0, 11.25, 20.0])
        
        model.add_derivative_column("v", "s", "t")
        
        result = model.get_column_data("v")
        
        # s = 5t^2, so v = 10t (analytically)
        # Discrete: (1.25-0)/(0.5-0) = 2.5 (at t=0)
        # (5-1.25)/(1-0.5) = 7.5 (at t=0.5)
        # etc.
        assert result[0] == pytest.approx(2.5)
        assert result[1] == pytest.approx(7.5)
        assert result[2] == pytest.approx(12.5)
        assert result[3] == pytest.approx(17.5)
        assert pd.isna(result[4])


class TestDerivativeUnits:
    """Test unit propagation for derivatives."""
    
    def test_unit_auto_calculation_both_units(self):
        """Test automatic unit calculation when both columns have units."""
        model = DataTableModel()
        
        model.add_data_column("time", unit="s", data=[0, 1, 2, 3])
        model.add_data_column("distance", unit="m", data=[0, 10, 20, 30])
        
        model.add_derivative_column("velocity", "distance", "time")
        
        metadata = model.get_column_metadata("velocity")
        assert metadata.unit == "m/s"
    
    def test_unit_auto_calculation_numerator_only(self):
        """Test unit calculation when only numerator has unit."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0, 1, 2, 3])
        model.add_data_column("y", unit="kg", data=[0, 10, 20, 30])
        
        model.add_derivative_column("dydx", "y", "x")
        
        metadata = model.get_column_metadata("dydx")
        assert metadata.unit == "kg"
    
    def test_unit_auto_calculation_denominator_only(self):
        """Test unit calculation when only denominator has unit."""
        model = DataTableModel()
        
        model.add_data_column("x", unit="m", data=[0, 1, 2, 3])
        model.add_data_column("y", data=[0, 10, 20, 30])
        
        model.add_derivative_column("dydx", "y", "x")
        
        metadata = model.get_column_metadata("dydx")
        assert metadata.unit == "1/m"
    
    def test_unit_auto_calculation_no_units(self):
        """Test unit calculation when neither column has unit."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0, 1, 2, 3])
        model.add_data_column("y", data=[0, 10, 20, 30])
        
        model.add_derivative_column("dydx", "y", "x")
        
        metadata = model.get_column_metadata("dydx")
        assert metadata.unit is None
    
    def test_unit_manual_override(self):
        """Test manually specifying unit overrides auto-calculation."""
        model = DataTableModel()
        
        model.add_data_column("time", unit="s", data=[0, 1, 2, 3])
        model.add_data_column("distance", unit="m", data=[0, 10, 20, 30])
        
        # Override with custom unit
        model.add_derivative_column("velocity", "distance", "time", unit="km/h")
        
        metadata = model.get_column_metadata("velocity")
        assert metadata.unit == "km/h"


class TestDerivativeErrors:
    """Test error handling for derivative columns."""
    
    def test_duplicate_name(self):
        """Test error when derivative column name already exists."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0, 1, 2])
        model.add_data_column("y", data=[0, 1, 2])
        model.add_derivative_column("dydx", "y", "x")
        
        with pytest.raises(ColumnExistsError, match="already exists"):
            model.add_derivative_column("dydx", "y", "x")
    
    def test_numerator_not_found(self):
        """Test error when numerator column doesn't exist."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0, 1, 2])
        
        with pytest.raises(ColumnNotFoundError, match="Column 'y' does not exist"):
            model.add_derivative_column("dydx", "y", "x")
    
    def test_denominator_not_found(self):
        """Test error when denominator column doesn't exist."""
        model = DataTableModel()
        
        model.add_data_column("y", data=[0, 1, 2])
        
        with pytest.raises(ColumnNotFoundError, match="Column 'x' does not exist"):
            model.add_derivative_column("dydx", "y", "x")
    
    def test_invalid_method(self):
        """Test error when method is invalid."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0, 1, 2])
        model.add_data_column("y", data=[0, 1, 2])
        
        with pytest.raises(ValueError, match="Invalid method 'invalid'"):
            model.add_derivative_column("dydx", "y", "x", method="invalid")
    
    def test_non_numeric_numerator(self):
        """Test error when numerator is not numeric."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0, 1, 2])
        model.add_data_column("labels", dtype=DataType.STRING, data=["a", "b", "c"])
        
        with pytest.raises(ValueError, match="Numerator column 'labels' must be numeric"):
            model.add_derivative_column("dydx", "labels", "x")
    
    def test_non_numeric_denominator(self):
        """Test error when denominator is not numeric."""
        model = DataTableModel()
        
        model.add_data_column("labels", dtype=DataType.STRING, data=["a", "b", "c"])
        model.add_data_column("y", data=[0, 1, 2])
        
        with pytest.raises(ValueError, match="Denominator column 'labels' must be numeric"):
            model.add_derivative_column("dydx", "y", "labels")


class TestDerivativeDependencies:
    """Test dependency tracking and recalculation for derivatives."""
    
    def test_dependency_registration(self):
        """Test that dependencies are registered correctly."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0, 1, 2, 3])
        model.add_data_column("y", data=[0, 1, 4, 9])
        model.add_derivative_column("dydx", "y", "x")
        
        # Check dependencies
        assert "y" in model._dependencies["dydx"]
        assert "x" in model._dependencies["dydx"]
        
        # Check reverse dependencies
        assert "dydx" in model._dependents["y"]
        assert "dydx" in model._dependents["x"]
    
    def test_recalculation_when_numerator_changes(self):
        """Test derivative recalculates when numerator changes."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0, 1, 2, 3])
        model.add_data_column("y", data=[0, 1, 4, 9])
        model.add_derivative_column("dydx", "y", "x")
        
        original = model.get_column_data("dydx").copy()
        
        # Change y data using setData (make it linear: y = 2x)
        y_col = model._column_order.index("y")
        for row in range(4):
            idx = model.index(row, y_col)
            model.setData(idx, row * 2.0)
        
        # Derivative should recalculate (should now be constant = 2)
        new = model.get_column_data("dydx")
        
        assert not original.equals(new)
        assert new[0] == pytest.approx(2.0)
        assert new[1] == pytest.approx(2.0)
        assert new[2] == pytest.approx(2.0)
    
    def test_recalculation_when_denominator_changes(self):
        """Test derivative recalculates when denominator changes."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0, 1, 2, 3])
        model.add_data_column("y", data=[0, 2, 4, 6])
        model.add_derivative_column("dydx", "y", "x")
        
        original = model.get_column_data("dydx").copy()
        
        # Change x spacing using setData (now x = [0, 2, 4, 6])
        x_col = model._column_order.index("x")
        for row in range(4):
            idx = model.index(row, x_col)
            model.setData(idx, row * 2.0)
        
        # Derivative should recalculate (dy=2, dx=2, so dydx=1)
        new = model.get_column_data("dydx")
        
        assert not original.equals(new)
        assert new[0] == pytest.approx(1.0)
        assert new[1] == pytest.approx(1.0)
        assert new[2] == pytest.approx(1.0)
    
    def test_cascading_recalculation(self):
        """Test cascading updates through dependency chain."""
        model = DataTableModel()
        
        # Create chain: x -> y=2x -> dydx -> total=dydx+1
        model.add_data_column("x", data=[0, 1, 2, 3])
        model.add_calculated_column("y", "{x} * 2")
        model.add_derivative_column("dydx", "y", "x")
        model.add_calculated_column("total", "{dydx} + 1")
        
        # Change x using setData
        x_col = model._column_order.index("x")
        for row in range(4):
            idx = model.index(row, x_col)
            model.setData(idx, row * 2.0)  # [0, 2, 4, 6]
        
        # Check cascade: y should be 2x, dydx should be 2, total should be 3
        y = model.get_column_data("y")
        dydx = model.get_column_data("dydx")
        total = model.get_column_data("total")
        
        assert y[1] == pytest.approx(4.0)  # 2*2
        assert dydx[0] == pytest.approx(2.0)  # constant derivative
        assert total[0] == pytest.approx(3.0)  # 2+1


class TestDerivativeIntegration:
    """Test integration with other features."""
    
    def test_derivative_in_formula(self):
        """Test using derivative column in a calculated formula."""
        model = DataTableModel()
        
        # Position and time
        model.add_data_column("t", data=[0, 1, 2, 3, 4])
        model.add_data_column("x", data=[0, 5, 20, 45, 80])
        
        # Velocity = dx/dt
        model.add_derivative_column("v", "x", "t")
        
        # Kinetic energy = 0.5 * m * v^2 (assume m=1)
        model.add_calculated_column("KE", "0.5 * {v} ** 2")
        
        ke = model.get_column_data("KE")
        v = model.get_column_data("v")
        
        # Check KE calculation using velocity
        assert ke[0] == pytest.approx(0.5 * v[0] ** 2)
        assert ke[1] == pytest.approx(0.5 * v[1] ** 2)
    
    def test_derivative_of_calculated_column(self):
        """Test taking derivative of a calculated column."""
        model = DataTableModel()
        
        # Time and position formula
        model.add_data_column("t", data=[0, 1, 2, 3, 4])
        model.add_calculated_column("x", "{t} ** 2")  # x = t^2
        
        # Velocity = dx/dt (should be 2t)
        model.add_derivative_column("v", "x", "t")
        
        v = model.get_column_data("v")
        
        # Discrete derivative of t^2
        # At t=0: (1-0)/(1-0) = 1
        # At t=1: (4-1)/(2-1) = 3
        # At t=2: (9-4)/(3-2) = 5
        assert v[0] == pytest.approx(1.0)
        assert v[1] == pytest.approx(3.0)
        assert v[2] == pytest.approx(5.0)
    
    def test_second_derivative(self):
        """Test computing second derivative (derivative of derivative)."""
        model = DataTableModel()
        
        # Time and position
        model.add_data_column("t", data=[0, 1, 2, 3, 4, 5])
        model.add_data_column("x", data=[0, 1, 4, 9, 16, 25])  # x = t^2
        
        # First derivative: velocity
        model.add_derivative_column("v", "x", "t")
        
        # Second derivative: acceleration
        model.add_derivative_column("a", "v", "t")
        
        a = model.get_column_data("a")
        
        # x = t^2, so v = 2t (discrete), and a = 2 (constant)
        # Should be roughly constant = 2
        assert a[0] == pytest.approx(2.0, abs=0.1)
        assert a[1] == pytest.approx(2.0, abs=0.1)
    
    def test_with_range_column(self):
        """Test derivative with range column."""
        model = DataTableModel()
        
        # Create evenly-spaced time
        model.add_range_column("t", start=0, end=4, points=5, unit="s")
        
        # Position data
        model.add_data_column("x", unit="m", data=[0, 5, 20, 45, 80])
        
        # Velocity
        model.add_derivative_column("v", "x", "t")
        
        metadata = model.get_column_metadata("v")
        assert metadata.unit == "m/s"
        
        v = model.get_column_data("v")
        # Should have reasonable velocity values
        assert v[0] > 0  # Moving forward


class TestDerivativeEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_constant_data(self):
        """Test derivative of constant data (should be zero)."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0, 1, 2, 3, 4])
        model.add_data_column("y", data=[5, 5, 5, 5, 5])
        
        model.add_derivative_column("dydx", "y", "x")
        
        result = model.get_column_data("dydx")
        
        # All derivatives should be 0 (except last which is NaN)
        assert result[0] == pytest.approx(0.0)
        assert result[1] == pytest.approx(0.0)
        assert result[2] == pytest.approx(0.0)
        assert result[3] == pytest.approx(0.0)
    
    def test_negative_values(self):
        """Test derivative with negative values."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[-2, -1, 0, 1, 2])
        model.add_data_column("y", data=[4, 1, 0, 1, 4])  # y = x^2
        
        model.add_derivative_column("dydx", "y", "x")
        
        result = model.get_column_data("dydx")
        
        # Discrete derivative of x^2
        assert result[0] == pytest.approx(-3.0)  # (1-4)/(-1-(-2))
        assert result[1] == pytest.approx(-1.0)  # (0-1)/(0-(-1))
        assert result[2] == pytest.approx(1.0)   # (1-0)/(1-0)
        assert result[3] == pytest.approx(3.0)   # (4-1)/(2-1)
    
    def test_non_uniform_spacing(self):
        """Test derivative with non-uniformly spaced data."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0, 1, 3, 6, 10])
        model.add_data_column("y", data=[0, 2, 6, 12, 20])  # y = 2x
        
        model.add_derivative_column("dydx", "y", "x")
        
        result = model.get_column_data("dydx")
        
        # Should still get 2 for all points (linear relationship)
        assert result[0] == pytest.approx(2.0)
        assert result[1] == pytest.approx(2.0)
        assert result[2] == pytest.approx(2.0)
        assert result[3] == pytest.approx(2.0)
    
    def test_two_point_data(self):
        """Test derivative with minimum data (2 points)."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0, 1])
        model.add_data_column("y", data=[0, 2])
        
        model.add_derivative_column("dydx", "y", "x")
        
        result = model.get_column_data("dydx")
        
        # First point: (2-0)/(1-0) = 2
        # Second point: NaN (no forward difference)
        assert result[0] == pytest.approx(2.0)
        assert pd.isna(result[1])
    
    def test_metadata_properties(self):
        """Test that derivative column metadata is set correctly."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0, 1, 2])
        model.add_data_column("y", data=[0, 1, 4])
        
        model.add_derivative_column(
            "dydx", 
            "y", 
            "x", 
            unit="custom",
            description="Test derivative",
            precision=4
        )
        
        metadata = model.get_column_metadata("dydx")
        
        assert metadata.column_type == ColumnType.DERIVATIVE
        assert metadata.derivative_numerator == "y"
        assert metadata.derivative_denominator == "x"
        assert metadata.unit == "custom"
        assert metadata.description == "Test derivative"
        assert metadata.precision == 4
    
    def test_division_by_zero_handling(self):
        """Test handling when denominator has zero differences."""
        model = DataTableModel()
        
        # x has repeated values (zero differences)
        model.add_data_column("x", data=[1, 1, 1, 2, 3])
        model.add_data_column("y", data=[0, 1, 2, 3, 4])
        
        model.add_derivative_column("dydx", "y", "x")
        
        result = model.get_column_data("dydx")
        
        # First two should be inf or nan (division by zero)
        # Later points should work
        assert pd.isna(result[0]) or np.isinf(result[0])
        assert pd.isna(result[1]) or np.isinf(result[1])
