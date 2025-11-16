"""Calculation engine for AdvancedDataTableWidget.

This module handles all calculation operations including:
- Formula evaluation for calculated columns
- Derivative calculations (discrete dy/dx)
- Uncertainty propagation
- Recalculation orchestration
"""

from typing import Optional, Dict, Any, List, Callable, Tuple
import numpy as np

from .models import AdvancedColumnType, ColumnMetadata
from .formula_evaluator import SafeFormulaEvaluator
from .constants import ERROR_PREFIX
from .exceptions import (
    FormulaEvaluationError,
    UncertaintyCalculationError
)
from utils.uncertainty import UncertaintyCalculator


class CalculationEngine:
    """Handles all calculations for the data table.
    
    This class orchestrates formula evaluation, derivative calculations,
    and uncertainty propagation for calculated columns.
    
    Attributes:
        _formula_evaluator: Safe formula evaluation engine
        _uncertainty_calculator: Uncertainty propagation calculator
        _variables: Global variables available in formulas
    """
    
    def __init__(self):
        """Initialize the calculation engine."""
        self._formula_evaluator = SafeFormulaEvaluator()
        self._uncertainty_calculator = UncertaintyCalculator()
        self._variables: Dict[str, float] = {}
    
    def set_variables(self, variables: Dict[str, float]):
        """Set global variables for formula evaluation.
        
        Args:
            variables: Dictionary of variable name -> value
        """
        self._variables = variables.copy()
    
    def get_variables(self) -> Dict[str, float]:
        """Get current global variables.
        
        Returns:
            Copy of variables dictionary
        """
        return self._variables.copy()
    
    def evaluate_formula(
        self,
        formula: str,
        column_values: Dict[str, Any],
        row_index: int
    ) -> Tuple[Optional[float], Optional[str], Optional[str]]:
        """Evaluate a formula for a specific row.
        
        Args:
            formula: Formula string with {diminutive} references
            column_values: Dictionary of diminutive -> (value, unit) for all columns
            row_index: Row index being calculated
            
        Returns:
            Tuple of (result_value, result_unit, error_message)
            - result_value: Calculated numeric value or None on error
            - result_unit: Unit string or None
            - error_message: Error message or None if successful
        """
        try:
            # Merge column values with global variables
            # Variables are plain numbers, column_values are (value, unit) tuples
            eval_context = {}
            for name, value in self._variables.items():
                eval_context[name] = (value, None)  # Variables are unitless
            eval_context.update(column_values)
            
            # Evaluate formula with units
            value, unit = self._formula_evaluator.evaluate_with_units(formula, eval_context)
            
            return value, unit, None
            
        except Exception as e:
            error_msg = f"{ERROR_PREFIX} Row {row_index}: {str(e)}"
            return None, None, error_msg
    
    def calculate_derivative(
        self,
        numerator_values: List[float],
        denominator_values: List[float],
        row_index: int
    ) -> Optional[float]:
        """Calculate discrete derivative at a specific row.
        
        Uses forward difference: dy/dx = (y[i+1] - y[i]) / (x[i+1] - x[i])
        Last row returns None (derivative undefined for forward difference).
        
        Args:
            numerator_values: List of y values
            denominator_values: List of x values
            row_index: Row index to calculate derivative for
            
        Returns:
            Derivative value or None if cannot be calculated
        """
        try:
            total_rows = len(numerator_values)
            
            # Validate arrays have same length
            if len(denominator_values) != total_rows:
                return None
            
            # Check if we have at least 2 points
            if total_rows < 2:
                return None
            
            # Last row: derivative is undefined for forward difference
            if row_index >= total_rows - 1:
                return None
            
            # Forward difference: use current and next row
            y_diff = numerator_values[row_index + 1] - numerator_values[row_index]
            x_diff = denominator_values[row_index + 1] - denominator_values[row_index]
            
            # Avoid division by zero
            if abs(x_diff) < 1e-15:
                return None
            
            return y_diff / x_diff
            
        except (ValueError, TypeError, IndexError):
            return None
    
    def calculate_uncertainty(
        self,
        formula: str,
        column_values: Dict[str, float],
        uncertainty_values: Dict[str, float],
        row_index: int
    ) -> Tuple[Optional[float], Optional[str]]:
        """Calculate propagated uncertainty for a formula.
        
        Uses the formula: δf = sqrt(Σ(∂f/∂xᵢ * δxᵢ)²)
        
        Args:
            formula: Formula string with {diminutive} references
            column_values: Dictionary of diminutive -> value
            uncertainty_values: Dictionary of diminutive -> uncertainty
            row_index: Row index being calculated
            
        Returns:
            Tuple of (uncertainty_value, error_message)
            - uncertainty_value: Calculated uncertainty or None on error
            - error_message: Error message or None if successful
        """
        try:
            # Filter out variables with no uncertainty
            filtered_uncertainties = {
                key: val for key, val in uncertainty_values.items()
                if val is not None and val > 0
            }
            
            if not filtered_uncertainties:
                # No uncertainties to propagate
                return None, None
            
            # Calculate combined uncertainty using the correct API
            uncertainty = self._uncertainty_calculator.calculate_uncertainty(
                formula,
                column_values,
                filtered_uncertainties
            )
            
            return uncertainty, None
            
        except Exception as e:
            error_msg = f"{ERROR_PREFIX} Row {row_index} uncertainty: {str(e)}"
            return None, error_msg
    
    def recalculate_column(
        self,
        metadata: ColumnMetadata,
        column_index: int,
        get_column_values: Callable,
        get_uncertainty_values: Callable,
        row_count: int
    ) -> List[Tuple[Optional[float], Optional[str], Optional[float], Optional[str]]]:
        """Recalculate all values in a column.
        
        Args:
            metadata: Column metadata
            column_index: Column index
            get_column_values: Function(row) -> Dict[str, Any] to get column values
            get_uncertainty_values: Function(row) -> Dict[str, float] to get uncertainties
            row_count: Total number of rows
            
        Returns:
            List of tuples for each row: (value, unit, uncertainty, error)
        """
        if metadata.column_type == AdvancedColumnType.CALCULATED:
            return self._recalculate_calculated_column(
                metadata, column_index, get_column_values, get_uncertainty_values, row_count
            )
        elif metadata.column_type == AdvancedColumnType.DERIVATIVE:
            return self._recalculate_derivative_column(
                metadata, column_index, get_column_values, row_count
            )
        else:
            # Not a calculated column type
            return []
    
    def _recalculate_calculated_column(
        self,
        metadata: ColumnMetadata,
        column_index: int,
        get_column_values: Callable,
        get_uncertainty_values: Callable,
        row_count: int
    ) -> List[Tuple[Optional[float], Optional[str], Optional[float], Optional[str]]]:
        """Recalculate a CALCULATED column.
        
        Args:
            metadata: Column metadata
            column_index: Column index
            get_column_values: Function to get column values for a row
            get_uncertainty_values: Function to get uncertainties for a row
            row_count: Total number of rows
            
        Returns:
            List of (value, unit, uncertainty, error) tuples
        """
        if not metadata.formula:
            return []
        
        results = []
        
        for row in range(row_count):
            # Get column values for this row
            col_vals = get_column_values(row)
            
            # Evaluate formula
            value, unit, error = self.evaluate_formula(metadata.formula, col_vals, row)
            
            # Calculate uncertainty if enabled
            uncertainty = None
            unc_error = None
            
            if metadata.propagate_uncertainty and value is not None:
                unc_vals = get_uncertainty_values(row)
                uncertainty, unc_error = self.calculate_uncertainty(
                    metadata.formula, col_vals, unc_vals, row
                )
            
            results.append((value, unit, uncertainty, unc_error or error))
        
        return results
    
    def _recalculate_derivative_column(
        self,
        metadata: ColumnMetadata,
        column_index: int,
        get_column_values: Callable,
        row_count: int
    ) -> List[Tuple[Optional[float], Optional[str], Optional[float], Optional[str]]]:
        """Recalculate a DERIVATIVE column.
        
        Args:
            metadata: Column metadata
            column_index: Column index
            get_column_values: Function to get column values for a row
            row_count: Total number of rows
            
        Returns:
            List of (value, unit, uncertainty, error) tuples
        """
        if metadata.derivative_numerator is None or metadata.derivative_denominator is None:
            return []
        
        # Extract all numerator and denominator values
        numerator_values = []
        denominator_values = []
        
        for row in range(row_count):
            col_vals = get_column_values(row)
            
            # Get diminutives for numerator/denominator
            # Note: This assumes get_column_values returns a dict with diminutive keys
            # The actual implementation will need to handle this mapping
            numerator_values.append(col_vals.get(f"col_{metadata.derivative_numerator}"))
            denominator_values.append(col_vals.get(f"col_{metadata.derivative_denominator}"))
        
        # Calculate derivatives for each row
        results = []
        
        for row in range(row_count):
            value = self.calculate_derivative(numerator_values, denominator_values, row)
            
            # Derivative columns don't have uncertainty propagation yet
            # Unit is calculated separately in the widget
            results.append((value, None, None, None))
        
        return results
    
    def validate_formula(self, formula: str, available_diminutives: List[str]) -> Tuple[bool, Optional[str]]:
        """Validate a formula without evaluating it.
        
        Args:
            formula: Formula string to validate
            available_diminutives: List of valid diminutives
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check for empty formula
            if not formula or not formula.strip():
                return False, "Formula cannot be empty"
            
            # Extract references
            from .column_manager import ColumnManager
            temp_manager = ColumnManager()
            refs = temp_manager.extract_formula_references(formula)
            
            # Check if all references are valid
            invalid_refs = [ref for ref in refs if ref not in available_diminutives and ref not in self._variables]
            
            if invalid_refs:
                return False, f"Unknown references: {', '.join(invalid_refs)}"
            
            # Try to parse by attempting evaluation with dummy values
            try:
                test_values = {}
                for dim in available_diminutives:
                    test_values[dim] = (1.0, None)
                for var in self._variables:
                    test_values[var] = (1.0, None)
                self._formula_evaluator.evaluate_with_units(formula, test_values)
            except Exception as e:
                return False, f"Syntax error: {str(e)}"
            
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    def preview_formula_unit(
        self,
        formula: str,
        column_units: Dict[str, str]
    ) -> Optional[str]:
        """Preview the resulting unit of a formula.
        
        Args:
            formula: Formula string
            column_units: Dictionary of diminutive -> unit
            
        Returns:
            Predicted unit string or None if cannot be determined
        """
        try:
            # Create sample values (all 1.0) with units
            sample_values = {}
            
            for dim, unit in column_units.items():
                sample_values[dim] = (1.0, unit) if unit else (1.0, None)
            
            # Add variables
            for var_name, var_value in self._variables.items():
                if var_name not in sample_values:
                    sample_values[var_name] = (var_value, None)
            
            # Evaluate to get unit
            _, unit = self._formula_evaluator.evaluate_with_units(formula, sample_values)
            
            return unit
            
        except Exception:
            return None
    
    def get_formula_dependencies(self, formula: str) -> List[str]:
        """Get all column diminutives referenced in a formula.
        
        Args:
            formula: Formula string
            
        Returns:
            List of referenced diminutives (excluding global variables)
        """
        from .column_manager import ColumnManager
        temp_manager = ColumnManager()
        all_refs = temp_manager.extract_formula_references(formula)
        
        # Filter out global variables
        column_refs = [ref for ref in all_refs if ref not in self._variables]
        
        return column_refs
