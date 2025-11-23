"""
Common exception classes for DataManip application.

This module provides reusable exception classes for data operations
across different widgets and components.
"""

from typing import Optional, List
from difflib import get_close_matches


# ============================================================================
# Base Exceptions
# ============================================================================

class DataManipError(Exception):
    """Base exception for all DataManip errors."""
    pass


# ============================================================================
# Data Table Exceptions
# ============================================================================

class DataTableError(DataManipError):
    """Base exception for DataTable errors."""
    pass


class ColumnExistsError(DataTableError):
    """Raised when trying to create a column that already exists."""
    
    def __init__(self, name: str, suggestion: Optional[str] = None):
        """Initialize exception.
        
        Args:
            name: Column name that already exists
            suggestion: Suggested alternative name
        """
        msg = f"Column '{name}' already exists"
        if suggestion:
            msg += f". Did you mean to use '{suggestion}'?"
        super().__init__(msg)
        self.column_name = name


class ColumnNotFoundError(DataTableError):
    """Raised when trying to access a column that doesn't exist."""
    
    def __init__(self, name: str, available: Optional[List[str]] = None):
        """Initialize exception.
        
        Args:
            name: Column name that was not found
            available: List of available column names for suggestions
        """
        msg = f"Column '{name}' does not exist"
        if available:
            # Suggest similar names
            suggestions = get_close_matches(name, available, n=3, cutoff=0.6)
            if suggestions:
                quoted_suggestions = [f"'{s}'" for s in suggestions]
                msg += f". Did you mean: {', '.join(quoted_suggestions)}?"
            else:
                quoted_cols = [f"'{c}'" for c in available[:5]]
                msg += f". Available columns: {', '.join(quoted_cols)}"
                if len(available) > 5:
                    msg += f" (and {len(available) - 5} more)"
        super().__init__(msg)
        self.column_name = name


class ColumnInUseError(DataTableError):
    """Raised when trying to delete a column that other columns depend on."""
    
    def __init__(self, name: str, dependents: List[str]):
        """Initialize exception.
        
        Args:
            name: Column name that is in use
            dependents: List of columns that depend on this column
        """
        quoted_deps = [f"'{d}'" for d in dependents]
        msg = f"Cannot remove column '{name}': it is used by {', '.join(quoted_deps)}"
        super().__init__(msg)
        self.column_name = name
        self.dependents = dependents


# ============================================================================
# Validation Exceptions
# ============================================================================

class ValidationError(DataManipError):
    """Raised when validation fails."""
    pass


class InvalidNameError(ValidationError):
    """Raised when a name is invalid (identifier, filename, etc.)."""
    pass


class InvalidValueError(ValidationError):
    """Raised when a value is invalid (out of range, wrong type, etc.)."""
    pass
