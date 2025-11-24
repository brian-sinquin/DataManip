"""Keyboard shortcuts for DataTable widget."""

from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication
from typing import List, Tuple
import pandas as pd

from ..shared import show_warning


def setup_table_shortcuts(widget):
    """Setup keyboard shortcuts for clipboard operations.
    
    Args:
        widget: DataTableWidget instance
    """
    # Copy: Ctrl+C
    copy_shortcut = QShortcut(QKeySequence.StandardKey.Copy, widget)
    copy_shortcut.activated.connect(lambda: _on_copy(widget))
    
    # Paste: Ctrl+V
    paste_shortcut = QShortcut(QKeySequence.StandardKey.Paste, widget)
    paste_shortcut.activated.connect(lambda: _on_paste(widget))
    
    # Cut: Ctrl+X
    cut_shortcut = QShortcut(QKeySequence.StandardKey.Cut, widget)
    cut_shortcut.activated.connect(lambda: _on_cut(widget))
    
    # Delete: Del
    delete_shortcut = QShortcut(QKeySequence.StandardKey.Delete, widget)
    delete_shortcut.activated.connect(lambda: _on_delete(widget))


def _get_selected_cells(widget) -> List[Tuple[int, int]]:
    """Get list of selected cells as (row, col) tuples.
    
    Args:
        widget: DataTableWidget instance
        
    Returns:
        List of (row, col) tuples
    """
    selection = widget.view.selectionModel().selectedIndexes()
    return [(index.row(), index.column()) for index in selection]


def _on_copy(widget):
    """Handle copy operation (Ctrl+C).
    
    Args:
        widget: DataTableWidget instance
    """
    selection = _get_selected_cells(widget)
    if not selection:
        return
    
    # Convert selection to TSV format
    tsv_data = _selection_to_tsv(widget, selection)
    if tsv_data:
        clipboard = QApplication.clipboard()
        clipboard.setText(tsv_data)


def _selection_to_tsv(widget, selection: List[Tuple[int, int]]) -> str:
    """Convert selection to TSV format.
    
    Args:
        widget: DataTableWidget instance
        selection: List of (row, col) tuples
        
    Returns:
        TSV-formatted string
    """
    if not selection:
        return ""
    
    # Group by row
    rows_dict = {}
    for row, col in selection:
        if row not in rows_dict:
            rows_dict[row] = {}
        rows_dict[row][col] = (row, col)
    
    # Build TSV output
    lines = []
    for row in sorted(rows_dict.keys()):
        cols_dict = rows_dict[row]
        min_col = min(cols_dict.keys())
        max_col = max(cols_dict.keys())
        
        # Build line with all columns in range
        values = []
        for col in range(min_col, max_col + 1):
            if col < len(widget.study.table.columns):
                col_name = widget.study.table.columns[col]
                if col in cols_dict and row < len(widget.study.table.data):
                    value = widget.study.table.data[col_name].iloc[row]
                    values.append(str(value) if pd.notna(value) else "")
                else:
                    values.append("")
        
        lines.append("\t".join(values))
    
    return "\n".join(lines)


def _on_paste(widget):
    """Handle paste operation (Ctrl+V).
    
    Args:
        widget: DataTableWidget instance
    """
    clipboard = QApplication.clipboard()
    tsv_data = clipboard.text()
    if not tsv_data:
        return
    
    selection = _get_selected_cells(widget)
    if not selection:
        return
    
    # Get top-left of selection
    start_row = min(row for row, col in selection)
    start_col = min(col for row, col in selection)
    
    # Parse and paste TSV data
    _paste_tsv(widget, tsv_data, start_row, start_col)


def _paste_tsv(widget, tsv_data: str, start_row: int, start_col: int):
    """Paste TSV data into table.
    
    Args:
        widget: DataTableWidget instance
        tsv_data: Tab-separated values
        start_row: Starting row
        start_col: Starting column
    """
    from studies.data_table_study import ColumnType
    from core.undo_manager import UndoAction, ActionType
    
    lines = tsv_data.strip().split('\n')
    errors = []
    
    # Track old values for undo
    old_values = {}
    new_values = {}
    affected_columns = set()
    
    for row_offset, line in enumerate(lines):
        values = line.split('\t')
        for col_offset, value in enumerate(values):
            target_row = start_row + row_offset
            target_col = start_col + col_offset
            
            # Check bounds
            if target_row >= len(widget.study.table.data):
                continue
            if target_col >= len(widget.study.table.columns):
                continue
            
            col_name = widget.study.table.columns[target_col]
            
            # Skip non-editable columns
            if col_name in widget.study.column_metadata:
                col_type = widget.study.column_metadata[col_name].get("type", "data")
                if col_type != ColumnType.DATA:
                    continue
            
            # Save old value for undo
            old_val = widget.study.table.data.iloc[target_row, target_col]
            old_values[(target_row, target_col, col_name)] = old_val
            affected_columns.add(col_name)
            
            # Set value
            try:
                if value.strip() == "":
                    new_val = pd.NA
                else:
                    # Try to convert to appropriate type
                    try:
                        new_val = float(value)
                    except ValueError:
                        new_val = value
                
                widget.study.table.data.loc[target_row, col_name] = new_val
                new_values[(target_row, target_col, col_name)] = new_val
            except Exception as e:
                errors.append(f"Row {target_row}, Col {col_name}: {str(e)}")
    
    # Create undo action for paste
    if old_values:
        def undo_paste():
            for (row, col, col_name), old_val in old_values.items():
                widget.study.table.data.iloc[row, col] = old_val
            widget._refresh_data(affected_columns)
        
        def redo_paste():
            for (row, col, col_name), new_val in new_values.items():
                widget.study.table.data.loc[row, col_name] = new_val
            widget._refresh_data(affected_columns)
        
        cell_count = len(old_values)
        action = UndoAction(
            action_type=ActionType.MODIFY_DATA,
            undo_func=undo_paste,
            redo_func=redo_paste,
            description=f"Paste {cell_count} cell{'s' if cell_count > 1 else ''}"
        )
        widget.study.undo_manager.push(action)
    
    # Refresh view (incremental update)
    widget._refresh_data(affected_columns)
    
    if errors:
        show_warning(widget, "Paste Warnings", f"Some cells could not be pasted:\n" + "\n".join(errors[:5]))


def _on_cut(widget):
    """Handle cut operation (Ctrl+X).
    
    Args:
        widget: DataTableWidget instance
    """
    _on_copy(widget)
    _on_delete(widget)


def _on_delete(widget):
    """Handle delete operation (Del key).
    
    Args:
        widget: DataTableWidget instance
    """
    from studies.data_table_study import ColumnType
    from core.undo_manager import UndoAction, ActionType
    
    selection = _get_selected_cells(widget)
    if not selection:
        return
    
    # Track old values for undo
    old_values = {}
    affected_columns = set()
    
    # Clear selected cells
    for row, col in selection:
        if col >= len(widget.study.table.columns):
            continue
        
        col_name = widget.study.table.columns[col]
        
        # Skip non-editable columns
        if col_name in widget.study.column_metadata:
            col_type = widget.study.column_metadata[col_name].get("type", "data")
            if col_type != ColumnType.DATA:
                continue
        
        # Save old value for undo
        if row < len(widget.study.table.data):
            old_val = widget.study.table.data.iloc[row, col]
            old_values[(row, col, col_name)] = old_val
            affected_columns.add(col_name)
            
            # Clear value
            widget.study.table.data.loc[row, col_name] = pd.NA
    
    # Create undo action for delete
    if old_values:
        def undo_delete():
            for (row, col, col_name), old_val in old_values.items():
                widget.study.table.data.iloc[row, col] = old_val
            widget._refresh_data(affected_columns)
        
        def redo_delete():
            for (row, col, col_name), _ in old_values.items():
                widget.study.table.data.loc[row, col_name] = pd.NA
            widget._refresh_data(affected_columns)
        
        cell_count = len(old_values)
        action = UndoAction(
            action_type=ActionType.MODIFY_DATA,
            undo_func=undo_delete,
            redo_func=redo_delete,
            description=f"Delete {cell_count} cell{'s' if cell_count > 1 else ''}"
        )
        widget.study.undo_manager.push(action)
    
    # Refresh view (incremental update)
    widget._refresh_data(affected_columns)
