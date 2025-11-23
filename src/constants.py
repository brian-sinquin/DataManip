"""Application-wide constants for DataManip.

This module contains all hardcoded values used throughout the application,
organized by category for easy maintenance and consistency.
"""

# =============================================================================
# UI Window Sizes
# =============================================================================

# Main application window
MAIN_WINDOW_WIDTH = 1200
MAIN_WINDOW_HEIGHT = 800

# Dialog sizes
DIALOG_SMALL_WIDTH = 400
DIALOG_SMALL_HEIGHT = 200

DIALOG_MEDIUM_WIDTH = 450
DIALOG_MEDIUM_HEIGHT = 300

DIALOG_LARGE_WIDTH = 500
DIALOG_LARGE_HEIGHT = 400

DIALOG_XLARGE_WIDTH = 800
DIALOG_XLARGE_HEIGHT = 600

# Specific dialog sizes
DIALOG_RENAME_WIDTH = 400
DIALOG_RENAME_HEIGHT = 180

DIALOG_DERIVATIVE_WIDTH = 450
DIALOG_DERIVATIVE_HEIGHT = 400

DIALOG_CONSTANTS_WIDTH = 500
DIALOG_CONSTANTS_HEIGHT = 400

# =============================================================================
# UI Widget Sizes
# =============================================================================

# Table and list dimensions
TABLE_ROW_HEIGHT = 24  # Compact row height
TABLE_PREVIEW_MAX_HEIGHT = 300

# Input field constraints
FORMULA_INPUT_MAX_HEIGHT = 100
DELIMITER_INPUT_MAX_WIDTH = 50
COLUMN_COMBO_MIN_WIDTH = 200

# Splitter sizes
STATS_SPLITTER_LEFT = 300
STATS_SPLITTER_RIGHT = 700

# =============================================================================
# Export/Import Settings
# =============================================================================

# DPI options for plot export
PLOT_DPI_OPTIONS = ["72", "100", "150", "200", "300", "600"]

# CSV import settings
CSV_MAX_HEADER_ROW = 100

# Excel export settings
EXCEL_MAX_COLUMN_WIDTH = 50
EXCEL_COLUMN_WIDTH_PADDING = 2

# =============================================================================
# Statistics & Visualization
# =============================================================================

# Histogram settings
HISTOGRAM_MIN_BINS = 10
HISTOGRAM_MAX_BINS = 50

# Percentiles
PERCENTILE_Q50 = 50  # Median

# =============================================================================
# Display Precision
# =============================================================================

# Number of significant digits to display in cells
DISPLAY_PRECISION = 3

# =============================================================================
# Column Symbols
# =============================================================================

# Unicode symbols for visual column type identification
COLUMN_SYMBOLS = {
    "data": "✎",         # Pencil - editable
    "calculated": "ƒ",   # Function symbol
    "derivative": "d/dx", # Derivative notation
    "range": "⋯",        # Range dots
    "uncertainty": "δ",  # Delta - uncertainty
}

# =============================================================================
# Application Metadata
# =============================================================================

APP_NAME = "DataManip"
APP_VERSION = "0.2.0"
APP_DESCRIPTION = "Data Analysis for Experimental Sciences"
