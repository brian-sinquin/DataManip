"""
Uncertainty propagation for DataTableV2 calculated columns.

This module provides automatic uncertainty propagation for calculated columns
using the standard error propagation formula:
    δf = sqrt(Σ(∂f/∂xᵢ * δxᵢ)²)

The propagation uses SymPy for symbolic differentiation and supports:
- Simple arithmetic operations (+, -, *, /, **)
- Mathematical functions (sin, cos, exp, log, sqrt, etc.)
- Multiple variable dependencies
- Unit-aware calculations
"""

import ast
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Set, Any
import sympy as sp

from .formula_parser import FormulaParser


class UncertaintyPropagator:
    """Handles automatic uncertainty propagation for calculated columns.
    
    This class integrates with DataTableModel to automatically calculate
    and update uncertainty columns when data or uncertainties change.
    """
    
    # Map AST operators to SymPy equivalents (for formula conversion)
    @staticmethod
    def formula_to_sympy(formula: str, variable_names: List[str]) -> sp.Expr:
        """Convert a formula string to SymPy symbolic expression.
        
        Args:
            formula: Formula string (e.g., "{A} + {B}")
            variable_names: List of variable names referenced in formula
            
        Returns:
            SymPy expression
            
        Raises:
            ValueError: If formula contains unsupported operations
        """
        import ast
        
        # Replace {var} with var for parsing
        expr_str = formula
        for var in variable_names:
            expr_str = expr_str.replace(f"{{{var}}}", var)
        
        try:
            # Parse to AST
            tree = ast.parse(expr_str, mode='eval')
            
            # Create SymPy symbols
            symbols = {name: sp.Symbol(name) for name in variable_names}
            
            # Convert AST to SymPy
            return UncertaintyPropagator._ast_to_sympy(tree.body, symbols)
            
        except Exception as e:
            raise ValueError(f"Cannot convert formula to symbolic form: {e}")
    
    @staticmethod
    def _ast_to_sympy(node: ast.AST, symbols: Dict[str, sp.Symbol]) -> Any:
        """Recursively convert AST nodes to SymPy expressions."""
        import ast
        
        if isinstance(node, ast.Constant):
            return sp.sympify(node.value)
        
        elif isinstance(node, ast.Name):
            if node.id in symbols:
                return symbols[node.id]
            elif node.id == 'pi':
                return sp.pi
            elif node.id == 'e':
                return sp.E
            else:
                raise ValueError(f"Unknown variable: {node.id}")
        
        elif isinstance(node, ast.BinOp):
            left = UncertaintyPropagator._ast_to_sympy(node.left, symbols)
            right = UncertaintyPropagator._ast_to_sympy(node.right, symbols)
            
            if isinstance(node.op, ast.Add):
                return left + right
            elif isinstance(node.op, ast.Sub):
                return left - right
            elif isinstance(node.op, ast.Mult):
                return left * right
            elif isinstance(node.op, ast.Div):
                return left / right
            elif isinstance(node.op, ast.Pow):
                return left ** right
            else:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        
        elif isinstance(node, ast.UnaryOp):
            operand = UncertaintyPropagator._ast_to_sympy(node.operand, symbols)
            if isinstance(node.op, ast.USub):
                return -operand
            elif isinstance(node.op, ast.UAdd):
                return operand
            else:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
        
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                args = [UncertaintyPropagator._ast_to_sympy(arg, symbols) for arg in node.args]
                
                # Map function names to SymPy functions
                func_map = {
                    'abs': sp.Abs,
                    'sqrt': sp.sqrt,
                    'sin': sp.sin,
                    'cos': sp.cos,
                    'tan': sp.tan,
                    'log': sp.log,
                    'log10': lambda x: sp.log(x, 10),
                    'exp': sp.exp,
                }
                
                if func_name in func_map:
                    return func_map[func_name](*args)
                else:
                    raise ValueError(f"Unsupported function: {func_name}")
            else:
                raise ValueError("Complex function calls not supported")
        
        else:
            raise ValueError(f"Unsupported expression element: {type(node).__name__}")
    
    @staticmethod
    def calculate_uncertainty(
        formula: str,
        variable_names: List[str],
        values: Dict[str, pd.Series],
        uncertainties: Dict[str, pd.Series]
    ) -> pd.Series:
        """Calculate propagated uncertainty for all rows.
        
        Args:
            formula: Formula string (e.g., "{A} + {B}")
            variable_names: List of variable names in formula
            values: Dict mapping variable names to their value Series
            uncertainties: Dict mapping variable names to their uncertainty Series
            
        Returns:
            Series of propagated uncertainties
            
        Example:
            >>> formula = "{A} + {B}"
            >>> values = {"A": pd.Series([1, 2, 3]), "B": pd.Series([10, 20, 30])}
            >>> uncerts = {"A": pd.Series([0.1, 0.1, 0.1]), "B": pd.Series([0.5, 0.5, 0.5])}
            >>> result = calculate_uncertainty(formula, ["A", "B"], values, uncerts)
            >>> # Result: sqrt(0.1² + 0.5²) = 0.509... for all rows
        """
        # Convert formula to SymPy expression
        try:
            sympy_expr = UncertaintyPropagator.formula_to_sympy(formula, variable_names)
        except Exception as e:
            # If conversion fails, return NaN series
            length = len(next(iter(values.values()))) if values else 0
            return pd.Series([np.nan] * length)
        
        # Calculate partial derivatives
        partial_derivs = {}
        for var_name in variable_names:
            var_symbol = sp.Symbol(var_name)
            partial_derivs[var_name] = sp.diff(sympy_expr, var_symbol)
        
        # Get length from first value series
        length = len(next(iter(values.values()))) if values else 0
        
        # Calculate uncertainty for each row
        result_uncertainties = []
        
        for i in range(length):
            # Get values for this row
            row_values = {var: values[var].iloc[i] for var in variable_names}
            row_uncerts = {var: uncertainties.get(var, pd.Series([0.0] * length)).iloc[i] 
                          for var in variable_names}
            
            # If any input value is NaN, result uncertainty is NaN
            if any(pd.isna(row_values[var]) for var in variable_names):
                result_uncertainties.append(np.nan)
                continue
            
            # Calculate variance contributions
            variance = 0.0
            
            for var_name in variable_names:
                # Skip if no uncertainty for this variable
                if var_name not in uncertainties:
                    continue
                
                # Get value and uncertainty for this variable
                var_value = row_values[var_name]
                var_uncert = row_uncerts[var_name]
                
                # Skip if uncertainty is NaN
                if pd.isna(var_uncert):
                    continue
                
                # Evaluate partial derivative at this point
                try:
                    # Substitute all variable values
                    subs_dict = {sp.Symbol(name): val for name, val in row_values.items() 
                                if not pd.isna(val)}
                    deriv_value = float(partial_derivs[var_name].evalf(subs=subs_dict))
                    
                    # Add contribution to variance: (∂f/∂xᵢ * δxᵢ)²
                    contribution = deriv_value * var_uncert
                    variance += contribution ** 2
                    
                except Exception:
                    # If evaluation fails (e.g., division by zero), mark as NaN
                    variance = np.nan
                    break
            
            # Combined uncertainty = sqrt(variance)
            if pd.isna(variance):
                result_uncertainties.append(np.nan)
            else:
                result_uncertainties.append(np.sqrt(variance))
        
        return pd.Series(result_uncertainties)
    
    @staticmethod
    def get_formula_dependencies(formula: str) -> Set[str]:
        """Extract variable names from formula.
        
        Args:
            formula: Formula string with variables in {braces}
            
        Returns:
            Set of variable names
        """
        import re
        # Find all {variable} patterns
        pattern = r'\{([^}]+)\}'
        matches = re.findall(pattern, formula)
        return set(matches)
    
    @staticmethod
    def get_uncertainty_column_name(column_name: str) -> str:
        """Get the standard uncertainty column name for a data column.
        
        Args:
            column_name: Name of the data column
            
        Returns:
            Name for the uncertainty column (e.g., "A" -> "A_u")
        """
        return f"{column_name}_u"
    
    @staticmethod
    def has_uncertainty_column(column_name: str, available_columns: List[str]) -> bool:
        """Check if an uncertainty column exists for the given data column.
        
        Args:
            column_name: Name of the data column
            available_columns: List of all available column names
            
        Returns:
            True if uncertainty column exists
        """
        uncert_name = UncertaintyPropagator.get_uncertainty_column_name(column_name)
        return uncert_name in available_columns
    
    @staticmethod
    def get_available_uncertainties(
        variable_names: List[str],
        available_columns: List[str]
    ) -> Set[str]:
        """Get which variables have uncertainty columns available.
        
        Args:
            variable_names: List of variables used in formula
            available_columns: List of all available column names
            
        Returns:
            Set of variable names that have uncertainty columns
        """
        return {
            var for var in variable_names
            if UncertaintyPropagator.has_uncertainty_column(var, available_columns)
        }
