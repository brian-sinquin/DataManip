"""Custom exception classes for AdvancedDataTableWidget.

This module provides specific exception types for different error conditions,
making error handling more precise and descriptive.
"""


class DataTableError(Exception):
    """Base exception for all data table errors."""
    pass


class ColumnError(DataTableError):
    """Base exception for column-related errors."""
    pass


class ColumnNotFoundError(ColumnError):
    """Raised when a column cannot be found by index or diminutive."""
    
    def __init__(self, column_identifier: str | int):
        if isinstance(column_identifier, int):
            msg = f"Column index {column_identifier} does not exist"
        else:
            msg = f"Column '{column_identifier}' not found"
        super().__init__(msg)
        self.column_identifier = column_identifier


class DuplicateDiminutiveError(ColumnError):
    """Raised when attempting to create a column with a duplicate diminutive."""
    
    def __init__(self, diminutive: str):
        super().__init__(f"Diminutive '{diminutive}' already exists")
        self.diminutive = diminutive


class InvalidColumnTypeError(ColumnError):
    """Raised when an operation is invalid for a column's type."""
    
    def __init__(self, operation: str, column_type: str):
        super().__init__(f"Cannot {operation} for {column_type} columns")
        self.operation = operation
        self.column_type = column_type


class InvalidColumnIndexError(ColumnError):
    """Raised when a column index is out of range."""
    
    def __init__(self, index: int, max_index: int):
        super().__init__(f"Column index {index} out of range (0-{max_index})")
        self.index = index
        self.max_index = max_index


class FormulaError(DataTableError):
    """Base exception for formula-related errors."""
    pass


class InvalidFormulaError(FormulaError):
    """Raised when a formula is syntactically invalid."""
    
    def __init__(self, formula: str, reason: str):
        super().__init__(f"Invalid formula '{formula}': {reason}")
        self.formula = formula
        self.reason = reason


class FormulaEvaluationError(FormulaError):
    """Raised when formula evaluation fails at runtime."""
    
    def __init__(self, formula: str, error: str):
        super().__init__(f"Error evaluating formula '{formula}': {error}")
        self.formula = formula
        self.error = error


class UndefinedVariableError(FormulaError):
    """Raised when a formula references an undefined variable or column."""
    
    def __init__(self, variable: str):
        super().__init__(f"Undefined variable or column: '{variable}'")
        self.variable = variable


class UnitError(DataTableError):
    """Base exception for unit-related errors."""
    pass


class UnitMismatchError(UnitError):
    """Raised when units are incompatible in an operation."""
    
    def __init__(self, operation: str, unit1: str, unit2: str):
        super().__init__(f"Unit mismatch in {operation}: '{unit1}' and '{unit2}' are incompatible")
        self.operation = operation
        self.unit1 = unit1
        self.unit2 = unit2


class InvalidUnitError(UnitError):
    """Raised when a unit string cannot be parsed."""
    
    def __init__(self, unit: str):
        super().__init__(f"Invalid unit: '{unit}'")
        self.unit = unit


class ValidationError(DataTableError):
    """Base exception for validation errors."""
    pass


class MissingRequiredValueError(ValidationError):
    """Raised when a required value is missing."""
    
    def __init__(self, field_name: str):
        super().__init__(f"Required value missing: {field_name}")
        self.field_name = field_name


class InvalidValueError(ValidationError):
    """Raised when a value doesn't meet validation criteria."""
    
    def __init__(self, field_name: str, value, reason: str):
        super().__init__(f"Invalid value for {field_name}: {reason}")
        self.field_name = field_name
        self.value = value
        self.reason = reason


class RangeError(ValidationError):
    """Raised when range parameters are invalid."""
    
    def __init__(self, reason: str):
        super().__init__(f"Invalid range: {reason}")
        self.reason = reason


class UncertaintyError(DataTableError):
    """Base exception for uncertainty calculation errors."""
    pass


class UncertaintyCalculationError(UncertaintyError):
    """Raised when uncertainty calculation fails."""
    
    def __init__(self, formula: str, error: str):
        super().__init__(f"Error calculating uncertainty for '{formula}': {error}")
        self.formula = formula
        self.error = error


class MissingUncertaintyDataError(UncertaintyError):
    """Raised when required uncertainty data is missing."""
    
    def __init__(self, variable: str):
        super().__init__(f"Missing uncertainty data for variable: '{variable}'")
        self.variable = variable
