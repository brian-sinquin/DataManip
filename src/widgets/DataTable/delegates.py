"""
Custom delegates for DataTableV2 cell editing and display.

Provides specialized editors and formatters for different data types.
"""

from typing import Any, Optional
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QWidget, QLineEdit
from PySide6.QtCore import QModelIndex, Qt, QAbstractItemModel
from PySide6.QtGui import QPainter

from .column_metadata import DataType, ColumnMetadata


class NumericDelegate(QStyledItemDelegate):
    """Delegate for numeric columns (FLOAT, INTEGER).
    
    Formats numbers with appropriate precision and validates input.
    """
    
    def __init__(self, precision: int = 6, parent=None):
        """Initialize delegate.
        
        Args:
            precision: Number of decimal places for floats
            parent: Parent object
        """
        super().__init__(parent)
        self.precision = precision
    
    def displayText(self, value: Any, locale) -> str:
        """Format value for display.
        
        Args:
            value: Value to format
            locale: Locale for formatting
            
        Returns:
            Formatted string
        """
        if value is None or value == "":
            return ""
        
        try:
            # Try to convert to float
            num_val = float(value)
            
            # Check for NaN/inf
            if num_val != num_val:  # NaN check
                return ""
            if num_val == float('inf'):
                return "∞"
            if num_val == float('-inf'):
                return "-∞"
            
            # Format with precision
            return f"{num_val:.{self.precision}g}"
        except (ValueError, TypeError):
            return str(value)
    
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, 
                    index: QModelIndex) -> Optional[QWidget]:
        """Create editor widget for cell.
        
        Args:
            parent: Parent widget
            option: Style options
            index: Model index
            
        Returns:
            Editor widget or None
        """
        editor = QLineEdit(parent)
        editor.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return editor
    
    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
        """Set editor's initial value.
        
        Args:
            editor: Editor widget
            index: Model index
        """
        if isinstance(editor, QLineEdit):
            value = index.data(Qt.ItemDataRole.EditRole)
            if value is not None and value != "":
                editor.setText(str(value))
            else:
                editor.setText("")
    
    def setModelData(self, editor: QWidget, model: QAbstractItemModel, 
                    index: QModelIndex) -> None:
        """Save editor's value to model.
        
        Args:
            editor: Editor widget
            model: Data model
            index: Model index
        """
        if isinstance(editor, QLineEdit):
            text = editor.text().strip()
            if text == "":
                model.setData(index, None, Qt.ItemDataRole.EditRole)
            else:
                try:
                    value = float(text)
                    model.setData(index, value, Qt.ItemDataRole.EditRole)
                except ValueError:
                    # Invalid input, don't update
                    pass


class IntegerDelegate(NumericDelegate):
    """Delegate for integer columns."""
    
    def displayText(self, value: Any, locale) -> str:
        """Format integer value for display.
        
        Args:
            value: Value to format
            locale: Locale for formatting
            
        Returns:
            Formatted string
        """
        if value is None or value == "":
            return ""
        
        try:
            int_val = int(float(value))
            return str(int_val)
        except (ValueError, TypeError):
            return str(value)
    
    def setModelData(self, editor: QWidget, model: QAbstractItemModel, 
                    index: QModelIndex) -> None:
        """Save integer value to model.
        
        Args:
            editor: Editor widget
            model: Data model
            index: Model index
        """
        if isinstance(editor, QLineEdit):
            text = editor.text().strip()
            if text == "":
                model.setData(index, None, Qt.ItemDataRole.EditRole)
            else:
                try:
                    value = int(float(text))
                    model.setData(index, value, Qt.ItemDataRole.EditRole)
                except ValueError:
                    pass


class StringDelegate(QStyledItemDelegate):
    """Delegate for string columns."""
    
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, 
                    index: QModelIndex) -> Optional[QWidget]:
        """Create editor widget.
        
        Args:
            parent: Parent widget
            option: Style options
            index: Model index
            
        Returns:
            Editor widget
        """
        editor = QLineEdit(parent)
        editor.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        return editor


class BooleanDelegate(QStyledItemDelegate):
    """Delegate for boolean columns.
    
    Displays as checkbox-style True/False.
    """
    
    def displayText(self, value: Any, locale) -> str:
        """Format boolean for display.
        
        Args:
            value: Value to format
            locale: Locale for formatting
            
        Returns:
            "True" or "False"
        """
        if value is None or value == "":
            return ""
        
        try:
            bool_val = bool(value)
            return "True" if bool_val else "False"
        except (ValueError, TypeError):
            return str(value)
    
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, 
                    index: QModelIndex) -> Optional[QWidget]:
        """Create editor widget.
        
        Args:
            parent: Parent widget
            option: Style options
            index: Model index
            
        Returns:
            Editor widget
        """
        editor = QLineEdit(parent)
        editor.setPlaceholderText("true/false")
        return editor
    
    def setModelData(self, editor: QWidget, model: QAbstractItemModel, 
                    index: QModelIndex) -> None:
        """Save boolean value to model.
        
        Args:
            editor: Editor widget
            model: Data model
            index: Model index
        """
        if isinstance(editor, QLineEdit):
            text = editor.text().strip().lower()
            if text in ("true", "1", "yes", "t", "y"):
                model.setData(index, True, Qt.ItemDataRole.EditRole)
            elif text in ("false", "0", "no", "f", "n"):
                model.setData(index, False, Qt.ItemDataRole.EditRole)
            elif text == "":
                model.setData(index, None, Qt.ItemDataRole.EditRole)


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
