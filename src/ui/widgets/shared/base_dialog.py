"""
Base dialog classes for consistent UI patterns.

Provides reusable dialog components to reduce code duplication
and ensure consistent user experience across all dialogs.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QLineEdit
)
from PySide6.QtCore import Qt
from typing import Optional
from .validators import validate_column_name as validate_col_name


class BaseDialog(QDialog):
    """Base class for all dialogs with consistent layout and buttons.
    
    Provides:
    - Standard button layout (Cancel/OK)
    - Optional description label
    - Form layout container
    - Consistent sizing and styling
    """
    
    def __init__(
        self,
        title: str,
        description: Optional[str] = None,
        parent=None,
        width: int = 400,
        height: int = 250
    ):
        """Initialize base dialog.
        
        Args:
            title: Dialog window title
            description: Optional description text shown at top
            parent: Parent widget
            width: Dialog width in pixels
            height: Dialog height in pixels
        """
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(width, height)
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        
        # Description label if provided
        if description:
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            self.main_layout.addWidget(desc_label)
        
        # Form layout for input fields
        self.form_layout = QFormLayout()
        self.main_layout.addLayout(self.form_layout)
        
        # Stretch before buttons
        self.main_layout.addStretch()
        
        # Button layout
        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        self.button_layout.addWidget(self.cancel_btn)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self._on_ok_clicked)
        self.button_layout.addWidget(self.ok_btn)
        
        self.main_layout.addLayout(self.button_layout)
    
    def _on_ok_clicked(self):
        """Handle OK button click with validation."""
        if self.validate():
            self.accept()
    
    def validate(self) -> bool:
        """Validate dialog inputs before accepting.
        
        Override in subclasses to provide custom validation.
        
        Returns:
            True if validation passes, False otherwise
        """
        return True
    
    def add_form_row(self, label: str, widget):
        """Add a row to the form layout.
        
        Args:
            label: Label text
            widget: Input widget
        """
        self.form_layout.addRow(label, widget)
    
    def add_widget(self, widget, stretch: int = 0):
        """Add a widget to the main layout before buttons.
        
        Args:
            widget: Widget to add
            stretch: Stretch factor
        """
        # Insert before stretch and buttons
        insert_index = self.main_layout.count() - 2
        self.main_layout.insertWidget(insert_index, widget, stretch)
    
    def add_help_text(self, text: str):
        """Add help text with HTML formatting.
        
        Args:
            text: Help text (can include HTML tags)
        """
        help_label = QLabel(f"<small>{text}</small>")
        help_label.setWordWrap(True)
        self.add_widget(help_label)
    
    def set_ok_button_text(self, text: str):
        """Change OK button text.
        
        Args:
            text: New button text
        """
        self.ok_btn.setText(text)
    
    def set_cancel_button_text(self, text: str):
        """Change Cancel button text.
        
        Args:
            text: New button text
        """
        self.cancel_btn.setText(text)


class BaseColumnDialog(BaseDialog):
    """Base class for column addition/editing dialogs.
    
    Provides common fields:
    - Column name input
    - Unit input (optional)
    - Standard validation
    """
    
    def __init__(
        self,
        title: str,
        description: Optional[str] = None,
        parent=None,
        width: int = 400,
        height: int = 250,
        existing_columns: Optional[list] = None
    ):
        """Initialize column dialog.
        
        Args:
            title: Dialog title
            description: Optional description
            parent: Parent widget
            width: Dialog width
            height: Dialog height
            existing_columns: List of existing column names for validation
        """
        super().__init__(title, description, parent, width, height)
        
        self.existing_columns = existing_columns or []
        
        # Common input fields
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., time, position, velocity")
        self.add_form_row("Column Name:", self.name_edit)
        
        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText("e.g., m, s, kg")
        self.add_form_row("Unit (optional):", self.unit_edit)
    
    def validate_column_name(self, name: str, allow_existing: bool = False) -> tuple[bool, str]:
        """Validate column name using centralized validator.
        
        Args:
            name: Column name to validate
            allow_existing: Whether to allow existing names (for edit dialogs)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return validate_col_name(name, self.existing_columns, allow_existing)
