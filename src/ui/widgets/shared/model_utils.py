"""
Utility functions for Qt models.

Provides reusable model operations and formatting.
"""

from PySide6.QtCore import QAbstractTableModel
from typing import Any
from ..data_table.constants import DISPLAY_PRECISION


def format_cell_value(value: Any) -> str:
    """Format cell value for display with configurable precision.
    
    Uses DISPLAY_PRECISION constant (33 significant digits) for numeric values.
    This function is used for DisplayRole in Qt models - EditRole should
    return full precision to avoid data loss during editing.
    
    Args:
        value: Cell value (int, float, or other type)
        
    Returns:
        Formatted string:
        - Empty string for None or NaN
        - Scientific notation (e.g., '1.23e+10') for numbers
        - String representation for other types
    
    Example:
        >>> format_cell_value(3.141592653589793)
        '3.141592653589793'
        >>> format_cell_value(None)
        ''
    """
    if value is None or (isinstance(value, float) and value != value):  # NaN
        return ""
    
    if isinstance(value, (int, float)):
        return f"{value:.{DISPLAY_PRECISION}g}"
    
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
