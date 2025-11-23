"""Constants for DataTable widget styling and symbols.

This module defines visual constants specific to the DataTable widget:
- COLUMN_SYMBOLS: Unicode symbols for visual column type identification in headers, tooltips, and dialogs

The column symbols provide quick visual feedback about column types:
- ✎ (pencil): DATA columns - user-editable
- ƒ (function): CALCULATED columns - formula-based
- d/dx: DERIVATIVE columns - numerical differentiation
- ⋯ (ellipsis): RANGE columns - generated sequences
- δ (delta): UNCERTAINTY columns - error propagation

For DISPLAY_PRECISION, import from the main constants module.
"""

from constants import DISPLAY_PRECISION

# Column type symbols for headers
COLUMN_SYMBOLS = {
    "data": "✎",         # Pencil - editable
    "calculated": "ƒ",   # Function symbol
    "derivative": "d/dx", # Derivative notation
    "range": "⋯",        # Range dots
    "uncertainty": "δ",  # Delta - uncertainty
}
