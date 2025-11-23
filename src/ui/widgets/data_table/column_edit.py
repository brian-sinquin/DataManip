"""Column editing dialogs for DataTable widget."""

from studies.data_table_study import ColumnType
from ..shared import show_warning
from ..column_dialogs import AddCalculatedColumnDialog
from ..column_dialogs_extended import (
    AddDerivativeColumnDialog, AddRangeColumnDialog,
    EditDataColumnDialog, EditUncertaintyColumnDialog
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
        widget._refresh_table()


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
        widget._refresh_table()


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
    
    from ..column_dialogs_extended import EditUncertaintyColumnDialog
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
        widget._refresh_table()


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
        
        # Recalculate derivative
        widget._refresh_table()


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
    
    dialog.start_spin.setValue(col_meta.get("start", 0))
    dialog.stop_spin.setValue(col_meta.get("stop", 10))
    
    if "count" in col_meta and col_meta["count"]:
        dialog.count_spin.setValue(col_meta["count"])
    if "step" in col_meta and col_meta["step"]:
        dialog.step_spin.setValue(col_meta["step"])
    
    unit = col_meta.get("unit")
    if unit:
        dialog.unit_edit.setText(unit)
    
    if dialog.exec():
        values = dialog.get_values()
        
        # Update metadata
        widget.study.column_metadata[col_name].update(values)
        
        # Regenerate range data
        widget._refresh_table()
