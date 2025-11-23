"""
Unified formula evaluation engine.

Handles scalar, array, and table formulas with unit awareness
and uncertainty propagation.
"""

from __future__ import annotations
from typing import Any, Dict, Optional, Set
import re
import numpy as np
import pandas as pd
from sympy import sympify, symbols
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
import pint

# Initialize unit registry
ureg = pint.UnitRegistry()


class FormulaError(Exception):
    """Formula evaluation error."""
    pass


class FormulaEngine:
    """Unified formula engine for all calculation types.
    
    Evaluates formulas with:
    - Scalar values (constants, variables)
    - Array operations (element-wise)
    - Table operations (DataFrame operations)
    - Unit tracking and conversion
    - Uncertainty propagation (future)
    """
    
    def __init__(self):
        """Initialize formula engine."""
        self._dependencies: Dict[str, Set[str]] = {}  # {target: {deps}}
        
    def evaluate(
        self,
        formula: str,
        context: Dict[str, Any],
        units: Optional[Dict[str, str]] = None
    ) -> Any:
        """Evaluate formula with given context.
        
        Args:
            formula: Formula string (e.g., "{x} * 2 + {y}")
            context: Dictionary of available variables/columns
            units: Optional unit specifications for variables
            
        Returns:
            Evaluation result (scalar, array, or Series)
            
        Raises:
            FormulaError: If evaluation fails
        """
        try:
            # Extract dependencies
            deps = self.extract_dependencies(formula)
            
            # Check all dependencies are available
            missing = [d for d in deps if d not in context]
            if missing:
                raise FormulaError(f"Missing variables: {', '.join(missing)}")
            
            # Replace {var} with var for evaluation
            eval_formula = formula
            for dep in deps:
                eval_formula = eval_formula.replace(f"{{{dep}}}", dep)
            
            # Prepare evaluation context
            eval_context = {}
            # Add numpy functions (use np. prefix internally)
            eval_context['np'] = np
            eval_context['pd'] = pd
            # Add common functions without prefix for convenience
            eval_context.update({
                'sqrt': np.sqrt,
                'sin': np.sin,
                'cos': np.cos,
                'tan': np.tan,
                'exp': np.exp,
                'log': np.log,
                'log10': np.log10,
                'abs': np.abs,
                'pi': np.pi,
                'e': np.e,
                'arcsin': np.arcsin,
                'arccos': np.arccos,
                'arctan': np.arctan,
            })
            eval_context.update(context)  # User variables
            
            # Evaluate
            result = eval(eval_formula, {"__builtins__": {}}, eval_context)
            
            # Ensure result is properly formatted
            if isinstance(result, np.ndarray):
                result = pd.Series(result)
            elif isinstance(result, (int, float, np.number)):
                # Scalar result - needs to be broadcast if arrays are present in context
                # Check if any arrays/Series were used
                has_arrays = any(isinstance(v, (np.ndarray, pd.Series)) for v in context.values())
                if has_arrays:
                    # Find the length from any array in context
                    for v in context.values():
                        if isinstance(v, (np.ndarray, pd.Series)):
                            length = len(v)
                            result = pd.Series([result] * length)
                            break
                # else: keep as scalar
            elif isinstance(result, pd.Series):
                # Already a Series
                pass
            
            return result
            
        except Exception as e:
            raise FormulaError(f"Formula evaluation failed: {str(e)}")
    
    def extract_dependencies(self, formula: str) -> list[str]:
        """Extract variable/column names from formula.
        
        Args:
            formula: Formula string using {name} syntax
            
        Returns:
            List of dependency names
        """
        pattern = r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}'
        matches = re.findall(pattern, formula)
        return list(set(matches))  # Remove duplicates
    
    def register_formula(self, target: str, formula: str):
        """Register formula and its dependencies.
        
        Args:
            target: Name of calculated variable/column
            formula: Formula string
        """
        deps = self.extract_dependencies(formula)
        self._dependencies[target] = set(deps)
    
    def get_dependencies(self, target: str) -> Set[str]:
        """Get dependencies for a target.
        
        Args:
            target: Variable/column name
            
        Returns:
            Set of dependency names
        """
        return self._dependencies.get(target, set()).copy()
    
    def get_calculation_order(self, changed: list[str]) -> list[str]:
        """Get order to recalculate formulas after changes.
        
        Args:
            changed: List of changed variable/column names
            
        Returns:
            Ordered list of targets to recalculate
            
        Raises:
            FormulaError: If circular dependency detected
        """
        # Find all affected targets using BFS
        affected = set()
        queue = list(changed)
        visited = set()
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            # Find targets that depend on current
            for target, deps in self._dependencies.items():
                if current in deps and target not in affected:
                    affected.add(target)
                    queue.append(target)
        
        # Topological sort
        sorted_targets = []
        remaining = affected.copy()
        
        max_iterations = len(remaining) + 1
        iteration = 0
        
        while remaining:
            iteration += 1
            if iteration > max_iterations:
                raise FormulaError(f"Circular dependency detected: {remaining}")
            
            # Find targets with no unresolved dependencies
            ready = []
            for target in remaining:
                deps = self._dependencies.get(target, set())
                unresolved = deps & remaining
                if not unresolved:
                    ready.append(target)
            
            if not ready:
                raise FormulaError(f"Circular dependency detected: {remaining}")
            
            sorted_targets.extend(sorted(ready))  # Sort for determinism
            remaining -= set(ready)
        
        return sorted_targets
    
    def validate_formula(self, formula: str, available: list[str]) -> tuple[bool, Optional[str]]:
        """Validate formula syntax and dependencies.
        
        Args:
            formula: Formula string to validate
            available: List of available variable/column names
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            deps = self.extract_dependencies(formula)
            missing = [d for d in deps if d not in available]
            
            if missing:
                return False, f"Undefined variables: {', '.join(missing)}"
            
            # Try to parse (basic syntax check)
            test_formula = formula
            for dep in deps:
                test_formula = test_formula.replace(f"{{{dep}}}", "1")
            
            try:
                compile(test_formula, "<string>", "eval")
            except SyntaxError as e:
                return False, f"Syntax error: {str(e)}"
            
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    def clear(self):
        """Clear all registered formulas."""
        self._dependencies.clear()
