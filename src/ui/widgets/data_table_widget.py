"""
DataTable widget for editing tabular data.

Provides a Qt table view for DataTableStudy with inline editing,
column management, and formula evaluation.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QHeaderView,
    QToolBar, QPushButton, QMenu, QLineEdit, QLabel, QInputDialog,
    QApplication
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QAction, QBrush, QColor, QKeySequence, QShortcut
from typing import Any, Optional, Tuple, List
import pandas as pd

from studies.data_table_study import DataTableStudy, ColumnType
from .dialog_utils import show_error, show_warning, confirm_action, validate_column_name
from .model_utils import format_cell_value, emit_full_model_update
from .column_dialogs import (
    AddDataColumnDialog, 
    AddCalculatedColumnDialog, 
    AddDerivativeColumnDialog,
    AddRangeColumnDialog,
)

# Column type symbols for headers
COLUMN_SYMBOLS = {
    "data": "✎",         # Pencil - editable
    "calculated": "ƒ",   # Function symbol
    "derivative": "d/dx", # Derivative notation
    "range": "⋯",        # Range dots
    "uncertainty": "δ",  # Delta - uncertainty
}

# Column type text colors (for headers)
COLUMN_TEXT_COLORS = {
    "data": QColor(0, 0, 0),           # Black
    "calculated": QColor(180, 120, 0), # Dark yellow/orange
    "derivative": QColor(0, 80, 180),  # Dark blue
    "range": QColor(0, 120, 60),       # Dark green
    "uncertainty": QColor(140, 0, 140), # Purple
}

# Column type background colors (for cells)
COLUMN_BG_COLORS = {
    "data": QColor(255, 255, 255),      # White - editable
    "calculated": QColor(255, 250, 240), # Light cream
    "derivative": QColor(240, 245, 255), # Light blue
    "range": QColor(240, 255, 245),      # Light green
    "uncertainty": QColor(250, 240, 250), # Light purple
}

# Alternate row colors
COLUMN_BG_COLORS_ALT = {
    "data": QColor(248, 248, 248),      # Light gray
    "calculated": QColor(252, 248, 235), # Darker cream
    "derivative": QColor(235, 242, 252), # Darker blue
    "range": QColor(235, 252, 242),      # Darker green
    "uncertainty": QColor(248, 235, 248), # Darker purple
}


class EditableHeaderView(QHeaderView):
    """Custom header view that allows double-click to edit column properties."""
    
    def __init__(self, orientation, parent=None):
        """Initialize header view.
        
        Args:
            orientation: Qt.Horizontal or Qt.Vertical
            parent: Parent widget
        """
        super().__init__(orientation, parent)
        self.table_widget = None
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click on header to edit column properties.
        
        Args:
            event: Mouse event
        """
        if self.orientation() == Qt.Horizontal and self.table_widget:
            logical_index = self.logicalIndexAt(event.pos())
            if logical_index >= 0:
                self.table_widget._edit_column_properties(logical_index)
        else:
            super().mouseDoubleClickEvent(event)


class DataTableModel(QAbstractTableModel):
    """Qt model for DataTableStudy."""
    
    def __init__(self, study: DataTableStudy):
        """Initialize model.
        
        Args:
            study: DataTableStudy to display
        """
        super().__init__()
        self.study = study
    
    def rowCount(self, parent=QModelIndex()) -> int:
        """Get row count."""
        if parent.isValid():
            return 0
        return len(self.study.table.data)
    
    def columnCount(self, parent=QModelIndex()) -> int:
        """Get column count."""
        if parent.isValid():
            return 0
        return len(self.study.table.columns)
    
    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> Any:  # type: ignore
        """Get cell data.
        
        Args:
            index: Cell index
            role: Data role
            
        Returns:
            Cell value or None
        """
        if not index.isValid():
            return None
        
        if role == Qt.DisplayRole or role == Qt.EditRole:  # type: ignore
            value = self.study.table.data.iloc[index.row(), index.column()]
            return format_cell_value(value)
        
        # Foreground color for non-editable columns
        if role == Qt.ForegroundRole:  # type: ignore
            col_name = self.study.table.columns[index.column()]
            col_type = self.study.get_column_type(col_name)
            if col_type != ColumnType.DATA:
                # Slightly dimmed for calculated columns
                return QBrush(QColor(80, 80, 80))
        
        return None
    
    def setData(self, index: QModelIndex, value: Any, role=Qt.EditRole) -> bool:  # type: ignore
        """Set cell data.
        
        Args:
            index: Cell index
            value: New value
            role: Data role
            
        Returns:
            True if successful
        """
        if not index.isValid() or role != Qt.EditRole:  # type: ignore
            return False
        
        col_name = self.study.table.columns[index.column()]
        
        # Check if column is editable
        col_type = self.study.get_column_type(col_name)
        if col_type != ColumnType.DATA:
            return False  # Can't edit calculated columns
        
        # Convert and set value
        try:
            if value == "":
                value = None
            else:
                value = float(value)
            
            self.study.table.data.iloc[index.row(), index.column()] = value
            
            # Trigger recalculation
            self.study.on_data_changed(col_name)
            
            # Emit data changed for entire table (dependent columns may have changed)
            emit_full_model_update(self)
            
            return True
        except (ValueError, TypeError):
            return False
    
    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole) -> Any:  # type: ignore
        """Get header data.
        
        Args:
            section: Row/column index
            orientation: Horizontal or vertical
            role: Data role
            
        Returns:
            Header value or None
        """
        if role == Qt.DisplayRole:  # type: ignore
            if orientation == Qt.Horizontal:  # type: ignore
                if section < len(self.study.table.columns):
                    col_name = self.study.table.columns[section]
                    col_type = self.study.get_column_type(col_name)
                    symbol = COLUMN_SYMBOLS.get(col_type, "")
                    
                    # Show column name with type symbol
                    header = f"{symbol} {col_name}" if symbol else col_name
                    
                    # Add unit if present
                    unit = self.study.get_column_unit(col_name)
                    if unit:
                        header += f" [{unit}]"
                    
                    return header
            else:
                return str(section + 1)
        
        # Header text color based on column type
        if role == Qt.ForegroundRole and orientation == Qt.Horizontal:  # type: ignore
            if section < len(self.study.table.columns):
                col_name = self.study.table.columns[section]
                col_type = self.study.get_column_type(col_name)
                color = COLUMN_TEXT_COLORS.get(col_type, QColor(0, 0, 0))
                return QBrush(color)
        
        # Tooltip with column info
        if role == Qt.ToolTipRole and orientation == Qt.Horizontal:  # type: ignore
            if section < len(self.study.table.columns):
                col_name = self.study.table.columns[section]
                col_type = self.study.get_column_type(col_name)
                
                tooltip = f"Column: {col_name}\nType: {col_type.upper()}"
                
                # Add type-specific info
                col_meta = self.study.column_metadata.get(col_name, {})
                if col_type == "calculated":
                    formula = col_meta.get("formula", "")
                    tooltip += f"\nFormula: {formula}"
                elif col_type == "derivative":
                    derivative_of = col_meta.get("derivative_of", "")
                    order = col_meta.get("derivative_order", 1)
                    tooltip += f"\nDerivative of: {derivative_of}\nOrder: {order}"
                elif col_type == "range":
                    range_type = col_meta.get("range_type", "")
                    tooltip += f"\nRange type: {range_type}"
                
                unit = self.study.get_column_unit(col_name)
                if unit:
                    tooltip += f"\nUnit: {unit}"
                
                return tooltip
        
        return None
    
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:  # type: ignore
        """Get cell flags.
        
        Args:
            index: Cell index
            
        Returns:
            Item flags
        """
        if not index.isValid():
            return Qt.NoItemFlags  # type: ignore
        
        col_name = self.study.table.columns[index.column()]
        col_type = self.study.get_column_type(col_name)
        
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable  # type: ignore
        
        # Only data columns are editable
        if col_type == ColumnType.DATA:
            flags |= Qt.ItemIsEditable  # type: ignore
        
        return flags


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
        
        # Search/Filter bar
        self.search_bar = self._create_search_bar()
        layout.addWidget(self.search_bar)
        self.search_bar.hide()  # Hidden by default
        
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
        self.view.verticalHeader().setDefaultSectionSize(24)  # Compact rows
        self.view.setAlternatingRowColors(True)  # Better readability
        self.view.setContextMenuPolicy(Qt.CustomContextMenu)  # type: ignore
        self.view.customContextMenuRequested.connect(self._show_context_menu)
        self.view.setSelectionMode(QTableView.ExtendedSelection)  # type: ignore
        self.view.setSelectionBehavior(QTableView.SelectRows)  # type: ignore
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
        
        # View options
        self.search_action = QAction("🔍 Search", self)
        self.search_action.setShortcut("Ctrl+F")
        self.search_action.setCheckable(True)
        self.search_action.setToolTip("Toggle search bar (Ctrl+F)")
        self.search_action.triggered.connect(self._toggle_search)
        toolbar.addAction(self.search_action)
        
        
        return toolbar
    
    def _create_search_bar(self) -> QWidget:
        """Create search/filter bar.
        
        Returns:
            QWidget with search controls
        """
        search_widget = QWidget()
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(5, 2, 5, 2)
        
        search_layout.addWidget(QLabel("Search:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to search in all columns...")
        self.search_input.textChanged.connect(self._filter_table)
        search_layout.addWidget(self.search_input)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(lambda: self.search_input.clear())
        search_layout.addWidget(clear_btn)
        
        close_btn = QPushButton("✖")
        close_btn.setFixedWidth(30)
        close_btn.clicked.connect(lambda: self._toggle_search(False))
        search_layout.addWidget(close_btn)
        
        return search_widget
    
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
        menu = QMenu(self.view)
        
        # Get clicked index
        index = self.view.indexAt(position)
        
        if index.isValid():
            # Cell context menu
            col_name = self.study.table.columns[index.column()]
            col_type = self.study.get_column_type(col_name)
            
            menu.addAction(f"Column: {col_name}").setEnabled(False)
            menu.addAction(f"Type: {col_type.upper()}").setEnabled(False)
            menu.addSeparator()
            
            # Column actions
            rename_action = menu.addAction("Rename Column")
            rename_action.triggered.connect(lambda: self._rename_column(index.column()))
            
            if col_type == ColumnType.CALCULATED:
                edit_action = menu.addAction("Edit Formula")
                edit_action.triggered.connect(lambda: self._edit_column(col_name))
            
            delete_col_action = menu.addAction("Delete Column")
            delete_col_action.triggered.connect(lambda: self._delete_column(col_name))
            
            # Convert column option (for non-DATA columns)
            if col_type != ColumnType.DATA:
                menu.addSeparator()
                convert_action = menu.addAction("Convert to DATA Column")
                convert_action.triggered.connect(self._convert_column_to_data)
            
            menu.addSeparator()
            
            # Row actions
            insert_row_action = menu.addAction("Insert Row Above")
            insert_row_action.triggered.connect(lambda: self._insert_row(index.row()))
            
            delete_row_action = menu.addAction("Delete This Row")
            delete_row_action.triggered.connect(lambda: self._delete_row(index.row()))
            
            menu.addSeparator()
            
            # Data operations
            copy_action = menu.addAction("Copy Cell")
            copy_action.setShortcut("Ctrl+C")
            copy_action.triggered.connect(lambda: self._copy_selection())
            
            if col_type == ColumnType.DATA:
                paste_action = menu.addAction("Paste")
                paste_action.setShortcut("Ctrl+V")
                paste_action.triggered.connect(lambda: self._paste_data())
        else:
            # General context menu
            add_row_action = menu.addAction("Add Row")
            add_row_action.triggered.connect(self._add_row)
            
            menu.addSeparator()
            
            resize_action = menu.addAction("Auto-resize Columns")
            resize_action.triggered.connect(self._auto_resize_columns)
        
        menu.exec(self.view.viewport().mapToGlobal(position))
    
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
        # Simple implementation: add row at end then move data
        # TODO: Implement proper row insertion
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
        from PySide6.QtWidgets import QApplication
        
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
        from PySide6.QtWidgets import QApplication
        
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
    
    def _toggle_search(self, checked: Optional[bool] = None):
        """Toggle search bar visibility.
        
        Args:
            checked: Override toggle state (True=show, False=hide, None=toggle)
        """
        if checked is None:
            checked = self.search_action.isChecked()
        
        self.search_bar.setVisible(checked)
        self.search_action.setChecked(checked)
        
        if checked:
            self.search_input.setFocus()
        else:
            self.search_input.clear()
    
    def _filter_table(self, text: str):
        """Filter table rows based on search text.
        
        Args:
            text: Search text
        """
        # Simple implementation: hide rows that don't match
        if not text:
            # Show all rows
            for row in range(self.model.rowCount()):
                self.view.setRowHidden(row, False)
            return
        
        text_lower = text.lower()
        for row in range(self.model.rowCount()):
            match_found = False
            for col in range(self.model.columnCount()):
                index = self.model.index(row, col)
                value = self.model.data(index, Qt.DisplayRole)  # type: ignore
                if value and text_lower in str(value).lower():
                    match_found = True
                    break
            
            self.view.setRowHidden(row, not match_found)
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts for clipboard operations."""
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
    
    def _get_selected_cells(self) -> List[Tuple[int, int]]:
        """Get list of selected cells as (row, col) tuples.
        
        Returns:
            List of (row, col) tuples
        """
        selection = self.view.selectionModel().selectedIndexes()
        return [(index.row(), index.column()) for index in selection]
    
    def _on_copy(self):
        """Handle copy operation (Ctrl+C)."""
        selection = self._get_selected_cells()
        if not selection:
            return
        
        # Convert selection to TSV format
        tsv_data = self._selection_to_tsv(selection)
        if tsv_data:
            clipboard = QApplication.clipboard()
            clipboard.setText(tsv_data)
    
    def _selection_to_tsv(self, selection: List[Tuple[int, int]]) -> str:
        """Convert selection to TSV format.
        
        Args:
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
                if col < len(self.study.table.columns):
                    col_name = self.study.table.columns[col]
                    if col in cols_dict and row < len(self.study.table.data):
                        value = self.study.table.data[col_name].iloc[row]
                        values.append(str(value) if pd.notna(value) else "")
                    else:
                        values.append("")
            
            lines.append("\t".join(values))
        
        return "\n".join(lines)
    
    def _on_paste(self):
        """Handle paste operation (Ctrl+V)."""
        clipboard = QApplication.clipboard()
        tsv_data = clipboard.text()
        if not tsv_data:
            return
        
        selection = self._get_selected_cells()
        if not selection:
            return
        
        # Get top-left of selection
        start_row = min(row for row, col in selection)
        start_col = min(col for row, col in selection)
        
        # Parse and paste TSV data
        self._paste_tsv(tsv_data, start_row, start_col)
    
    def _paste_tsv(self, tsv_data: str, start_row: int, start_col: int):
        """Paste TSV data into table.
        
        Args:
            tsv_data: Tab-separated values
            start_row: Starting row
            start_col: Starting column
        """
        lines = tsv_data.strip().split('\n')
        errors = []
        
        for row_offset, line in enumerate(lines):
            values = line.split('\\t')
            for col_offset, value in enumerate(values):
                target_row = start_row + row_offset
                target_col = start_col + col_offset
                
                # Check bounds
                if target_row >= len(self.study.table.data):
                    continue
                if target_col >= len(self.study.table.columns):
                    continue
                
                col_name = self.study.table.columns[target_col]
                
                # Skip non-editable columns
                if col_name in self.study.column_metadata:
                    col_type = self.study.column_metadata[col_name].get("type", "data")
                    if col_type != ColumnType.DATA:
                        continue
                
                # Set value
                try:
                    if value.strip() == "":
                        self.study.table.data.loc[target_row, col_name] = pd.NA
                    else:
                        # Try to convert to appropriate type
                        try:
                            self.study.table.data.loc[target_row, col_name] = float(value)
                        except ValueError:
                            self.study.table.data.loc[target_row, col_name] = value
                except Exception as e:
                    errors.append(f"Row {target_row}, Col {col_name}: {str(e)}")
        
        # Recalculate formulas
        self.study.recalculate_all()
        
        # Refresh view
        self.model.layoutChanged.emit()  # type: ignore
        
        if errors:
            show_warning(self, "Paste Warnings", f"Some cells could not be pasted:\n" + "\n".join(errors[:5]))
    
    def _on_cut(self):
        """Handle cut operation (Ctrl+X)."""
        self._on_copy()
        self._on_delete()
    
    def _on_delete(self):
        """Handle delete operation (Del key)."""
        selection = self._get_selected_cells()
        if not selection:
            return
        
        # Clear selected cells
        for row, col in selection:
            if col >= len(self.study.table.columns):
                continue
            
            col_name = self.study.table.columns[col]
            
            # Skip non-editable columns
            if col_name in self.study.column_metadata:
                col_type = self.study.column_metadata[col_name].get("type", "data")
                if col_type != ColumnType.DATA:
                    continue
            
            # Clear value
            if row < len(self.study.table.data):
                self.study.table.data.loc[row, col_name] = pd.NA
        
        # Recalculate and refresh
        self.study.recalculate_all()
        self.model.layoutChanged.emit()  # type: ignore
    
    def _edit_column_properties(self, col_index: int):
        """Open dialog to edit column properties.
        
        Args:
            col_index: Column index
        """
        if col_index >= len(self.study.table.columns):
            return
        
        col_name = self.study.table.columns[col_index]
        col_meta = self.study.column_metadata.get(col_name, {})
        col_type = col_meta.get("type", "data")
        
        # Open appropriate dialog based on column type
        if col_type == ColumnType.DATA:
            self._edit_data_column(col_name)
        elif col_type == ColumnType.CALCULATED:
            self._edit_calculated_column(col_name)
        elif col_type == ColumnType.DERIVATIVE:
            self._edit_derivative_column(col_name)
        elif col_type == ColumnType.RANGE:
            self._edit_range_column(col_name)
    
    def _edit_data_column(self, col_name: str):
        """Edit data column properties.
        
        Args:
            col_name: Column name
        """
        # Future: Open dialog to edit column properties
        show_warning(self, "Edit Column", f"Column editing dialog for '{col_name}' coming soon!")
    
    def _edit_calculated_column(self, col_name: str):
        """Edit calculated column properties.
        
        Args:
            col_name: Column name
        """
        # Future: Open dialog to edit column properties
        show_warning(self, "Edit Column", f"Column editing dialog for '{col_name}' coming soon!")
    
    def _edit_derivative_column(self, col_name: str):
        """Edit derivative column properties.
        
        Args:
            col_name: Column name
        """
        # Future: Open dialog to edit column properties  
        show_warning(self, "Edit Column", f"Column editing dialog for '{col_name}' coming soon!")
    
    def _edit_range_column(self, col_name: str):
        """Edit range column properties.
        
        Args:
            col_name: Column name
        """
        # Future: Open dialog to edit column properties
        show_warning(self, "Edit Column", f"Column editing dialog for '{col_name}' coming soon!")
    
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
        
        # Confirm conversion
        if not confirm_action(
            self,
            "Convert Column",
            f"Convert '{col_name}' from {col_type.upper()} to DATA column?\\n\\n"
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
