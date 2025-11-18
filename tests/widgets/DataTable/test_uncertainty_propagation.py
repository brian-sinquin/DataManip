"""
Tests for uncertainty propagation in DataTableV2.

This module tests automatic uncertainty calculation and propagation for
calculated columns, including:
- Simple formulas (+, -, *, /)
- Complex formulas with power operations
- Trigonometric functions
- Multiple dependencies
- Edge cases and error handling
"""

import pytest
import pandas as pd
import numpy as np

from widgets.DataTable.model import DataTableModel
from widgets.DataTable.column_metadata import ColumnType


class TestUncertaintyPropagationBasics:
    """Test basic uncertainty propagation functionality."""
    
    def test_propagation_flag_in_metadata(self):
        """Test that propagate_uncertainty flag is stored in metadata."""
        model = DataTableModel()
        model.add_data_column("x", data=pd.Series([1.0, 2.0, 3.0]))
        model.add_calculated_column("y", formula="{x} * 2", propagate_uncertainty=True)
        
        metadata = model.get_column_metadata("y")
        assert metadata.propagate_uncertainty == True
    
    def test_uncertainty_column_created(self):
        """Test that uncertainty column is automatically created."""
        model = DataTableModel()
        model.add_data_column("x", data=pd.Series([1.0, 2.0, 3.0]))
        model.add_data_column("x_u", data=pd.Series([0.1, 0.1, 0.1]))
        
        model.add_calculated_column("y", formula="{x} * 2", propagate_uncertainty=True)
        
        # Check that y_u column exists
        assert "y_u" in model.get_column_names()
        assert model.get_column_metadata("y_u").column_type == ColumnType.UNCERTAINTY
    
    def test_simple_addition_uncertainty(self):
        """Test uncertainty propagation for addition: y = x1 + x2."""
        model = DataTableModel()
        model.add_data_column("x1", data=pd.Series([10.0, 20.0, 30.0]))
        model.add_data_column("x1_u", data=pd.Series([0.5, 0.5, 0.5]))
        model.add_data_column("x2", data=pd.Series([5.0, 10.0, 15.0]))
        model.add_data_column("x2_u", data=pd.Series([0.2, 0.2, 0.2]))
        
        model.add_calculated_column("y", formula="{x1} + {x2}", propagate_uncertainty=True)
        
        # δy = sqrt((δx1)² + (δx2)²) = sqrt(0.5² + 0.2²) = sqrt(0.29) ≈ 0.5385
        y_uncert = model.get_column_data("y_u")
        expected = np.sqrt(0.5**2 + 0.2**2)
        
        np.testing.assert_array_almost_equal(y_uncert, [expected] * 3, decimal=4)
    
    def test_simple_multiplication_uncertainty(self):
        """Test uncertainty propagation for multiplication: y = x1 * x2."""
        model = DataTableModel()
        model.add_data_column("x1", data=pd.Series([10.0]))
        model.add_data_column("x1_u", data=pd.Series([0.5]))
        model.add_data_column("x2", data=pd.Series([5.0]))
        model.add_data_column("x2_u", data=pd.Series([0.2]))
        
        model.add_calculated_column("y", formula="{x1} * {x2}", propagate_uncertainty=True)
        
        # δy = sqrt((x2*δx1)² + (x1*δx2)²)
        # δy = sqrt((5*0.5)² + (10*0.2)²) = sqrt(2.5² + 2²) = sqrt(10.25) ≈ 3.2016
        y_uncert = model.get_column_data("y_u")
        expected = np.sqrt((5 * 0.5)**2 + (10 * 0.2)**2)
        
        np.testing.assert_almost_equal(y_uncert.iloc[0], expected, decimal=4)
    
    def test_power_operation_uncertainty(self):
        """Test uncertainty propagation for power: y = x**2."""
        model = DataTableModel()
        model.add_data_column("x", data=pd.Series([3.0]))
        model.add_data_column("x_u", data=pd.Series([0.1]))
        
        model.add_calculated_column("y", formula="{x}**2", propagate_uncertainty=True)
        
        # δy = |2*x| * δx = 2*3*0.1 = 0.6
        y_uncert = model.get_column_data("y_u")
        expected = 2 * 3.0 * 0.1
        
        np.testing.assert_almost_equal(y_uncert.iloc[0], expected, decimal=4)


class TestUncertaintyPropagationComplex:
    """Test uncertainty propagation for complex formulas."""
    
    def test_division_uncertainty(self):
        """Test uncertainty for division: y = x1 / x2."""
        model = DataTableModel()
        model.add_data_column("x1", data=pd.Series([100.0]))
        model.add_data_column("x1_u", data=pd.Series([5.0]))
        model.add_data_column("x2", data=pd.Series([10.0]))
        model.add_data_column("x2_u", data=pd.Series([0.5]))
        
        model.add_calculated_column("y", formula="{x1} / {x2}", propagate_uncertainty=True)
        
        # δy = sqrt((1/x2 * δx1)² + (-x1/x2² * δx2)²)
        # δy = sqrt((1/10 * 5)² + (-100/100 * 0.5)²)
        # δy = sqrt(0.5² + 0.5²) = sqrt(0.5) ≈ 0.7071
        y_uncert = model.get_column_data("y_u")
        expected = np.sqrt((1/10 * 5)**2 + (-100/100 * 0.5)**2)
        
        np.testing.assert_almost_equal(y_uncert.iloc[0], expected, decimal=4)
    
    def test_complex_formula_uncertainty(self):
        """Test uncertainty for complex formula: y = (x1 + x2) * x3."""
        model = DataTableModel()
        model.add_data_column("x1", data=pd.Series([5.0]))
        model.add_data_column("x1_u", data=pd.Series([0.2]))
        model.add_data_column("x2", data=pd.Series([3.0]))
        model.add_data_column("x2_u", data=pd.Series([0.1]))
        model.add_data_column("x3", data=pd.Series([2.0]))
        model.add_data_column("x3_u", data=pd.Series([0.05]))
        
        model.add_calculated_column("y", formula="({x1} + {x2}) * {x3}", 
                                   propagate_uncertainty=True)
        
        # y = (5 + 3) * 2 = 16
        # ∂y/∂x1 = x3 = 2
        # ∂y/∂x2 = x3 = 2
        # ∂y/∂x3 = x1 + x2 = 8
        # δy = sqrt((2*0.2)² + (2*0.1)² + (8*0.05)²)
        # δy = sqrt(0.16 + 0.04 + 0.16) = sqrt(0.36) = 0.6
        y_uncert = model.get_column_data("y_u")
        expected = np.sqrt((2*0.2)**2 + (2*0.1)**2 + (8*0.05)**2)
        
        np.testing.assert_almost_equal(y_uncert.iloc[0], expected, decimal=4)


class TestUncertaintyPropagationFunctions:
    """Test uncertainty propagation for mathematical functions."""
    
    def test_sqrt_uncertainty(self):
        """Test uncertainty for sqrt function."""
        model = DataTableModel()
        model.add_data_column("x", data=pd.Series([4.0]))
        model.add_data_column("x_u", data=pd.Series([0.1]))
        
        model.add_calculated_column("y", formula="sqrt({x})", propagate_uncertainty=True)
        
        # δy = |1/(2*sqrt(x))| * δx = 1/(2*2) * 0.1 = 0.025
        y_uncert = model.get_column_data("y_u")
        expected = 1 / (2 * np.sqrt(4.0)) * 0.1
        
        np.testing.assert_almost_equal(y_uncert.iloc[0], expected, decimal=4)
    
    def test_trigonometric_uncertainty(self):
        """Test uncertainty for sin function."""
        model = DataTableModel()
        model.add_data_column("x", data=pd.Series([0.0]))  # sin(0) = 0
        model.add_data_column("x_u", data=pd.Series([0.01]))
        
        model.add_calculated_column("y", formula="sin({x})", propagate_uncertainty=True)
        
        # δy = |cos(x)| * δx = cos(0) * 0.01 = 1 * 0.01 = 0.01
        y_uncert = model.get_column_data("y_u")
        expected = np.cos(0.0) * 0.01
        
        np.testing.assert_almost_equal(y_uncert.iloc[0], expected, decimal=4)


class TestUncertaintyPropagationEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_no_uncertainty_columns_available(self):
        """Test when no uncertainty columns exist for dependencies."""
        model = DataTableModel()
        model.add_data_column("x", data=pd.Series([1.0, 2.0, 3.0]))
        # No x_u column
        
        model.add_calculated_column("y", formula="{x} * 2", propagate_uncertainty=True)
        
        # Uncertainty column should exist but contain zeros
        assert "y_u" in model.get_column_names()
        y_uncert = model.get_column_data("y_u")
        np.testing.assert_array_equal(y_uncert, [0.0, 0.0, 0.0])
    
    def test_partial_uncertainty_availability(self):
        """Test when only some dependencies have uncertainties."""
        model = DataTableModel()
        model.add_data_column("x1", data=pd.Series([10.0]))
        model.add_data_column("x1_u", data=pd.Series([0.5]))
        model.add_data_column("x2", data=pd.Series([5.0]))
        # No x2_u
        
        model.add_calculated_column("y", formula="{x1} + {x2}", propagate_uncertainty=True)
        
        # Should only propagate from x1: δy = 0.5
        y_uncert = model.get_column_data("y_u")
        np.testing.assert_almost_equal(y_uncert.iloc[0], 0.5, decimal=4)
    
    def test_nan_handling(self):
        """Test that NaN values in data are handled correctly."""
        model = DataTableModel()
        model.add_data_column("x", data=pd.Series([1.0, np.nan, 3.0]))
        model.add_data_column("x_u", data=pd.Series([0.1, 0.1, 0.1]))
        
        model.add_calculated_column("y", formula="{x} * 2", propagate_uncertainty=True)
        
        # Uncertainty for row with NaN should be NaN
        y_uncert = model.get_column_data("y_u")
        assert not np.isnan(y_uncert.iloc[0])
        assert np.isnan(y_uncert.iloc[1])
        assert not np.isnan(y_uncert.iloc[2])


class TestUncertaintyPropagationRecalculation:
    """Test that uncertainties update when data changes."""
    
    def test_recalculation_on_data_change(self):
        """Test that uncertainty recalculates when data changes."""
        from PySide6.QtCore import Qt
        
        model = DataTableModel()
        model.add_data_column("x", data=pd.Series([10.0, 20.0]))
        model.add_data_column("x_u", data=pd.Series([1.0, 1.0]))
        
        model.add_calculated_column("y", formula="{x} * 2", propagate_uncertainty=True)
        
        # Initial uncertainty: δy = 2 * δx = 2 * 1.0 = 2.0
        y_uncert_initial = model.get_column_data("y_u").iloc[0]
        np.testing.assert_almost_equal(y_uncert_initial, 2.0, decimal=4)
        
        # Change x_u
        idx = model.index(0, model._column_order.index("x_u"))
        model.setData(idx, 2.0, Qt.ItemDataRole.EditRole)
        
        # New uncertainty: δy = 2 * 2.0 = 4.0
        y_uncert_new = model.get_column_data("y_u").iloc[0]
        np.testing.assert_almost_equal(y_uncert_new, 4.0, decimal=4)
    
    def test_recalculation_on_value_change(self):
        """Test that uncertainty recalculates when values change (for nonlinear formulas)."""
        from PySide6.QtCore import Qt
        
        model = DataTableModel()
        model.add_data_column("x", data=pd.Series([2.0]))
        model.add_data_column("x_u", data=pd.Series([0.1]))
        
        model.add_calculated_column("y", formula="{x}**2", propagate_uncertainty=True)
        
        # Initial: δy = |2*x| * δx = |2*2| * 0.1 = 0.4
        y_uncert_initial = model.get_column_data("y_u").iloc[0]
        np.testing.assert_almost_equal(y_uncert_initial, 0.4, decimal=4)
        
        # Change x to 3
        idx = model.index(0, model._column_order.index("x"))
        model.setData(idx, 3.0, Qt.ItemDataRole.EditRole)
        
        # New: δy = |2*3| * 0.1 = 0.6
        y_uncert_new = model.get_column_data("y_u").iloc[0]
        np.testing.assert_almost_equal(y_uncert_new, 0.6, decimal=4)


class TestUncertaintyPropagationIntegration:
    """Test integration with other features."""
    
    def test_with_multiple_calculated_columns(self):
        """Test uncertainty propagation with multiple dependent calculated columns."""
        model = DataTableModel()
        model.add_data_column("x", data=pd.Series([5.0]))
        model.add_data_column("x_u", data=pd.Series([0.2]))
        
        # y = x * 2 (with uncertainty)
        model.add_calculated_column("y", formula="{x} * 2", propagate_uncertainty=True)
        
        # z = y + 10 (with uncertainty, depends on calculated column)
        model.add_calculated_column("z", formula="{y} + 10", propagate_uncertainty=True)
        
        # y = 10, δy = 2 * 0.2 = 0.4
        # z = 20, δz = δy = 0.4
        y_uncert = model.get_column_data("y_u").iloc[0]
        z_uncert = model.get_column_data("z_u").iloc[0]
        
        np.testing.assert_almost_equal(y_uncert, 0.4, decimal=4)
        np.testing.assert_almost_equal(z_uncert, 0.4, decimal=4)
    
    def test_uncertainty_column_properties(self):
        """Test that uncertainty column has correct metadata."""
        model = DataTableModel()
        model.add_data_column("x", data=pd.Series([1.0]))
        model.add_data_column("x_u", data=pd.Series([0.1]))
        
        model.add_calculated_column("y", formula="{x} * 2", unit="m", propagate_uncertainty=True)
        
        # Check y_u metadata
        y_u_meta = model.get_column_metadata("y_u")
        assert y_u_meta.column_type == ColumnType.UNCERTAINTY
        assert y_u_meta.unit == "m"  # Same unit as y
        assert y_u_meta.uncertainty_reference == "y"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
