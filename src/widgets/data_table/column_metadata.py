"""
Column metadata definitions for DataTableV2.

This module defines the column types and metadata structure used in the new
data table implementation.
"""

from dataclasses import dataclass, field
from typing import Optional

from constants.column_types import ColumnType
from constants.data_types import DataType


@dataclass
class ColumnMetadata:
    """Metadata for a single column.
    
    This is a lightweight dataclass that stores all information about a column
    including its type, name, unit, and type-specific parameters.
    
    Attributes:
        name: Column name (used in formulas and display)
        column_type: Type of column (DATA, CALCULATED, etc.)
        dtype: Data type for storage (FLOAT, INTEGER, STRING, etc.)
        unit: Physical unit (e.g., 'm', 's', 'kg')
        description: Human-readable description
        
        # Formula-related (for CALCULATED columns)
        formula: Formula expression using {name} syntax
        
        # Derivative-related (for DERIVATIVE columns)
        derivative_numerator: Name of numerator column (dy)
        derivative_denominator: Name of denominator column (dx)
        
        # Range-related (for RANGE columns)
        range_start: Start value
        range_end: End value
        range_points: Number of points
        
        # Interpolation-related (for INTERPOLATION columns)
        interp_x_column: Name of X data column
        interp_y_column: Name of Y data column
        interp_method: Interpolation method ('linear', 'cubic', etc.)
        
        # Uncertainty-related (for UNCERTAINTY columns)
        uncertainty_reference: Name of column this uncertainty belongs to
        
        # Display properties
        precision: Number of decimal places for display
        editable: Whether users can edit this column
    """
    
    name: str
    column_type: ColumnType
    dtype: DataType = DataType.FLOAT
    unit: Optional[str] = None
    description: Optional[str] = None
    
    # Formula properties
    formula: Optional[str] = None
    propagate_uncertainty: bool = False  # If True, auto-calculate uncertainty for this column
    
    # Derivative properties
    derivative_numerator: Optional[str] = None
    derivative_denominator: Optional[str] = None
    
    # Range properties
    range_start: Optional[float] = None
    range_end: Optional[float] = None
    range_points: Optional[int] = None
    
    # Interpolation properties
    interp_x_column: Optional[str] = None
    interp_y_column: Optional[str] = None
    interp_eval_column: Optional[str] = None  # Column to evaluate interpolation at (if different from x)
    interp_method: Optional[str] = "linear"
    
    # Uncertainty properties
    uncertainty_reference: Optional[str] = None
    
    # Display properties
    precision: int = 6
    editable: bool = field(init=False)
    
    def __post_init__(self):
        """Set derived properties after initialization."""
        # Only DATA columns and manually-created UNCERTAINTY columns are editable
        # Propagated uncertainty columns (with uncertainty_reference set) are read-only
        # RANGE, CALCULATED, and DERIVATIVE columns are always read-only (auto-generated)
        if self.column_type == ColumnType.DATA:
            self.editable = True
        elif self.column_type == ColumnType.UNCERTAINTY:
            # Uncertainty columns are only editable if they're manual (no reference)
            # Propagated uncertainty columns (with uncertainty_reference) are read-only
            self.editable = self.uncertainty_reference is None
        else:
            # CALCULATED, DERIVATIVE, RANGE, INTERPOLATION are always read-only
            self.editable = False
        
        # Force numeric types for calculated columns
        if self.column_type in (ColumnType.CALCULATED, ColumnType.DERIVATIVE, 
                               ColumnType.RANGE, ColumnType.UNCERTAINTY):
            self.dtype = DataType.FLOAT
    
    def is_data_column(self) -> bool:
        """Check if this is a DATA column."""
        return self.column_type == ColumnType.DATA
    
    def is_calculated_column(self) -> bool:
        """Check if this is a CALCULATED column."""
        return self.column_type == ColumnType.CALCULATED
    
    def is_derivative_column(self) -> bool:
        """Check if this is a DERIVATIVE column."""
        return self.column_type == ColumnType.DERIVATIVE
    
    def is_range_column(self) -> bool:
        """Check if this is a RANGE column."""
        return self.column_type == ColumnType.RANGE
    
    def is_interpolation_column(self) -> bool:
        """Check if this is an INTERPOLATION column."""
        return self.column_type == ColumnType.INTERPOLATION
    
    def is_uncertainty_column(self) -> bool:
        """Check if this is an UNCERTAINTY column."""
        return self.column_type == ColumnType.UNCERTAINTY
    
    def get_display_header(self) -> str:
        """Get formatted header text for display.
        
        Returns:
            Formatted string like "name [unit]" or just "name"
        """
        if self.unit:
            return f"{self.name} [{self.unit}]"
        return self.name
    
    def get_symbol(self) -> str:
        """Get the visual symbol for this column type.
        
        Returns:
            Unicode character representing the column type
        """
        symbols = {
            ColumnType.DATA: "●",
            ColumnType.CALCULATED: "ƒ",
            ColumnType.DERIVATIVE: "∂",
            ColumnType.RANGE: "▬",
            ColumnType.INTERPOLATION: "⌇",
            ColumnType.UNCERTAINTY: "σ",
        }
        return symbols.get(self.column_type, "?")
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate that the metadata is consistent.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate CALCULATED columns
        if self.column_type == ColumnType.CALCULATED:
            if not self.formula:
                return False, "CALCULATED column must have a formula"
        
        # Validate DERIVATIVE columns
        if self.column_type == ColumnType.DERIVATIVE:
            if not self.derivative_numerator or not self.derivative_denominator:
                return False, "DERIVATIVE column must have numerator and denominator"
        
        # Validate RANGE columns
        if self.column_type == ColumnType.RANGE:
            if self.range_start is None or self.range_end is None or not self.range_points:
                return False, "RANGE column must have start, end, and points"
            if self.range_points < 2:
                return False, "RANGE column must have at least 2 points"
        
        # Validate INTERPOLATION columns
        if self.column_type == ColumnType.INTERPOLATION:
            if not self.interp_x_column or not self.interp_y_column:
                return False, "INTERPOLATION column must have X and Y columns"
        
        # Validate UNCERTAINTY columns
        if self.column_type == ColumnType.UNCERTAINTY:
            if not self.uncertainty_reference:
                return False, "UNCERTAINTY column must reference a data column"
        
        return True, None
