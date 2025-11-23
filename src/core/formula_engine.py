"""
Unified formula evaluation engine.

Handles scalar, array, and table formulas with unit awareness
and uncertainty propagation.
"""

from __future__ import annotations
from typing import Any, Dict, Optional, Set
import re
import logging
import numpy as np
import pandas as pd
from sympy import sympify, symbols
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
import pint

from core.exceptions import (
    FormulaError,
    FormulaSyntaxError,
    FormulaEvaluationError,
    CircularDependencyError,
    MissingDependencyError
)

# Initialize unit registry
ureg = pint.UnitRegistry()

# Setup logger
logger = logging.getLogger(__name__)


class FormulaEngine:
    """Unified formula engine for all calculation types.
    
    Evaluates formulas with:
    - Scalar values (constants, variables)
    - Array operations (element-wise, automatic broadcasting)
    - Table operations (DataFrame operations)
    - Unit tracking and conversion
    - Uncertainty propagation (future)
    - Workspace constants (numeric, calculated, functions)
    
    Array Operations:
    - Standard operators (+, -, *, /, **, etc.) work element-wise automatically
    - No special syntax needed: {column} - 1 works element-wise on arrays
    - Mixing scalars and arrays: scalar is broadcast to match array length
    - Example: {velocity} * 2 multiplies each velocity value by 2
    - Example: {position} - {offset} subtracts element-wise if both are arrays
    - Example: {data} - np.mean({data}) subtracts scalar mean from each element
    
    Note: Python/numpy operators are already element-wise. MATLAB-style
    dot operators (.+, .-, .*, etc.) are NOT needed and NOT supported.
    """
    
    def __init__(self):
        """Initialize formula engine."""
        self._dependencies: Dict[str, Set[str]] = {}  # {target: {deps}}
        self._math_functions = self._build_math_context()
        
        # Performance caching
        self._workspace_cache: Dict[int, Dict[str, Any]] = {}  # {workspace_id: evaluated_constants}
        self._workspace_cache_version: Dict[int, int] = {}  # {workspace_id: version}
        self._compiled_formulas: Dict[str, tuple[str, list[str]]] = {}  # {formula: (eval_formula, deps)}
    
    def _build_math_context(self) -> Dict[str, Any]:
        """Build standard math function context.
        
        Returns:
            Dictionary of math functions for formula evaluation
        """
        return {
            'np': np,
            'pd': pd,
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
            # Array aggregate functions
            'len': len,
            'sum': np.sum,
            'mean': np.mean,
            'min': np.min,
            'max': np.max,
            'std': np.std,
            'median': np.median,
            'var': np.var,
            'cumsum': np.cumsum,
            'cumprod': np.cumprod,
            'diff': np.diff,
            'round': np.round,
            'floor': np.floor,
            'ceil': np.ceil,
            'sign': np.sign,
        }
    
    def evaluate_constant(
        self,
        const_name: str,
        const_data: Dict[str, Any],
        all_constants: Dict[str, Dict[str, Any]],
        context: Dict[str, Any],
        visited: Optional[Set[str]] = None,
        suppress_warnings: bool = False
    ) -> Any:
        """Evaluate a workspace constant (numeric, calculated, or function).
        
        Args:
            const_name: Name of constant to evaluate
            const_data: Constant definition data
            all_constants: Dictionary of all workspace constants
            context: Optional existing context to check for cached values
            visited: Set of constants being evaluated (for circular dep detection)
            suppress_warnings: Whether to suppress warning messages
            
        Returns:
            Evaluated constant value (scalar for numeric/calculated, callable for function)
            
        Raises:
            ValueError: If circular dependency detected
        """
        # Return cached value if already computed
        if const_name in context:
            return context[const_name]
        
        const_type = const_data.get("type")
        
        # Fast path for numeric constants
        if const_type == "constant":
            value = const_data["value"]
            context[const_name] = value
            return value
        
        # Initialize visited set for circular dependency detection
        if visited is None:
            visited = set()
        
        # Check for circular dependency
        if const_name in visited:
            raise ValueError(f"Circular dependency detected: {const_name}")
        
        # Add to visited set
        visited = visited.copy()
        visited.add(const_name)
        
        if const_type == "calculated":
            return self._evaluate_calculated_constant(
                const_name, const_data, context, suppress_warnings
            )
        
        elif const_type == "function":
            return self._evaluate_function_constant(
                const_name, const_data, context
            )
        
        return None
    
    def _evaluate_calculated_constant(
        self,
        const_name: str,
        const_data: Dict[str, Any],
        context: Dict[str, Any],
        suppress_warnings: bool
    ) -> Any:
        """Evaluate a calculated constant.
        
        Args:
            const_name: Constant name
            const_data: Constant data dictionary
            context: Evaluation context
            suppress_warnings: Whether to suppress warnings
            
        Returns:
            Evaluated value or None on error
        """
        calc_formula = const_data["formula"]
        
        # Build evaluation context
        calc_context = self._math_functions.copy()
        calc_context.update(context)
        
        # Evaluate the formula
        try:
            result = eval(calc_formula, {"__builtins__": {}}, calc_context)
            context[const_name] = result
            return result
        except Exception as e:
            if not suppress_warnings:
                logger.warning(f"Failed to evaluate calculated constant '{const_name}': {e}")
            return None
    
    def _evaluate_function_constant(
        self,
        const_name: str,
        const_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Any:
        """Evaluate a function constant.
        
        Args:
            const_name: Constant name
            const_data: Constant data dictionary
            context: Evaluation context
            
        Returns:
            Callable function
        """
        func_formula = const_data["formula"]
        func_params = const_data["parameters"]
        
        # Replace {param} placeholders with param names
        eval_formula = func_formula
        for param in func_params:
            eval_formula = eval_formula.replace(f"{{{param}}}", param)
        
        # Create closure that captures formula and parameters
        def make_function(formula_str, params, math_funcs):
            def custom_function(*args):
                if len(args) != len(params):
                    raise ValueError(f"Expected {len(params)} arguments, got {len(args)}")
                func_context = math_funcs.copy()
                for param, value in zip(params, args):
                    func_context[param] = value
                return eval(formula_str, {"__builtins__": {}}, func_context)
            return custom_function
        
        func = make_function(eval_formula, func_params, self._math_functions)
        context[const_name] = func
        return func
    
    def build_context_with_workspace(
        self,
        base_context: Dict[str, Any],
        workspace_constants: Optional[Dict[str, Dict[str, Any]]] = None,
        workspace_id: Optional[int] = None,
        workspace_version: int = 0
    ) -> Dict[str, Any]:
        """Build complete evaluation context including workspace constants.
        
        Uses caching to avoid re-evaluating workspace constants on every call.
        
        Args:
            base_context: Base context with columns/variables
            workspace_constants: Optional workspace constants dictionary
            workspace_id: Optional workspace ID for caching (use id(workspace))
            workspace_version: Workspace version number for cache invalidation
            
        Returns:
            Complete evaluation context
        """
        # Start with base context (columns/variables)
        context = base_context.copy()
        
        # Add math functions (reuse same dict without copying)
        context.update(self._math_functions)
        
        # Add workspace constants if provided
        if workspace_constants:
            # Try to use cached evaluation
            if workspace_id is not None:
                cached_version = self._workspace_cache_version.get(workspace_id, -1)
                if cached_version == workspace_version and workspace_id in self._workspace_cache:
                    # Cache hit - reuse evaluated constants
                    context.update(self._workspace_cache[workspace_id])
                    return context
            
            # Cache miss - evaluate and cache
            constants_context = self._evaluate_workspace_constants(workspace_constants)
            
            # Cache the result
            if workspace_id is not None:
                self._workspace_cache[workspace_id] = constants_context
                self._workspace_cache_version[workspace_id] = workspace_version
            
            context.update(constants_context)
        
        return context
    
    def _evaluate_workspace_constants(
        self,
        workspace_constants: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Evaluate all workspace constants and return as context dict.
        
        Args:
            workspace_constants: Dictionary of workspace constants
            
        Returns:
            Dictionary of evaluated constant values
        """
        constants_context = {}
        
        # Evaluate constants in multiple passes to handle dependencies
        remaining = set(workspace_constants.keys())
        max_passes = len(workspace_constants) + 1
        pass_count = 0
        
        while remaining and pass_count < max_passes:
            progress = False
            # Suppress warnings on all but the last pass
            is_last_pass = pass_count >= max_passes - 1
            
            for const_name in list(remaining):
                const_data = workspace_constants[const_name]
                result = self.evaluate_constant(
                    const_name, const_data, workspace_constants, constants_context,
                    suppress_warnings=not is_last_pass
                )
                if result is not None or const_data.get("type") == "function":
                    remaining.remove(const_name)
                    progress = True
            
            if not progress:
                # No progress made, remaining constants have circular dependencies or errors
                # Try one more time with warnings enabled to show actual errors
                if not is_last_pass:
                    for const_name in remaining:
                        const_data = workspace_constants[const_name]
                        self.evaluate_constant(
                            const_name, const_data, workspace_constants, constants_context,
                            suppress_warnings=False
                        )
                break
            pass_count += 1
        
        return constants_context
    
    def invalidate_workspace_cache(self, workspace_id: Optional[int] = None):
        """Invalidate workspace constants cache.
        
        Args:
            workspace_id: Optional workspace ID to invalidate. If None, clears all.
        """
        if workspace_id is None:
            self._workspace_cache.clear()
            self._workspace_cache_version.clear()
        else:
            self._workspace_cache.pop(workspace_id, None)
            self._workspace_cache_version.pop(workspace_id, None)
        
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
            # Check if formula is already compiled
            if formula in self._compiled_formulas:
                eval_formula, deps = self._compiled_formulas[formula]
            else:
                # Extract dependencies
                deps = self.extract_dependencies(formula)
                
                # Replace {var} with var for evaluation
                eval_formula = formula
                for dep in deps:
                    eval_formula = eval_formula.replace(f"{{{dep}}}", dep)
                
                # Cache the compiled formula
                self._compiled_formulas[formula] = (eval_formula, deps)
            
            # Check all dependencies are available
            missing = [d for d in deps if d not in context]
            if missing:
                raise FormulaError(f"Missing variables: {', '.join(missing)}")
            
            # Build evaluation context - reuse math functions dict
            eval_context = context.copy()
            eval_context.update(self._math_functions)
            
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
    
    def rename_variable(self, old_name: str, new_name: str):
        """Rename a variable in all registered formulas.
        
        Args:
            old_name: Current variable name
            new_name: New variable name
        """
        # Update dependencies: if old_name is a dependency, replace with new_name
        for target, deps in self._dependencies.items():
            if old_name in deps:
                deps.remove(old_name)
                deps.add(new_name)
        
        # If old_name was a target, rename it
        if old_name in self._dependencies:
            self._dependencies[new_name] = self._dependencies.pop(old_name)
    
    def clear(self):
        """Clear all registered formulas."""
        self._dependencies.clear()
