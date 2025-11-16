"""
Context menu for AdvancedDataTableWidget.

Provides right-click menu options for column operations including:
- Edit column properties (including uncertainty settings)
- Add calculated columns
- Add derivative columns
- Remove columns
- Copy header text
- Manage variables
- Copy cell values and selections
- Convert calculated columns to data columns
"""

from PySide6.QtWidgets import QMenu, QDialog, QMessageBox, QApplication
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from .models import AdvancedColumnType, AdvancedColumnDataType


class HeaderContextMenu(QMenu):
    """Context menu for table header (column operations)."""

    def __init__(self, table_widget, column_index, parent=None):
        super().__init__(parent)
        self.table = table_widget
        self.col = column_index
        
        if self.col < 0 or self.col >= len(self.table._columns):
            return
        
        metadata = self.table._columns[self.col]

        # Edit Column
        edit_act = QAction("Edit Column...", self)
        edit_act.triggered.connect(lambda: self.table.edit_header(self.col))
        self.addAction(edit_act)
        
        self.addSeparator()
        
        # Convert to DATA (only for CALCULATED, DERIVATIVE, INTERPOLATION, RANGE)
        if metadata.column_type in [AdvancedColumnType.CALCULATED, 
                                     AdvancedColumnType.DERIVATIVE,
                                     AdvancedColumnType.INTERPOLATION,
                                     AdvancedColumnType.RANGE]:
            convert_act = QAction("Convert to Data Column", self)
            convert_act.triggered.connect(self._convert_to_data)
            self.addAction(convert_act)
            self.addSeparator()

        # Add columns based on this column
        add_calc = QAction("Add Calculated Column...", self)
        add_calc.triggered.connect(self._add_calculated_column)
        self.addAction(add_calc)
        
        add_deriv = QAction("Add Derivative Column...", self)
        add_deriv.triggered.connect(self._add_derivative_column)
        self.addAction(add_deriv)
        
        add_interp = QAction("Add Interpolation Column...", self)
        add_interp.triggered.connect(self._add_interpolation_column)
        self.addAction(add_interp)

        self.addSeparator()
        
        # Copy header
        copy_act = QAction("Copy Header Text", self)
        copy_act.triggered.connect(self._copy_header)
        self.addAction(copy_act)
        
        self.addSeparator()

        # Remove column
        remove_act = QAction("Delete Column", self)
        remove_act.triggered.connect(self._remove_column)
        self.addAction(remove_act)
        
        self.addSeparator()
        
        # Manage variables (table-wide action)
        manage_vars = QAction("Manage Variables...", self)
        manage_vars.triggered.connect(self._manage_variables)
        self.addAction(manage_vars)

    def _convert_to_data(self):
        """Convert this column to a DATA column, preserving current values."""
        if hasattr(self.table, 'convert_column_to_data'):
            self.table.convert_column_to_data(self.col)

    def _add_calculated_column(self):
        """Open the formula editor dialog to create a calculated column."""
        from .formula_dialog import FormulaEditorDialog
        
        dialog = FormulaEditorDialog(self.table, None, self.table)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            results = dialog.get_results()
            try:
                self.table.addCalculatedColumn(
                    header_label=results['diminutive'],
                    formula=results['formula'],
                    diminutive=results['diminutive'],
                    description=results['description'],
                    propagate_uncertainty=results['propagate_uncertainty']
                )
            except Exception as e:
                QMessageBox.warning(self.table, "Error", str(e))
    
    def _add_derivative_column(self):
        """Open the derivative column dialog."""
        from .derivative_dialog import DerivativeEditorDialog
        
        dialog = DerivativeEditorDialog(self.table, None, self.table)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            results = dialog.get_results()
            try:
                self.table.addDerivativeColumn(
                    header_label=results['diminutive'],
                    numerator_index=results['numerator_index'],
                    denominator_index=results['denominator_index'],
                    diminutive=results['diminutive'],
                    unit=results['unit'],
                    description=results['description']
                )
            except Exception as e:
                QMessageBox.warning(self.table, "Error", str(e))
    
    def _add_interpolation_column(self):
        """Open the interpolation column dialog."""
        from .interpolation_dialog import InterpolationDialog
        
        dialog = InterpolationDialog(self.table, self.table, None)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            results = dialog.get_results()
            try:
                self.table.addInterpolationColumn(
                    header_label=results['diminutive'],
                    interpolation_x_column=results['interpolation_x_column'],
                    interpolation_y_column=results['interpolation_y_column'],
                    interpolation_method=results['interpolation_method'],
                    diminutive=results['diminutive'],
                    unit=results['unit'],
                    description=results['description']
                )
            except Exception as e:
                QMessageBox.warning(self.table, "Error", str(e))

    def _remove_column(self):
        """Remove the column after confirmation."""
        header = self.table.getColumnDiminutive(self.col) or f"Column {self.col}"
        reply = QMessageBox.question(
            self.table, "Delete Column",
            f"Delete column '{header}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.table.removeColumn(self.col)

    def _copy_header(self):
        """Copy header text to clipboard."""
        header_item = self.table.horizontalHeaderItem(self.col)
        header = header_item.text() if header_item else ""
        QApplication.clipboard().setText(header)

    def _manage_variables(self):
        """Open the variables management dialog."""
        self.table.manage_variables()


class CellContextMenu(QMenu):
    """Context menu for table cells (data operations)."""

    def __init__(self, table_widget, row, column, parent=None):
        super().__init__(parent)
        self.table = table_widget
        self.row = row
        self.col = column
        
        # Copy cell value
        copy_cell_act = QAction("Copy Cell Value", self)
        copy_cell_act.triggered.connect(self._copy_cell)
        self.addAction(copy_cell_act)
        
        # Copy selection
        selected_ranges = self.table.selectedRanges()
        if selected_ranges:
            copy_selection_act = QAction("Copy Selection", self)
            copy_selection_act.triggered.connect(self._copy_selection)
            self.addAction(copy_selection_act)
        
        self.addSeparator()
        
        # Paste (only for editable cells)
        if self._is_cell_editable(self.row, self.col):
            paste_act = QAction("Paste", self)
            paste_act.triggered.connect(self._paste)
            self.addAction(paste_act)
        
        # Clear selection
        if selected_ranges:
            clear_act = QAction("Clear Selection", self)
            clear_act.triggered.connect(self._clear_selection)
            self.addAction(clear_act)

    def _is_cell_editable(self, row, col):
        """Check if a cell can be edited (DATA or UNCERTAINTY columns only)."""
        if col < 0 or col >= len(self.table._columns):
            return False
        metadata = self.table._columns[col]
        return metadata.column_type in [AdvancedColumnType.DATA, AdvancedColumnType.UNCERTAINTY]

    def _copy_cell(self):
        """Copy the current cell value to clipboard."""
        item = self.table.item(self.row, self.col)
        if item:
            QApplication.clipboard().setText(item.text())

    def _copy_selection(self):
        """Copy selected cells to clipboard in tab-delimited format."""
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            return
        
        # Get the bounding box of all selections
        min_row = min(r.topRow() for r in selected_ranges)
        max_row = max(r.bottomRow() for r in selected_ranges)
        min_col = min(r.leftColumn() for r in selected_ranges)
        max_col = max(r.rightColumn() for r in selected_ranges)
        
        # Build clipboard text
        lines = []
        for row in range(min_row, max_row + 1):
            row_data = []
            for col in range(min_col, max_col + 1):
                item = self.table.item(row, col)
                row_data.append(item.text() if item else "")
            lines.append("\t".join(row_data))
        
        QApplication.clipboard().setText("\n".join(lines))

    def _paste(self):
        """Paste clipboard content to selected cells."""
        clipboard_text = QApplication.clipboard().text()
        if not clipboard_text:
            return
        
        # Parse clipboard (tab-delimited, newline-separated)
        lines = clipboard_text.strip().split("\n")
        data = [line.split("\t") for line in lines]
        
        # Start from current cell
        start_row = self.row
        start_col = self.col
        
        # Paste data
        from PySide6.QtWidgets import QTableWidgetItem
        for row_offset, row_data in enumerate(data):
            for col_offset, value in enumerate(row_data):
                target_row = start_row + row_offset
                target_col = start_col + col_offset
                
                # Check bounds
                if target_row >= self.table.rowCount() or target_col >= self.table.columnCount():
                    continue
                
                # Only paste to editable cells
                if self._is_cell_editable(target_row, target_col):
                    item = self.table.item(target_row, target_col)
                    if not item:
                        item = QTableWidgetItem(value)
                        self.table.setItem(target_row, target_col, item)
                    else:
                        item.setText(value)

    def _clear_selection(self):
        """Clear all selected cells (only editable ones)."""
        selected_ranges = self.table.selectedRanges()
        for selected_range in selected_ranges:
            for row in range(selected_range.topRow(), selected_range.bottomRow() + 1):
                for col in range(selected_range.leftColumn(), selected_range.rightColumn() + 1):
                    if self._is_cell_editable(row, col):
                        item = self.table.item(row, col)
                        if item:
                            item.setText("")


class EmptyTableContextMenu(QMenu):
    """Context menu for empty areas of the table (table-wide operations)."""

    def __init__(self, table_widget, parent=None):
        super().__init__(parent)
        self.table = table_widget
        
        # Add Data Column
        add_data_act = QAction("Add Data Column...", self)
        add_data_act.triggered.connect(self._add_data_column)
        self.addAction(add_data_act)
        
        # Add Range Column
        add_range_act = QAction("Add Range Column...", self)
        add_range_act.triggered.connect(self._add_range_column)
        self.addAction(add_range_act)
        
        # Add Calculated Column
        add_calc_act = QAction("Add Calculated Column...", self)
        add_calc_act.triggered.connect(self._add_calculated_column)
        self.addAction(add_calc_act)
        
        # Add Derivative Column
        add_deriv_act = QAction("Add Derivative Column...", self)
        add_deriv_act.triggered.connect(self._add_derivative_column)
        self.addAction(add_deriv_act)
        
        # Add Interpolation Column
        add_interp_act = QAction("Add Interpolation Column...", self)
        add_interp_act.triggered.connect(self._add_interpolation_column)
        self.addAction(add_interp_act)
        
        self.addSeparator()
        
        # Manage Variables
        manage_vars_act = QAction("Manage Variables...", self)
        manage_vars_act.triggered.connect(self._manage_variables)
        self.addAction(manage_vars_act)

    def _add_data_column(self):
        """Add a new data column."""
        from .data_column_dialog import DataColumnEditorDialog
        
        dialog = DataColumnEditorDialog(self.table, None, self.table)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            results = dialog.get_results()
            try:
                col_index = self.table.addColumn(
                    header_label=results['diminutive'],
                    col_type=AdvancedColumnType.DATA,
                    data_type=AdvancedColumnDataType.NUMERICAL,
                    diminutive=results['diminutive'],
                    unit=results['unit'],
                    description=results['description']
                )
                # If uncertainty propagation is enabled, create uncertainty column
                if results.get('propagate_uncertainty', False):
                    self.table.addUncertaintyColumn(col_index)
            except Exception as e:
                QMessageBox.warning(self.table, "Error", str(e))

    def _add_range_column(self):
        """Add a new range column."""
        from .range_dialog import RangeColumnDialog
        
        dialog = RangeColumnDialog(self.table, self.table)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            results = dialog.get_results()
            try:
                self.table.addRangeColumn(
                    header_label=results['diminutive'],
                    start=results['start'],
                    end=results['end'],
                    points=results['points'],
                    diminutive=results['diminutive'],
                    unit=results['unit'],
                    description=results['description']
                )
            except Exception as e:
                QMessageBox.warning(self.table, "Error", str(e))

    def _add_calculated_column(self):
        """Add a new calculated column."""
        from .formula_dialog import FormulaEditorDialog
        
        dialog = FormulaEditorDialog(self.table, None, self.table)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            results = dialog.get_results()
            try:
                self.table.addCalculatedColumn(
                    header_label=results['diminutive'],
                    formula=results['formula'],
                    diminutive=results['diminutive'],
                    description=results['description'],
                    propagate_uncertainty=results['propagate_uncertainty']
                )
            except Exception as e:
                QMessageBox.warning(self.table, "Error", str(e))

    def _add_derivative_column(self):
        """Add a new derivative column."""
        from .derivative_dialog import DerivativeEditorDialog
        
        dialog = DerivativeEditorDialog(self.table, None, self.table)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            results = dialog.get_results()
            try:
                self.table.addDerivativeColumn(
                    header_label=results['diminutive'],
                    numerator_index=results['numerator_index'],
                    denominator_index=results['denominator_index'],
                    diminutive=results['diminutive'],
                    unit=results['unit'],
                    description=results['description']
                )
            except Exception as e:
                QMessageBox.warning(self.table, "Error", str(e))

    def _add_interpolation_column(self):
        """Add a new interpolation column."""
        from .interpolation_dialog import InterpolationDialog
        
        dialog = InterpolationDialog(self.table, self.table, None)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            results = dialog.get_results()
            try:
                self.table.addInterpolationColumn(
                    header_label=results['diminutive'],
                    interpolation_x_column=results['interpolation_x_column'],
                    interpolation_y_column=results['interpolation_y_column'],
                    interpolation_method=results['interpolation_method'],
                    diminutive=results['diminutive'],
                    unit=results['unit'],
                    description=results['description']
                )
            except Exception as e:
                QMessageBox.warning(self.table, "Error", str(e))

    def _manage_variables(self):
        """Open variables management dialog."""
        self.table.manage_variables()




# Legacy class for backward compatibility (redirects to HeaderContextMenu)
class DataTableContextMenu(HeaderContextMenu):
    """Legacy context menu - use HeaderContextMenu instead.
    
    Maintained for backward compatibility with existing code.
    """
    pass
