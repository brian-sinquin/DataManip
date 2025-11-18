"""
View layer for DataTableV2.

This module implements the QTableView widget that displays the data model.
"""

from typing import Optional, TYPE_CHECKING
from PySide6.QtWidgets import QTableView, QHeaderView, QApplication, QMessageBox
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QFont, QKeySequence, QShortcut, QMouseEvent

if TYPE_CHECKING:
    from PySide6.QtWidgets import QToolBar

from .model import DataTableModel
from .delegates import create_delegate_for_column
from .context_menu import (
    HeaderContextMenu, CellContextMenu, RowContextMenu, EmptyTableContextMenu
)


class DataTableView(QTableView):
    """Custom QTableView for displaying DataTableModel.
    
    Features:
    - Connects to DataTableModel
    - Custom header formatting
    - Column resizing
    - Row/column selection
    """
    
    def __init__(self, parent=None):
        """Initialize the table view.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Configure view properties
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectItems)
        self.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)
        
        # Configure horizontal header
        h_header = self.horizontalHeader()
        h_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        h_header.setStretchLastSection(True)
        h_header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Configure vertical header (row numbers)
        v_header = self.verticalHeader()
        v_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        v_header.setDefaultSectionSize(25)
        
        # Set default font
        font = QFont()
        font.setPointSize(10)
        self.setFont(font)
        
        # Store model reference
        self._data_model: Optional[DataTableModel] = None
        
        # Set up clipboard shortcuts
        self._setup_shortcuts()
        
        # Set up context menus
        self._setup_context_menus()
    
    def _setup_context_menus(self):
        """Set up context menu handling."""
        # Enable context menus
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # Enable header context menus
        h_header = self.horizontalHeader()
        h_header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        h_header.customContextMenuRequested.connect(self._show_header_context_menu)
        
        # Enable double-click on header to edit
        h_header.sectionDoubleClicked.connect(self._on_header_double_clicked)
        
        # Enable row header context menus
        v_header = self.verticalHeader()
        v_header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        v_header.customContextMenuRequested.connect(self._show_row_context_menu)
    
    def _setup_shortcuts(self):
        """Set up keyboard shortcuts for clipboard and undo/redo operations."""
        # Copy: Ctrl+C
        copy_shortcut = QShortcut(QKeySequence.StandardKey.Copy, self)
        copy_shortcut.activated.connect(self._on_copy)
        
        # Paste: Ctrl+V
        paste_shortcut = QShortcut(QKeySequence.StandardKey.Paste, self)
        paste_shortcut.activated.connect(self._on_paste)
        
        # Cut: Ctrl+X
        cut_shortcut = QShortcut(QKeySequence.StandardKey.Cut, self)
        cut_shortcut.activated.connect(self._on_cut)
        
        # Delete: Del
        delete_shortcut = QShortcut(QKeySequence.StandardKey.Delete, self)
        delete_shortcut.activated.connect(self._on_delete)
        
        # Undo: Ctrl+Z
        undo_shortcut = QShortcut(QKeySequence.StandardKey.Undo, self)
        undo_shortcut.activated.connect(self._on_undo)
        
        # Redo: Ctrl+Y (Windows) or Ctrl+Shift+Z (Mac/Linux)
        redo_shortcut = QShortcut(QKeySequence.StandardKey.Redo, self)
        redo_shortcut.activated.connect(self._on_redo)
    
    def _on_copy(self):
        """Handle copy operation (Ctrl+C)."""
        if not self._data_model:
            return
        
        # Get selected cells as (row, col) tuples
        selection = self.get_selected_cells()
        if not selection:
            return
        
        # Convert to TSV and copy to clipboard
        tsv_data = self._data_model.copy_selection_to_tsv(selection)
        if tsv_data:
            clipboard = QApplication.clipboard()
            clipboard.setText(tsv_data)
    
    def _on_paste(self):
        """Handle paste operation (Ctrl+V)."""
        if not self._data_model:
            return
        
        # Get clipboard text
        clipboard = QApplication.clipboard()
        tsv_data = clipboard.text()
        if not tsv_data:
            return
        
        # Get top-left of selection
        selection = self.get_selected_cells()
        if not selection:
            return
        
        start_row = min(row for row, col in selection)
        start_col = min(col for row, col in selection)
        
        # Paste data
        rows_pasted, cells_pasted, errors = self._data_model.paste_from_tsv(
            tsv_data, start_row, start_col, skip_readonly=True
        )
        
        # TODO: Show errors to user if any
        if errors:
            print(f"Paste errors: {errors}")
    
    def _on_cut(self):
        """Handle cut operation (Ctrl+X)."""
        # Copy then clear
        self._on_copy()
        self._on_delete()
    
    def _on_delete(self):
        """Handle delete operation (Del key)."""
        if not self._data_model:
            return
        
        selection = self.get_selected_cells()
        if not selection:
            return
        
        self._data_model.clear_selection(selection)
    
    def _on_undo(self):
        """Handle undo operation (Ctrl+Z)."""
        if self._data_model and hasattr(self._data_model, 'undo'):
            self._data_model.undo()
    
    def _on_redo(self):
        """Handle redo operation (Ctrl+Y or Ctrl+Shift+Z)."""
        if self._data_model and hasattr(self._data_model, 'redo'):
            self._data_model.redo()
    
    def setModel(self, model: DataTableModel) -> None:
        """Set the data model for this view.
        
        Args:
            model: DataTableModel instance
        """
        self._data_model = model
        super().setModel(model)
        
        # Set up delegates for each column
        if model:
            for col_name in model.get_column_names():
                metadata = model.get_column_metadata(col_name)
                col_idx = model._column_order.index(col_name)
                delegate = create_delegate_for_column(metadata, self)
                self.setItemDelegateForColumn(col_idx, delegate)
        
        # Adjust column widths after setting model
        self.resizeColumnsToContents()
        
        # Connect to model signals for dynamic updates
        if model:
            model.columnAdded.connect(self._on_column_added)
            model.columnRemoved.connect(self._on_column_removed)
    
    def _on_column_added(self, name: str) -> None:
        """Handle column added signal.
        
        Args:
            name: Name of added column
        """
        # Set up delegate for new column
        if self._data_model:
            metadata = self._data_model.get_column_metadata(name)
            col_idx = self._data_model._column_order.index(name)
            delegate = create_delegate_for_column(metadata, self)
            self.setItemDelegateForColumn(col_idx, delegate)
            
            # Resize the new column to fit contents
            self.resizeColumnToContents(col_idx)
    
    def _on_column_removed(self, name: str) -> None:
        """Handle column removed signal.
        
        Args:
            name: Name of removed column
        """
        # View automatically updates when model changes
        pass
    
    def get_selected_cells(self) -> list[tuple[int, int]]:
        """Get list of selected cell coordinates.
        
        Returns:
            List of (row, column) tuples
        """
        selection = self.selectionModel().selectedIndexes()
        return [(idx.row(), idx.column()) for idx in selection]
    
    def get_selected_rows(self) -> list[int]:
        """Get list of selected row indices.
        
        Returns:
            List of row indices (unique, sorted)
        """
        selection = self.selectionModel().selectedIndexes()
        rows = set(idx.row() for idx in selection)
        return sorted(rows)
    
    def get_selected_columns(self) -> list[int]:
        """Get list of selected column indices.
        
        Returns:
            List of column indices (unique, sorted)
        """
        selection = self.selectionModel().selectedIndexes()
        cols = set(idx.column() for idx in selection)
        return sorted(cols)
    
    def clear_selection(self) -> None:
        """Clear current selection."""
        self.selectionModel().clearSelection()
    
    def select_cell(self, row: int, col: int) -> None:
        """Select a single cell.
        
        Args:
            row: Row index
            col: Column index
        """
        if self._data_model:
            idx = self._data_model.index(row, col)
            self.selectionModel().select(idx, self.selectionModel().SelectionFlag.ClearAndSelect)
    
    def select_row(self, row: int) -> None:
        """Select an entire row.
        
        Args:
            row: Row index
        """
        self.selectRow(row)
    
    def select_column(self, col: int) -> None:
        """Select an entire column.
        
        Args:
            col: Column index
        """
        self.selectColumn(col)
    
    # ========================================================================
    # Event Handlers
    # ========================================================================
    
    def keyPressEvent(self, event):
        """Handle key press events, including auto-row creation on Enter.
        
        Args:
            event: QKeyEvent instance
        """
        # Check for Enter/Return key
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            current_index = self.currentIndex()
            if current_index.isValid() and self._data_model:
                current_row = current_index.row()
                current_col = current_index.column()
                row_count = self._data_model.rowCount()
                col_count = self._data_model.columnCount()
                
                # If in the last cell (last row, last column), create new row
                if current_row == row_count - 1 and current_col == col_count - 1:
                    # Add a new row
                    self._data_model.insertRows(row_count, 1)
                    # Move to first cell of new row
                    new_index = self._data_model.index(row_count, 0)
                    self.setCurrentIndex(new_index)
                    return
        
        # Default behavior for all other keys
        super().keyPressEvent(event)
    
    # ========================================================================
    # Context Menu Handlers
    # ========================================================================
    
    def _show_context_menu(self, pos: QPoint):
        """Show context menu for cells.
        
        Args:
            pos: Position where menu was requested
        """
        index = self.indexAt(pos)
        
        if index.isValid():
            # Show cell context menu
            menu = CellContextMenu(self, index.row(), index.column(), self)
            menu.exec(self.viewport().mapToGlobal(pos))
        else:
            # Show empty table context menu
            menu = EmptyTableContextMenu(self, self)
            menu.exec(self.viewport().mapToGlobal(pos))
    
    def _show_header_context_menu(self, pos: QPoint):
        """Show context menu for column headers.
        
        Args:
            pos: Position where menu was requested
        """
        # Get column index from position
        col_index = self.horizontalHeader().logicalIndexAt(pos)
        
        if col_index >= 0:
            menu = HeaderContextMenu(self, col_index, self)
            menu.exec(self.horizontalHeader().mapToGlobal(pos))
    
    def _show_row_context_menu(self, pos: QPoint):
        """Show context menu for row headers.
        
        Args:
            pos: Position where menu was requested
        """
        # Get row index from position
        row_index = self.verticalHeader().logicalIndexAt(pos)
        
        if row_index >= 0:
            menu = RowContextMenu(self, row_index, self)
            menu.exec(self.verticalHeader().mapToGlobal(pos))
    
    def _on_header_double_clicked(self, column_index: int):
        """Handle double-click on header to edit column.
        
        Args:
            column_index: Index of the clicked column
        """
        if self._data_model and column_index >= 0 and column_index < self._data_model.columnCount():
            col_name = self._data_model._column_order[column_index]
            self.edit_column(col_name)
    
    # ========================================================================
    # Dialog Methods
    # ========================================================================
    
    def edit_column(self, column_name: str):
        """Open edit dialog for a column.
        
        Args:
            column_name: Name of the column to edit
        """
        if not self._data_model:
            return
        
        metadata = self._data_model.get_column_metadata(column_name)
        existing_names = [n for n in self._data_model.get_column_names() if n != column_name]
        
        # Choose appropriate dialog based on column type
        if metadata.is_data_column():
            from .column_dialogs import AddDataColumnDialog
            dialog = AddDataColumnDialog(
                parent=self,
                existing_names=existing_names,
                column_metadata=metadata
            )
            
            if dialog.exec():
                results = dialog.get_results()
                try:
                    self._data_model.edit_data_column(
                        column_name,
                        new_name=results['name'],
                        unit=results['unit'],
                        description=results['description'],
                        precision=results['precision']
                    )
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to edit column: {str(e)}")
        
        elif metadata.is_calculated_column():
            from .column_dialogs import AddCalculatedColumnDialog
            dialog = AddCalculatedColumnDialog(
                parent=self,
                model=self._data_model,
                existing_names=existing_names,
                column_metadata=metadata
            )
            
            if dialog.exec():
                results = dialog.get_results()
                try:
                    self._data_model.edit_calculated_column(
                        column_name,
                        new_name=results['name'],
                        formula=results['formula'],
                        description=results['description'],
                        precision=results['precision'],
                        propagate_uncertainty=results['propagate_uncertainty']
                    )
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to edit column: {str(e)}")
        
        elif metadata.is_derivative_column():
            from .column_dialogs import AddDerivativeColumnDialog
            dialog = AddDerivativeColumnDialog(
                parent=self,
                model=self._data_model,
                existing_names=existing_names,
                column_metadata=metadata
            )
            
            if dialog.exec():
                results = dialog.get_results()
                try:
                    self._data_model.edit_derivative_column(
                        column_name,
                        new_name=results['name'],
                        numerator_column=results['numerator_column'],
                        denominator_column=results['denominator_column'],
                        description=results['description'],
                        precision=results['precision']
                    )
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to edit column: {str(e)}")
        
        elif metadata.is_range_column():
            from .column_dialogs import AddRangeColumnDialog
            dialog = AddRangeColumnDialog(
                parent=self,
                existing_names=existing_names,
                column_metadata=metadata
            )
            
            if dialog.exec():
                results = dialog.get_results()
                try:
                    self._data_model.edit_range_column(
                        column_name,
                        new_name=results['name'],
                        start=results['start'],
                        end=results['end'],
                        points=results['points'],
                        unit=results['unit'],
                        description=results['description'],
                        precision=results['precision']
                    )
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to edit column: {str(e)}")
        
        elif metadata.is_interpolation_column():
            from .column_dialogs import AddInterpolationColumnDialog
            dialog = AddInterpolationColumnDialog(
                parent=self,
                model=self._data_model,
                existing_names=existing_names,
                column_metadata=metadata
            )
            
            if dialog.exec():
                results = dialog.get_results()
                try:
                    self._data_model.edit_interpolation_column(
                        column_name,
                        new_name=results['name'],
                        x_column=results['x_column'],
                        y_column=results['y_column'],
                        method=results['method'],
                        description=results['description'],
                        precision=results['precision']
                    )
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to edit column: {str(e)}")
        
        else:
            QMessageBox.information(
                self,
                "Not Editable",
                f"Columns of type '{metadata.column_type.value}' cannot be edited directly.\n"
                f"Consider converting to a data column first."
            )
    
    def _show_add_data_column_dialog(self):
        """Show dialog to add a new data column."""
        if not self._data_model:
            return
        
        from .column_dialogs import AddDataColumnDialog
        dialog = AddDataColumnDialog(
            parent=self,
            existing_names=self._data_model.get_column_names()
        )
        
        if dialog.exec():
            results = dialog.get_results()
            try:
                self._data_model.add_data_column(
                    name=results['name'],
                    dtype=results['dtype'],
                    unit=results['unit'],
                    description=results['description'],
                    precision=results['precision']
                )
                
                # Create uncertainty column if requested
                if results.get('create_uncertainty', False):
                    self._data_model.add_uncertainty_column(results['name'])
                    
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to add column: {str(e)}")
    
    def _show_add_calculated_column_dialog(self):
        """Show dialog to add a new calculated column."""
        if not self._data_model:
            return
        
        from .column_dialogs import AddCalculatedColumnDialog
        dialog = AddCalculatedColumnDialog(
            parent=self,
            model=self._data_model,
            existing_names=self._data_model.get_column_names()
        )
        
        if dialog.exec():
            results = dialog.get_results()
            try:
                self._data_model.add_calculated_column(
                    name=results['name'],
                    formula=results['formula'],
                    description=results['description'],
                    precision=results['precision'],
                    propagate_uncertainty=results['propagate_uncertainty']
                )
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to add column: {str(e)}")
    
    def _show_add_range_column_dialog(self):
        """Show dialog to add a new range column."""
        if not self._data_model:
            return
        
        from .column_dialogs import AddRangeColumnDialog
        dialog = AddRangeColumnDialog(
            parent=self,
            existing_names=self._data_model.get_column_names()
        )
        
        if dialog.exec():
            results = dialog.get_results()
            try:
                self._data_model.add_range_column(
                    name=results['name'],
                    start=results['start'],
                    end=results['end'],
                    points=results['points'],
                    unit=results['unit'],
                    description=results['description'],
                    precision=results['precision']
                )
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to add column: {str(e)}")
    
    def _show_add_derivative_column_dialog(self):
        """Show dialog to add a new derivative column."""
        if not self._data_model:
            return
        
        from .column_dialogs import AddDerivativeColumnDialog
        dialog = AddDerivativeColumnDialog(
            parent=self,
            model=self._data_model,
            existing_names=self._data_model.get_column_names()
        )
        
        if dialog.exec():
            results = dialog.get_results()
            try:
                self._data_model.add_derivative_column(
                    name=results['name'],
                    numerator=results['numerator_column'],
                    denominator=results['denominator_column'],
                    description=results['description'],
                    precision=results['precision']
                )
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to add column: {str(e)}")
    
    def _show_add_interpolation_column_dialog(self):
        """Show dialog to add a new interpolation column."""
        if not self._data_model:
            return
        
        from .column_dialogs import AddInterpolationColumnDialog
        dialog = AddInterpolationColumnDialog(
            parent=self,
            model=self._data_model,
            existing_names=self._data_model.get_column_names()
        )
        
        if dialog.exec():
            results = dialog.get_results()
            try:
                self._data_model.add_interpolation_column(
                    name=results['name'],
                    x_column=results['x_column'],
                    y_column=results['y_column'],
                    method=results['method'],
                    unit=results['unit'],
                    description=results['description'],
                    precision=results['precision']
                )
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to add column: {str(e)}")
    
    def _show_add_uncertainty_column_dialog(self):
        """Show dialog to add a new manual uncertainty column."""
        if not self._data_model:
            return
        
        from .column_dialogs import AddUncertaintyColumnDialog
        dialog = AddUncertaintyColumnDialog(
            parent=self,
            model=self._data_model
        )
        
        if dialog.exec():
            results = dialog.get_results()
            try:
                # Add the uncertainty column
                self._data_model.add_uncertainty_column(
                    data_column_name=results['reference_column'],
                    name=results['name'],
                    unit=results['unit'],
                    description=results['description'],
                    precision=results['precision']
                )
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to add column: {str(e)}")
    
    def _show_variables_dialog(self):
        """Show dialog to manage global variables/constants."""
        if not self._data_model:
            return
        
        from .variables_dialog import VariablesDialog
        dialog = VariablesDialog(
            parent=self,
            current_variables=self._data_model.get_variables()
        )
        
        if dialog.exec():
            new_variables = dialog.get_variables()
            self._data_model.set_variables(new_variables)
    
    def create_toolbar(self, parent=None) -> 'QToolBar':
        """Create and return a toolbar for this view.
        
        Args:
            parent: Parent widget for the toolbar
            
        Returns:
            DataTableToolbar instance
        """
        from .toolbar import DataTableToolbar
        return DataTableToolbar(self, parent)


class DataTableWidget(DataTableView):
    """All-in-one widget with built-in model.
    
    This is a convenience class that creates its own DataTableModel.
    For more control, use DataTableView with a separate model.
    """
    
    def __init__(self, parent=None):
        """Initialize widget with built-in model.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Create and set model
        self._internal_model = DataTableModel()
        self.setModel(self._internal_model)
    
    def model(self) -> DataTableModel:
        """Get the internal data model.
        
        Returns:
            DataTableModel instance
        """
        return self._internal_model
    
    # Convenience methods that delegate to model
    
    def add_data_column(self, *args, **kwargs):
        """Add a data column. See DataTableModel.add_data_column()."""
        return self._internal_model.add_data_column(*args, **kwargs)
    
    def add_calculated_column(self, *args, **kwargs):
        """Add a calculated column. See DataTableModel.add_calculated_column()."""
        return self._internal_model.add_calculated_column(*args, **kwargs)
    
    def add_range_column(self, *args, **kwargs):
        """Add a range column. See DataTableModel.add_range_column()."""
        return self._internal_model.add_range_column(*args, **kwargs)
    
    def add_derivative_column(self, *args, **kwargs):
        """Add a derivative column. See DataTableModel.add_derivative_column()."""
        return self._internal_model.add_derivative_column(*args, **kwargs)
    
    def add_interpolation_column(self, *args, **kwargs):
        """Add an interpolation column. See DataTableModel.add_interpolation_column()."""
        return self._internal_model.add_interpolation_column(*args, **kwargs)
    
    def remove_column(self, *args, **kwargs):
        """Remove a column. See DataTableModel.remove_column()."""
        return self._internal_model.remove_column(*args, **kwargs)
    
    def get_column_data(self, *args, **kwargs):
        """Get column data. See DataTableModel.get_column_data()."""
        return self._internal_model.get_column_data(*args, **kwargs)
    
    def to_dataframe(self):
        """Convert to DataFrame. See DataTableModel.to_dataframe()."""
        return self._internal_model.to_dataframe()
    
    # File I/O convenience methods
    
    def save_to_json(self, *args, **kwargs):
        """Save to JSON file. See DataTableModel.save_to_json()."""
        return self._internal_model.save_to_json(*args, **kwargs)
    
    def load_from_json(self, *args, **kwargs):
        """Load from JSON file. See DataTableModel.load_from_json()."""
        return self._internal_model.load_from_json(*args, **kwargs)
    
    def save_to_csv(self, *args, **kwargs):
        """Save to CSV file. See DataTableModel.save_to_csv()."""
        return self._internal_model.save_to_csv(*args, **kwargs)
    
    def load_from_csv(self, *args, **kwargs):
        """Load from CSV file. See DataTableModel.load_from_csv()."""
        return self._internal_model.load_from_csv(*args, **kwargs)
    
    def save_to_excel(self, *args, **kwargs):
        """Save to Excel file. See DataTableModel.save_to_excel()."""
        return self._internal_model.save_to_excel(*args, **kwargs)
    
    def load_from_excel(self, *args, **kwargs):
        """Load from Excel file. See DataTableModel.load_from_excel()."""
        return self._internal_model.load_from_excel(*args, **kwargs)
    
    def create_toolbar(self, parent=None) -> 'QToolBar':
        """Create and return a toolbar for this view.
        
        Args:
            parent: Parent widget for the toolbar
            
        Returns:
            DataTableToolbar instance
        """
        from .toolbar import DataTableToolbar
        return DataTableToolbar(self, parent)
