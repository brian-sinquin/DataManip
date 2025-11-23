"""Constants for DataTable widget styling and symbols."""

from PySide6.QtGui import QColor

# Column type symbols for headers
COLUMN_SYMBOLS = {
    "data": "✎",         # Pencil - editable
    "calculated": "ƒ",   # Function symbol
    "derivative": "d/dx", # Derivative notation
    "range": "⋯",        # Range dots
    "uncertainty": "δ",  # Delta - uncertainty
}

# Column type text colors (for headers)
COLUMN_TEXT_COLORS = {
    "data": QColor(0, 0, 0),           # Black
    "calculated": QColor(180, 120, 0), # Dark yellow/orange
    "derivative": QColor(0, 80, 180),  # Dark blue
    "range": QColor(0, 120, 60),       # Dark green
    "uncertainty": QColor(140, 0, 140), # Purple
}

# Column type background colors (for cells)
COLUMN_BG_COLORS = {
    "data": QColor(255, 255, 255),      # White - editable
    "calculated": QColor(255, 250, 240), # Light cream
    "derivative": QColor(240, 245, 255), # Light blue
    "range": QColor(240, 255, 245),      # Light green
    "uncertainty": QColor(250, 240, 250), # Light purple
}

# Alternate row colors
COLUMN_BG_COLORS_ALT = {
    "data": QColor(248, 248, 248),      # Light gray
    "calculated": QColor(252, 248, 235), # Darker cream
    "derivative": QColor(235, 242, 252), # Darker blue
    "range": QColor(235, 252, 242),      # Darker green
    "uncertainty": QColor(248, 235, 248), # Darker purple
}
