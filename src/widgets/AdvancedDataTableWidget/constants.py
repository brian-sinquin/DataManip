"""Constants and configuration values for AdvancedDataTableWidget.

This module centralizes all magic strings, symbols, and configuration
values used throughout the advanced data table widget to ensure consistency
and ease of maintenance.
"""

# ============================================================================
# Display and Formatting Constants
# ============================================================================

# Numeric precision for cell display
DEFAULT_NUMERIC_PRECISION = ".6g"

# Error prefix for formula evaluation errors
ERROR_PREFIX = "#ERROR: "

# ============================================================================
# Column Type Symbols
# ============================================================================
# Visual indicators shown in column headers to identify column types at a glance

# Symbol for DATA columns (measured/input data points)
SYMBOL_DATA = "● "  # Black circle

# Symbol for CALCULATED columns (values derived from formulas)
SYMBOL_CALCULATED = "ƒ "  # Script f (function)

# Symbol for DERIVATIVE columns (discrete differences dy/dx)
SYMBOL_DERIVATIVE = "∂ "  # Partial derivative symbol

# Symbol for UNCERTAINTY columns (standard deviation/error values)
SYMBOL_UNCERTAINTY = "σ "  # Sigma (standard deviation)

# Symbol for INTERPOLATION columns (interpolated values)
SYMBOL_INTERPOLATION = "⊶ "  # Interpolation symbol

# Symbol for RANGE columns (auto-generated evenly spaced values)
SYMBOL_RANGE = "⋯ "  # Horizontal ellipsis

# ============================================================================
# Formula Patterns
# ============================================================================

# Pattern for formula references using {diminutive} syntax
FORMULA_REFERENCE_PATTERN = r'\{([^}]+)\}'

# Pattern for backward compatibility with [diminutive] syntax
BACKWARD_COMPAT_PATTERN = r'\[([^\]]+)\]'

# ============================================================================
# Uncertainty Column Display
# ============================================================================

# Display text for uncertainty column headers
UNCERTAINTY_HEADER_TEXT = "±"

# ============================================================================
# Validation Limits
# ============================================================================

# Maximum number of points allowed in range columns
MAX_RANGE_POINTS = 1000

# Minimum number of points required in range columns
MIN_RANGE_POINTS = 2

# ============================================================================
# Common Physical Units
# ============================================================================

COMMON_UNITS = [
    "-- Common Units --",
    # Temperature
    "°C", "°F", "K",
    # Pressure
    "Pa", "kPa", "MPa", "bar", "atm", "mmHg",
    # Voltage
    "V", "mV", "kV",
    # Current
    "A", "mA", "µA",
    # Length
    "m", "cm", "mm", "km", "in", "ft",
    # Time
    "s", "ms", "µs", "min", "h",
    # Mass
    "kg", "g", "mg", "lb", "oz",
    # Velocity
    "m/s", "km/h", "mph",
    # Frequency
    "Hz", "kHz", "MHz", "GHz",
    # Concentration
    "%", "ppm", "ppb",
]

# ============================================================================
# UI Messages
# ============================================================================

# Status messages
MSG_COLUMN_ADDED = "Added column '{name}'"
MSG_COLUMN_REMOVED = "Removed column '{name}'"
MSG_ROW_ADDED = "Added new row"
MSG_ROW_REMOVED = "Removed row"
MSG_DATA_CLEARED = "All data cleared"
MSG_RECALCULATED = "Recalculated {count} column(s)"

# Error messages
ERR_COLUMN_NOT_FOUND = "Column '{name}' not found"
ERR_INVALID_COLUMN_INDEX = "Column index {index} out of range"
ERR_DUPLICATE_DIMINUTIVE = "Diminutive '{dim}' already exists"
ERR_INVALID_FORMULA = "Invalid formula: {error}"
ERR_UNIT_MISMATCH = "Unit mismatch: {error}"
ERR_DIVISION_BY_ZERO = "Division by zero"
ERR_MISSING_DIMINUTIVE = "Diminutive is required"
ERR_INVALID_RANGE = "Invalid range parameters"
ERR_TOO_MANY_POINTS = f"Number of points limited to {MAX_RANGE_POINTS}"

# Confirmation messages
CONFIRM_REMOVE_COLUMN = "Remove column '{name}'?"
CONFIRM_REMOVE_UNCERTAINTY = "Remove uncertainty column for '{name}'?"
CONFIRM_CLEAR_ALL = "Clear all data and columns?\nThis action cannot be undone."
CONFIRM_REMOVE_ROW = "Remove the last row?"

# ============================================================================
# Dialog Titles
# ============================================================================

DIALOG_EDIT_DATA_COLUMN = "Edit Data Column - {name}"
DIALOG_EDIT_FORMULA = "Edit Calculated Column - {name}"
DIALOG_EDIT_DERIVATIVE = "Edit Derivative Column - {name}"
DIALOG_ADD_DERIVATIVE = "Add Derivative Column"
DIALOG_ADD_RANGE = "Create Range Column"
DIALOG_EDIT_INTERPOLATION = "Edit Interpolation Column - {name}"
DIALOG_ADD_INTERPOLATION = "Add Interpolation Column"
DIALOG_MANAGE_VARIABLES = "Manage Variables"

# ============================================================================
# Tooltip Templates
# ============================================================================

TOOLTIP_UNCERTAINTY_OF = "Uncertainty of {name}"
TOOLTIP_UNCERTAINTY_OF_WITH_UNIT = "Uncertainty of {name} [{unit}]"
TOOLTIP_DERIVATIVE = "Derivative: d({num})/d({den})"

# ============================================================================
# Formula Help Text
# ============================================================================

FORMULA_HELP_TEXT = """Operators: + - * / ** (power) ( )
Functions: sin, cos, tan, sqrt, log, exp, etc.
Examples:
  {temp} * 1.8 + 32
  {m} * {g}  (mass × gravity)
  ({x} ** 2 + {y} ** 2) ** 0.5

Tip: Use "Manage Variables" (right-click menu)
to define constants like {g}, {c}, {pi}"""

# ============================================================================
# Uncertainty Info Messages
# ============================================================================

INFO_UNCERTAINTY_EXISTS = "✓ Uncertainty column already exists (Column {index})"
INFO_UNCERTAINTY_WILL_CREATE = "ⓘ Will create a new uncertainty column when applied"
INFO_UNCERTAINTY_WILL_REMOVE = "⚠ Will remove existing uncertainty column (Column {index})"
INFO_UNCERTAINTY_AUTO_UPDATE = "ⓘ Uncertainty column already exists (Column {index}).\n   It will be automatically updated based on input uncertainties."
INFO_UNCERTAINTY_AUTO_CREATE = "ⓘ An uncertainty column will be created automatically.\n   Only inputs with uncertainty columns will contribute to the calculation."
INFO_UNCERTAINTY_WILL_BE_REMOVED = "⚠ Existing uncertainty column (Column {index}) will be removed."

# ============================================================================
# Interpolation Methods
# ============================================================================

INTERPOLATION_METHODS = {
    'linear': 'Linear Interpolation',
    'cubic': 'Cubic Spline',
    'quadratic': 'Quadratic Spline',
    'nearest': 'Nearest Neighbor'
}
