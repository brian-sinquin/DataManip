"""
Custom Qt delegates for cell editing and display.

This module provides reusable delegates for different data types that can be
used across various table widgets in the application.
"""

from typing import Any, Optional
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QWidget, QLineEdit
from PySide6.QtCore import QModelIndex, Qt, QAbstractItemModel


class NumericDelegate(QStyledItemDelegate):
    """Delegate for numeric columns (floating point).
    
    Formats numbers with appropriate precision and validates input.
    """
    
    def __init__(self, precision: int = 6, parent=None):
        """Initialize delegate.
        
        Args:
            precision: Number of decimal places for display
            parent: Parent object
        """
        super().__init__(parent)
        self.precision = precision
    
    def displayText(self, value: Any, locale) -> str:
        """Format value for display."""
        if value is None or value == "":
            return ""
        
        try:
            num_val = float(value)
            
            # Handle special values
            if num_val != num_val:  # NaN
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
        """Create editor widget for cell."""
        editor = QLineEdit(parent)
        editor.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return editor
    
    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
        """Set editor's initial value."""
        if isinstance(editor, QLineEdit):
            value = index.data(Qt.ItemDataRole.EditRole)
            editor.setText(str(value) if value not in (None, "") else "")
    
    def setModelData(self, editor: QWidget, model: QAbstractItemModel, 
                    index: QModelIndex) -> None:
        """Save editor's value to model."""
        if isinstance(editor, QLineEdit):
            text = editor.text().strip()
            if text == "":
                model.setData(index, None, Qt.ItemDataRole.EditRole)
            else:
                try:
                    model.setData(index, float(text), Qt.ItemDataRole.EditRole)
                except ValueError:
                    pass  # Invalid input, don't update


class IntegerDelegate(NumericDelegate):
    """Delegate for integer columns."""
    
    def displayText(self, value: Any, locale) -> str:
        """Format integer value for display."""
        if value is None or value == "":
            return ""
        
        try:
            return str(int(float(value)))
        except (ValueError, TypeError):
            return str(value)
    
    def setModelData(self, editor: QWidget, model: QAbstractItemModel, 
                    index: QModelIndex) -> None:
        """Save integer value to model."""
        if isinstance(editor, QLineEdit):
            text = editor.text().strip()
            if text == "":
                model.setData(index, None, Qt.ItemDataRole.EditRole)
            else:
                try:
                    model.setData(index, int(float(text)), Qt.ItemDataRole.EditRole)
                except ValueError:
                    pass


class StringDelegate(QStyledItemDelegate):
    """Delegate for string columns."""
    
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, 
                    index: QModelIndex) -> Optional[QWidget]:
        """Create editor widget."""
        editor = QLineEdit(parent)
        editor.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        return editor


class BooleanDelegate(QStyledItemDelegate):
    """Delegate for boolean columns.
    
    Displays as checkbox-style True/False.
    """
    
    def displayText(self, value: Any, locale) -> str:
        """Format boolean for display."""
        if value is None or value == "":
            return ""
        
        try:
            return "True" if bool(value) else "False"
        except (ValueError, TypeError):
            return str(value)
    
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, 
                    index: QModelIndex) -> Optional[QWidget]:
        """Create editor widget."""
        editor = QLineEdit(parent)
        editor.setPlaceholderText("true/false")
        return editor
    
    def setModelData(self, editor: QWidget, model: QAbstractItemModel, 
                    index: QModelIndex) -> None:
        """Save boolean value to model."""
        if isinstance(editor, QLineEdit):
            text = editor.text().strip().lower()
            if text in ("true", "1", "yes", "t", "y"):
                model.setData(index, True, Qt.ItemDataRole.EditRole)
            elif text in ("false", "0", "no", "f", "n"):
                model.setData(index, False, Qt.ItemDataRole.EditRole)
            elif text == "":
                model.setData(index, None, Qt.ItemDataRole.EditRole)
