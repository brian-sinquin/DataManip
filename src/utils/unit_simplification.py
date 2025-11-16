"""
Unit simplification utilities for derivative calculations.

This module provides functions to simplify unit expressions,
particularly for derivatives where units like (m/s)/s should simplify to m/s².
"""

import re
from typing import Optional


def simplify_derivative_unit(numerator_unit: str, denominator_unit: str) -> str:
    """Simplify a derivative unit expression.
    
    Handles common cases like:
    - (m/s) / s → m/s²
    - (m/s²) / s → m/s³
    - m / s → m/s
    - (kg·m/s) / s → kg·m/s²
    
    Args:
        numerator_unit: Unit of the numerator (dy)
        denominator_unit: Unit of the denominator (dx)
        
    Returns:
        Simplified unit string
    """
    # Handle dimensionless cases
    if not numerator_unit or numerator_unit == "dimensionless" or numerator_unit == "":
        if not denominator_unit or denominator_unit == "dimensionless" or denominator_unit == "":
            return ""
        return f"1/{denominator_unit}"
    
    if not denominator_unit or denominator_unit == "dimensionless" or denominator_unit == "":
        return numerator_unit
    
    # Try to simplify common patterns
    # Pattern: (unit/time) / time → unit/time²
    # Example: (m/s) / s → m/s²
    pattern = r'\(([^/]+)/([^)]+)\)\s*/\s*\2$'
    match = re.match(pattern, f"({numerator_unit})/({denominator_unit})")
    
    if match:
        base_unit = match.group(1).strip()
        time_unit = match.group(2).strip()
        # Check if time_unit already has a power
        power_match = re.match(r'(.+)\^(\d+)$', time_unit)
        if power_match:
            unit_base = power_match.group(1)
            power = int(power_match.group(2))
            return f"{base_unit}/{unit_base}^{power + 1}"
        else:
            return f"{base_unit}/{time_unit}²"
    
    # Check if numerator has form "unit/time" and denominator is same time
    # (m/s) and s
    num_pattern = r'^([^/]+)/(.+)$'
    num_match = re.match(num_pattern, numerator_unit)
    
    if num_match:
        num_base = num_match.group(1).strip()
        num_denom = num_match.group(2).strip()
        
        # Remove parentheses for comparison
        num_denom_clean = num_denom.strip('()')
        den_clean = denominator_unit.strip('()')
        
        if num_denom_clean == den_clean:
            # Check if denominator already has a power
            power_match = re.match(r'(.+)²$', num_denom_clean)
            if power_match:
                # e.g., m/s² divided by s → m/s³
                base = power_match.group(1)
                return f"{num_base}/{base}³"
            
            power_match = re.match(r'(.+)³$', num_denom_clean)
            if power_match:
                base = power_match.group(1)
                return f"{num_base}/{base}⁴"
            
            # No existing power, add ²
            return f"{num_base}/{num_denom_clean}²"
    
    # Default: just return the division expression
    # Clean up extra parentheses if units are simple
    num_needs_parens = '/' in numerator_unit or ' ' in numerator_unit
    den_needs_parens = '/' in denominator_unit or ' ' in denominator_unit
    
    if num_needs_parens:
        numerator_unit = f"({numerator_unit})"
    if den_needs_parens:
        denominator_unit = f"({denominator_unit})"
    
    return f"{numerator_unit}/{denominator_unit}"


def format_unit_superscript(unit: str) -> str:
    """Convert numeric powers to superscript characters.
    
    Converts:
    - ^2 or ² → ²
    - ^3 or ³ → ³
    - ^4 → ⁴
    
    Args:
        unit: Unit string that may contain powers
        
    Returns:
        Unit string with superscript powers
    """
    # Map of numbers to superscripts
    superscripts = {
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
        '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'
    }
    
    # Replace ^N with superscript
    def replace_power(match):
        power = match.group(1)
        return ''.join(superscripts.get(d, d) for d in power)
    
    unit = re.sub(r'\^(\d+)', replace_power, unit)
    
    return unit
