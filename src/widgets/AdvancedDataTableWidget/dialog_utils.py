"""Utility functions for dialog column/variable population.

This module provides reusable functions to populate column lists and combo boxes
in various dialogs, eliminating code duplication.
"""

from typing import Optional, List, Tuple
from PySide6.QtWidgets import QListWidget, QComboBox

from .models import AdvancedColumnType, AdvancedColumnDataType


def get_column_type_label(col_type: AdvancedColumnType) -> str:
    """Get the display label for a column type.
    
    Args:
        col_type: The column type
        
    Returns:
        String label like " [calc]", " [deriv]", etc., or empty string for DATA
    """
    if col_type == AdvancedColumnType.CALCULATED:
        return " [calc]"
    elif col_type == AdvancedColumnType.DERIVATIVE:
        return " [deriv]"
    elif col_type == AdvancedColumnType.RANGE:
        return " [range]"
    elif col_type == AdvancedColumnType.INTERPOLATION:
        return " [interp]"
    else:
        return ""


def populate_formula_columns_list(
    list_widget: QListWidget,
    table_widget,
    column_index_to_skip: Optional[int] = None
) -> None:
    """Populate a QListWidget with variables and columns for formula editing.
    
    This adds:
    1. Global variables (if any) with format: "varname = value (unit) → {varname}"
    2. Available columns with format: "diminutive [type] → {diminutive}"
    
    Excludes UNCERTAINTY columns and optionally the column being edited.
    
    Args:
        list_widget: The QListWidget to populate
        table_widget: The AdvancedDataTableWidget instance
        column_index_to_skip: Optional column index to skip (for edit mode)
    """
    list_widget.clear()
    
    # Add global variables first
    variables = getattr(table_widget, '_variables', {})
    if variables:
        list_widget.addItem("--- Variables ---")
        for var_name, (var_value, var_unit) in variables.items():
            unit_str = f" ({var_unit})" if var_unit else ""
            item_text = f"{var_name} = {var_value}{unit_str} → {{{var_name}}}"
            list_widget.addItem(item_text)
        list_widget.addItem("")  # Spacer
    
    # Add columns section
    list_widget.addItem("--- Columns ---")
    for col_idx in range(table_widget.columnCount()):
        # Skip the column being edited
        if column_index_to_skip is not None and col_idx == column_index_to_skip:
            continue
            
        col_type = table_widget.getColumnType(col_idx)
        # Include all column types except UNCERTAINTY
        if col_type != AdvancedColumnType.UNCERTAINTY:
            diminutive = table_widget.getColumnDiminutive(col_idx)
            col_type_label = get_column_type_label(col_type)
            item_text = f"{diminutive}{col_type_label} → {{{diminutive}}}"
            list_widget.addItem(item_text)


def populate_column_combo_boxes(
    combo_boxes: List[QComboBox],
    table_widget,
    column_index_to_skip: Optional[int] = None,
    include_type_labels: bool = True,
    include_units: bool = True,
    placeholder_text: str = "-- Select Column --"
) -> None:
    """Populate QComboBox widgets with available columns.
    
    This is used for derivative dialogs and interpolation dialogs where you
    select columns from combo boxes.
    
    Excludes UNCERTAINTY columns and optionally the column being edited.
    
    Args:
        combo_boxes: List of QComboBox widgets to populate (e.g., [numerator, denominator])
        table_widget: The AdvancedDataTableWidget instance
        column_index_to_skip: Optional column index to skip (for edit mode)
        include_type_labels: Whether to include type labels like [calc], [deriv]
        include_units: Whether to include unit information like [m/s]
        placeholder_text: The placeholder text for the first item
    """
    for combo_box in combo_boxes:
        combo_box.clear()
        combo_box.addItem(placeholder_text, None)
    
    for col_idx in range(table_widget.columnCount()):
        # Skip the column being edited
        if column_index_to_skip is not None and col_idx == column_index_to_skip:
            continue
        
        col_type = table_widget.getColumnType(col_idx)
        # Include all numeric column types except UNCERTAINTY
        if col_type != AdvancedColumnType.UNCERTAINTY:
            diminutive = table_widget.getColumnDiminutive(col_idx)
            unit = table_widget.getColumnUnit(col_idx)
            
            # Build display text
            display_text = diminutive
            
            if include_units and unit:
                display_text += f" [{unit}]"
            
            if include_type_labels:
                type_label = get_column_type_label(col_type)
                display_text += type_label
            
            # Add to all combo boxes
            for combo_box in combo_boxes:
                combo_box.addItem(display_text, col_idx)


def populate_interpolation_column_combos(
    combo_boxes: List[QComboBox],
    table_widget,
    column_index_to_skip: Optional[int] = None
) -> None:
    """Populate QComboBox widgets with numeric columns for interpolation.
    
    This is specialized for interpolation dialogs - only includes NUMERICAL columns.
    
    Args:
        combo_boxes: List of QComboBox widgets to populate (e.g., [x_combo, y_combo])
        table_widget: The AdvancedDataTableWidget instance
        column_index_to_skip: Optional column index to skip (for edit mode)
    """
    for combo_box in combo_boxes:
        combo_box.clear()
        combo_box.addItem("-- Select Column --", None)
    
    for col_idx in range(table_widget.columnCount()):
        # Skip the column being edited
        if column_index_to_skip is not None and col_idx == column_index_to_skip:
            continue
        
        # _columns is a list, not a dict - use index access
        if col_idx >= len(table_widget._columns):
            continue
        
        metadata = table_widget._columns[col_idx]
        if not metadata:
            continue
        
        # Only allow numeric columns
        if metadata.data_type != AdvancedColumnDataType.NUMERICAL:
            continue
        
        # Allow all numeric column types except UNCERTAINTY
        col_type = metadata.column_type
        if col_type != AdvancedColumnType.UNCERTAINTY:
            # Create display text with type indicator
            type_label = get_column_type_label(col_type)
            
            display_text = f"{metadata.diminutive}{type_label}"
            if metadata.unit:
                display_text += f" [{metadata.unit}]"
            
            # Add to all combo boxes
            for combo_box in combo_boxes:
                combo_box.addItem(display_text, col_idx)
