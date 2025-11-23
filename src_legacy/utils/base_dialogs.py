"""
Base dialog classes with common validation patterns.

This module provides reusable base classes for dialogs that need input
validation with visual feedback.
"""

from typing import Callable, Optional
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QDialogButtonBox
from PySide6.QtCore import Qt


class ValidatedDialog(QDialog):
    """Base class for dialogs with input validation.
    
    Provides common validation UI pattern:
    - Error/success label for feedback
    - OK button that can be enabled/disabled based on validation
    - Built-in validation result display
    
    Subclasses should:
    1. Call super().__init__() and then _setup_validation_ui()
    2. Call _validate() whenever inputs change
    3. Implement _perform_validation() to check inputs
    
    Example:
        >>> class MyDialog(ValidatedDialog):
        ...     def __init__(self, parent=None):
        ...         super().__init__(parent)
        ...         # ... setup UI ...
        ...         self._setup_validation_ui()
        ...         self.name_edit.textChanged.connect(self._validate)
        ...     
        ...     def _perform_validation(self) -> tuple[bool, Optional[str]]:
        ...         name = self.name_edit.text()
        ...         if not name:
        ...             return False, "Name cannot be empty"
        ...         return True, None
    """
    
    def __init__(self, parent=None):
        """Initialize base dialog."""
        super().__init__(parent)
        self._validation_label: Optional[QLabel] = None
        self._ok_button: Optional[QPushButton] = None
    
    def _setup_validation_ui(self, button_box: QDialogButtonBox) -> QLabel:
        """Setup validation UI components.
        
        Call this after creating your dialog's button box.
        
        Args:
            button_box: The dialog's button box containing OK/Cancel buttons
            
        Returns:
            The created validation label (for layout purposes)
        """
        # Get OK button from button box
        self._ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        
        # Create validation label
        self._validation_label = QLabel()
        self._validation_label.setWordWrap(True)
        self._validation_label.setStyleSheet("font-size: 9pt;")
        
        # Run initial validation
        self._validate()
        
        return self._validation_label
    
    def _validate(self) -> bool:
        """Validate inputs and update UI.
        
        Returns:
            True if validation passed, False otherwise
        """
        is_valid, error_msg = self._perform_validation()
        
        if is_valid:
            self._show_validation_success()
        else:
            self._show_validation_error(error_msg or "Invalid input")
        
        # Enable/disable OK button
        if self._ok_button:
            self._ok_button.setEnabled(is_valid)
        
        return is_valid
    
    def _perform_validation(self) -> tuple[bool, Optional[str]]:
        """Perform actual validation logic.
        
        Subclasses must implement this method.
        
        Returns:
            Tuple of (is_valid, error_message)
            error_message is None if valid, otherwise contains error description
        """
        raise NotImplementedError("Subclasses must implement _perform_validation()")
    
    def _show_validation_success(self, message: str = "✓ Valid") -> None:
        """Show success validation message.
        
        Args:
            message: Success message to display
        """
        if self._validation_label:
            self._validation_label.setText(message)
            self._validation_label.setStyleSheet("color: green; font-size: 9pt;")
    
    def _show_validation_error(self, message: str) -> None:
        """Show error validation message.
        
        Args:
            message: Error message to display
        """
        if self._validation_label:
            self._validation_label.setText(f"⚠ {message}")
            self._validation_label.setStyleSheet("color: red; font-size: 9pt;")
    
    def _clear_validation_message(self) -> None:
        """Clear the validation message."""
        if self._validation_label:
            self._validation_label.setText("")


class NameValidatedDialog(ValidatedDialog):
    """Base dialog for validating identifier names.
    
    Provides built-in validation for column names, variable names, etc.
    
    Subclasses should:
    1. Set self.name_edit to the QLineEdit for the name
    2. Optionally set self.existing_names to check for duplicates
    3. Call _setup_name_validation() after UI setup
    """
    
    def __init__(self, parent=None):
        """Initialize name validation dialog."""
        super().__init__(parent)
        self.name_edit = None  # Subclass should set this
        self.existing_names: list[str] = []
        self.current_name: Optional[str] = None  # For edit mode
    
    def _setup_name_validation(self, button_box: QDialogButtonBox) -> QLabel:
        """Setup name validation.
        
        Args:
            button_box: The dialog's button box
            
        Returns:
            The validation label
        """
        if self.name_edit:
            self.name_edit.textChanged.connect(self._validate)
        
        return self._setup_validation_ui(button_box)
    
    def _perform_validation(self) -> tuple[bool, Optional[str]]:
        """Validate the name input.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.name_edit:
            return True, None
        
        from utils.validators import validate_identifier_name
        
        name = self.name_edit.text().strip()
        is_valid, error_msg = validate_identifier_name(
            name,
            existing_names=self.existing_names,
            current_name=self.current_name
        )
        
        return is_valid, error_msg
