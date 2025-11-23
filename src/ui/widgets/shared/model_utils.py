"""
Utility functions for Qt models.

Provides reusable model operations and formatting.
"""

from PySide6.QtCore import QAbstractTableModel
from typing import Any


def format_cell_value(value: Any) -> str:
    """Format cell value for display.
    
    Args:
        value: Cell value
        
    Returns:
        Formatted string
    """
    if value is None or (isinstance(value, float) and value != value):  # NaN
        return ""
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
