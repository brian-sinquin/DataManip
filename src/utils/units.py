"""Unit formatting utilities for prettier display using UTF-8 characters.

This module provides functions to format scientific units with:
- Superscript characters for exponents (² ³ ⁴ etc.) instead of **
- Interpunct (·) or multiplication sign (×) instead of spaces
- Proper unicode formatting for better readability
"""

# Superscript mapping for common exponents
SUPERSCRIPT_MAP = {
    '0': '⁰',
    '1': '¹',
    '2': '²',
    '3': '³',
    '4': '⁴',
    '5': '⁵',
    '6': '⁶',
    '7': '⁷',
    '8': '⁸',
    '9': '⁹',
    '-': '⁻',
    '+': '⁺',
}

# Subscript mapping for chemical formulas (future use)
SUBSCRIPT_MAP = {
    '0': '₀',
    '1': '₁',
    '2': '₂',
    '3': '₃',
    '4': '₄',
    '5': '₅',
    '6': '₆',
    '7': '₇',
    '8': '₈',
    '9': '₉',
}


def to_superscript(text: str) -> str:
    """Convert a string of digits and signs to superscript.
    
    Args:
        text: String to convert (e.g., "2", "-1", "10")
        
    Returns:
        Superscript version of the text
        
    Examples:
        >>> to_superscript("2")
        '²'
        >>> to_superscript("-1")
        '⁻¹'
        >>> to_superscript("10")
        '¹⁰'
    """
    return ''.join(SUPERSCRIPT_MAP.get(c, c) for c in str(text))


def format_unit_pretty(unit_str: str, use_dot: bool = True, use_superscript: bool = True) -> str:
    """Format a unit string with UTF-8 characters for prettier display.
    
    Transformations:
    - ** or ^ → superscript characters (² ³ ⁴ etc.)
    - / unit**n → unit⁻ⁿ (convert division to negative exponent)
    - * or space → · (interpunct) or × (multiplication sign)
    
    Args:
        unit_str: The unit string to format (e.g., "kg*m/s**2", "m s^-1")
        use_dot: If True, use · (interpunct), if False use × (multiplication)
        use_superscript: If True, convert exponents to superscript
        
    Returns:
        Formatted unit string
        
    Examples:
        >>> format_unit_pretty("kg*m/s**2")
        'kg·m·s⁻²'
        >>> format_unit_pretty("m**3")
        'm³'
        >>> format_unit_pretty("kg m s**-2")
        'kg·m·s⁻²'
        >>> format_unit_pretty("m/s")
        'm·s⁻¹'
    """
    if not unit_str:
        return ""
    
    import re
    result = unit_str
    
    # First, normalize spaces around operators
    result = re.sub(r'\s*\*\s*', '*', result)
    result = re.sub(r'\s*/\s*', '/', result)
    result = re.sub(r'\s*\*\*\s*', '**', result)
    
    # Convert divisions to negative exponents
    # Pattern: / followed by unit name, optionally followed by **exponent
    # Examples: /s**2 -> s**-2, /m -> m**-1
    
    # Split by / to handle denominators
    parts = result.split('/')
    if len(parts) > 1:
        # First part is numerator
        numerator = parts[0]
        
        # Process denominators - convert each to negative exponent
        denominators = []
        for denom_part in parts[1:]:
            # Find all units with optional exponents in the denominator
            # Pattern: unit_name optionally followed by **exponent
            # Use findall to extract unit tokens
            unit_pattern = r'([a-zA-Z_]\w*)(?:\*\*([\-+]?\d+))?'
            matches = re.findall(unit_pattern, denom_part)
            
            for unit_name, exponent in matches:
                if not unit_name:
                    continue
                    
                if exponent:
                    # Unit has exponent: unit**n -> unit**-n (negate the exponent)
                    exp = int(exponent)
                    denominators.append(f"{unit_name}**{-exp}")
                else:
                    # Unit without exponent: unit -> unit**-1
                    denominators.append(f"{unit_name}**-1")
        
        # Combine numerator and converted denominators
        if denominators:
            result = numerator + '*' + '*'.join(denominators)
        else:
            result = numerator
    
    # Handle exponents (** or ^) - convert to superscript
    if use_superscript:
        # Pattern to match **N or ^N where N is one or more digits, possibly with - or +
        pattern = r'\s*(\*\*|\^)\s*([\-+]?\d+)'
        
        def replace_exponent(match):
            exponent = match.group(2)
            return to_superscript(exponent)
        
        result = re.sub(pattern, replace_exponent, result)
    
    # Replace multiplication operators
    # Use interpunct · (U+00B7) or multiplication sign × (U+00D7)
    mult_char = '·' if use_dot else '×'
    
    # Replace * with the chosen multiplication character
    result = result.replace('*', mult_char)
    
    # Replace spaces between units with the multiplication character
    result = re.sub(r'(?<=\w)\s+(?=\w)', mult_char, result)
    
    return result


def format_pint_unit(pint_unit, use_dot: bool = True, use_superscript: bool = True) -> str:
    """Format a Pint unit object with pretty UTF-8 characters.
    
    Args:
        pint_unit: A Pint Unit or UnitRegistry unit
        use_dot: If True, use · (interpunct), if False use × (multiplication)
        use_superscript: If True, convert exponents to superscript
        
    Returns:
        Formatted unit string
        
    Examples:
        >>> import pint
        >>> ureg = pint.UnitRegistry()
        >>> format_pint_unit(ureg.meter / ureg.second**2)
        'm/s²'
    """
    # Get compact string representation from Pint using short format (~)
    unit_str = f"{pint_unit:~}"
    return format_unit_pretty(unit_str, use_dot=use_dot, use_superscript=use_superscript)


def format_value_with_unit(value: float, unit_str: str, 
                           precision: int | None = None,
                           use_dot: bool = True, 
                           use_superscript: bool = True) -> str:
    """Format a value with its unit, using pretty UTF-8 formatting.
    
    Args:
        value: The numerical value
        unit_str: The unit string
        precision: Number of decimal places (None for automatic)
        use_dot: If True, use · for multiplication
        use_superscript: If True, use superscript for exponents
        
    Returns:
        Formatted string like "9.81 m/s²"
        
    Examples:
        >>> format_value_with_unit(9.81, "m/s**2")
        '9.81 m/s²'
        >>> format_value_with_unit(100, "kg*m**2", precision=1)
        '100.0 kg·m²'
    """
    pretty_unit = format_unit_pretty(unit_str, use_dot=use_dot, use_superscript=use_superscript)
    
    if precision is not None:
        value_str = f"{value:.{precision}f}"
    else:
        value_str = str(value)
    
    if pretty_unit:
        return f"{value_str} {pretty_unit}"
    else:
        return value_str
