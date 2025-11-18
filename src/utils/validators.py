"""
Validation utilities for common input validation patterns.

This module provides reusable validation functions for:
- Column/variable names
- Numeric inputs
- File paths
- Formula syntax
"""

import re
from typing import Optional, List, Tuple


def validate_identifier_name(
    name: str,
    existing_names: Optional[List[str]] = None,
    current_name: Optional[str] = None,
    allow_empty: bool = False,
    min_length: int = 1,
    max_length: Optional[int] = None
) -> Tuple[bool, Optional[str]]:
    """Validate an identifier name (column, variable, etc.).
    
    Rules:
    - Must contain only alphanumeric characters, underscore, and hyphen
    - Cannot be a duplicate of existing names
    - Must meet length requirements
    
    Args:
        name: Name to validate
        existing_names: List of existing names to check for duplicates
        current_name: Current name (for edit mode - excluded from duplicate check)
        allow_empty: If True, empty names are considered valid
        min_length: Minimum length (default: 1)
        max_length: Maximum length (None = no limit)
        
    Returns:
        Tuple of (is_valid, error_message)
        error_message is None if valid, otherwise contains the error description
        
    Examples:
        >>> validate_identifier_name("my_column")
        (True, None)
        >>> validate_identifier_name("my column")
        (False, "Name should only contain letters, numbers, _, -")
        >>> validate_identifier_name("x", existing_names=["x", "y"])
        (False, "Name 'x' already exists")
    """
    # Check if empty
    name = name.strip()
    if not name:
        if allow_empty:
            return True, None
        return False, "Name cannot be empty"
    
    # Check length
    if len(name) < min_length:
        return False, f"Name must be at least {min_length} character(s) long"
    if max_length and len(name) > max_length:
        return False, f"Name must be at most {max_length} characters long"
    
    # Check for invalid characters (allow only alphanumeric, _, -)
    if not re.match(r'^[a-zA-Z0-9_\-]+$', name):
        return False, "Name should only contain letters, numbers, _, -"
    
    # Check for duplicates
    if existing_names:
        # In edit mode, exclude the current name from duplicate check
        check_names = [n for n in existing_names if n != current_name]
        if name in check_names:
            return False, f"Name '{name}' already exists"
    
    return True, None


def validate_numeric_input(
    value_str: str,
    allow_empty: bool = False,
    allow_negative: bool = True,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    integer_only: bool = False
) -> Tuple[bool, Optional[str], Optional[float]]:
    """Validate numeric input string.
    
    Args:
        value_str: String to validate and convert
        allow_empty: If True, empty strings are valid (returns None)
        allow_negative: If True, negative numbers are allowed
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        integer_only: If True, only integers are allowed
        
    Returns:
        Tuple of (is_valid, error_message, parsed_value)
        parsed_value is None if invalid or empty
        
    Examples:
        >>> validate_numeric_input("42.5")
        (True, None, 42.5)
        >>> validate_numeric_input("-5", allow_negative=False)
        (False, "Negative numbers not allowed", None)
        >>> validate_numeric_input("abc")
        (False, "Invalid number", None)
    """
    value_str = value_str.strip()
    
    # Handle empty input
    if not value_str:
        if allow_empty:
            return True, None, None
        return False, "Value cannot be empty", None
    
    # Try to parse
    try:
        if integer_only:
            value = int(value_str)
        else:
            value = float(value_str)
    except ValueError:
        return False, "Invalid number", None
    
    # Check negative
    if not allow_negative and value < 0:
        return False, "Negative numbers not allowed", None
    
    # Check range
    if min_value is not None and value < min_value:
        return False, f"Value must be at least {min_value}", None
    if max_value is not None and value > max_value:
        return False, f"Value must be at most {max_value}", None
    
    return True, None, value


def validate_formula_braces(formula: str) -> Tuple[bool, Optional[str]]:
    """Validate that braces in formula are balanced.
    
    Args:
        formula: Formula string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Examples:
        >>> validate_formula_braces("{x} + {y}")
        (True, None)
        >>> validate_formula_braces("{x + y")
        (False, "Unbalanced { } braces")
    """
    if formula.count('{') != formula.count('}'):
        return False, "Unbalanced { } braces"
    
    # Check proper nesting
    depth = 0
    for char in formula:
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth < 0:
                return False, "Unbalanced { } braces (closing before opening)"
    
    if depth != 0:
        return False, "Unbalanced { } braces"
    
    return True, None


def extract_formula_variables(formula: str) -> List[str]:
    """Extract variable names from formula using {name} syntax.
    
    Args:
        formula: Formula string with {variable} references
        
    Returns:
        List of unique variable names (sorted)
        
    Examples:
        >>> extract_formula_variables("{x} + {y} * {x}")
        ['x', 'y']
        >>> extract_formula_variables("2 * {temperature}")
        ['temperature']
    """
    pattern = r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}'
    matches = re.findall(pattern, formula)
    return sorted(set(matches))


def validate_formula_variables(
    formula: str,
    available_variables: List[str]
) -> Tuple[bool, Optional[str], List[str]]:
    """Validate that all variables in formula exist.
    
    Args:
        formula: Formula string
        available_variables: List of available variable names
        
    Returns:
        Tuple of (is_valid, error_message, referenced_variables)
        
    Examples:
        >>> validate_formula_variables("{x} + {y}", ["x", "y", "z"])
        (True, None, ['x', 'y'])
        >>> validate_formula_variables("{x} + {unknown}", ["x", "y"])
        (False, "Unknown variable(s): unknown", ['x', 'unknown'])
    """
    # Extract variables from formula
    referenced = extract_formula_variables(formula)
    
    # Check if all exist
    missing = [var for var in referenced if var not in available_variables]
    
    if missing:
        return False, f"Unknown variable(s): {', '.join(missing)}", referenced
    
    return True, None, referenced


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """Sanitize a filename by removing/replacing invalid characters.
    
    Args:
        filename: Filename to sanitize
        replacement: Character to replace invalid characters with
        
    Returns:
        Sanitized filename
        
    Examples:
        >>> sanitize_filename("my/file:name.txt")
        'my_file_name.txt'
        >>> sanitize_filename("data (2024).csv")
        'data _2024_.csv'
    """
    # Replace invalid filename characters
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, replacement, filename)
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    
    # Ensure not empty
    if not sanitized:
        sanitized = "unnamed"
    
    return sanitized


def validate_file_extension(
    filename: str,
    allowed_extensions: List[str],
    case_sensitive: bool = False
) -> Tuple[bool, Optional[str]]:
    """Validate file extension.
    
    Args:
        filename: Filename to check
        allowed_extensions: List of allowed extensions (with or without dot)
        case_sensitive: If True, extension check is case-sensitive
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Examples:
        >>> validate_file_extension("data.csv", [".csv", ".txt"])
        (True, None)
        >>> validate_file_extension("data.xlsx", [".csv", ".txt"])
        (False, "File extension must be one of: .csv, .txt")
    """
    # Normalize extensions (ensure they start with dot)
    normalized_exts = []
    for ext in allowed_extensions:
        if not ext.startswith('.'):
            ext = '.' + ext
        if not case_sensitive:
            ext = ext.lower()
        normalized_exts.append(ext)
    
    # Get file extension
    if '.' not in filename:
        return False, f"File extension must be one of: {', '.join(normalized_exts)}"
    
    file_ext = '.' + filename.rsplit('.', 1)[1]
    if not case_sensitive:
        file_ext = file_ext.lower()
    
    # Check if allowed
    if file_ext not in normalized_exts:
        return False, f"File extension must be one of: {', '.join(normalized_exts)}"
    
    return True, None
