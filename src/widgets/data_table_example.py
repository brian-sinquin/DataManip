"""Example of a custom widget with data that uses TranslatableMixin."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel
from PySide6.QtCore import Qt

from widgets.translatable import TranslatableMixin
from utils.lang import get_lang_manager


class DataTableExample(QWidget, TranslatableMixin):
    """
    Example widget that contains data and translatable UI elements.
    The data is preserved when language changes, only UI text is updated.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize translatable mixin
        TranslatableMixin.__init__(self)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title label (translatable)
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.title_label)
        self.register_translatable(self.title_label, "data_table.title", "text")
        
        # Data table (data is preserved, only headers are translated)
        self.table = QTableWidget(5, 3)
        layout.addWidget(self.table)
        
        # Set some example data (this will NOT be lost on language change)
        for row in range(5):
            for col in range(3):
                self.table.setItem(row, col, QTableWidgetItem(f"Data {row},{col}"))
        
        # Initial translation
        self.refresh_translations()
        self._update_table_headers()
    
    def _update_table_headers(self):
        """Update table headers with current language."""
        lang = get_lang_manager()
        headers = [
            lang.get("data_table.column1", "Column 1"),
            lang.get("data_table.column2", "Column 2"),
            lang.get("data_table.column3", "Column 3"),
        ]
        self.table.setHorizontalHeaderLabels(headers)
    
    def refresh_translations(self):
        """Override to also update table headers."""
        super().refresh_translations()
        self._update_table_headers()
    
    def add_data(self, row: int, col: int, data: str):
        """Add data to the table (this data is preserved across language changes)."""
        self.table.setItem(row, col, QTableWidgetItem(data))
