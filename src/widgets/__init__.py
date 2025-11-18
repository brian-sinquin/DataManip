"""Widgets package for DataManip - contains small, self-contained functional widgets."""

__all__ = []

# DataTable widget - main data table component
from .DataTable.view import DataTableView, DataTableWidget
from .DataTable.model import DataTableModel
from .DataTable.column_metadata import ColumnType, DataType, ColumnMetadata

__all__.extend([
    'DataTableView',
    'DataTableWidget', 
    'DataTableModel',
    'ColumnType',
    'DataType',
    'ColumnMetadata'
])
