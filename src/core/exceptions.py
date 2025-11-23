"""
Custom exception classes for DataManip.

Provides domain-specific exceptions for better error handling
and more meaningful error messages.
"""

from typing import Optional, List, Any


class DataManipError(Exception):
    """Base exception for all DataManip errors."""
    pass


# ============================================================================
# Core Errors
# ============================================================================

class DataObjectError(DataManipError):
    """Errors related to DataObject operations."""
    pass


class ColumnNotFoundError(DataObjectError):
    """Raised when a column doesn't exist in the data object."""
    
    def __init__(self, column_name: str, available_columns: Optional[List[str]] = None):
        self.column_name = column_name
        self.available_columns = available_columns
        
        message = f"Column '{column_name}' not found"
        if available_columns:
            message += f". Available columns: {', '.join(available_columns)}"
        
        super().__init__(message)


class ColumnExistsError(DataObjectError):
    """Raised when trying to add a column that already exists."""
    
    def __init__(self, column_name: str):
        self.column_name = column_name
        super().__init__(f"Column '{column_name}' already exists")


class InvalidColumnTypeError(DataObjectError):
    """Raised when an invalid column type is specified."""
    
    def __init__(self, column_type: str, valid_types: Optional[List[str]] = None):
        self.column_type = column_type
        self.valid_types = valid_types
        
        message = f"Invalid column type: '{column_type}'"
        if valid_types:
            message += f". Valid types: {', '.join(valid_types)}"
        
        super().__init__(message)


# ============================================================================
# Formula Errors
# ============================================================================

class FormulaError(DataManipError):
    """Base class for formula-related errors."""
    pass


class FormulaSyntaxError(FormulaError):
    """Raised when a formula has syntax errors."""
    
    def __init__(self, formula: str, details: Optional[str] = None):
        self.formula = formula
        self.details = details
        
        message = f"Invalid formula syntax: '{formula}'"
        if details:
            message += f"\nDetails: {details}"
        
        super().__init__(message)


class FormulaEvaluationError(FormulaError):
    """Raised when formula evaluation fails."""
    
    def __init__(self, formula: str, error: Exception):
        self.formula = formula
        self.original_error = error
        
        message = f"Failed to evaluate formula: '{formula}'\nError: {str(error)}"
        super().__init__(message)


class CircularDependencyError(FormulaError):
    """Raised when circular dependencies are detected in formulas."""
    
    def __init__(self, cycle: list):
        self.cycle = cycle
        cycle_str = " -> ".join(cycle)
        super().__init__(f"Circular dependency detected: {cycle_str}")


class MissingDependencyError(FormulaError):
    """Raised when a formula references undefined variables."""
    
    def __init__(self, variable: str, formula: str):
        self.variable = variable
        self.formula = formula
        super().__init__(
            f"Formula references undefined variable '{variable}': {formula}"
        )


# ============================================================================
# Uncertainty Errors
# ============================================================================

class UncertaintyError(DataManipError):
    """Base class for uncertainty propagation errors."""
    pass


class UncertaintyPropagationError(UncertaintyError):
    """Raised when uncertainty propagation fails."""
    
    def __init__(self, column: str, reason: str):
        self.column = column
        self.reason = reason
        super().__init__(
            f"Failed to propagate uncertainty for column '{column}': {reason}"
        )


class MissingUncertaintyError(UncertaintyError):
    """Raised when required uncertainty data is missing."""
    
    def __init__(self, column: str):
        self.column = column
        super().__init__(
            f"Uncertainty data not found for column '{column}'. "
            f"Expected column '{column}_u' to exist."
        )


# ============================================================================
# Study Errors
# ============================================================================

class StudyError(DataManipError):
    """Base class for study-related errors."""
    pass


class StudyNotFoundError(StudyError):
    """Raised when a study doesn't exist in workspace."""
    
    def __init__(self, study_name: str):
        self.study_name = study_name
        super().__init__(f"Study '{study_name}' not found in workspace")


class InvalidStudyTypeError(StudyError):
    """Raised when an invalid study type is specified."""
    
    def __init__(self, study_type: str, valid_types: Optional[List[str]] = None):
        self.study_type = study_type
        self.valid_types = valid_types
        
        message = f"Invalid study type: '{study_type}'"
        if valid_types:
            message += f". Valid types: {', '.join(valid_types)}"
        
        super().__init__(message)


# ============================================================================
# Workspace Errors
# ============================================================================

class WorkspaceError(DataManipError):
    """Base class for workspace-related errors."""
    pass


class ConstantNotFoundError(WorkspaceError):
    """Raised when a workspace constant doesn't exist."""
    
    def __init__(self, constant_name: str):
        self.constant_name = constant_name
        super().__init__(f"Workspace constant '{constant_name}' not found")


class ConstantEvaluationError(WorkspaceError):
    """Raised when a calculated constant fails to evaluate."""
    
    def __init__(self, constant_name: str, error: Exception):
        self.constant_name = constant_name
        self.original_error = error
        super().__init__(
            f"Failed to evaluate constant '{constant_name}': {str(error)}"
        )


# ============================================================================
# I/O Errors
# ============================================================================

class IOError(DataManipError):
    """Base class for input/output errors."""
    pass


class FileImportError(IOError):
    """Raised when file import fails."""
    
    def __init__(self, filepath: str, reason: str):
        self.filepath = filepath
        self.reason = reason
        super().__init__(f"Failed to import '{filepath}': {reason}")


class FileExportError(IOError):
    """Raised when file export fails."""
    
    def __init__(self, filepath: str, reason: str):
        self.filepath = filepath
        self.reason = reason
        super().__init__(f"Failed to export to '{filepath}': {reason}")


class UnsupportedFileFormatError(IOError):
    """Raised when file format is not supported."""
    
    def __init__(self, filepath: str, supported_formats: Optional[List[str]] = None):
        self.filepath = filepath
        self.supported_formats = supported_formats
        
        message = f"Unsupported file format: '{filepath}'"
        if supported_formats:
            message += f". Supported formats: {', '.join(supported_formats)}"
        
        super().__init__(message)


# ============================================================================
# Validation Errors
# ============================================================================

class ValidationError(DataManipError):
    """Base class for validation errors."""
    pass


class InvalidNameError(ValidationError):
    """Raised when a name doesn't meet validation criteria."""
    
    def __init__(self, name: str, reason: str):
        self.name = name
        self.reason = reason
        super().__init__(f"Invalid name '{name}': {reason}")


class InvalidValueError(ValidationError):
    """Raised when a value doesn't meet validation criteria."""
    
    def __init__(self, field: str, value: Any, reason: str):
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(f"Invalid value for '{field}': {reason}")


class RangeError(ValidationError):
    """Raised when a value is out of valid range."""
    
    def __init__(self, value: Any, min_val: Optional[Any] = None, max_val: Optional[Any] = None):
        self.value = value
        self.min_val = min_val
        self.max_val = max_val
        
        message = f"Value {value} out of range"
        if min_val is not None and max_val is not None:
            message += f" [{min_val}, {max_val}]"
        elif min_val is not None:
            message += f" (minimum: {min_val})"
        elif max_val is not None:
            message += f" (maximum: {max_val})"
        
        super().__init__(message)
