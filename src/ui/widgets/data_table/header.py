"""Custom header view with editable column properties."""

from PySide6.QtWidgets import QHeaderView
from PySide6.QtCore import Qt


class EditableHeaderView(QHeaderView):
    """Custom header view that allows double-click to edit column properties."""
    
    def __init__(self, orientation, parent=None):
        """Initialize header view.
        
        Args:
            orientation: Qt.Horizontal or Qt.Vertical
            parent: Parent widget
        """
        super().__init__(orientation, parent)
        self.table_widget = None
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click on header to edit column properties.
        
        Args:
            event: Mouse event
        """
        if self.orientation() == Qt.Horizontal and self.table_widget:
            logical_index = self.logicalIndexAt(event.pos())
            if logical_index >= 0:
                self.table_widget._edit_column_properties(logical_index)
        else:
            super().mouseDoubleClickEvent(event)
