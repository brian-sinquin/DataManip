"""
Unit tests for FormulaEngine class.
"""

import pytest
import pandas as pd
from models.formula_engine import FormulaEngine
from utils.exceptions import ColumnNotFoundError
from utils.formula_parser import FormulaError


class TestFormulaEngineBasic:
    """Basic formula engine tests."""
    
    def test_initialization(self):
        """Test formula engine initialization."""
        engine = FormulaEngine()
        assert engine._dependencies == {}
        assert engine._dependents == {}
    
    def test_register_simple_formula(self):
        """Test registering a simple formula."""
        engine = FormulaEngine()
        deps = engine.register_formula("c", "{a} + {b}")
        
        assert set(deps) == {"a", "b"}
        assert engine.get_dependencies("c") == {"a", "b"}
        assert "c" in engine.get_dependents("a")
        assert "c" in engine.get_dependents("b")
    
    def test_unregister_column(self):
        """Test unregistering a column."""
        engine = FormulaEngine()
        engine.register_formula("c", "{a} + {b}")
        
        engine.unregister_column("c")
        
        assert "c" not in engine._dependencies
        assert "c" not in engine._dependents
        assert "c" not in engine.get_dependents("a")
        assert "c" not in engine.get_dependents("b")
    
    def test_get_dependencies_empty(self):
        """Test getting dependencies for column with none."""
        engine = FormulaEngine()
        deps = engine.get_dependencies("nonexistent")
        assert deps == set()
    
    def test_get_dependents_empty(self):
        """Test getting dependents for column with none."""
        engine = FormulaEngine()
        deps = engine.get_dependents("nonexistent")
        assert deps == set()
    
    def test_has_dependents(self):
        """Test checking if column has dependents."""
        engine = FormulaEngine()
        engine.register_formula("c", "{a} + {b}")
        
        assert engine.has_dependents("a") is True
        assert engine.has_dependents("b") is True
        assert engine.has_dependents("c") is False
        assert engine.has_dependents("nonexistent") is False


class TestFormulaDependencies:
    """Test dependency tracking."""
    
    def test_chain_dependencies(self):
        """Test chain of dependencies: a -> b -> c."""
        engine = FormulaEngine()
        engine.register_formula("b", "{a} * 2")
        engine.register_formula("c", "{b} + 10")
        
        # Check dependencies
        assert engine.get_dependencies("b") == {"a"}
        assert engine.get_dependencies("c") == {"b"}
        
        # Check dependents
        assert "b" in engine.get_dependents("a")
        assert "c" in engine.get_dependents("b")
    
    def test_multiple_dependencies(self):
        """Test formula with multiple dependencies."""
        engine = FormulaEngine()
        engine.register_formula("result", "{a} + {b} + {c}")
        
        deps = engine.get_dependencies("result")
        assert deps == {"a", "b", "c"}
        
        for col in ["a", "b", "c"]:
            assert "result" in engine.get_dependents(col)
    
    def test_update_formula_dependencies(self):
        """Test updating a formula changes dependencies."""
        engine = FormulaEngine()
        
        # Initial formula
        engine.register_formula("result", "{a} + {b}")
        assert engine.get_dependencies("result") == {"a", "b"}
        
        # Update formula
        engine.register_formula("result", "{c} * {d}")
        assert engine.get_dependencies("result") == {"c", "d"}
        
        # Old dependencies should be removed
        assert "result" not in engine.get_dependents("a")
        assert "result" not in engine.get_dependents("b")
        
        # New dependencies should be added
        assert "result" in engine.get_dependents("c")
        assert "result" in engine.get_dependents("d")


class TestRecalculationOrder:
    """Test recalculation order computation."""
    
    def test_simple_recalculation_order(self):
        """Test simple dependency chain."""
        engine = FormulaEngine()
        engine.register_formula("b", "{a} * 2")
        engine.register_formula("c", "{b} + 10")
        
        order = engine.get_recalculation_order(["a"])
        
        # b must come before c
        assert order.index("b") < order.index("c")
        assert set(order) == {"b", "c"}
    
    def test_recalculation_order_multiple_roots(self):
        """Test multiple changed columns."""
        engine = FormulaEngine()
        engine.register_formula("c", "{a} + {b}")
        
        order = engine.get_recalculation_order(["a", "b"])
        
        assert order == ["c"]
    
    def test_recalculation_order_complex(self):
        """Test complex dependency graph."""
        engine = FormulaEngine()
        engine.register_formula("b", "{a} * 2")
        engine.register_formula("c", "{a} + 10")
        engine.register_formula("d", "{b} + {c}")
        
        order = engine.get_recalculation_order(["a"])
        
        # b and c must come before d
        b_idx = order.index("b")
        c_idx = order.index("c")
        d_idx = order.index("d")
        
        assert b_idx < d_idx
        assert c_idx < d_idx
    
    def test_circular_dependency_detection(self):
        """Test circular dependency raises error."""
        engine = FormulaEngine()
        engine.register_formula("b", "{a}")
        engine.register_formula("c", "{b}")
        
        # Manually create circular dependency
        engine._dependencies["a"] = {"c"}
        engine._dependents["c"] = {"a"}
        
        with pytest.raises(FormulaError, match="Circular dependency"):
            engine.get_recalculation_order(["a"])
    
    def test_empty_recalculation_order(self):
        """Test recalculation when no dependents."""
        engine = FormulaEngine()
        order = engine.get_recalculation_order(["a"])
        assert order == []


class TestFormulaEvaluation:
    """Test formula evaluation."""
    
    def test_evaluate_simple_formula(self):
        """Test evaluating simple addition."""
        engine = FormulaEngine()
        
        data = {
            "a": pd.Series([1, 2, 3]),
            "b": pd.Series([4, 5, 6])
        }
        
        result = engine.evaluate_formula("{a} + {b}", data, row_count=3)
        
        pd.testing.assert_series_equal(result, pd.Series([5, 7, 9]), check_names=False)
    
    def test_evaluate_formula_with_constants(self):
        """Test formula with constants."""
        engine = FormulaEngine()
        
        data = {"x": pd.Series([1, 2, 3])}
        variables = {"k": (10.0, None)}
        
        result = engine.evaluate_formula("{x} * k", data, variables, row_count=3)
        
        pd.testing.assert_series_equal(result, pd.Series([10.0, 20.0, 30.0]), check_names=False)
    
    def test_evaluate_formula_missing_column(self):
        """Test formula with missing column raises error."""
        engine = FormulaEngine()
        
        data = {"a": pd.Series([1, 2, 3])}
        
        with pytest.raises(ColumnNotFoundError, match="undefined columns"):
            engine.evaluate_formula("{a} + {missing}", data, row_count=3)
    
    def test_evaluate_formula_scalar_result(self):
        """Test formula returning scalar expands to series."""
        engine = FormulaEngine()
        
        data = {}
        variables = {"pi": (3.14159, None)}
        
        result = engine.evaluate_formula("2 * pi", data, variables, row_count=5)
        
        assert len(result) == 5
        assert all(abs(val - 6.28318) < 0.0001 for val in result)


class TestFormulaValidation:
    """Test formula validation."""
    
    def test_validate_valid_formula(self):
        """Test validating valid formula."""
        engine = FormulaEngine()
        
        valid, error = engine.validate_formula("{a} + {b}", ["a", "b", "c"])
        
        assert valid is True
        assert error is None
    
    def test_validate_missing_columns(self):
        """Test validating formula with missing columns."""
        engine = FormulaEngine()
        
        valid, error = engine.validate_formula("{a} + {missing}", ["a", "b"])
        
        assert valid is False
        assert "undefined columns" in error
    
    def test_validate_self_reference(self):
        """Test validating formula with self-reference."""
        engine = FormulaEngine()
        
        valid, error = engine.validate_formula("{a} + {result}", ["a", "result"], target_column="result")
        
        assert valid is False
        assert "cannot reference itself" in error
    
    def test_validate_circular_dependency(self):
        """Test validating formula creating circular dependency."""
        engine = FormulaEngine()
        engine.register_formula("b", "{a}")
        
        valid, error = engine.validate_formula("{b}", ["a", "b"], target_column="a")
        
        assert valid is False
        assert "Circular dependency" in error


class TestFormulaEngineUtilities:
    """Test utility methods."""
    
    def test_extract_dependencies(self):
        """Test extracting dependencies from formula."""
        engine = FormulaEngine()
        
        deps = engine.extract_dependencies("{a} + {b} * {c}")
        
        assert set(deps) == {"a", "b", "c"}
    
    def test_clear(self):
        """Test clearing all dependencies."""
        engine = FormulaEngine()
        engine.register_formula("b", "{a}")
        engine.register_formula("c", "{b}")
        
        engine.clear()
        
        assert engine._dependencies == {}
        assert engine._dependents == {}
    
    def test_get_all_formulas(self):
        """Test getting all registered formulas."""
        engine = FormulaEngine()
        engine.register_formula("b", "{a}")
        engine.register_formula("c", "{a} + {b}")
        
        all_formulas = engine.get_all_formulas()
        
        assert all_formulas == {
            "b": {"a"},
            "c": {"a", "b"}
        }
    
    def test_to_dict(self):
        """Test exporting to dictionary."""
        engine = FormulaEngine()
        engine.register_formula("b", "{a}")
        engine.register_formula("c", "{b}")
        
        state = engine.to_dict()
        
        assert "dependencies" in state
        assert "dependents" in state
        assert set(state["dependencies"]["b"]) == {"a"}
        assert set(state["dependents"]["a"]) == {"b"}
