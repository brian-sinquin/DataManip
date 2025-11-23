"""
Uncertainty propagation calculations.

Handles symbolic differentiation and numerical uncertainty propagation
for calculated columns using the formula: δf = √(Σ(∂f/∂xᵢ · δxᵢ)²)
"""

from __future__ import annotations
from typing import Dict, List, Optional, Set
import pandas as pd
import numpy as np
import sympy as sp

from utils.uncertainty import FormulaToSymPy


class UncertaintyPropagator:
    """Handles uncertainty propagation for calculated columns."""
    
    @staticmethod
    def calculate_propagated_uncertainty(
        formula: str,
        dependencies: List[str],
        values: Dict[str, pd.Series],
        uncertainties: Dict[str, pd.Series],
        workspace_constants: Optional[Dict[str, Dict]] = None,
        math_functions: Optional[Dict] = None
    ) -> pd.Series:
        """Calculate propagated uncertainty using symbolic differentiation.
        
        Args:
            formula: Formula expression with {variable} placeholders
            dependencies: List of variable names in formula
            values: Dictionary mapping variable names to value Series
            uncertainties: Dictionary mapping variable names to uncertainty Series
            workspace_constants: Optional workspace constants for substitution
            math_functions: Optional math function context
            
        Returns:
            Series of propagated uncertainties
            
        Raises:
            ValueError: If formula cannot be parsed or evaluated
        """
        if not values:
            return pd.Series([np.nan] * len(next(iter(values.values()))))
        
        data_length = len(next(iter(values.values())))
        workspace_constants = workspace_constants or {}
        
        # Prepare formula for SymPy (remove curly braces and np. prefix)
        formula_for_sympy = formula
        for dep in dependencies:
            formula_for_sympy = formula_for_sympy.replace(f"{{{dep}}}", dep)
        formula_for_sympy = formula_for_sympy.replace("np.", "")
        
        # Filter to only column dependencies (not workspace constants)
        column_deps = list(values.keys())
        
        try:
            # Convert to SymPy expression
            sympy_expr = FormulaToSymPy.convert(formula_for_sympy, list(dependencies))
            
            # Calculate partial derivatives only for column dependencies
            partial_derivs = {}
            for var_name in column_deps:
                var_symbol = sp.Symbol(var_name)
                partial_derivs[var_name] = sp.diff(sympy_expr, var_symbol)
            
            # Calculate uncertainty for each row
            result_uncertainties = []
            
            for i in range(data_length):
                uncertainty = UncertaintyPropagator._calculate_row_uncertainty(
                    i, column_deps, dependencies, values, uncertainties,
                    partial_derivs, workspace_constants
                )
                result_uncertainties.append(uncertainty)
            
            return pd.Series(result_uncertainties)
            
        except Exception:
            # If calculation fails, return NaN
            return pd.Series([np.nan] * data_length)
    
    @staticmethod
    def _calculate_row_uncertainty(
        row_index: int,
        column_deps: List[str],
        all_deps: List[str],
        values: Dict[str, pd.Series],
        uncertainties: Dict[str, pd.Series],
        partial_derivs: Dict[str, sp.Expr],
        workspace_constants: Dict[str, Dict]
    ) -> float:
        """Calculate uncertainty for a single row.
        
        Args:
            row_index: Row index to calculate
            column_deps: Column dependencies (variables in table)
            all_deps: All dependencies (including workspace constants)
            values: Value series dictionary
            uncertainties: Uncertainty series dictionary
            partial_derivs: Partial derivatives dictionary
            workspace_constants: Workspace constants dictionary
            
        Returns:
            Calculated uncertainty value for the row
        """
        # Get values for this row (only for column dependencies)
        row_values = {var: values[var].iloc[row_index] for var in column_deps}
        row_uncerts = {var: uncertainties[var].iloc[row_index] for var in column_deps}
        
        # If any input value is NaN, result uncertainty is NaN
        if any(pd.isna(row_values[var]) for var in column_deps):
            return np.nan
        
        # Calculate variance contributions
        variance = 0.0
        
        for var_name in column_deps:
            var_uncert = row_uncerts[var_name]
            
            # Skip if uncertainty is NaN or 0 (no contribution)
            if pd.isna(var_uncert) or var_uncert == 0:
                continue
            
            try:
                # Build substitution dictionary with column values
                subs_dict = {
                    sp.Symbol(var): val 
                    for var, val in row_values.items() 
                    if not pd.isna(val)
                }
                
                # Add workspace constants to substitution
                for dep in all_deps:
                    if dep not in column_deps and dep in workspace_constants:
                        const_info = workspace_constants[dep]
                        if const_info["type"] == "constant":
                            subs_dict[sp.Symbol(dep)] = const_info["value"]
                        elif const_info["type"] == "calculated" and "value" in const_info:
                            subs_dict[sp.Symbol(dep)] = const_info["value"]
                
                # Evaluate partial derivative
                deriv_value = float(partial_derivs[var_name].evalf(subs=subs_dict))
                
                # Add contribution to variance: (∂f/∂xᵢ * δxᵢ)²
                contribution = deriv_value * var_uncert
                variance += contribution ** 2
                
            except Exception:
                return np.nan
        
        # Combined uncertainty = sqrt(variance)
        return np.sqrt(variance) if not pd.isna(variance) else np.nan
    
    @staticmethod
    def build_propagated_formula_string(
        dependencies: List[str],
        column_names: Set[str],
        partial_derivs: Dict[str, sp.Expr]
    ) -> str:
        """Build ASCII representation of propagated uncertainty formula.
        
        Args:
            dependencies: List of all dependencies
            column_names: Set of column names (to filter out constants)
            partial_derivs: Partial derivatives dictionary
            
        Returns:
            ASCII formula string like "sqrt((∂f/∂x * δx)² + (∂f/∂y * δy)²)"
        """
        terms = []
        for var in dependencies:
            if var in column_names and f"{var}_u" in column_names:
                terms.append(f"(∂f/∂{var} * δ{var})²")
        
        if terms:
            return "sqrt(" + " + ".join(terms) + ")"
        return ""
