"""
Data models and constants for AdvancedDataTableWidget.

This module contains:
- Enums for column types and data types
- Data classes for column metadata
- Constants used throughout the widget
"""

from enum import Enum
from typing import Optional
from dataclasses import dataclass

# Import constants from centralized constants module
from .constants import (
    DEFAULT_NUMERIC_PRECISION,
    ERROR_PREFIX,
    FORMULA_REFERENCE_PATTERN,
    BACKWARD_COMPAT_PATTERN,
    COMMON_UNITS
)


class AdvancedColumnType(Enum):
    """Enum representing the type of a column in the table."""
    DATA = "data"
    CALCULATED = "calculated"
    UNCERTAINTY = "uncertainty"
    DERIVATIVE = "derivative"
    INTERPOLATION = "interpolation"
    RANGE = "range"


class AdvancedColumnDataType(Enum):
    """Enum representing the data type of a column."""
    NUMERICAL = "numerical"
    CATEGORICAL = "categorical"
    TEXT = "text"


@dataclass
class ColumnMetadata:
    """Unified metadata storage for table columns.
    
    Attributes:
        column_type: The type of column (DATA, CALCULATED, UNCERTAINTY, DERIVATIVE, INTERPOLATION, RANGE)
        data_type: The data type (NUMERICAL, CATEGORICAL, TEXT)
        diminutive: Short form used in formulas and shown in column header
        description: Full description shown as tooltip on the header
        unit: Optional unit of measurement (e.g., '°C', 'kPa')
        formula: Optional formula for calculated columns
        uncertainty_reference: Optional reference to the data column for uncertainty columns
        propagate_uncertainty: Whether to calculate and propagate uncertainty for calculated columns
        derivative_numerator: Optional column index for derivative numerator (dy)
        derivative_denominator: Optional column index for derivative denominator (dx)
        interpolation_x_column: Optional column index for x values in interpolation
        interpolation_y_column: Optional column index for y values in interpolation
        interpolation_evaluation_column: Optional column index for evaluation x values (defaults to interpolation_x_column)
        interpolation_method: Interpolation method ('linear', 'cubic', etc.)
        range_start: Start value for range columns
        range_end: End value for range columns
        range_points: Number of points for range columns
    """
    column_type: AdvancedColumnType
    data_type: AdvancedColumnDataType
    diminutive: str
    description: Optional[str] = None
    unit: Optional[str] = None
    formula: Optional[str] = None
    uncertainty_reference: Optional[int] = None  # For uncertainty columns
    propagate_uncertainty: bool = False  # For calculated columns
    derivative_numerator: Optional[int] = None  # For derivative columns (dy)
    derivative_denominator: Optional[int] = None  # For derivative columns (dx)
    interpolation_x_column: Optional[int] = None  # For interpolation columns (x values)
    interpolation_y_column: Optional[int] = None  # For interpolation columns (y values)
    interpolation_evaluation_column: Optional[int] = None  # For interpolation columns (evaluation x values)
    interpolation_method: Optional[str] = None  # For interpolation columns ('linear', 'cubic', etc.)
    range_start: Optional[float] = None  # For range columns
    range_end: Optional[float] = None  # For range columns
    range_points: Optional[int] = None  # For range columns

    def is_data_column(self) -> bool:
        """Check if this is a data column."""
        return self.column_type == AdvancedColumnType.DATA

    def is_calculated_column(self) -> bool:
        """Check if this is a calculated column."""
        return self.column_type == AdvancedColumnType.CALCULATED

    def is_uncertainty_column(self) -> bool:
        """Check if this is an uncertainty column."""
        return self.column_type == AdvancedColumnType.UNCERTAINTY

    def is_derivative_column(self) -> bool:
        """Check if this is a derivative column."""
        return self.column_type == AdvancedColumnType.DERIVATIVE

    def is_interpolation_column(self) -> bool:
        """Check if this is an interpolation column."""
        return self.column_type == AdvancedColumnType.INTERPOLATION

    def is_range_column(self) -> bool:
        """Check if this is a range column."""
        return self.column_type == AdvancedColumnType.RANGE
