"""Cell formatting utilities for AdvancedDataTableWidget.

This module provides consistent formatting for table cell display including:
- Numeric value formatting with precision
- Error message display
- Unit display
- Special value handling (inf, nan, None)
"""

from PySide6.QtWidgets import QTableWidgetItem
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
import math
from typing import Optional, Union

from .constants import DEFAULT_NUMERIC_PRECISION, ERROR_PREFIX
from utils.units import format_unit_pretty


class CellFormatter:
    """Handles consistent cell formatting for the data table."""
    
    # Colors for different cell states
    COLOR_ERROR = QColor(255, 0, 0)  # Red for errors
    COLOR_INVALID = QColor(255, 0, 0)  # Red for inf/nan
    COLOR_NORMAL = None  # Default color
    
    @staticmethod
    def create_numeric_item(
        value: Union[int, float],
        precision: str = DEFAULT_NUMERIC_PRECISION,
        editable: bool = True
    ) -> QTableWidgetItem:
        """Create a table item for a numeric value.
        
        Args:
            value: The numeric value to display
            precision: Format string for numeric precision (e.g., ".6g")
            editable: Whether the cell should be editable
            
        Returns:
            QTableWidgetItem configured for the numeric value
        """
        # Check for special values (inf, nan)
        if isinstance(value, float) and (math.isinf(value) or math.isnan(value)):
            return CellFormatter.create_invalid_item(str(value), editable=False)
        
        # Format the value
        if isinstance(value, float):
            display_text = f"{value:{precision}}"
        else:
            display_text = str(value)
        
        item = QTableWidgetItem(display_text)
        item.setData(Qt.ItemDataRole.UserRole, value)  # Store actual numeric value
        
        # Set editability
        if not editable:
            item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        
        return item
    
    @staticmethod
    def create_error_item(
        error_message: str,
        include_prefix: bool = True,
        editable: bool = False
    ) -> QTableWidgetItem:
        """Create a table item displaying an error message.
        
        Args:
            error_message: The error message to display
            include_prefix: Whether to prepend ERROR_PREFIX
            editable: Whether the cell should be editable (usually False for errors)
            
        Returns:
            QTableWidgetItem configured as an error display
        """
        if include_prefix and not error_message.startswith(ERROR_PREFIX):
            display_text = f"{ERROR_PREFIX}{error_message}"
        else:
            display_text = error_message
        
        item = QTableWidgetItem(display_text)
        item.setForeground(CellFormatter.COLOR_ERROR)
        
        # Error cells are typically not editable
        if not editable:
            item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        
        return item
    
    @staticmethod
    def create_invalid_item(
        display_text: str,
        editable: bool = False
    ) -> QTableWidgetItem:
        """Create a table item for invalid values (inf, nan, etc.).
        
        Args:
            display_text: Text to display (e.g., "inf", "nan")
            editable: Whether the cell should be editable
            
        Returns:
            QTableWidgetItem configured for invalid value display
        """
        item = QTableWidgetItem(display_text)
        item.setForeground(CellFormatter.COLOR_INVALID)
        
        # Try to parse and store the value
        try:
            value = float(display_text)
            item.setData(Qt.ItemDataRole.UserRole, value)
        except ValueError:
            pass
        
        if not editable:
            item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        
        return item
    
    @staticmethod
    def create_empty_item(editable: bool = True) -> QTableWidgetItem:
        """Create an empty table item.
        
        Args:
            editable: Whether the cell should be editable
            
        Returns:
            Empty QTableWidgetItem
        """
        item = QTableWidgetItem("")
        
        if not editable:
            item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        
        return item
    
    @staticmethod
    def create_text_item(
        text: str,
        editable: bool = True
    ) -> QTableWidgetItem:
        """Create a table item for text display.
        
        Args:
            text: Text to display
            editable: Whether the cell should be editable
            
        Returns:
            QTableWidgetItem configured for text display
        """
        item = QTableWidgetItem(text)
        
        if not editable:
            item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        
        return item
    
    @staticmethod
    def format_value_for_display(
        value: Optional[Union[int, float, str]],
        precision: str = DEFAULT_NUMERIC_PRECISION
    ) -> str:
        """Format a value for display without creating a QTableWidgetItem.
        
        Args:
            value: Value to format
            precision: Format string for numeric values
            
        Returns:
            Formatted string for display
        """
        if value is None:
            return ""
        
        if isinstance(value, str):
            return value
        
        if isinstance(value, float):
            # Check for special values
            if math.isinf(value) or math.isnan(value):
                return str(value)
            return f"{value:{precision}}"
        
        return str(value)
    
    @staticmethod
    def extract_numeric_value(item: Optional[QTableWidgetItem]) -> Optional[float]:
        """Extract numeric value from a table item.
        
        First tries to get stored data, then parses text.
        
        Args:
            item: QTableWidgetItem to extract value from
            
        Returns:
            Numeric value or None if not available/parseable
        """
        if item is None:
            return None
        
        # Try to get stored data first
        stored_value = item.data(Qt.ItemDataRole.UserRole)
        if stored_value is not None and isinstance(stored_value, (int, float)):
            return float(stored_value)
        
        # Fall back to parsing text
        text = item.text()
        if not text or text.startswith(ERROR_PREFIX):
            return None
        
        try:
            return float(text)
        except ValueError:
            return None
    
    @staticmethod
    def is_error_cell(item: Optional[QTableWidgetItem]) -> bool:
        """Check if a cell contains an error.
        
        Args:
            item: QTableWidgetItem to check
            
        Returns:
            True if cell contains an error, False otherwise
        """
        if item is None:
            return False
        
        text = item.text()
        return text.startswith(ERROR_PREFIX)
    
    @staticmethod
    def is_empty_cell(item: Optional[QTableWidgetItem]) -> bool:
        """Check if a cell is empty.
        
        Args:
            item: QTableWidgetItem to check
            
        Returns:
            True if cell is empty, False otherwise
        """
        if item is None:
            return True
        
        text = item.text()
        return not text or text.strip() == ""
    
    @staticmethod
    def format_header_with_unit(
        symbol: str,
        diminutive: str,
        unit: Optional[str] = None
    ) -> str:
        """Format a column header with symbol, diminutive, and unit.
        
        Args:
            symbol: Column type symbol (e.g., "● ", "ƒ ")
            diminutive: Column diminutive/short name
            unit: Optional unit string
            
        Returns:
            Formatted header string
        """
        if unit and unit.strip():
            pretty_unit = format_unit_pretty(unit, use_dot=True, use_superscript=True)
            return f"{symbol}{diminutive} [{pretty_unit}]"
        else:
            return f"{symbol}{diminutive}"
