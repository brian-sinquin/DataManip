"""Unified validation functions for column names, formulas, and values.

Centralizes all validation logic to eliminate duplication across dialogs,
widgets, and backend code.
"""

from typing import Optional


def validate_column_name(
    name: str,
    existing_columns: Optional[list] = None,
    allow_existing: bool = False
) -> tuple[bool, str]:
    """Validate column name according to naming rules.
    
    Rules:
    - Cannot be empty
    - Must be alphanumeric (underscores and hyphens allowed)
    - Cannot start with a digit
    - Must be unique (unless allow_existing=True)
    
    Args:
        name: Column name to validate
        existing_columns: List of existing column names (optional)
        allow_existing: Whether to allow existing names (for edit operations)
        
    Returns:
        Tuple of (is_valid, error_message)
        - (True, "") if valid
        - (False, "error message") if invalid
        
    Examples:
        >>> validate_column_name("velocity")
        (True, "")
        >>> validate_column_name("2fast")
        (False, "Column name cannot start with a digit")
        >>> validate_column_name("my var")
        (False, "Column name must be alphanumeric (underscores and hyphens allowed)")
    """
    if not name:
        return False, "Column name cannot be empty"
    
    if not name.replace('_', '').replace('-', '').isalnum():
        return False, "Column name must be alphanumeric (underscores and hyphens allowed)"
    
    if name[0].isdigit():
        return False, "Column name cannot start with a digit"
    
    if not allow_existing and existing_columns and name in existing_columns:
        return False, f"Column '{name}' already exists"
    
    return True, ""


def validate_constant_name(
    name: str,
    existing_constants: Optional[list] = None,
    allow_existing: bool = False
) -> tuple[bool, str]:
    """Validate constant name according to naming rules.
    
    Same rules as column names but for workspace constants.
    
    Args:
        name: Constant name to validate
        existing_constants: List of existing constant names (optional)
        allow_existing: Whether to allow existing names (for edit operations)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, "Constant name cannot be empty"
    
    if not name.replace('_', '').isalnum():
        return False, "Constant name must be alphanumeric (underscores allowed)"
    
    if name[0].isdigit():
        return False, "Constant name cannot start with a digit"
    
    # Check for reserved Python keywords
    import keyword
    if keyword.iskeyword(name):
        return False, f"'{name}' is a reserved Python keyword"
    
    if not allow_existing and existing_constants and name in existing_constants:
        return False, f"Constant '{name}' already exists"
    
    return True, ""


def validate_formula(formula: str, allow_empty: bool = False) -> tuple[bool, str]:
    """Validate formula syntax (basic checks).
    
    Args:
        formula: Formula string to validate
        allow_empty: Whether empty formulas are allowed
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not formula:
        if allow_empty:
            return True, ""
        return False, "Formula cannot be empty"
    
    # Check for balanced braces (for {variable} syntax)
    if formula.count('{') != formula.count('}'):
        return False, "Unbalanced braces in formula"
    
    # Basic syntax check - try to compile
    try:
        # Replace {var} with valid Python names for compilation check
        import re
        test_formula = formula
        variables = re.findall(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}', formula)
        for var in variables:
            test_formula = test_formula.replace(f"{{{var}}}", var)
        
        compile(test_formula, "<string>", "eval")
        return True, ""
    except SyntaxError as e:
        return False, f"Syntax error: {str(e)}"
    except Exception as e:
        return False, f"Invalid formula: {str(e)}"


def validate_numeric_value(
    value: str,
    allow_empty: bool = False,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None
) -> tuple[bool, str]:
    """Validate numeric value.
    
    Args:
        value: String representation of number
        allow_empty: Whether empty values are allowed
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not value:
        if allow_empty:
            return True, ""
        return False, "Value cannot be empty"
    
    try:
        num = float(value)
        
        if min_value is not None and num < min_value:
            return False, f"Value must be >= {min_value}"
        
        if max_value is not None and num > max_value:
            return False, f"Value must be <= {max_value}"
        
        return True, ""
    except ValueError:
        return False, "Value must be a valid number"


def validate_parameter_name(name: str, existing_params: Optional[list] = None) -> tuple[bool, str]:
    """Validate function parameter name.
    
    Args:
        name: Parameter name to validate
        existing_params: List of existing parameter names
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, "Parameter name cannot be empty"
    
    if not name.isidentifier():
        return False, "Parameter name must be a valid Python identifier"
    
    import keyword
    if keyword.iskeyword(name):
        return False, f"'{name}' is a reserved Python keyword"
    
    if existing_params and name in existing_params:
        return False, f"Parameter '{name}' already exists"
    
    return True, ""


def validate_unit(unit: str) -> tuple[bool, str]:
    """Validate unit string (basic check).
    
    Currently just checks for reasonable characters.
    Could be enhanced to use pint library for full validation.
    
    Args:
        unit: Unit string (e.g., "m", "kg/s^2")
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not unit:
        return True, ""  # Empty units are allowed
    
    # Allow alphanumeric, /, ^, *, (, ), and common special chars
    import re
    if not re.match(r'^[a-zA-Z0-9/*^().\- ]+$', unit):
        return False, "Unit contains invalid characters"
    
    return True, ""
