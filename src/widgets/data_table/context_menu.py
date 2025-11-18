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

from utils.qt_helpers import add_action, add_separator

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
        add_action(self, "Edit Column Properties...", self._edit_column)
        add_separator(self)
        
        # Add new columns
        add_action(self, "Add Data Column...", self.view._show_add_data_column_dialog)
        add_action(self, "Add Calculated Column...", self.view._show_add_calculated_column_dialog)
        add_action(self, "Add Range Column...", self.view._show_add_range_column_dialog)
        add_action(self, "Add Derivative Column...", self.view._show_add_derivative_column_dialog)
        add_action(self, "Add Interpolation Column...", self.view._show_add_interpolation_column_dialog)
        add_separator(self)
        
        # Copy header text
        add_action(self, "Copy Header Text", self._copy_header)
        add_separator(self)
        
        # Delete column
        add_action(self, f"Delete Column '{col_name}'", self._delete_column)
    
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
        selected_cells = self.view.get_selected_cells()
        
        # Copy operations
        add_action(self, "Copy Cell Value", self._copy_cell)
        if len(selected_cells) > 1:
            add_action(self, f"Copy Selection ({len(selected_cells)} cells)", self._copy_selection)
        add_separator(self)
        
        # Paste and clear (only if editable)
        if self._is_cell_editable(row, column):
            add_action(self, "Paste", self._paste)
            add_action(self, "Clear", self._clear_cell)
        
        # Clear selection (if multiple editable cells selected)
        if len(selected_cells) > 1:
            editable_count = sum(1 for r, c in selected_cells if self._is_cell_editable(r, c))
            if editable_count > 0:
                add_action(self, f"Clear Selection ({editable_count} editable cells)", self._clear_selection)
    
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
        add_action(self, "Add Data Column...", self.view._show_add_data_column_dialog)
        add_action(self, "Add Calculated Column...", self.view._show_add_calculated_column_dialog)
        add_action(self, "Add Range Column...", self.view._show_add_range_column_dialog)
        add_action(self, "Add Derivative Column...", self.view._show_add_derivative_column_dialog)
        add_action(self, "Add Interpolation Column...", self.view._show_add_interpolation_column_dialog)
        add_action(
            self, 
            "Add Uncertainty Column...", 
            self.view._show_add_uncertainty_column_dialog,
            "Add a manual uncertainty column for entering error values"
        )
        add_separator(self)
        
        # Manage global variables
        add_action(
            self,
            "Manage Variables...",
            self.view._show_variables_dialog,
            "Define global constants (g, pi, etc.) to use in formulas"
        )
        add_separator(self)
        
        # Insert row
        add_action(self, "Insert Row", self._insert_row)
    
    def _insert_row(self):
        """Insert a new row at the end."""
        if self.view._data_model:
            row_count = self.view._data_model.rowCount()
            self.view._data_model.insertRows(row_count, 1)
