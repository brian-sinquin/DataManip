"""
DataTableV2 - Modern, efficient data table widget.

This is a complete rewrite of the data table widget using Qt's Model/View
architecture with Pandas/NumPy backend for high performance.

Example usage:
    >>> from widgets.DataTableV2 import DataTableWidget
    >>> widget = DataTableWidget()
    >>> widget.add_data_column("time", unit="s", data=[0, 1, 2, 3])
    >>> widget.add_calculated_column("position", formula="{time} * 5", unit="m")
    >>> widget.show()
"""

# Core classes
from .model import DataTableModel
from .view import DataTableView, DataTableWidget
from .column_metadata import ColumnType, ColumnMetadata, DataType
from .delegates import (
    NumericDelegate,
    IntegerDelegate,
    StringDelegate,
    BooleanDelegate,
    create_delegate_for_column
)

__version__ = "2.0.0-alpha"
__all__ = [
    # Main classes (most users need these)
    "DataTableWidget",      # All-in-one widget (easiest to use)
    "DataTableView",        # View component
    "DataTableModel",       # Model component
    
    # Metadata
    "ColumnType",
    "ColumnMetadata",
    "DataType",
    
    # Delegates (for advanced customization)
    "NumericDelegate",
    "IntegerDelegate",
    "StringDelegate",
    "BooleanDelegate",
    "create_delegate_for_column",
]
