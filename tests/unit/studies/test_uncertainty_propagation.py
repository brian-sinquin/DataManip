"""Tests for uncertainty propagation in DataTableStudy."""

import numpy as np
import pytest

from core.workspace import Workspace
from studies.data_table_study import DataTableStudy, ColumnType


class TestUncertaintyPropagationBasics:
    """Test basic uncertainty propagation functionality."""
    
    def test_propagate_uncertainty_flag(self):
        """Test that propagate_uncertainty flag is stored in metadata."""
        study = DataTableStudy("test")
        study.add_column("x", ColumnType.DATA, initial_data=np.array([1.0, 2.0, 3.0]))
        study.add_column("y", ColumnType.CALCULATED, formula="{x} * 2", propagate_uncertainty=True)
        
        assert study.column_metadata["y"]["propagate_uncertainty"] == True
    
    def test_uncertainty_column_created(self):
        """Test that uncertainty column is automatically created."""
        study = DataTableStudy("test")
        study.add_column("x", ColumnType.DATA, initial_data=np.array([1.0, 2.0, 3.0]))
        study.add_column("x_u", ColumnType.UNCERTAINTY, uncertainty_reference="x", initial_data=np.array([0.1, 0.1, 0.1]))
        
        study.add_column("y", ColumnType.CALCULATED, formula="{x} * 2", propagate_uncertainty=True)
        
        # Check that y_u column exists
        assert "y_u" in study.table.columns
        assert study.column_metadata["y_u"]["type"] == ColumnType.UNCERTAINTY
    
    def test_simple_multiplication_uncertainty(self):
        """Test uncertainty propagation for multiplication: y = x1 * x2."""
        study = DataTableStudy("test")
        study.add_column("x1", ColumnType.DATA, initial_data=np.array([10.0]))
        study.add_column("x1_u", ColumnType.DATA, initial_data=np.array([0.5]))
        study.add_column("x2", ColumnType.DATA, initial_data=np.array([5.0]))
        study.add_column("x2_u", ColumnType.DATA, initial_data=np.array([0.2]))
        
        study.add_column("y", ColumnType.CALCULATED, formula="{x1} * {x2}", propagate_uncertainty=True)
        
        # δy = sqrt((x2*δx1)² + (x1*δx2)²)
        # δy = sqrt((5*0.5)² + (10*0.2)²) = sqrt(2.5² + 2²) = sqrt(10.25) ≈ 3.2016
        y_uncert = study.table.get_column("y_u").iloc[0]
        expected = np.sqrt((5*0.5)**2 + (10*0.2)**2)
        
        np.testing.assert_almost_equal(y_uncert, expected, decimal=4)
    
    def test_simple_addition_uncertainty(self):
        """Test uncertainty propagation for addition: y = x1 + x2."""
        study = DataTableStudy("test")
        study.add_column("x1", ColumnType.DATA, initial_data=np.array([10.0, 20.0, 30.0]))
        study.add_column("x1_u", ColumnType.DATA, initial_data=np.array([0.5, 0.5, 0.5]))
        study.add_column("x2", ColumnType.DATA, initial_data=np.array([5.0, 10.0, 15.0]))
        study.add_column("x2_u", ColumnType.DATA, initial_data=np.array([0.2, 0.2, 0.2]))
        
        study.add_column("y", ColumnType.CALCULATED, formula="{x1} + {x2}", propagate_uncertainty=True)
        
        # For addition: δy = sqrt(δx1² + δx2²)
        y_uncert = study.table.get_column("y_u").values
        expected = np.sqrt(0.5**2 + 0.2**2)
        
        np.testing.assert_array_almost_equal(y_uncert, [expected] * 3, decimal=4)
    
    def test_power_operation_uncertainty(self):
        """Test uncertainty propagation for power: y = x**2."""
        study = DataTableStudy("test")
        study.add_column("x", ColumnType.DATA, initial_data=np.array([3.0]))
        study.add_column("x_u", ColumnType.DATA, initial_data=np.array([0.1]))
        
        study.add_column("y", ColumnType.CALCULATED, formula="{x}**2", propagate_uncertainty=True)
        
        # δy = |2*x| * δx = 2*3*0.1 = 0.6
        y_uncert = study.table.get_column("y_u").iloc[0]
        expected = 2 * 3.0 * 0.1
        
        np.testing.assert_almost_equal(y_uncert, expected, decimal=4)


class TestUncertaintyPropagationComplex:
    """Test uncertainty propagation for complex formulas."""
    
    def test_division_uncertainty(self):
        """Test uncertainty for division: y = x1 / x2."""
        study = DataTableStudy("test")
        study.add_column("x1", ColumnType.DATA, initial_data=np.array([100.0]))
        study.add_column("x1_u", ColumnType.DATA, initial_data=np.array([5.0]))
        study.add_column("x2", ColumnType.DATA, initial_data=np.array([10.0]))
        study.add_column("x2_u", ColumnType.DATA, initial_data=np.array([0.5]))
        
        study.add_column("y", ColumnType.CALCULATED, formula="{x1} / {x2}", propagate_uncertainty=True)
        
        # δy = sqrt((1/x2 * δx1)² + (-x1/x2² * δx2)²)
        # δy = sqrt((1/10 * 5)² + (-100/100 * 0.5)²)
        # δy = sqrt(0.25 + 0.25) = sqrt(0.5) ≈ 0.7071
        y_uncert = study.table.get_column("y_u").iloc[0]
        expected = np.sqrt((1/10 * 5)**2 + (-100/100 * 0.5)**2)
        
        np.testing.assert_almost_equal(y_uncert, expected, decimal=4)
    
    def test_complex_formula_uncertainty(self):
        """Test uncertainty for complex formula: y = (x1 + x2) * x3."""
        study = DataTableStudy("test")
        study.add_column("x1", ColumnType.DATA, initial_data=np.array([5.0]))
        study.add_column("x1_u", ColumnType.DATA, initial_data=np.array([0.2]))
        study.add_column("x2", ColumnType.DATA, initial_data=np.array([3.0]))
        study.add_column("x2_u", ColumnType.DATA, initial_data=np.array([0.1]))
        study.add_column("x3", ColumnType.DATA, initial_data=np.array([2.0]))
        study.add_column("x3_u", ColumnType.DATA, initial_data=np.array([0.05]))
        
        study.add_column("y", ColumnType.CALCULATED, formula="({x1} + {x2}) * {x3}", 
                        propagate_uncertainty=True)
        
        # y = (5 + 3) * 2 = 16
        # ∂y/∂x1 = x3 = 2
        # ∂y/∂x2 = x3 = 2
        # ∂y/∂x3 = x1 + x2 = 8
        # δy = sqrt((2*0.2)² + (2*0.1)² + (8*0.05)²)
        # δy = sqrt(0.16 + 0.04 + 0.16) = sqrt(0.36) = 0.6
        y_uncert = study.table.get_column("y_u").iloc[0]
        expected = np.sqrt((2*0.2)**2 + (2*0.1)**2 + (8*0.05)**2)
        
        np.testing.assert_almost_equal(y_uncert, expected, decimal=4)


class TestUncertaintyPropagationFunctions:
    """Test uncertainty propagation for mathematical functions."""
    
    def test_sqrt_uncertainty(self):
        """Test uncertainty for sqrt function."""
        study = DataTableStudy("test")
        study.add_column("x", ColumnType.DATA, initial_data=np.array([4.0]))
        study.add_column("x_u", ColumnType.DATA, initial_data=np.array([0.1]))
        
        study.add_column("y", ColumnType.CALCULATED, formula="sqrt({x})", propagate_uncertainty=True)
        
        # δy = |1/(2*sqrt(x))| * δx = 1/(2*2) * 0.1 = 0.025
        y_uncert = study.table.get_column("y_u").iloc[0]
        expected = 1 / (2 * np.sqrt(4.0)) * 0.1
        
        np.testing.assert_almost_equal(y_uncert, expected, decimal=4)
    
    def test_sin_uncertainty(self):
        """Test uncertainty for sin function."""
        study = DataTableStudy("test")
        study.add_column("x", ColumnType.DATA, initial_data=np.array([0.0]))  # sin(0) = 0
        study.add_column("x_u", ColumnType.DATA, initial_data=np.array([0.01]))
        
        study.add_column("y", ColumnType.CALCULATED, formula="sin({x})", propagate_uncertainty=True)
        
        # δy = |cos(x)| * δx = cos(0) * 0.01 = 1 * 0.01 = 0.01
        y_uncert = study.table.get_column("y_u").iloc[0]
        expected = np.cos(0.0) * 0.01
        
        np.testing.assert_almost_equal(y_uncert, expected, decimal=4)


class TestUncertaintyPropagationEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_no_uncertainty_columns_available(self):
        """Test when no uncertainty columns exist for dependencies."""
        study = DataTableStudy("test")
        study.add_column("x", ColumnType.DATA, initial_data=np.array([1.0, 2.0, 3.0]))
        # No x_u column
        
        study.add_column("y", ColumnType.CALCULATED, formula="{x} * 2", propagate_uncertainty=True)
        
        # Uncertainty column should exist but contain zeros
        assert "y_u" in study.table.columns
        y_uncert = study.table.get_column("y_u").values
        np.testing.assert_array_equal(y_uncert, [0.0, 0.0, 0.0])
    
    def test_partial_uncertainty_columns(self):
        """Test when only some dependencies have uncertainties."""
        study = DataTableStudy("test")
        study.add_column("x1", ColumnType.DATA, initial_data=np.array([10.0]))
        study.add_column("x1_u", ColumnType.DATA, initial_data=np.array([0.5]))
        study.add_column("x2", ColumnType.DATA, initial_data=np.array([5.0]))
        # No x2_u column
        
        study.add_column("y", ColumnType.CALCULATED, formula="{x1} * {x2}", propagate_uncertainty=True)
        
        # Should only propagate from x1
        # δy = |x2| * δx1 = 5 * 0.5 = 2.5
        y_uncert = study.table.get_column("y_u").iloc[0]
        expected = 5.0 * 0.5
        
        np.testing.assert_almost_equal(y_uncert, expected, decimal=4)
    
    def test_uncertainty_updates_on_data_change(self):
        """Test that uncertainty updates when data changes."""
        study = DataTableStudy("test")
        study.add_column("x", ColumnType.DATA, initial_data=np.array([2.0]))
        study.add_column("x_u", ColumnType.DATA, initial_data=np.array([0.1]))
        
        study.add_column("y", ColumnType.CALCULATED, formula="{x}**2", propagate_uncertainty=True)
        
        # Initial: δy = |2*x| * δx = 2*2*0.1 = 0.4
        initial_uncert = study.table.get_column("y_u").iloc[0]
        np.testing.assert_almost_equal(initial_uncert, 0.4, decimal=4)
        
        # Change x to 3.0
        study.table.set_column("x", np.array([3.0]))
        study.on_data_changed("x")
        
        # New: δy = |2*x| * δx = 2*3*0.1 = 0.6
        new_uncert = study.table.get_column("y_u").iloc[0]
        np.testing.assert_almost_equal(new_uncert, 0.6, decimal=4)
