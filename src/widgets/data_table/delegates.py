"""
Delegate factory for DataTableV2.

This module creates appropriate delegates for each column type by importing
them from the reusable utils.delegates module.
"""

from PySide6.QtWidgets import QStyledItemDelegate

from .column_metadata import DataType, ColumnMetadata
from utils.delegates import NumericDelegate, IntegerDelegate, StringDelegate, BooleanDelegate


def create_delegate_for_column(metadata: ColumnMetadata, parent=None) -> QStyledItemDelegate:
    """Create appropriate delegate for a column based on its metadata.
    
    Args:
        metadata: Column metadata
        parent: Parent object
        
    Returns:
        Delegate instance
    """
    if metadata.dtype == DataType.FLOAT:
        return NumericDelegate(precision=metadata.precision, parent=parent)
    elif metadata.dtype == DataType.INTEGER:
        return IntegerDelegate(precision=0, parent=parent)
    elif metadata.dtype == DataType.BOOLEAN:
        return BooleanDelegate(parent=parent)
    elif metadata.dtype == DataType.STRING:
        return StringDelegate(parent=parent)
    elif metadata.dtype == DataType.CATEGORY:
        return StringDelegate(parent=parent)  # Could be ComboBox delegate in future
    else:
        return QStyledItemDelegate(parent=parent)
