"""Unit tests for uncertainty propagation utilities."""

import pytest
import numpy as np
import pandas as pd
from utils.uncertainty_propagation import UncertaintyPropagator


class TestUncertaintyPropagator:
    """Tests for UncertaintyPropagator class."""
    
    def test_simple_addition(self):
        """Test uncertainty propagation for addition."""
        propagator = UncertaintyPropagator()
        
        formula = "{x} + {y}"
        dependencies = ["x", "y"]
        values = {
            "x": pd.Series([1.0, 2.0, 3.0]),
            "y": pd.Series([4.0, 5.0, 6.0])
        }
        uncertainties = {
            "x": pd.Series([0.1, 0.1, 0.1]),
            "y": pd.Series([0.2, 0.2, 0.2])
        }
        
        result = propagator.calculate_propagated_uncertainty(
            formula, dependencies, values, uncertainties
        )
        
        # For addition: δ(x+y) = √(δx² + δy²)
        expected = np.sqrt(0.1**2 + 0.2**2)
        np.testing.assert_array_almost_equal(result, [expected] * 3)
    
    def test_simple_multiplication(self):
        """Test uncertainty propagation for multiplication."""
        propagator = UncertaintyPropagator()
        
        formula = "{x} * {y}"
        dependencies = ["x", "y"]
        values = {
            "x": pd.Series([2.0, 3.0, 4.0]),
            "y": pd.Series([5.0, 6.0, 7.0])
        }
        uncertainties = {
            "x": pd.Series([0.1, 0.1, 0.1]),
            "y": pd.Series([0.2, 0.2, 0.2])
        }
        
        result = propagator.calculate_propagated_uncertainty(
            formula, dependencies, values, uncertainties
        )
        
        # For multiplication: δ(x*y) = |x*y| * √((δx/x)² + (δy/y)²)
        x_vals = values["x"].values
        y_vals = values["y"].values
        expected = np.abs(x_vals * y_vals) * np.sqrt(
            (0.1 / x_vals)**2 + (0.2 / y_vals)**2
        )
        np.testing.assert_array_almost_equal(result, expected, decimal=4)
    
    def test_power_function(self):
        """Test uncertainty propagation for power."""
        propagator = UncertaintyPropagator()
        
        formula = "{x}**2"
        dependencies = ["x"]
        values = {"x": pd.Series([1.0, 2.0, 3.0])}
        uncertainties = {"x": pd.Series([0.1, 0.1, 0.1])}
        
        result = propagator.calculate_propagated_uncertainty(
            formula, dependencies, values, uncertainties
        )
        
        # For x^2: δ(x²) = 2x * δx
        x_vals = values["x"].values
        expected = 2 * x_vals * 0.1
        np.testing.assert_array_almost_equal(result, expected, decimal=4)
    
    def test_sqrt_function(self):
        """Test uncertainty propagation for square root."""
        propagator = UncertaintyPropagator()
        
        formula = "sqrt({x})"
        dependencies = ["x"]
        values = {"x": pd.Series([4.0, 9.0, 16.0])}
        uncertainties = {"x": pd.Series([0.1, 0.2, 0.3])}
        
        result = propagator.calculate_propagated_uncertainty(
            formula, dependencies, values, uncertainties
        )
        
        # For sqrt(x): δ(√x) = δx / (2√x)
        x_vals = values["x"].values
        ux = uncertainties["x"].values
        expected = ux / (2 * np.sqrt(x_vals))
        np.testing.assert_array_almost_equal(result, expected, decimal=4)
    
    def test_division(self):
        """Test uncertainty propagation for division."""
        propagator = UncertaintyPropagator()
        
        formula = "{x} / {y}"
        dependencies = ["x", "y"]
        values = {
            "x": pd.Series([10.0, 20.0, 30.0]),
            "y": pd.Series([2.0, 4.0, 5.0])
        }
        uncertainties = {
            "x": pd.Series([0.5, 0.5, 0.5]),
            "y": pd.Series([0.1, 0.1, 0.1])
        }
        
        result = propagator.calculate_propagated_uncertainty(
            formula, dependencies, values, uncertainties
        )
        
        # For division: δ(x/y) = |x/y| * √((δx/x)² + (δy/y)²)
        x_vals = values["x"].values
        y_vals = values["y"].values
        ux = uncertainties["x"].values
        uy = uncertainties["y"].values
        expected = np.abs(x_vals / y_vals) * np.sqrt(
            (ux / x_vals)**2 + (uy / y_vals)**2
        )
        np.testing.assert_array_almost_equal(result, expected, decimal=4)
    
    def test_complex_formula(self):
        """Test uncertainty propagation for complex formula."""
        propagator = UncertaintyPropagator()
        
        formula = "{x}**2 + 2*{x}*{y} + {y}**2"
        dependencies = ["x", "y"]
        values = {
            "x": pd.Series([1.0, 2.0, 3.0]),
            "y": pd.Series([2.0, 3.0, 4.0])
        }
        uncertainties = {
            "x": pd.Series([0.1, 0.1, 0.1]),
            "y": pd.Series([0.1, 0.1, 0.1])
        }
        
        result = propagator.calculate_propagated_uncertainty(
            formula, dependencies, values, uncertainties
        )
        
        # Should return valid uncertainty values (not NaN)
        assert not np.any(np.isnan(result))
        assert np.all(result > 0)
    
    def test_with_numpy_functions(self):
        """Test uncertainty propagation with numpy functions."""
        propagator = UncertaintyPropagator()
        
        formula = "np.sin({x})"
        dependencies = ["x"]
        values = {"x": pd.Series([0.0, np.pi/4, np.pi/2])}
        uncertainties = {"x": pd.Series([0.01, 0.01, 0.01])}
        
        result = propagator.calculate_propagated_uncertainty(
            formula, dependencies, values, uncertainties
        )
        
        # For sin(x): δ(sin(x)) = |cos(x)| * δx
        x_vals = values["x"].values
        expected = np.abs(np.cos(x_vals)) * 0.01
        np.testing.assert_array_almost_equal(result, expected, decimal=4)
    
    def test_single_variable(self):
        """Test propagation with single variable."""
        propagator = UncertaintyPropagator()
        
        formula = "2 * {x}"
        dependencies = ["x"]
        values = {"x": pd.Series([1.0, 2.0, 3.0])}
        uncertainties = {"x": pd.Series([0.1, 0.2, 0.3])}
        
        result = propagator.calculate_propagated_uncertainty(
            formula, dependencies, values, uncertainties
        )
        
        # For 2*x: δ(2x) = 2 * δx
        expected = 2 * uncertainties["x"]
        np.testing.assert_array_almost_equal(result, expected, decimal=4)
    
    def test_empty_values(self):
        """Test handling of empty values."""
        propagator = UncertaintyPropagator()
        
        formula = "{x} + {y}"
        dependencies = ["x", "y"]
        values = {"x": pd.Series([]), "y": pd.Series([])}
        uncertainties = {"x": pd.Series([]), "y": pd.Series([])}
        
        # Should return empty series
        result = propagator.calculate_propagated_uncertainty(
            formula, dependencies, values, uncertainties
        )
        assert len(result) == 0
    
    def test_constant_formula(self):
        """Test formula with only constants."""
        propagator = UncertaintyPropagator()
        
        formula = "5.0"
        dependencies = []
        values = {"dummy": pd.Series([1.0, 2.0, 3.0])}
        uncertainties = {"dummy": pd.Series([0.0, 0.0, 0.0])}
        
        result = propagator.calculate_propagated_uncertainty(
            formula, dependencies, values, uncertainties
        )
        
        # Constant has zero uncertainty
        assert len(result) == 3
        # Result might be 0 or NaN for constants
        assert np.all(result >= 0) or np.all(np.isnan(result))
