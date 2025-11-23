"""Tests for derivative uncertainty propagation."""

import numpy as np
import pytest
from studies.data_table_study import DataTableStudy, ColumnType


class TestDerivativeUncertaintyPropagation:
    """Test automatic uncertainty propagation for derivative columns."""
    
    def test_first_derivative_with_uncertainty(self):
        """Test that first derivative propagates uncertainty."""
        study = DataTableStudy("test")
        
        # Create x and y = x^2 with uncertainty
        x_data = np.linspace(0, 10, 11)
        y_data = x_data ** 2
        dy_data = np.full(11, 0.1)  # Constant uncertainty in y
        
        study.add_column("x", ColumnType.DATA, initial_data=x_data)
        study.add_column("y", ColumnType.DATA, initial_data=y_data)
        study.add_column("dy", ColumnType.UNCERTAINTY, 
                        uncertainty_reference="y", initial_data=dy_data)
        
        # Add derivative dy/dx
        study.add_column("dydx", ColumnType.DERIVATIVE,
                        derivative_of="y", with_respect_to="x", order=1,
                        propagate_uncertainty=True)
        
        # Add uncertainty column for derivative
        study.add_column("d_dydx", ColumnType.UNCERTAINTY,
                        uncertainty_reference="dydx")
        
        # Recalculate to propagate uncertainty
        study._recalculate_uncertainty("dydx")
        
        # Get the uncertainty values
        d_dydx = study.table.get_column("d_dydx").values
        
        # Check that uncertainties were calculated (not NaN or zero)
        assert not np.all(np.isnan(d_dydx))
        assert not np.all(d_dydx == 0)
        
        # For δ(dy/dx) ≈ δy / Δx, with Δx=1 and δy=0.1
        # Expected uncertainty ≈ 0.1
        expected_uncert = 0.1  # δy / Δx = 0.1 / 1.0
        np.testing.assert_array_almost_equal(d_dydx, expected_uncert, decimal=1)
    
    def test_derivative_without_uncertainty_gives_zero(self):
        """Test that derivative of column without uncertainty gives zero uncertainty."""
        study = DataTableStudy("test")
        
        # Create x and y without uncertainty
        x_data = np.linspace(0, 10, 11)
        y_data = x_data ** 2
        
        study.add_column("x", ColumnType.DATA, initial_data=x_data)
        study.add_column("y", ColumnType.DATA, initial_data=y_data)
        
        # Add derivative
        study.add_column("dydx", ColumnType.DERIVATIVE,
                        derivative_of="y", with_respect_to="x", order=1)
        
        # Add uncertainty column for derivative
        study.add_column("d_dydx", ColumnType.UNCERTAINTY,
                        uncertainty_reference="dydx")
        
        # Recalculate
        study._recalculate_uncertainty("dydx")
        
        # Should be all zeros
        d_dydx = study.table.get_column("d_dydx").values
        np.testing.assert_array_almost_equal(d_dydx, 0.0)
    
    def test_second_derivative_uncertainty(self):
        """Test that second derivative has larger uncertainty."""
        study = DataTableStudy("test")
        
        # Create x and y = x^3 with uncertainty
        x_data = np.linspace(0, 10, 21)
        y_data = x_data ** 3
        dy_data = np.full(21, 1.0)  # Constant uncertainty
        
        study.add_column("x", ColumnType.DATA, initial_data=x_data)
        study.add_column("y", ColumnType.DATA, initial_data=y_data)
        study.add_column("dy", ColumnType.UNCERTAINTY,
                        uncertainty_reference="y", initial_data=dy_data)
        
        # Add second derivative d²y/dx²
        study.add_column("d2ydx2", ColumnType.DERIVATIVE,
                        derivative_of="y", with_respect_to="x", order=2)
        study.add_column("d_d2ydx2", ColumnType.UNCERTAINTY,
                        uncertainty_reference="d2ydx2")
        
        # Recalculate
        study._recalculate_uncertainty("d2ydx2")
        
        # Get uncertainty
        d_d2ydx2 = study.table.get_column("d_d2ydx2").values
        
        # Second derivative uncertainty should be larger than first
        # δ(d²y/dx²) = δy / (Δx)²
        assert not np.all(np.isnan(d_d2ydx2))
        assert np.all(d_d2ydx2 > 0)
        
        # With Δx ≈ 0.5, δy=1.0: expected ≈ 1.0 / 0.5² = 4.0
        assert np.mean(d_d2ydx2) > 1.0  # Should be significantly larger
    
    def test_derivative_with_d_prefix_uncertainty(self):
        """Test that derivative finds uncertainty with 'd' prefix."""
        study = DataTableStudy("test")
        
        # Create columns with 'd' prefix uncertainty
        x_data = np.linspace(0, 5, 11)
        y_data = x_data ** 2
        
        study.add_column("x", ColumnType.DATA, initial_data=x_data)
        study.add_column("y", ColumnType.DATA, initial_data=y_data)
        study.add_column("dy", ColumnType.DATA, initial_data=np.full(11, 0.2))
        
        # Add derivative
        study.add_column("v", ColumnType.DERIVATIVE,
                        derivative_of="y", with_respect_to="x", order=1)
        study.add_column("dv", ColumnType.UNCERTAINTY,
                        uncertainty_reference="v")
        
        # Manually set dy as uncertainty column in metadata
        study.column_metadata["dy"]["type"] = ColumnType.UNCERTAINTY
        study.column_metadata["dy"]["uncertainty_reference"] = "y"
        
        # Recalculate
        study._recalculate_uncertainty("v")
        
        # Should find 'dy' and propagate
        dv = study.table.get_column("dv").values
        assert not np.all(dv == 0)
        assert not np.all(np.isnan(dv))
    
    def test_from_dict_recalculates_derivative_uncertainty(self):
        """Test that loading from dict recalculates derivative uncertainties."""
        study = DataTableStudy("test")
        
        # Create data with derivative and uncertainty
        x_data = np.linspace(0, 10, 11)
        y_data = x_data ** 2
        
        study.add_column("x", ColumnType.DATA, initial_data=x_data)
        study.add_column("y", ColumnType.DATA, initial_data=y_data)
        study.add_column("dy", ColumnType.UNCERTAINTY,
                        uncertainty_reference="y", 
                        initial_data=np.full(11, 0.15))
        study.add_column("dydx", ColumnType.DERIVATIVE,
                        derivative_of="y", with_respect_to="x", order=1)
        study.add_column("d_dydx", ColumnType.UNCERTAINTY,
                        uncertainty_reference="dydx")
        
        # Convert to dict and back
        study_dict = study.to_dict()
        loaded_study = DataTableStudy.from_dict(study_dict)
        
        # Check that uncertainty was recalculated
        d_dydx = loaded_study.table.get_column("d_dydx").values
        assert not np.all(np.isnan(d_dydx))
        assert not np.all(d_dydx == 0)
        
        # Should have reasonable values
        assert np.mean(d_dydx) > 0.1
