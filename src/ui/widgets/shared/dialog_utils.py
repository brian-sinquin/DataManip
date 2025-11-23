"""
Utility functions for dialogs and user interactions.

Centralizes common dialog patterns to reduce code duplication.
"""

from PySide6.QtWidgets import QMessageBox, QWidget
from typing import Optional
from .validators import validate_column_name as validate_col_name_func


def show_error(parent: Optional[QWidget], title: str, message: str):
    """Show error message dialog.
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Error message
    """
    QMessageBox.critical(parent, title, message)


def show_warning(parent: Optional[QWidget], title: str, message: str):
    """Show warning message dialog.
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Warning message
    """
    QMessageBox.warning(parent, title, message)


def show_info(parent: Optional[QWidget], title: str, message: str):
    """Show information message dialog.
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Information message
    """
    QMessageBox.information(parent, title, message)


def confirm_action(parent: Optional[QWidget], title: str, message: str) -> bool:
    """Show confirmation dialog.
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Confirmation message
        
    Returns:
        True if user confirmed, False otherwise
    """
    reply = QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.Yes | QMessageBox.No  # type: ignore
    )
    return reply == QMessageBox.Yes  # type: ignore


def validate_column_name(
    parent: Optional[QWidget],
    name: str,
    existing_columns: list,
    field_label: str = "Column name"
) -> bool:
    """Validate column name and show error if invalid.
    
    Args:
        parent: Parent widget
        name: Column name to validate
        existing_columns: List of existing column names
        field_label: Label for the field being validated
        
    Returns:
        True if valid, False otherwise
    """
    is_valid, error_msg = validate_col_name_func(name, existing_columns, allow_existing=False)
    
    if not is_valid:
        show_warning(parent, "Error", error_msg)
        return False
    
    return True
