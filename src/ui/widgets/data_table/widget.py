"""Main DataTable widget."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableView, QHeaderView, QToolBar,
    QPushButton, QMenu, QInputDialog, QApplication
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from typing import Tuple, List, Optional
import pandas as pd

from studies.data_table_study import DataTableStudy, ColumnType
from ..shared import show_error, show_warning, confirm_action, validate_column_name, emit_full_model_update
from ..column_dialogs import (
    AddDataColumnDialog,
    AddCalculatedColumnDialog,
    AddDerivativeColumnDialog,
    AddRangeColumnDialog
)

from .model import DataTableModel
from .header import EditableHeaderView
from constants import COLUMN_SYMBOLS, TABLE_ROW_HEIGHT


class DataTableWidget(QWidget):
    """Widget for viewing/editing DataTableStudy.
    
    Features:
    - Table view with inline editing
    - Toolbar for column operations
    - Add/remove rows and columns
    - Column type management
    """
    
    # Signal emitted when data changes (for plot/statistics updates)
    dataChanged = Signal(str)  # Emits study name
    
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
        
        add_uncert_col = add_column_menu.addAction("δ Uncertainty Column")
        add_uncert_col.triggered.connect(lambda: self._add_column(ColumnType.UNCERTAINTY))
        add_uncert_col.setShortcut("Ctrl+Shift+U")
        
        add_calc_col = add_column_menu.addAction("ƒ Calculated Column (Formula)")
        add_calc_col.triggered.connect(lambda: self._add_column(ColumnType.CALCULATED))
        add_calc_col.setShortcut("Ctrl+Shift+C")
        
        add_deriv_col = add_column_menu.addAction("d/dx Derivative Column")
        add_deriv_col.triggered.connect(lambda: self._add_column(ColumnType.DERIVATIVE))
        
        add_range_col = add_column_menu.addAction("⋯ Range Column (Sequence)")
        add_range_col.triggered.connect(lambda: self._add_column(ColumnType.RANGE))
        
        add_column_btn.setMenu(add_column_menu)
        toolbar.addWidget(add_column_btn)
        
        # Fill column action
        fill_column_action = QAction("Fill Column", self)
        fill_column_action.setShortcut("Ctrl+Shift+F")
        fill_column_action.setToolTip("Fill selected column or cells with a value (Ctrl+Shift+F)")
        fill_column_action.triggered.connect(self._fill_column)
        toolbar.addAction(fill_column_action)
        
        toolbar.addSeparator()
        
        # View operations
        self.show_uncertainty_action = QAction("Hide Uncertainty Columns", self)
        self.show_uncertainty_action.setCheckable(True)
        self.show_uncertainty_action.setChecked(False)  # False = show, True = hide
        self.show_uncertainty_action.setToolTip("Toggle visibility of uncertainty (δ) columns")
        self.show_uncertainty_action.triggered.connect(self._toggle_uncertainty_columns)
        toolbar.addAction(self.show_uncertainty_action)
        
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
        # Get constants from workspace (numeric and calculated constants for use in formulas)
        if self.study.workspace:
            available_vars = [name for name, data in self.study.workspace.constants.items()
                            if data.get("type") in ["constant", "calculated"]]
        else:
            available_vars = []
        return available_cols, available_vars
    
    def _refresh_data(self, changed_columns: set = None):
        """Refresh after data changes (incremental update).
        
        Use for: cell edits, paste, fill, delete cell values.
        Only recalculates dependent columns (fast).
        
        Args:
            changed_columns: Column names that changed (or empty set if no formulas affected)
        """
        if changed_columns is None:
            changed_columns = set()
        
        # Mark columns dirty (if any)
        for col_name in changed_columns:
            self.study.mark_dirty(col_name)
        
        # Recalculate only affected columns (uses dependency tracking)
        if changed_columns:
            self.study._recalculate_dirty_columns()
        
        # Emit dataChanged for cell range (NOT layoutChanged - faster)
        if len(self.study.table.data) > 0 and len(self.study.table.columns) > 0:
            top_left = self.model.index(0, 0)
            bottom_right = self.model.index(
                len(self.study.table.data) - 1,
                len(self.study.table.columns) - 1
            )
            self.model.dataChanged.emit(top_left, bottom_right)
        
        # Notify other widgets
        self.dataChanged.emit(self.study.name)
    
    def _refresh_structure(self):
        """Refresh after structural changes (full reset).
        
        Use for: add/remove/rename column, change column type.
        Recalculates all formulas.
        """
        self.model.beginResetModel()
        self.study.recalculate_all()
        self.model.endResetModel()
        self.dataChanged.emit(self.study.name)
    
    def _refresh_batch(self):
        """Refresh after batch operations (full reset).
        
        Use for: add rows, multi-column adds, load from file.
        Recalculates all formulas.
        """
        self.model.beginResetModel()
        self.study.recalculate_all()
        self.model.endResetModel()
        self.dataChanged.emit(self.study.name)
    
    def _add_row(self):
        """Add row to table."""
        self.study.add_rows(1)
        self._refresh_batch()  # Batch operation - full reset
    
    def _auto_resize_columns(self):
        """Auto-resize all columns to fit content."""
        self.view.resizeColumnsToContents()
        # Ensure minimum width for readability
        for col in range(self.model.columnCount()):
            width = self.view.columnWidth(col)
            if width < 60:
                self.view.setColumnWidth(col, 60)
    
    def _toggle_uncertainty_columns(self):
        """Toggle visibility of uncertainty columns."""
        hide = self.show_uncertainty_action.isChecked()
        
        # Update action text
        if hide:
            self.show_uncertainty_action.setText("Show Uncertainty Columns")
        else:
            self.show_uncertainty_action.setText("Hide Uncertainty Columns")
        
        # Hide/show columns
        for col_idx, col_name in enumerate(self.study.table.columns):
            col_type = self.study.get_column_type(col_name)
            if col_type == ColumnType.UNCERTAINTY:
                self.view.setColumnHidden(col_idx, hide)
    
    def _add_column(self, col_type: str):
        """Add column to table.
        
        Args:
            col_type: Column type (DATA, CALCULATED, DERIVATIVE, RANGE, UNCERTAINTY)
        """
        if col_type == ColumnType.DATA:
            self._add_data_column()
        elif col_type == ColumnType.UNCERTAINTY:
            self._add_uncertainty_column()
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
            self._refresh_structure()  # Structural change - full reset
    
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
                self._refresh_structure()  # Structural change - full reset
            except Exception as e:
                show_error(self, "Error", f"Failed to add column: {str(e)}")
    
    def _add_derivative_column(self):
        """Add DERIVATIVE column."""
        # Get available columns for differentiation (data, calculated, range)
        data_cols = [
            c for c in self.study.table.columns 
            if self.study.get_column_type(c) in [ColumnType.DATA, ColumnType.CALCULATED, ColumnType.RANGE]
        ]
        
        if len(data_cols) < 2:
            show_warning(
                self, 
                "Error", 
                "Need at least 2 columns (data/calculated/range) to create derivative"
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
                self._refresh_structure()  # Structural change - full reset
            except Exception as e:
                show_error(self, "Error", f"Failed to add column: {str(e)}")
    
    def _add_uncertainty_column(self):
        """Add manual UNCERTAINTY column."""
        # Get available data/calculated columns to reference
        available_cols = [
            c for c in self.study.table.columns
            if self.study.get_column_type(c) in [ColumnType.DATA, ColumnType.CALCULATED]
        ]
        
        from ..column_dialogs import AddUncertaintyColumnDialog
        dialog = AddUncertaintyColumnDialog(available_cols, self)
        if dialog.exec():
            name, unit, ref_col = dialog.get_values()
            
            if not validate_column_name(self, name, self.study.table.columns):
                return
            
            self.study.add_column(
                name,
                ColumnType.UNCERTAINTY,
                unit=unit,
                uncertainty_reference=ref_col if ref_col else None
            )
            self._refresh_structure()  # Structural change - full reset
    
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
                self._refresh_structure()  # Structural change - full reset
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
            self._refresh_structure()  # Structural change - formula modified
    
    def _delete_column(self, col_name: str):
        """Delete column.
        
        Args:
            col_name: Column name
        """
        if confirm_action(self, "Confirm Delete", f"Delete column '{col_name}'?"):
            self.study.remove_column(col_name)
            self._refresh_structure()  # Structural change - full reset
    
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
            self._refresh_batch()  # Batch operation - full reset
    
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
            self._refresh_batch()  # Batch operation - full reset
    
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
    
    def _fill_column(self):
        """Fill selected column or cells with a value."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QRadioButton, QButtonGroup
        
        # Get selection
        selection = self.view.selectionModel().selectedIndexes()
        if not selection:
            show_warning(self, "No Selection", "Please select a column or cells to fill.")
            return
        
        # Get selected column(s)
        selected_cols = set(idx.column() for idx in selection)
        if len(selected_cols) > 1:
            show_warning(self, "Multiple Columns", "Please select cells from a single column only.")
            return
        
        col_idx = list(selected_cols)[0]
        col_name = self.study.table.columns[col_idx]
        col_type = self.study.get_column_type(col_name)
        
        # Only allow filling DATA columns
        if col_type != ColumnType.DATA:
            show_warning(
                self, 
                "Cannot Fill", 
                f"Cannot fill {col_type.upper()} column. Only DATA columns can be filled.\n"
                f"To modify this column, convert it to DATA type first."
            )
            return
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Fill Column: {col_name}")
        layout = QVBoxLayout(dialog)
        
        # Value input
        layout.addWidget(QLabel("Enter value to fill:"))
        value_input = QLineEdit()
        value_input.setPlaceholderText("e.g., 0, 1.5, -3.14")
        layout.addWidget(value_input)
        
        # Fill scope
        layout.addWidget(QLabel("\nFill scope:"))
        scope_group = QButtonGroup(dialog)
        
        selected_radio = QRadioButton(f"Selected cells only ({len(selection)} cells)")
        selected_radio.setChecked(True)
        scope_group.addButton(selected_radio)
        layout.addWidget(selected_radio)
        
        all_radio = QRadioButton(f"Entire column ({len(self.study.table.data)} rows)")
        scope_group.addButton(all_radio)
        layout.addWidget(all_radio)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        # Execute dialog
        if dialog.exec() != QDialog.Accepted:
            return
        
        # Get value
        value_str = value_input.text().strip()
        if not value_str:
            show_warning(self, "Empty Value", "Please enter a value.")
            return
        
        # Parse value
        try:
            value = float(value_str)
        except ValueError:
            show_warning(self, "Invalid Value", f"'{value_str}' is not a valid number.")
            return
        
        # Fill cells
        if selected_radio.isChecked():
            # Fill selected cells only
            for idx in selection:
                row = idx.row()
                self.study.table.data.iloc[row, col_idx] = value
        else:
            # Fill entire column
            self.study.table.data.iloc[:, col_idx] = value
        
        # Mark dependent columns as dirty and recalculate
        self._refresh_data({col_name})  # Data change - incremental update
        
        # Show confirmation
        scope_text = f"{len(selection)} cells" if selected_radio.isChecked() else "entire column"
        from ..shared import show_info
        show_info(self, "Fill Complete", f"Filled {scope_text} with value {value}")
    
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
        
        self._refresh_structure()  # Structural change - column type changed
        show_warning(self, "Conversion Complete", f"Column '{col_name}' is now a DATA column.")
