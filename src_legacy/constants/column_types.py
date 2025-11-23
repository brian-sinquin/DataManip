"""Column type definitions."""

from enum import Enum


class ColumnType(Enum):
    """Types of columns in the data table."""
    
    DATA = "data"           # User-editable data column
    CALCULATED = "calc"     # Formula-based calculated column
    DERIVATIVE = "deriv"    # Discrete derivative (dy/dx)
    RANGE = "range"         # Evenly-spaced values
    INTERPOLATION = "interp"  # Interpolated values
    UNCERTAINTY = "unc"     # Uncertainty/error column
