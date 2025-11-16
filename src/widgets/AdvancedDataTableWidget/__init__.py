"""
AdvancedDataTableWidget Package

A sophisticated table widget for scientific data manipulation with support for:
- Data columns with units and diminutives
- Calculated columns with formula evaluation
- Uncertainty columns linked to data columns
- Interactive editing and automatic recalculation

Usage:
    from widgets.AdvancedDataTableWidget import AdvancedDataTableWidget
    
    table = AdvancedDataTableWidget()
    table.addColumn("Temperature", AdvancedColumnType.DATA, AdvancedColumnDataType.NUMERICAL)
"""

# Main widget
from .advanced_datatable import AdvancedDataTableWidget

# Models and enums
from .models import (
    AdvancedColumnType,
    AdvancedColumnDataType,
    ColumnMetadata,
    DEFAULT_NUMERIC_PRECISION,
    ERROR_PREFIX,
    FORMULA_REFERENCE_PATTERN,
    BACKWARD_COMPAT_PATTERN,
    COMMON_UNITS
)

# Utility classes
from .formula_evaluator import SafeFormulaEvaluator, ureg

# UI components
from .context_menu import DataTableContextMenu
from .toolbar import DataTableToolbar
from .dialogs import DataColumnEditorDialog, FormulaEditorDialog

# Define public API
__all__ = [
    # Main widget
    'AdvancedDataTableWidget',
    
    # Enums
    'AdvancedColumnType',
    'AdvancedColumnDataType',
    
    # Models
    'ColumnMetadata',
    
    # Constants
    'DEFAULT_NUMERIC_PRECISION',
    'ERROR_PREFIX',
    'FORMULA_REFERENCE_PATTERN',
    'BACKWARD_COMPAT_PATTERN',
    'COMMON_UNITS',
    
    # Utilities
    'SafeFormulaEvaluator',
    'ureg',  # Pint unit registry
    
    # UI Components
    'DataTableContextMenu',
    'DataTableToolbar',
    'DataColumnEditorDialog',
    'FormulaEditorDialog',
]
