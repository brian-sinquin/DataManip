"""Unit tests for FormulaEngine."""

import pytest
import pandas as pd
import numpy as np
from core.formula_engine import FormulaEngine, FormulaError


class TestDependencyExtraction:
    """Test formula dependency extraction."""
    
    def test_simple_dependency(self):
        """Test extracting simple dependencies."""
        engine = FormulaEngine()
        
        deps = engine.extract_dependencies("{x} + {y}")
        assert set(deps) == {"x", "y"}
    
    def test_no_dependencies(self):
        """Test formula with no dependencies."""
        engine = FormulaEngine()
        
        deps = engine.extract_dependencies("2 * 3 + 5")
        assert len(deps) == 0
    
    def test_complex_formula(self):
        """Test complex formula with multiple dependencies."""
        engine = FormulaEngine()
        
        deps = engine.extract_dependencies("sqrt({x}**2 + {y}**2) / {z}")
        assert set(deps) == {"x", "y", "z"}
    
    def test_duplicate_dependencies(self):
        """Test handling duplicate dependencies."""
        engine = FormulaEngine()
        
        deps = engine.extract_dependencies("{x} + {x} * {y}")
        assert set(deps) == {"x", "y"}


class TestFormulaEvaluation:
    """Test formula evaluation."""
    
    def test_scalar_formula(self):
        """Test evaluating scalar formula."""
        engine = FormulaEngine()
        
        result = engine.evaluate(
            "{x} + {y}",
            {"x": 5, "y": 10}
        )
        assert result == 15
    
    def test_array_formula(self):
        """Test evaluating array formula."""
        engine = FormulaEngine()
        
        result = engine.evaluate(
            "{x} * 2",
            {"x": pd.Series([1, 2, 3])}
        )
        assert isinstance(result, pd.Series)
        assert result.tolist() == [2, 4, 6]
    
    def test_mixed_scalar_array(self):
        """Test formula with mixed scalar and array."""
        engine = FormulaEngine()
        
        result = engine.evaluate(
            "{x} + {c}",
            {"x": pd.Series([1, 2, 3]), "c": 10}
        )
        assert isinstance(result, pd.Series)
        assert result.tolist() == [11, 12, 13]
    
    def test_numpy_functions(self):
        """Test using numpy functions."""
        engine = FormulaEngine()
        
        result = engine.evaluate(
            "sqrt({x})",
            {"x": pd.Series([4, 9, 16])}
        )
        assert result.tolist() == [2.0, 3.0, 4.0]
    
    def test_missing_dependency(self):
        """Test error on missing dependency."""
        engine = FormulaEngine()
        
        with pytest.raises(FormulaError, match="Missing variables"):
            engine.evaluate("{x} + {y}", {"x": 5})


class TestDependencyTracking:
    """Test dependency tracking and calculation order."""
    
    def test_register_formula(self):
        """Test registering formula."""
        engine = FormulaEngine()
        
        engine.register_formula("z", "{x} + {y}")
        deps = engine.get_dependencies("z")
        assert deps == {"x", "y"}
    
    def test_simple_calculation_order(self):
        """Test getting calculation order."""
        engine = FormulaEngine()
        
        engine.register_formula("b", "{a} * 2")
        engine.register_formula("c", "{b} + 1")
        
        order = engine.get_calculation_order(["a"])
        assert order == ["b", "c"]
    
    def test_independent_formulas(self):
        """Test independent formulas."""
        engine = FormulaEngine()
        
        engine.register_formula("b", "{a} * 2")
        engine.register_formula("c", "{a} + 1")
        
        order = engine.get_calculation_order(["a"])
        # Both depend on 'a', order doesn't matter
        assert set(order) == {"b", "c"}
    
    def test_circular_dependency(self):
        """Test circular dependency detection."""
        engine = FormulaEngine()
        
        engine.register_formula("a", "{b} + 1")
        engine.register_formula("b", "{a} * 2")
        
        with pytest.raises(FormulaError, match="Circular dependency"):
            engine.get_calculation_order(["a"])
    
    def test_complex_dependency_chain(self):
        """Test complex dependency chain."""
        engine = FormulaEngine()
        
        engine.register_formula("b", "{a}")
        engine.register_formula("c", "{b}")
        engine.register_formula("d", "{c}")
        engine.register_formula("e", "{b} + {d}")
        
        order = engine.get_calculation_order(["a"])
        
        # Check proper ordering: b before c, c before d, both b and d before e
        b_idx = order.index("b")
        c_idx = order.index("c")
        d_idx = order.index("d")
        e_idx = order.index("e")
        
        assert b_idx < c_idx
        assert c_idx < d_idx
        assert b_idx < e_idx
        assert d_idx < e_idx


class TestFormulaValidation:
    """Test formula validation."""
    
    def test_valid_formula(self):
        """Test validating correct formula."""
        engine = FormulaEngine()
        
        valid, error = engine.validate_formula("{x} + {y}", ["x", "y"])
        assert valid is True
        assert error is None
    
    def test_undefined_variable(self):
        """Test validation with undefined variable."""
        engine = FormulaEngine()
        
        valid, error = engine.validate_formula("{x} + {z}", ["x", "y"])
        assert valid is False
        assert "Undefined variables" in error
    
    def test_syntax_error(self):
        """Test validation with syntax error."""
        engine = FormulaEngine()
        
        valid, error = engine.validate_formula("{x} +", ["x"])
        assert valid is False
        assert "Syntax error" in error


class TestVariableRenaming:
    """Test variable renaming in formulas."""
    
    def test_rename_dependency(self):
        """Test renaming a variable that is a dependency."""
        engine = FormulaEngine()
        
        # Register formula that depends on 'x'
        engine.register_formula("y", "{x} * 2")
        
        # Rename x to x_new
        engine.rename_variable("x", "x_new")
        
        # Check that dependency was updated
        deps = engine.get_dependencies("y")
        assert "x_new" in deps
        assert "x" not in deps
    
    def test_rename_target(self):
        """Test renaming a variable that is a target."""
        engine = FormulaEngine()
        
        # Register formula with 'old_col' as target
        engine.register_formula("old_col", "{x} + {y}")
        
        # Rename old_col to new_col
        engine.rename_variable("old_col", "new_col")
        
        # Check that target was renamed
        assert "new_col" in engine._dependencies
        assert "old_col" not in engine._dependencies
        assert engine.get_dependencies("new_col") == {"x", "y"}
    
    def test_rename_multiple_dependencies(self):
        """Test renaming a variable used in multiple formulas."""
        engine = FormulaEngine()
        
        # Register multiple formulas that depend on 'x'
        engine.register_formula("y", "{x} * 2")
        engine.register_formula("z", "{x} + {y}")
        engine.register_formula("w", "{x} / 3")
        
        # Rename x to x_renamed
        engine.rename_variable("x", "x_renamed")
        
        # Check that all dependencies were updated
        assert "x_renamed" in engine.get_dependencies("y")
        assert "x_renamed" in engine.get_dependencies("z")
        assert "x_renamed" in engine.get_dependencies("w")
        assert "x" not in engine.get_dependencies("y")
        assert "x" not in engine.get_dependencies("z")
        assert "x" not in engine.get_dependencies("w")
    
    def test_rename_preserves_other_dependencies(self):
        """Test that renaming preserves other dependencies."""
        engine = FormulaEngine()
        
        # Register formula with multiple dependencies
        engine.register_formula("result", "{x} + {y} + {z}")
        
        # Rename only x
        engine.rename_variable("x", "x_new")
        
        # Check that all dependencies are correct
        deps = engine.get_dependencies("result")
        assert deps == {"x_new", "y", "z"}
