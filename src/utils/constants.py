"""
Common constants used across the application.

This module contains constants that are shared across multiple widgets and modules.
"""

from typing import List

# ============================================================================
# Unit Constants
# ============================================================================

# Common physical units for quick selection in dialogs
COMMON_UNITS: List[str] = [
    "",  # No unit
    # Length
    "m", "cm", "mm", "μm", "nm", "km", "in", "ft",
    # Mass
    "kg", "g", "mg", "μg", "lb", "oz",
    # Time
    "s", "ms", "μs", "ns", "min", "h", "day",
    # Temperature
    "K", "°C", "°F",
    # Pressure
    "Pa", "kPa", "MPa", "bar", "atm", "psi", "mmHg",
    # Volume
    "L", "mL", "μL", "m³", "cm³",
    # Energy
    "J", "kJ", "MJ", "eV", "keV", "MeV", "cal", "kcal",
    # Power
    "W", "kW", "MW", "hp",
    # Electric
    "V", "mV", "A", "mA", "μA", "Ω", "kΩ", "MΩ",
    # Frequency
    "Hz", "kHz", "MHz", "GHz",
    # Angle
    "rad", "deg", "°",
    # Other
    "mol", "%", "ppm", "ppb",
]

# ============================================================================
# Symbol Constants
# ============================================================================

# Mathematical symbols for column type indicators
SYMBOL_DATA = "●"
SYMBOL_CALCULATED = "ƒ"
SYMBOL_DERIVATIVE = "∂"
SYMBOL_RANGE = "▬"
SYMBOL_INTERPOLATION = "⌇"
SYMBOL_UNCERTAINTY = "σ"

# ============================================================================
# Validation Constants
# ============================================================================

# Default limits for numeric inputs
DEFAULT_MAX_PRECISION = 15
DEFAULT_MAX_ROWS = 1_000_000
DEFAULT_MAX_COLUMNS = 1_000

# Default limits for text inputs
DEFAULT_MAX_NAME_LENGTH = 100
DEFAULT_MAX_DESCRIPTION_LENGTH = 500
DEFAULT_MAX_FORMULA_LENGTH = 1_000

# ============================================================================
# Display Constants
# ============================================================================

# Default number formatting
DEFAULT_NUMERIC_PRECISION = 6
DEFAULT_INTEGER_PRECISION = 0

# Default table dimensions
DEFAULT_COLUMN_WIDTH = 100
DEFAULT_ROW_HEIGHT = 25

# ============================================================================
# File I/O Constants
# ============================================================================

# Supported file extensions
SUPPORTED_DATA_EXTENSIONS = [".csv", ".tsv", ".txt", ".xlsx", ".xls", ".json"]
SUPPORTED_EXPORT_EXTENSIONS = [".csv", ".tsv", ".xlsx", ".json", ".html", ".md"]

# Default encoding
DEFAULT_FILE_ENCODING = "utf-8"

# ============================================================================
# Formula Constants
# ============================================================================

# Maximum formula dependencies to prevent circular references
MAX_FORMULA_DEPTH = 100

# Common mathematical constants
MATH_CONSTANTS = {
    "pi": 3.141592653589793,
    "e": 2.718281828459045,
    "phi": 1.618033988749895,  # Golden ratio
    "tau": 6.283185307179586,  # 2*pi
}

# ============================================================================
# Color Constants
# ============================================================================

# Colors for different column types (for future use)
COLOR_DATA = "#FFFFFF"           # White
COLOR_CALCULATED = "#E8F4F8"     # Light blue
COLOR_DERIVATIVE = "#F0E8F8"     # Light purple
COLOR_RANGE = "#E8F8F0"          # Light green
COLOR_UNCERTAINTY = "#F8F0E8"    # Light orange
COLOR_READONLY = "#F5F5F5"       # Light gray

# ============================================================================
# Application Constants
# ============================================================================

APP_NAME = "DataManip"
APP_VERSION = "1.0.0"
APP_ORGANIZATION = "DataManip"

# ============================================================================
# Error Messages
# ============================================================================

ERROR_CIRCULAR_DEPENDENCY = "Circular dependency detected in formula"
ERROR_MISSING_DEPENDENCY = "Formula references undefined variable"
ERROR_INVALID_FORMULA = "Invalid formula syntax"
ERROR_INCOMPATIBLE_UNITS = "Incompatible units in operation"
ERROR_DIVISION_BY_ZERO = "Division by zero"
ERROR_NUMERICAL_OVERFLOW = "Numerical overflow"
