"""
Context menu for DataTableV2.

Provides right-click menu options for:
- Headers: Edit column, add columns, delete column, copy header
- Cells: Copy, paste, clear
- Selections: Copy selection, clear selection
- Rows: Insert row, delete row(s)
"""

from PySide6.QtWidgets import QMenu, QMessageBox, QApplication
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .view import DataTableView
    from .model import DataTableModel


class HeaderContextMenu(QMenu):
    """Context menu for table headers (column operations)."""
    
    def __init__(self, view: 'DataTableView', column_index: int, parent=None):
        super().__init__(parent)
        self.view = view
        self.col = column_index
        self.model: 'DataTableModel' = view._data_model
        
        if self.model is None or self.col < 0 or self.col >= self.model.columnCount():
            return
        
        col_name = self.model._column_order[self.col]
        metadata = self.model.get_column_metadata(col_name)
        
        # Edit Column
        edit_act = QAction("Edit Column Properties...", self)
        edit_act.triggered.connect(self._edit_column)
        self.addAction(edit_act)
        
        self.addSeparator()
        
        # Add new columns
        add_data_act = QAction("Add Data Column...", self)
        add_data_act.triggered.connect(lambda: self.view._show_add_data_column_dialog())
        self.addAction(add_data_act)
        
        add_calc_act = QAction("Add Calculated Column...", self)
        add_calc_act.triggered.connect(lambda: self.view._show_add_calculated_column_dialog())
        self.addAction(add_calc_act)
        
        add_range_act = QAction("Add Range Column...", self)
        add_range_act.triggered.connect(lambda: self.view._show_add_range_column_dialog())
        self.addAction(add_range_act)
        
        add_deriv_act = QAction("Add Derivative Column...", self)
        add_deriv_act.triggered.connect(lambda: self.view._show_add_derivative_column_dialog())
        self.addAction(add_deriv_act)
        
        add_interp_act = QAction("Add Interpolation Column...", self)
        add_interp_act.triggered.connect(lambda: self.view._show_add_interpolation_column_dialog())
        self.addAction(add_interp_act)
        
        self.addSeparator()
        
        # Copy header text
        copy_header_act = QAction("Copy Header Text", self)
        copy_header_act.triggered.connect(self._copy_header)
        self.addAction(copy_header_act)
        
        self.addSeparator()
        
        # Delete column
        delete_act = QAction(f"Delete Column '{col_name}'", self)
        delete_act.triggered.connect(self._delete_column)
        self.addAction(delete_act)
    
    def _edit_column(self):
        """Open edit dialog for this column."""
        col_name = self.model._column_order[self.col]
        self.view.edit_column(col_name)
    
    def _copy_header(self):
        """Copy header text to clipboard."""
        col_name = self.model._column_order[self.col]
        metadata = self.model.get_column_metadata(col_name)
        header_text = metadata.get_display_header()
        QApplication.clipboard().setText(header_text)
    
    def _delete_column(self):
        """Delete the column after confirmation."""
        col_name = self.model._column_order[self.col]
        
        reply = QMessageBox.question(
            self.view,
            "Delete Column",
            f"Are you sure you want to delete column '{col_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.model.remove_column(col_name)
            except Exception as e:
                QMessageBox.warning(self.view, "Error", f"Failed to delete column: {str(e)}")


class CellContextMenu(QMenu):
    """Context menu for table cells (data operations)."""
    
    def __init__(self, view: 'DataTableView', row: int, column: int, parent=None):
        super().__init__(parent)
        self.view = view
        self.row = row
        self.col = column
        self.model: 'DataTableModel' = view._data_model
        
        # Copy cell value
        copy_cell_act = QAction("Copy Cell Value", self)
        copy_cell_act.triggered.connect(self._copy_cell)
        self.addAction(copy_cell_act)
        
        # Copy selection (if multiple cells selected)
        selected_cells = self.view.get_selected_cells()
        if len(selected_cells) > 1:
            copy_selection_act = QAction(f"Copy Selection ({len(selected_cells)} cells)", self)
            copy_selection_act.triggered.connect(self._copy_selection)
            self.addAction(copy_selection_act)
        
        self.addSeparator()
        
        # Paste (only if editable)
        if self._is_cell_editable(row, column):
            paste_act = QAction("Paste", self)
            paste_act.triggered.connect(self._paste)
            self.addAction(paste_act)
            
            # Clear
            clear_act = QAction("Clear", self)
            clear_act.triggered.connect(self._clear_cell)
            self.addAction(clear_act)
        
        # Clear selection (if multiple editable cells selected)
        if len(selected_cells) > 1:
            editable_count = sum(1 for r, c in selected_cells if self._is_cell_editable(r, c))
            if editable_count > 0:
                clear_selection_act = QAction(f"Clear Selection ({editable_count} editable cells)", self)
                clear_selection_act.triggered.connect(self._clear_selection)
                self.addAction(clear_selection_act)
    
    def _is_cell_editable(self, row: int, col: int) -> bool:
        """Check if a cell is editable."""
        if col < 0 or col >= self.model.columnCount():
            return False
        col_name = self.model._column_order[col]
        metadata = self.model.get_column_metadata(col_name)
        return metadata.editable
    
    def _copy_cell(self):
        """Copy current cell value to clipboard."""
        if self.model:
            idx = self.model.index(self.row, self.col)
            text = self.model.data(idx, Qt.ItemDataRole.DisplayRole)
            if text is not None:
                QApplication.clipboard().setText(str(text))
    
    def _copy_selection(self):
        """Copy selected cells to clipboard as TSV."""
        selection = self.view.get_selected_cells()
        if not selection or not self.model:
            return
        
        tsv_data = self.model.copy_selection_to_tsv(selection)
        if tsv_data:
            QApplication.clipboard().setText(tsv_data)
    
    def _paste(self):
        """Paste from clipboard to current cell."""
        if not self.model:
            return
        
        clipboard = QApplication.clipboard()
        tsv_data = clipboard.text()
        if not tsv_data:
            return
        
        # Paste starting at current cell
        try:
            self.model.paste_from_tsv(tsv_data, self.row, self.col, skip_readonly=True)
        except Exception as e:
            QMessageBox.warning(self.view, "Paste Error", str(e))
    
    def _clear_cell(self):
        """Clear current cell."""
        if self.model and self._is_cell_editable(self.row, self.col):
            self.model.clear_selection([(self.row, self.col)])
    
    def _clear_selection(self):
        """Clear all selected editable cells."""
        if not self.model:
            return
        
        selection = self.view.get_selected_cells()
        editable_cells = [(r, c) for r, c in selection if self._is_cell_editable(r, c)]
        if editable_cells:
            self.model.clear_selection(editable_cells)


class RowContextMenu(QMenu):
    """Context menu for row headers (row operations)."""
    
    def __init__(self, view: 'DataTableView', row: int, parent=None):
        super().__init__(parent)
        self.view = view
        self.row = row
        self.model: 'DataTableModel' = view._data_model
        
        # Insert row above
        insert_above_act = QAction("Insert Row Above", self)
        insert_above_act.triggered.connect(lambda: self._insert_row(self.row))
        self.addAction(insert_above_act)
        
        # Insert row below
        insert_below_act = QAction("Insert Row Below", self)
        insert_below_act.triggered.connect(lambda: self._insert_row(self.row + 1))
        self.addAction(insert_below_act)
        
        self.addSeparator()
        
        # Delete row(s)
        selected_rows = self.view.get_selected_rows()
        if len(selected_rows) > 1:
            delete_act = QAction(f"Delete {len(selected_rows)} Rows", self)
            delete_act.triggered.connect(self._delete_selected_rows)
        else:
            delete_act = QAction("Delete Row", self)
            delete_act.triggered.connect(lambda: self._delete_row(self.row))
        self.addAction(delete_act)
    
    def _insert_row(self, position: int):
        """Insert a row at the specified position."""
        if self.model:
            self.model.insertRows(position, 1)
    
    def _delete_row(self, row: int):
        """Delete a single row."""
        if self.model:
            reply = QMessageBox.question(
                self.view,
                "Delete Row",
                f"Delete row {row}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.model.removeRows(row, 1)
    
    def _delete_selected_rows(self):
        """Delete all selected rows."""
        if not self.model:
            return
        
        selected_rows = sorted(self.view.get_selected_rows(), reverse=True)
        if not selected_rows:
            return
        
        reply = QMessageBox.question(
            self.view,
            "Delete Rows",
            f"Delete {len(selected_rows)} selected rows?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Delete in reverse order to maintain indices
            for row in selected_rows:
                self.model.removeRows(row, 1)


class EmptyTableContextMenu(QMenu):
    """Context menu for empty areas of the table (table-wide operations)."""
    
    def __init__(self, view: 'DataTableView', parent=None):
        super().__init__(parent)
        self.view = view
        
        # Add columns
        add_data_act = QAction("Add Data Column...", self)
        add_data_act.triggered.connect(lambda: self.view._show_add_data_column_dialog())
        self.addAction(add_data_act)
        
        add_calc_act = QAction("Add Calculated Column...", self)
        add_calc_act.triggered.connect(lambda: self.view._show_add_calculated_column_dialog())
        self.addAction(add_calc_act)
        
        add_range_act = QAction("Add Range Column...", self)
        add_range_act.triggered.connect(lambda: self.view._show_add_range_column_dialog())
        self.addAction(add_range_act)
        
        add_deriv_act = QAction("Add Derivative Column...", self)
        add_deriv_act.triggered.connect(lambda: self.view._show_add_derivative_column_dialog())
        self.addAction(add_deriv_act)
        
        add_interp_act = QAction("Add Interpolation Column...", self)
        add_interp_act.triggered.connect(lambda: self.view._show_add_interpolation_column_dialog())
        self.addAction(add_interp_act)
        
        add_uncertainty_act = QAction("Add Uncertainty Column...", self)
        add_uncertainty_act.setToolTip("Add a manual uncertainty column for entering error values")
        add_uncertainty_act.triggered.connect(lambda: self.view._show_add_uncertainty_column_dialog())
        self.addAction(add_uncertainty_act)
        
        self.addSeparator()
        
        # Manage global variables
        vars_act = QAction("Manage Variables...", self)
        vars_act.setToolTip("Define global constants (g, pi, etc.) to use in formulas")
        vars_act.triggered.connect(lambda: self.view._show_variables_dialog())
        self.addAction(vars_act)
        
        self.addSeparator()
        
        # Insert row
        insert_row_act = QAction("Insert Row", self)
        insert_row_act.triggered.connect(self._insert_row)
        self.addAction(insert_row_act)
    
    def _insert_row(self):
        """Insert a new row at the end."""
        if self.view._data_model:
            row_count = self.view._data_model.rowCount()
            self.view._data_model.insertRows(row_count, 1)
