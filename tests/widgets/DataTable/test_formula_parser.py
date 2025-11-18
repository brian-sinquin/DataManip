"""
Unit tests for FormulaParser.

Tests cover:
- Dependency extraction
- Syntax validation
- Basic arithmetic operations (vectorized)
- Mathematical functions
- Comparison operations
- Error handling
- Edge cases
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

import pytest
import numpy as np
import pandas as pd

from widgets.DataTable.formula_parser import (
    FormulaParser,
    FormulaError,
    FormulaSyntaxError,
    FormulaEvaluationError
)


class TestDependencyExtraction:
    """Test extraction of variable dependencies from formulas."""
    
    def test_single_variable(self):
        """Test extracting single variable."""
        parser = FormulaParser()
        deps = parser.extract_dependencies("{x}")
        assert deps == ['x']
    
    def test_multiple_variables(self):
        """Test extracting multiple variables."""
        parser = FormulaParser()
        deps = parser.extract_dependencies("{x} + {y} * {z}")
        assert deps == ['x', 'y', 'z']
    
    def test_duplicate_variables(self):
        """Test that duplicates are removed."""
        parser = FormulaParser()
        deps = parser.extract_dependencies("{x} + {x} * {y}")
        assert deps == ['x', 'y']
    
    def test_no_variables(self):
        """Test formula with no variables."""
        parser = FormulaParser()
        deps = parser.extract_dependencies("2 + 3 * 5")
        assert deps == []
    
    def test_variables_in_functions(self):
        """Test extracting variables inside functions."""
        parser = FormulaParser()
        deps = parser.extract_dependencies("sin({x}) + cos({y})")
        assert deps == ['x', 'y']


class TestFormulaSyntaxValidation:
    """Test syntax validation without evaluation."""
    
    def test_valid_simple_formula(self):
        """Test valid simple formula."""
        parser = FormulaParser()
        valid, error = parser.validate_syntax("{x} + 2")
        assert valid
        assert error is None
    
    def test_valid_complex_formula(self):
        """Test valid complex formula with functions."""
        parser = FormulaParser()
        valid, error = parser.validate_syntax("sin({x}) * exp({y}) + log({z})")
        assert valid
        assert error is None
    
    def test_invalid_syntax(self):
        """Test invalid Python syntax."""
        parser = FormulaParser()
        valid, error = parser.validate_syntax("{x} +* 2")  # Invalid operator sequence
        assert not valid
        assert "Syntax error" in error or "syntax" in error.lower()
    
    def test_disallowed_function(self):
        """Test that disallowed functions are rejected."""
        parser = FormulaParser()
        valid, error = parser.validate_syntax("exec('print(1)')")
        assert not valid
        assert "not allowed" in error
    
    def test_valid_comparison(self):
        """Test valid comparison operations."""
        parser = FormulaParser()
        valid, error = parser.validate_syntax("{x} > {y}")
        assert valid
        assert error is None


class TestBasicArithmetic:
    """Test basic arithmetic operations."""
    
    def test_addition(self):
        """Test addition operation."""
        parser = FormulaParser()
        result = parser.evaluate("{x} + {y}", {'x': 10, 'y': 5})
        assert result == 15
    
    def test_subtraction(self):
        """Test subtraction operation."""
        parser = FormulaParser()
        result = parser.evaluate("{x} - {y}", {'x': 10, 'y': 3})
        assert result == 7
    
    def test_multiplication(self):
        """Test multiplication operation."""
        parser = FormulaParser()
        result = parser.evaluate("{x} * {y}", {'x': 6, 'y': 7})
        assert result == 42
    
    def test_division(self):
        """Test division operation."""
        parser = FormulaParser()
        result = parser.evaluate("{x} / {y}", {'x': 20, 'y': 4})
        assert result == 5.0
    
    def test_power(self):
        """Test power operation."""
        parser = FormulaParser()
        result = parser.evaluate("{x} ** 2", {'x': 5})
        assert result == 25
    
    def test_floor_division(self):
        """Test floor division."""
        parser = FormulaParser()
        result = parser.evaluate("{x} // {y}", {'x': 17, 'y': 5})
        assert result == 3
    
    def test_modulo(self):
        """Test modulo operation."""
        parser = FormulaParser()
        result = parser.evaluate("{x} % {y}", {'x': 17, 'y': 5})
        assert result == 2
    
    def test_complex_expression(self):
        """Test complex arithmetic expression."""
        parser = FormulaParser()
        result = parser.evaluate("{a} * {b} + {c} / {d}", 
                                {'a': 2, 'b': 3, 'c': 10, 'd': 5})
        assert result == 8.0  # 2*3 + 10/5 = 6 + 2


class TestVectorizedOperations:
    """Test vectorized operations on arrays."""
    
    def test_array_addition(self):
        """Test addition with NumPy arrays."""
        parser = FormulaParser()
        x = np.array([1, 2, 3])
        y = np.array([4, 5, 6])
        result = parser.evaluate("{x} + {y}", {'x': x, 'y': y})
        np.testing.assert_array_equal(result, np.array([5, 7, 9]))
    
    def test_series_multiplication(self):
        """Test multiplication with Pandas Series."""
        parser = FormulaParser()
        x = pd.Series([2, 3, 4])
        y = pd.Series([5, 6, 7])
        result = parser.evaluate("{x} * {y}", {'x': x, 'y': y})
        pd.testing.assert_series_equal(result, pd.Series([10, 18, 28]))
    
    def test_mixed_scalar_array(self):
        """Test mixing scalars and arrays."""
        parser = FormulaParser()
        x = np.array([1, 2, 3])
        result = parser.evaluate("{x} * 2 + 10", {'x': x})
        np.testing.assert_array_equal(result, np.array([12, 14, 16]))
    
    def test_complex_vectorized(self):
        """Test complex expression with arrays."""
        parser = FormulaParser()
        x = pd.Series([1.0, 2.0, 3.0])
        y = pd.Series([4.0, 5.0, 6.0])
        result = parser.evaluate("{x}**2 + {y}**2", {'x': x, 'y': y})
        expected = pd.Series([17.0, 29.0, 45.0])  # 1+16, 4+25, 9+36
        pd.testing.assert_series_equal(result, expected)


class TestMathematicalFunctions:
    """Test mathematical functions."""
    
    def test_sin(self):
        """Test sine function."""
        parser = FormulaParser()
        result = parser.evaluate("sin({x})", {'x': 0})
        assert abs(result) < 1e-10  # sin(0) ≈ 0
    
    def test_cos(self):
        """Test cosine function."""
        parser = FormulaParser()
        result = parser.evaluate("cos({x})", {'x': 0})
        assert abs(result - 1.0) < 1e-10  # cos(0) = 1
    
    def test_exp(self):
        """Test exponential function."""
        parser = FormulaParser()
        result = parser.evaluate("exp({x})", {'x': 0})
        assert abs(result - 1.0) < 1e-10  # e^0 = 1
    
    def test_log(self):
        """Test natural logarithm."""
        parser = FormulaParser()
        result = parser.evaluate("log({x})", {'x': np.e})
        assert abs(result - 1.0) < 1e-10  # ln(e) = 1
    
    def test_sqrt(self):
        """Test square root."""
        parser = FormulaParser()
        result = parser.evaluate("sqrt({x})", {'x': 16})
        assert result == 4.0
    
    def test_abs(self):
        """Test absolute value."""
        parser = FormulaParser()
        result = parser.evaluate("abs({x})", {'x': -5})
        assert result == 5
    
    def test_vectorized_sin(self):
        """Test vectorized sine function."""
        parser = FormulaParser()
        x = np.array([0, np.pi/2, np.pi])
        result = parser.evaluate("sin({x})", {'x': x})
        expected = np.array([0, 1, 0])
        np.testing.assert_array_almost_equal(result, expected, decimal=10)
    
    def test_nested_functions(self):
        """Test nested function calls."""
        parser = FormulaParser()
        result = parser.evaluate("sqrt(abs({x}))", {'x': -16})
        assert result == 4.0


class TestConstants:
    """Test mathematical constants."""
    
    def test_pi_constant(self):
        """Test pi constant."""
        parser = FormulaParser()
        result = parser.evaluate("pi", {})
        assert abs(result - np.pi) < 1e-10
    
    def test_e_constant(self):
        """Test e constant."""
        parser = FormulaParser()
        result = parser.evaluate("e", {})
        assert abs(result - np.e) < 1e-10
    
    def test_constant_in_formula(self):
        """Test using constants in formulas."""
        parser = FormulaParser()
        result = parser.evaluate("{r} * 2 * pi", {'r': 5})
        expected = 5 * 2 * np.pi
        assert abs(result - expected) < 1e-10


class TestComparisonOperations:
    """Test comparison operations."""
    
    def test_greater_than(self):
        """Test greater than comparison."""
        parser = FormulaParser()
        result = parser.evaluate("{x} > {y}", {'x': 10, 'y': 5})
        assert result == True
    
    def test_less_than(self):
        """Test less than comparison."""
        parser = FormulaParser()
        result = parser.evaluate("{x} < {y}", {'x': 3, 'y': 7})
        assert result == True
    
    def test_equal(self):
        """Test equality comparison."""
        parser = FormulaParser()
        result = parser.evaluate("{x} == {y}", {'x': 5, 'y': 5})
        assert result == True
    
    def test_vectorized_comparison(self):
        """Test vectorized comparison."""
        parser = FormulaParser()
        x = np.array([1, 5, 10])
        y = np.array([3, 3, 3])
        result = parser.evaluate("{x} > {y}", {'x': x, 'y': y})
        expected = np.array([False, True, True])
        np.testing.assert_array_equal(result, expected)


class TestErrorHandling:
    """Test error handling."""
    
    def test_undefined_variable(self):
        """Test error when variable is undefined."""
        parser = FormulaParser()
        with pytest.raises(FormulaEvaluationError, match="Undefined variable"):
            parser.evaluate("{x} + {y}", {'x': 10})  # Missing 'y'
    
    def test_division_by_zero(self):
        """Test division by zero handling."""
        parser = FormulaParser()
        # NumPy handles this by returning inf
        result = parser.evaluate("{x} / {y}", {'x': 10, 'y': 0})
        assert np.isinf(result)
    
    def test_invalid_function(self):
        """Test that invalid functions are rejected."""
        parser = FormulaParser()
        valid, error = parser.validate_syntax("invalid_func({x})")
        assert not valid
    
    def test_log_of_negative(self):
        """Test log of negative number."""
        parser = FormulaParser()
        result = parser.evaluate("log({x})", {'x': -1})
        # NumPy returns nan for log of negative
        assert np.isnan(result)


class TestAggregationFunctions:
    """Test aggregation functions (sum, mean, etc.)."""
    
    def test_sum_function(self):
        """Test sum aggregation."""
        parser = FormulaParser()
        x = np.array([1, 2, 3, 4, 5])
        result = parser.evaluate("sum({x})", {'x': x})
        assert result == 15
    
    def test_mean_function(self):
        """Test mean aggregation."""
        parser = FormulaParser()
        x = np.array([2, 4, 6, 8])
        result = parser.evaluate("mean({x})", {'x': x})
        assert result == 5.0
    
    def test_min_max_functions(self):
        """Test min and max aggregations."""
        parser = FormulaParser()
        x = np.array([3, 1, 4, 1, 5])
        min_result = parser.evaluate("min({x})", {'x': x})
        max_result = parser.evaluate("max({x})", {'x': x})
        assert min_result == 1
        assert max_result == 5


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_unary_minus(self):
        """Test unary minus operator."""
        parser = FormulaParser()
        result = parser.evaluate("-{x}", {'x': 5})
        assert result == -5
    
    def test_unary_plus(self):
        """Test unary plus operator."""
        parser = FormulaParser()
        result = parser.evaluate("+{x}", {'x': 5})
        assert result == 5
    
    def test_parentheses(self):
        """Test parentheses for order of operations."""
        parser = FormulaParser()
        result = parser.evaluate("({x} + {y}) * {z}", {'x': 2, 'y': 3, 'z': 4})
        assert result == 20  # (2+3)*4 = 20
    
    def test_empty_series(self):
        """Test with empty Series."""
        parser = FormulaParser()
        x = pd.Series([], dtype=float)
        y = pd.Series([], dtype=float)
        result = parser.evaluate("{x} + {y}", {'x': x, 'y': y})
        assert len(result) == 0
    
    def test_nan_handling(self):
        """Test NaN value handling."""
        parser = FormulaParser()
        x = np.array([1, np.nan, 3])
        result = parser.evaluate("{x} * 2", {'x': x})
        assert np.isnan(result[1])
        assert result[0] == 2
        assert result[2] == 6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
