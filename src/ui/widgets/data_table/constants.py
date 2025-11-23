"""Constants for DataTable widget styling and symbols.

This module defines visual and display constants for the DataTable widget:
- DISPLAY_PRECISION: Number of significant digits for cell display (EditRole preserves full precision)
- COLUMN_SYMBOLS: Unicode symbols for visual column type identification in headers, tooltips, and dialogs

The column symbols provide quick visual feedback about column types:
- ✎ (pencil): DATA columns - user-editable
- ƒ (function): CALCULATED columns - formula-based
- d/dx: DERIVATIVE columns - numerical differentiation
- ⋯ (ellipsis): RANGE columns - generated sequences
- δ (delta): UNCERTAINTY columns - error propagation
"""

# Display settings
DISPLAY_PRECISION = 33  # Number of significant digits to display in cells

# Column type symbols for headers
COLUMN_SYMBOLS = {
    "data": "✎",         # Pencil - editable
    "calculated": "ƒ",   # Function symbol
    "derivative": "d/dx", # Derivative notation
    "range": "⋯",        # Range dots
    "uncertainty": "δ",  # Delta - uncertainty
}
