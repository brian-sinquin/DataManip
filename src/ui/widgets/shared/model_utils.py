"""
Utility functions for Qt models.

Provides reusable model operations and formatting.
"""

from PySide6.QtCore import QAbstractTableModel
from typing import Any, Optional
from constants import DISPLAY_PRECISION

# Module-level variable for dynamic precision (defaults to constant)
_display_precision = DISPLAY_PRECISION


def set_display_precision(precision: int):
    """Set the display precision for all future cell formatting.
    
    Args:
        precision: Number of significant digits (1-15)
    """
    global _display_precision
    _display_precision = max(1, min(15, precision))


def get_display_precision() -> int:
    """Get the current display precision.
    
    Returns:
        Current precision value
    """
    return _display_precision


def format_cell_value(value: Any, precision: Optional[int] = None) -> str:
    """Format cell value for display with configurable precision.
    
    Uses module-level display precision (or constant) for numeric values.
    This function is used for DisplayRole in Qt models - EditRole should
    return full precision to avoid data loss during editing.
    
    Args:
        value: Cell value (int, float, or other type)
        precision: Optional override for precision (uses module-level if None)
        
    Returns:
        Formatted string:
        - Empty string for None or NaN
        - Scientific notation (e.g., '1.23e+10') for numbers
        - String representation for other types
    
    Example:
        >>> format_cell_value(3.141592653589793)
        '3.14'
        >>> format_cell_value(None)
        ''
    """
    if value is None or (isinstance(value, float) and value != value):  # NaN
        return ""
    
    if isinstance(value, (int, float)):
        prec = precision if precision is not None else _display_precision
        return f"{value:.{prec}g}"
    
    return str(value)


def emit_full_model_update(model: QAbstractTableModel):
    """Emit data changed signal for entire model.
    
    Args:
        model: Model to update
    """
    model.dataChanged.emit(
        model.index(0, 0),
        model.index(model.rowCount() - 1, model.columnCount() - 1)
    )
