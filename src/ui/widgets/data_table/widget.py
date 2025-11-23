"""Main DataTable widget."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableView, QHeaderView, QToolBar,
    QPushButton, QMenu, QInputDialog, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from typing import Tuple, List, Optional
import pandas as pd

from studies.data_table_study import DataTableStudy, ColumnType
from ..shared import show_error, show_warning, confirm_action, validate_column_name, emit_full_model_update
from ..column_dialogs import (
    AddDataColumnDialog,
    AddCalculatedColumnDialog,
    EditDataColumnDialog
)
from ..column_dialogs_extended import AddDerivativeColumnDialog, AddRangeColumnDialog

from .model import DataTableModel
from .header import EditableHeaderView
from .constants import COLUMN_SYMBOLS


class DataTableWidget(QWidget):
    """Widget for viewing/editing DataTableStudy.
    
    Features:
    - Table view with inline editing
    - Toolbar for column operations
    - Add/remove rows and columns
    - Column type management
    """
    
    def __init__(self, study: DataTableStudy):
        """Initialize widget.
        
        Args:
            study: DataTableStudy to display
        """
        super().__init__()
        
        self.study = study
        
        # Setup UI
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        self.toolbar = self._create_toolbar()
        layout.addWidget(self.toolbar)
        
        # Table view
        self.model = DataTableModel(study)
        self.view = QTableView()
        self.view.setModel(self.model)
        
        # Set custom header view with double-click editing
        header = EditableHeaderView(Qt.Horizontal, self.view)
        header.table_widget = self
        self.view.setHorizontalHeader(header)
        
        self.view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)  # type: ignore
        self.view.horizontalHeader().setStretchLastSection(True)  # type: ignore
        self.view.verticalHeader().setDefaultSectionSize(TABLE_ROW_HEIGHT)
        self.view.setAlternatingRowColors(True)  # Better readability
        self.view.setContextMenuPolicy(Qt.CustomContextMenu)  # type: ignore
        self.view.customContextMenuRequested.connect(self._show_context_menu)
        self.view.setSelectionMode(QTableView.ExtendedSelection)  # type: ignore
        self.view.setSelectionBehavior(QTableView.SelectItems)  # type: ignore
        layout.addWidget(self.view)
        
        # Setup keyboard shortcuts
        self._setup_shortcuts()
    
    def _create_toolbar(self) -> QToolBar:
        """Create toolbar.
        
        Returns:
            QToolBar instance
        """
        toolbar = QToolBar()
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)  # type: ignore
        
        # Row operations
        add_row_action = QAction("Add Row", self)
        add_row_action.setShortcut("Ctrl+R")
        add_row_action.setToolTip("Add a new empty row (Ctrl+R)")
        add_row_action.triggered.connect(self._add_row)
        toolbar.addAction(add_row_action)
        
        delete_row_action = QAction("Delete Row(s)", self)
        delete_row_action.setShortcut("Ctrl+D")
        delete_row_action.setToolTip("Delete selected row(s) (Ctrl+D)")
        delete_row_action.triggered.connect(self._delete_selected_rows)
        toolbar.addAction(delete_row_action)
        
        toolbar.addSeparator()
        
        # Column operations
        add_column_btn = QPushButton("Add Column")
        add_column_menu = QMenu(self)
        
        add_data_col = add_column_menu.addAction("✎ Data Column")
        add_data_col.triggered.connect(lambda: self._add_column(ColumnType.DATA))
        add_data_col.setShortcut("Ctrl+Shift+D")
        
        add_calc_col = add_column_menu.addAction("ƒ Calculated Column (Formula)")
        add_calc_col.triggered.connect(lambda: self._add_column(ColumnType.CALCULATED))
        add_calc_col.setShortcut("Ctrl+Shift+C")
        
        add_deriv_col = add_column_menu.addAction("d/dx Derivative Column")
        add_deriv_col.triggered.connect(lambda: self._add_column(ColumnType.DERIVATIVE))
        
        add_range_col = add_column_menu.addAction("⋯ Range Column (Sequence)")
        add_range_col.triggered.connect(lambda: self._add_column(ColumnType.RANGE))
        
        add_column_btn.setMenu(add_column_menu)
        toolbar.addWidget(add_column_btn)
        
        toolbar.addSeparator()
        
        # View operations
        auto_resize_action = QAction("Auto-resize Columns", self)
        auto_resize_action.setToolTip("Automatically resize all columns to fit content")
        auto_resize_action.triggered.connect(self._auto_resize_columns)
        toolbar.addAction(auto_resize_action)
        
        toolbar.addSeparator()
        
        return toolbar
    
    def _get_context(self, exclude_column: Optional[str] = None) -> Tuple[List[str], List[str]]:
        """Get available columns and variables.
        
        Args:
            exclude_column: Column to exclude from list
            
        Returns:
            Tuple of (available_columns, available_variables)
        """
        available_cols = [
            c for c in self.study.table.columns 
            if c != exclude_column
        ]
        # Get constants from workspace (only constant type for use in formulas)
        if self.study.workspace:
            available_vars = [name for name, data in self.study.workspace.constants.items()
                            if data.get("type") == "constant"]
        else:
            available_vars = []
        return available_cols, available_vars
    
    def _refresh_table(self):
        """Refresh entire table display."""
        self.study.recalculate_all()
        emit_full_model_update(self.model)
    
    def _add_row(self):
        """Add row to table."""
        self.study.add_rows(1)
        self.model.layoutChanged.emit()
    
    def _auto_resize_columns(self):
        """Auto-resize all columns to fit content."""
        self.view.resizeColumnsToContents()
        # Ensure minimum width for readability
        for col in range(self.model.columnCount()):
            width = self.view.columnWidth(col)
            if width < 60:
                self.view.setColumnWidth(col, 60)
    
    def _add_column(self, col_type: str):
        """Add column to table.
        
        Args:
            col_type: Column type (DATA, CALCULATED, DERIVATIVE, RANGE)
        """
        if col_type == ColumnType.DATA:
            self._add_data_column()
        
        elif col_type == ColumnType.CALCULATED:
            self._add_calculated_column()
        
        elif col_type == ColumnType.DERIVATIVE:
            self._add_derivative_column()
        
        elif col_type == ColumnType.RANGE:
            self._add_range_column()
    
    def _add_data_column(self):
        """Add DATA column."""
        dialog = AddDataColumnDialog(self)
        if dialog.exec():
            name, unit = dialog.get_values()
            
            if not validate_column_name(self, name, self.study.table.columns):
                return
            
            self.study.add_column(name, ColumnType.DATA, unit=unit)
            self.model.layoutChanged.emit()
    
    def _add_calculated_column(self):
        """Add CALCULATED column."""
        available_cols, available_vars = self._get_context()
        
        dialog = AddCalculatedColumnDialog(available_cols, available_vars, self)
        if dialog.exec():
            name, formula, unit, propagate_uncertainty = dialog.get_values()
            
            if not formula:
                show_warning(self, "Error", "Formula is required")
                return
            
            if not validate_column_name(self, name, self.study.table.columns):
                return
            
            try:
                self.study.add_column(
                    name, 
                    ColumnType.CALCULATED, 
                    formula=formula, 
                    unit=unit,
                    propagate_uncertainty=propagate_uncertainty
                )
                self.model.layoutChanged.emit()
            except Exception as e:
                show_error(self, "Error", f"Failed to add column: {str(e)}")
    
    def _add_derivative_column(self):
        """Add DERIVATIVE column."""
        # Get available data columns (not calculated/derivative)
        data_cols = [
            c for c in self.study.table.columns 
            if self.study.get_column_type(c) in [ColumnType.DATA, ColumnType.RANGE]
        ]
        
        if len(data_cols) < 2:
            show_warning(
                self, 
                "Error", 
                "Need at least 2 data/range columns to create derivative"
            )
            return
        
        dialog = AddDerivativeColumnDialog(data_cols, self)
        if dialog.exec():
            name, y_col, x_col, order, unit = dialog.get_values()
            
            if not name or not y_col or not x_col:
                show_warning(self, "Error", "All fields are required")
                return
            
            if not validate_column_name(self, name, self.study.table.columns):
                return
            
            try:
                self.study.add_column(
                    name, 
                    ColumnType.DERIVATIVE,
                    unit=unit,
                    derivative_of=y_col,
                    with_respect_to=x_col,
                    order=order
                )
                self.model.layoutChanged.emit()
            except Exception as e:
                show_error(self, "Error", f"Failed to add column: {str(e)}")
    
    def _add_range_column(self):
        """Add RANGE column."""
        dialog = AddRangeColumnDialog(self)
        if dialog.exec():
            result = dialog.get_values()
            name = result["name"]
            range_type = result["range_type"]
            unit = result.get("unit")
            
            if not name or not range_type:
                show_warning(self, "Error", "Column name and range type are required")
                return
            
            if not validate_column_name(self, name, self.study.table.columns):
                return
            
            try:
                self.study.add_column(
                    name,
                    ColumnType.RANGE,
                    unit=unit,
                    range_type=range_type,
                    range_start=result.get("start"),
                    range_stop=result.get("stop"),
                    range_count=result.get("count"),
                    range_step=result.get("step")
                )
                self.model.layoutChanged.emit()
            except Exception as e:
                show_error(self, "Error", f"Failed to add column: {str(e)}")
    
    def _show_context_menu(self, position):
        """Show context menu.
        
        Args:
            position: Menu position
        """
        from .context_menu import show_data_table_context_menu
        show_data_table_context_menu(self, position)
    
    def _edit_column(self, col_name: str):
        """Edit column formula.
        
        Args:
            col_name: Column name
        """
        # Get available columns and variables
        available_cols, available_vars = self._get_context(exclude_column=col_name)
        
        dialog = AddCalculatedColumnDialog(available_cols, available_vars, self)
        dialog.setWindowTitle("Edit Calculated Column")
        
        # Pre-fill with existing values
        dialog.name_edit.setText(col_name)
        dialog.name_edit.setEnabled(False)  # Can't rename
        
        formula = self.study.get_column_formula(col_name)
        if formula:
            dialog.formula_edit.setPlainText(formula)
        
        unit = self.study.get_column_unit(col_name)
        if unit:
            dialog.unit_edit.setText(unit)
        
        if dialog.exec():
            _, new_formula, new_unit, _ = dialog.get_values()
            
            # Update formula
            self.study.column_metadata[col_name]["formula"] = new_formula
            self.study.column_metadata[col_name]["unit"] = new_unit
            self.study.formula_engine.register_formula(col_name, new_formula)
            
            # Recalculate
            self._refresh_table()
    
    def _delete_column(self, col_name: str):
        """Delete column.
        
        Args:
            col_name: Column name
        """
        if confirm_action(self, "Confirm Delete", f"Delete column '{col_name}'?"):
            self.study.remove_column(col_name)
            self.model.layoutChanged.emit()
    
    def _insert_row(self, row: int):
        """Insert row at position.
        
        Args:
            row: Row index
        """
        # Current implementation: adds row at end (proper insertion would require DataFrame.insert)
        self._add_row()
    
    def _delete_row(self, row: int):
        """Delete row.
        
        Args:
            row: Row index
        """
        if confirm_action(self, "Confirm Delete", f"Delete row {row + 1}?"):
            self.study.remove_rows([row])
            self.model.layoutChanged.emit()
    
    def _rename_column(self, column_index: int):
        """Rename column via double-click on header.
        
        Args:
            column_index: Index of column to rename
        """
        old_name = self.study.table.columns[column_index]
        
        # Get new name from user
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Column",
            f"Rename '{old_name}' to:",
            text=old_name
        )
        
        if not ok or not new_name or new_name == old_name:
            return
        
        # Validate new name
        if not validate_column_name(self, new_name, self.study.table.columns):
            return
        
        # Rename column in study
        try:
            self.study.rename_column(old_name, new_name)
            
            # Update model
            emit_full_model_update(self.model)
        except Exception as e:
            show_error(self, "Rename Error", f"Failed to rename column: {str(e)}")
    
    def _delete_selected_rows(self):
        """Delete currently selected rows."""
        selected = self.view.selectionModel().selectedRows()
        if not selected:
            return
        
        rows = sorted([idx.row() for idx in selected], reverse=True)
        if confirm_action(self, "Confirm Delete", f"Delete {len(rows)} row(s)?"):
            self.study.remove_rows(rows)
            self.model.layoutChanged.emit()
    
    def _copy_selection(self):
        """Copy selected cells to clipboard."""
        selection = self.view.selectionModel().selectedIndexes()
        if not selection:
            return
        
        # Group by row
        rows = {}
        for index in selection:
            row = index.row()
            if row not in rows:
                rows[row] = []
            rows[row].append((index.column(), index.data()))
        
        # Build tab-separated text
        lines = []
        for row in sorted(rows.keys()):
            cols = sorted(rows[row])
            line = "\t".join(str(val) for _, val in cols)
            lines.append(line)
        
        text = "\n".join(lines)
        QApplication.clipboard().setText(text)
    
    def _paste_data(self):
        """Paste from clipboard into selected cells."""
        selection = self.view.selectionModel().selectedIndexes()
        if not selection:
            return
        
        # Get clipboard text
        text = QApplication.clipboard().text()
        if not text:
            return
        
        # Parse tab/newline separated data
        lines = text.strip().split('\n')
        start_row = selection[0].row()
        start_col = selection[0].column()
        
        try:
            for row_offset, line in enumerate(lines):
                values = line.split('\t')
                for col_offset, value in enumerate(values):
                    row = start_row + row_offset
                    col = start_col + col_offset
                    
                    if row < self.model.rowCount() and col < self.model.columnCount():
                        col_name = self.study.table.columns[col]
                        # Only paste into DATA columns
                        if self.study.get_column_type(col_name) == ColumnType.DATA:
                            try:
                                numeric_value = float(value) if value else None
                                self.study.table.data.at[row, col_name] = numeric_value
                            except (ValueError, TypeError):
                                pass  # Skip non-numeric values
            
            # Refresh display
            self._refresh_table()
        except Exception as e:
            show_error(self, "Paste Error", f"Failed to paste data: {str(e)}")
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts for clipboard operations."""
        from .shortcuts import setup_table_shortcuts
        setup_table_shortcuts(self)
    
    def _edit_column_properties(self, col_index: int):
        """Open dialog to edit column properties.
        
        Args:
            col_index: Column index
        """
        from .column_edit import edit_column_properties
        edit_column_properties(self, col_index)
    
    def _convert_column_to_data(self):
        """Convert selected column to DATA type."""
        current_col = self.view.currentIndex().column()
        if current_col < 0:
            show_warning(self, "No Selection", "Please select a column to convert.")
            return
        
        col_name = self.study.table.columns[current_col]
        col_type = self.study.get_column_type(col_name)
        
        if col_type == ColumnType.DATA:
            show_warning(self, "Already Data", f"Column '{col_name}' is already a DATA column.")
            return
        
        symbol = COLUMN_SYMBOLS.get(col_type, "")
        type_display = f"{symbol} {col_type.upper()}" if symbol else col_type.upper()
        
        # Confirm conversion
        if not confirm_action(
            self,
            "Convert Column",
            f"Convert '{col_name}' from {type_display} to DATA column?\n\n"
            "Current values will be preserved but the column will become editable."
        ):
            return
        
        # Convert: keep data, change metadata
        self.study.column_metadata[col_name]["type"] = ColumnType.DATA
        # Clear type-specific metadata
        for key in ["formula", "derivative_of", "with_respect_to", "range_type", "range_start", "range_stop", "range_count"]:
            self.study.column_metadata[col_name].pop(key, None)
        
        self._refresh_table()
        show_warning(self, "Conversion Complete", f"Column '{col_name}' is now a DATA column.")
