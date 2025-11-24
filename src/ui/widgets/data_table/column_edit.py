"""Column editing dialogs for DataTable widget."""

import numpy as np
import pandas as pd

from studies.data_table_study import ColumnType
from ..shared import show_warning
from ..column_dialogs import (
    AddCalculatedColumnDialog,
    AddDerivativeColumnDialog,
    AddRangeColumnDialog,
    EditDataColumnDialog,
    EditUncertaintyColumnDialog
)


def edit_column_properties(widget, col_index: int):
    """Open dialog to edit column properties.
    
    Args:
        widget: DataTableWidget instance
        col_index: Column index
    """
    if col_index >= len(widget.study.table.columns):
        return
    
    col_name = widget.study.table.columns[col_index]
    col_meta = widget.study.column_metadata.get(col_name, {})
    col_type = col_meta.get("type", "data")
    
    # Open appropriate dialog based on column type
    if col_type == ColumnType.DATA:
        _edit_data_column(widget, col_name)
    elif col_type == ColumnType.CALCULATED:
        _edit_calculated_column(widget, col_name)
    elif col_type == ColumnType.DERIVATIVE:
        _edit_derivative_column(widget, col_name)
    elif col_type == ColumnType.RANGE:
        _edit_range_column(widget, col_name)
    elif col_type == ColumnType.UNCERTAINTY:
        _edit_uncertainty_column(widget, col_name)


def _edit_data_column(widget, col_name: str):
    """Edit data column properties.
    
    Args:
        widget: DataTableWidget instance
        col_name: Column name
    """
    # Get current metadata
    col_meta = widget.study.column_metadata.get(col_name, {})
    current_unit = col_meta.get("unit")
    
    # Open edit dialog
    dialog = EditDataColumnDialog(col_name, current_unit, widget)
    
    if dialog.exec():
        new_name, new_unit = dialog.get_values()
        
        # Handle rename if needed
        if new_name != col_name:
            # Rename column in DataFrame
            widget.study.table.data.rename(columns={col_name: new_name}, inplace=True)
            
            # Update metadata
            widget.study.column_metadata[new_name] = widget.study.column_metadata.pop(col_name)
            
            # Update all formulas that reference this column
            widget.study.formula_engine.rename_variable(col_name, new_name)
            
            # Update formulas in metadata
            for meta in widget.study.column_metadata.values():
                if "formula" in meta:
                    formula = meta["formula"]
                    # Replace {old_name} with {new_name}
                    meta["formula"] = formula.replace(f"{{{col_name}}}", f"{{{new_name}}}")
        
        # Update unit
        widget.study.column_metadata[new_name if new_name != col_name else col_name]["unit"] = new_unit
        
        # Refresh table
        widget._refresh_structure()  # Structural change - column properties modified


def _edit_calculated_column(widget, col_name: str):
    """Edit calculated column properties.
    
    Args:
        widget: DataTableWidget instance
        col_name: Column name
    """
    # Get available columns and variables
    available_cols, available_vars = widget._get_context(exclude_column=col_name)
    
    dialog = AddCalculatedColumnDialog(available_cols, available_vars, widget)
    dialog.setWindowTitle(f"Edit Calculated Column: {col_name}")
    
    # Pre-fill with existing values
    col_meta = widget.study.column_metadata.get(col_name, {})
    dialog.name_edit.setText(col_name)
    dialog.name_edit.setEnabled(False)  # Can't rename calculated columns easily
    
    formula = col_meta.get("formula", "")
    if formula:
        dialog.formula_edit.setPlainText(formula)
    
    unit = col_meta.get("unit")
    if unit:
        dialog.unit_edit.setText(unit)
    
    # Pre-fill uncertainty propagation status
    propagate_unc = col_meta.get("propagate_uncertainty", False)
    dialog.uncertainty_checkbox.setChecked(propagate_unc)
    
    if dialog.exec():
        _, new_formula, new_unit, new_propagate_unc = dialog.get_values()
        
        old_propagate_unc = col_meta.get("propagate_uncertainty", False)
        uncert_name = f"{col_name}_u"
        
        # Update formula and unit
        widget.study.column_metadata[col_name]["formula"] = new_formula
        widget.study.column_metadata[col_name]["unit"] = new_unit
        widget.study.column_metadata[col_name]["propagate_uncertainty"] = new_propagate_unc
        widget.study.formula_engine.register_formula(col_name, new_formula)
        
        # Recalculate column with new formula
        widget.study._recalculate_column(col_name)
        
        # Handle uncertainty propagation changes
        if new_propagate_unc and not old_propagate_unc:
            # Enable uncertainty propagation - create uncertainty column if missing
            if uncert_name not in widget.study.table.columns:
                from studies.data_table_study import ColumnType
                uncert_values = widget.study._calculate_propagated_uncertainty(col_name)
                widget.study.add_column(
                    uncert_name,
                    column_type=ColumnType.UNCERTAINTY,
                    unit=new_unit,
                    initial_data=uncert_values,
                    uncertainty_reference=col_name
                )
        elif not new_propagate_unc and old_propagate_unc:
            # Disable uncertainty propagation - optionally remove uncertainty column
            if uncert_name in widget.study.table.columns:
                from ..shared import confirm_action
                if confirm_action(
                    widget, 
                    "Remove Uncertainty Column?",
                    f"Remove auto-created uncertainty column '{uncert_name}'?"
                ):
                    widget.study.remove_column(uncert_name)
        
        # Recalculate
        widget._refresh_structure()  # Structural change - formula/uncertainty modified


def _edit_uncertainty_column(widget, col_name: str):
    """Edit uncertainty column properties.
    
    Args:
        widget: DataTableWidget instance
        col_name: Column name
    """
    col_meta = widget.study.column_metadata.get(col_name, {})
    current_unit = col_meta.get("unit")
    ref_col = col_meta.get("uncertainty_reference")
    
    # Get available columns to reference
    from studies.data_table_study import ColumnType
    available_cols = [
        c for c in widget.study.table.columns
        if widget.study.get_column_type(c) in [ColumnType.DATA, ColumnType.CALCULATED]
    ]
    
    from ..column_dialogs import EditUncertaintyColumnDialog
    dialog = EditUncertaintyColumnDialog(col_name, current_unit, ref_col, available_cols, widget)
    
    if dialog.exec():
        new_name, new_unit, new_ref_col = dialog.get_values()
        
        # Rename if changed
        if new_name and new_name != col_name:
            widget.study.rename_column(col_name, new_name)
            col_name = new_name
        
        # Update unit and reference
        widget.study.column_metadata[col_name]["unit"] = new_unit
        widget.study.column_metadata[col_name]["uncertainty_reference"] = new_ref_col if new_ref_col else None
        
        # Refresh table
        widget._refresh_structure()  # Structural change - column properties modified


def _edit_derivative_column(widget, col_name: str):
    """Edit derivative column properties.
    
    Args:
        widget: DataTableWidget instance
        col_name: Column name
    """
    # Get columns available for differentiation (data, calculated, range)
    data_cols = [
        c for c in widget.study.table.columns
        if widget.study.get_column_type(c) in [ColumnType.DATA, ColumnType.CALCULATED, ColumnType.RANGE]
    ]
    
    if len(data_cols) < 2:
        show_warning(widget, "Edit Derivative", "Need at least 2 columns (data/calculated/range) for derivative")
        return
    
    dialog = AddDerivativeColumnDialog(data_cols, widget)
    dialog.setWindowTitle(f"Edit Derivative Column: {col_name}")
    
    # Pre-fill with existing values
    col_meta = widget.study.column_metadata.get(col_name, {})
    dialog.name_edit.setText(col_name)
    dialog.name_edit.setEnabled(False)  # Can't rename
    
    # Try to set current selections (use correct metadata keys)
    y_col = col_meta.get("derivative_of")  # Changed from y_column
    x_col = col_meta.get("with_respect_to")  # Changed from x_column
    order = col_meta.get("order", 1)
    unit = col_meta.get("unit")
    
    if y_col and y_col in data_cols:
        dialog.y_combo.setCurrentText(y_col)
    if x_col and x_col in data_cols:
        dialog.x_combo.setCurrentText(x_col)
    dialog.order_spin.setValue(order)
    if unit:
        dialog.unit_edit.setText(unit)
    
    if dialog.exec():
        # get_values() returns tuple: (name, y_col, x_col, order, unit)
        _, y_col, x_col, order, unit = dialog.get_values()
        
        # Update metadata (use correct metadata keys)
        widget.study.column_metadata[col_name].update({
            "derivative_of": y_col,
            "with_respect_to": x_col,
            "order": order,
            "unit": unit
        })
        
        # Recalculate derivative with new parameters
        widget.study._calculate_derivative(col_name)
        
        # Refresh table to show updated data
        widget._refresh_structure()  # Structural change - derivative parameters modified


def _edit_range_column(widget, col_name: str):
    """Edit range column properties.
    
    Args:
        widget: DataTableWidget instance
        col_name: Column name
    """
    dialog = AddRangeColumnDialog(widget)
    dialog.setWindowTitle(f"Edit Range Column: {col_name}")
    
    # Pre-fill with existing values
    col_meta = widget.study.column_metadata.get(col_name, {})
    dialog.name_edit.setText(col_name)
    dialog.name_edit.setEnabled(False)  # Can't rename
    
    # Set current range type and parameters
    range_type = col_meta.get("range_type", "linspace")
    if range_type == "linspace":
        dialog.type_combo.setCurrentIndex(0)
    elif range_type == "arange":
        dialog.type_combo.setCurrentIndex(1)
    elif range_type == "logspace":
        dialog.type_combo.setCurrentIndex(2)
    
    # Load values from metadata (with "range_" prefix)
    dialog.start_spin.setValue(col_meta.get("range_start", 0))
    dialog.stop_spin.setValue(col_meta.get("range_stop", 10))
    
    if "range_count" in col_meta and col_meta["range_count"]:
        dialog.count_spin.setValue(col_meta["range_count"])
    if "range_step" in col_meta and col_meta["range_step"]:
        dialog.step_spin.setValue(col_meta["range_step"])
    
    unit = col_meta.get("unit")
    if unit:
        dialog.unit_edit.setText(unit)
    
    if dialog.exec():
        values = dialog.get_values()
        
        # Convert keys to match expected metadata format (add "range_" prefix)
        metadata_update = {
            "range_type": values["range_type"],
            "range_start": values["start"],
            "range_stop": values["stop"],
            "range_count": values["count"],
            "range_step": values["step"],
            "unit": values["unit"]
        }
        
        # Update metadata
        widget.study.column_metadata[col_name].update(metadata_update)
        
        # Store old row count to detect size change
        old_row_count = len(widget.study.table.data)
        
        # Regenerate range data
        widget.study._generate_range(col_name)
        
        # Check if row count changed significantly
        new_row_count = len(widget.study.table.data)
        
        # If row count changed, resize DATA columns to match
        if new_row_count != old_row_count:
            for data_col in widget.study.table.columns:
                col_meta = widget.study.column_metadata.get(data_col, {})
                if col_meta.get("type") == "data":
                    # Get existing values (only the old length, not including NaN padding)
                    existing = widget.study.table.data[data_col].values[:old_row_count]
                    
                    # Resize by padding or truncating
                    if new_row_count > old_row_count:
                        # Pad with last value or NaN
                        last_val = existing[-1] if len(existing) > 0 and not pd.isna(existing[-1]) else np.nan
                        padding = np.full(new_row_count - old_row_count, last_val)
                        resized = np.concatenate([existing, padding])
                    else:
                        # Truncate
                        resized = existing[:new_row_count]
                    
                    widget.study.table.set_column(data_col, pd.Series(resized))
        
        # Use structure refresh (full reset) - necessary when row count changes
        widget._refresh_structure()
