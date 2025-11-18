"""Widgets package for DataManip - contains small, self-contained functional widgets."""

__all__ = []

# DataTable widget - main data table component
from .data_table.view import DataTableView, DataTableWidget
from .data_table.model import DataTableModel
from .data_table.column_metadata import ColumnType, DataType, ColumnMetadata

__all__.extend([
    'DataTableView',
    'DataTableWidget', 
    'DataTableModel',
    'ColumnType',
    'DataType',
    'ColumnMetadata'
])
