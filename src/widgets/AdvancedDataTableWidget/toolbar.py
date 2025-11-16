"""
Toolbar for AdvancedDataTableWidget.

Provides toolbar buttons and actions for common table operations:
- Add/remove columns (data and calculated)
- Add/remove rows
- Clear all data
- Recalculate formulas
- Auto-resize columns
"""

from PySide6.QtWidgets import QToolBar, QToolButton, QMenu, QMessageBox, QInputDialog, QDialog
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Signal, Qt
from enum import Enum
from typing import Optional

from .models import AdvancedColumnType, AdvancedColumnDataType


class DataTableToolbar(QToolBar):
    """Toolbar for AdvancedDataTableWidget with common operations."""

    # Signals
    addDataColumnRequested = Signal()
    addCalculatedColumnRequested = Signal()
    clearAllRequested = Signal()
    recalculateRequested = Signal()

    def __init__(self, table_widget, parent=None):
        super().__init__("Data Table Tools", parent)
        self.table_widget = table_widget

        # Set toolbar properties
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.setMovable(True)
        self.setFloatable(True)

        self._setup_actions()
        self._setup_toolbar()

        # Connect to table signals
        self.table_widget.columnAdded.connect(self._on_column_added)
        self.table_widget.columnRemoved.connect(self._on_column_removed)

    def _setup_actions(self):
        """Setup all toolbar actions."""

        # Column management actions
        self.add_data_column_action = QAction("Add Data Column", self)
        self.add_data_column_action.setIcon(self._get_icon("add_column"))
        self.add_data_column_action.setToolTip("Add a new data column")
        self.add_data_column_action.triggered.connect(self._add_data_column)
        
        self.add_range_column_action = QAction("Add Range Column", self)
        self.add_range_column_action.setIcon(self._get_icon("range"))
        self.add_range_column_action.setToolTip("Add a data column with evenly spaced values")
        self.add_range_column_action.triggered.connect(self._add_range_column)

        self.add_calculated_column_action = QAction("Add Calculated Column", self)
        self.add_calculated_column_action.setIcon(self._get_icon("calculated"))
        self.add_calculated_column_action.setToolTip("Add a new calculated column with formula")
        self.add_calculated_column_action.triggered.connect(self._add_calculated_column)
        
        self.add_interpolation_column_action = QAction("Add Interpolation Column", self)
        self.add_interpolation_column_action.setIcon(self._get_icon("interpolation"))
        self.add_interpolation_column_action.setToolTip("Add a new interpolation column")
        self.add_interpolation_column_action.triggered.connect(self._add_interpolation_column)

        self.remove_column_action = QAction("Remove Column", self)
        self.remove_column_action.setIcon(self._get_icon("remove"))
        self.remove_column_action.setToolTip("Remove the selected column")
        self.remove_column_action.triggered.connect(self._remove_column)
        self.remove_column_action.setEnabled(False)

        # Row management actions
        self.add_row_action = QAction("Add Row", self)
        self.add_row_action.setIcon(self._get_icon("add_row"))
        self.add_row_action.setToolTip("Add a new row")
        self.add_row_action.triggered.connect(self._add_row)

        self.remove_row_action = QAction("Remove Row", self)
        self.remove_row_action.setIcon(self._get_icon("remove_row"))
        self.remove_row_action.setToolTip("Remove the last row")
        self.remove_row_action.triggered.connect(self._remove_row)
        self.remove_row_action.setEnabled(self.table_widget.rowCount() > 0)

        # Data operations
        self.clear_all_action = QAction("Clear All", self)
        self.clear_all_action.setIcon(self._get_icon("clear"))
        self.clear_all_action.setToolTip("Clear all data and columns")
        self.clear_all_action.triggered.connect(self._clear_all)

        self.recalculate_action = QAction("Recalculate", self)
        self.recalculate_action.setIcon(self._get_icon("recalculate"))
        self.recalculate_action.setToolTip("Recalculate all calculated columns")
        self.recalculate_action.triggered.connect(self._recalculate)

        # View actions
        self.resize_columns_action = QAction("Auto-resize Columns", self)
        self.resize_columns_action.setIcon(self._get_icon("resize"))
        self.resize_columns_action.setToolTip("Automatically resize columns to fit content")
        self.resize_columns_action.triggered.connect(self._resize_columns)

    def _setup_toolbar(self):
        """Setup the toolbar layout."""

        # Add column management
        self.addAction(self.add_data_column_action)
        self.addAction(self.add_range_column_action)
        self.addAction(self.add_calculated_column_action)
        self.addAction(self.add_interpolation_column_action)
        self.addAction(self.remove_column_action)
        self.addSeparator()

        # Add row management
        self.addAction(self.add_row_action)
        self.addAction(self.remove_row_action)
        self.addSeparator()

        # Add data operations
        self.addAction(self.clear_all_action)
        self.addAction(self.recalculate_action)
        self.addSeparator()

        # Add view operations
        self.addAction(self.resize_columns_action)

    def _get_icon(self, icon_name: str) -> QIcon:
        """Get icon for action (placeholder - would use actual icons in real implementation)."""
        # For now, return empty icon. In a real implementation, you'd load actual icons
        # from resources or use Qt's built-in icons
        return QIcon()

    def _add_data_column(self):
        """Add a new data column."""
        from .data_column_dialog import DataColumnEditorDialog
        
        # Open dialog in create mode (column_index=None)
        dialog = DataColumnEditorDialog(self, None, self.table_widget)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            results = dialog.get_results()
            try:
                # Create the column with the provided properties
                col_index = self.table_widget.addColumn(
                    header_label=results['diminutive'],
                    col_type=AdvancedColumnType.DATA,
                    data_type=AdvancedColumnDataType.NUMERICAL,
                    diminutive=results['diminutive'],
                    unit=results['unit'],
                    description=results['description']
                )
                
                # Handle uncertainty column if requested
                if results.get('enable_uncertainty', False):
                    self.table_widget.addUncertaintyColumn(col_index)
                
                self._show_status_message(f"Added data column '{results['diminutive']}'")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to add column: {str(e)}")
    
    def _add_range_column(self):
        """Add a data column with a range of values."""
        from .range_dialog import RangeColumnDialog
        
        dialog = RangeColumnDialog(self, self.table_widget)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            results = dialog.get_results()
            try:
                # Add the range column
                col_index = self.table_widget.addRangeColumn(
                    header_label=results['diminutive'],
                    start=results['start'],
                    end=results['end'],
                    points=results['points'],
                    diminutive=results['diminutive'],
                    unit=results['unit'],
                    description=results['description']
                )
                self._show_status_message(
                    f"Added range column '{results['diminutive']}' "
                    f"({results['points']} points from {results['start']} to {results['end']})"
                )
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to add range column: {str(e)}")

    def _add_calculated_column(self):
        """Add a new calculated column."""
        from .formula_dialog import FormulaEditorDialog
        
        # Open formula editor dialog in create mode (column_index=None)
        dialog = FormulaEditorDialog(self, None, self.table_widget)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            results = dialog.get_results()
            try:
                # Create the calculated column
                col_index = self.table_widget.addCalculatedColumn(
                    header_label=results['diminutive'],
                    formula=results['formula'],
                    diminutive=results['diminutive'],
                    description=results['description'],
                    propagate_uncertainty=results['propagate_uncertainty']
                )
                self._show_status_message(f"Added calculated column '{results['diminutive']}'")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to add calculated column: {str(e)}")
    
    def _add_interpolation_column(self):
        """Add a new interpolation column."""
        from .interpolation_dialog import InterpolationDialog
        
        # Open interpolation dialog in create mode (column_index=None)
        dialog = InterpolationDialog(self, self.table_widget, None)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            results = dialog.get_results()
            try:
                # Create the interpolation column
                col_index = self.table_widget.addInterpolationColumn(
                    header_label=results['diminutive'],
                    interpolation_x_column=results['interpolation_x_column'],
                    interpolation_y_column=results['interpolation_y_column'],
                    interpolation_method=results['interpolation_method'],
                    diminutive=results['diminutive'],
                    unit=results['unit'],
                    description=results['description']
                )
                self._show_status_message(f"Added interpolation column '{results['diminutive']}'")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to add interpolation column: {str(e)}")

    def _remove_column(self):
        """Remove the currently selected column."""
        current_column = self.table_widget.currentColumn()
        if current_column < 0:
            QMessageBox.information(self, "No Selection", "Please select a column to remove.")
            return

        # Get column name for confirmation
        header_item = self.table_widget.horizontalHeaderItem(current_column)
        col_name = header_item.text() if header_item else f"Column {current_column}"

        # Confirm removal
        reply = QMessageBox.question(
            self, "Remove Column",
            f"Are you sure you want to remove the column '{col_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.table_widget.removeColumn(current_column):
                    self._show_status_message(f"Removed column '{col_name}'")
                else:
                    QMessageBox.warning(self, "Error", "Failed to remove column.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to remove column: {str(e)}")

    def _add_row(self):
        """Add a new row."""
        try:
            row_count = self.table_widget.rowCount()
            self.table_widget.insertRow(row_count)
            self._show_status_message("Added new row")
            self.remove_row_action.setEnabled(True)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to add row: {str(e)}")

    def _remove_row(self):
        """Remove the last row."""
        if self.table_widget.rowCount() == 0:
            return

        # Confirm removal
        reply = QMessageBox.question(
            self, "Remove Row",
            "Are you sure you want to remove the last row?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                last_row = self.table_widget.rowCount() - 1
                self.table_widget.removeRow(last_row)
                self._show_status_message("Removed last row")
                self.remove_row_action.setEnabled(self.table_widget.rowCount() > 0)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to remove row: {str(e)}")

    def _clear_all(self):
        """Clear all data."""
        reply = QMessageBox.question(
            self, "Clear All Data",
            "Are you sure you want to clear all data and columns?\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.table_widget.clear()
                self.table_widget.setRowCount(0)
                self.table_widget.setColumnCount(0)
                self._show_status_message("All data cleared")
                self.remove_row_action.setEnabled(False)
                self.remove_column_action.setEnabled(False)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to clear data: {str(e)}")

    def _recalculate(self):
        """Recalculate all calculated columns."""
        try:
            self.table_widget.recalculateAll()
            # Count calculated columns
            calculated_count = sum(1 for i in range(self.table_widget.columnCount())
                                 if self.table_widget.getColumnType(i) == AdvancedColumnType.CALCULATED)
            self._show_status_message(f"Recalculated {calculated_count} calculated column(s)")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to recalculate: {str(e)}")

    def _resize_columns(self):
        """Auto-resize columns to fit content."""
        try:
            self.table_widget.resizeColumnsToContents()
            self._show_status_message("Columns resized to fit content")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to resize columns: {str(e)}")

    def _on_column_added(self, col_index: int, header: str, col_type: AdvancedColumnType, data_type: AdvancedColumnDataType):
        """Handle column added signal."""
        self.remove_column_action.setEnabled(self.table_widget.columnCount() > 0)

    def _on_column_removed(self, col_index: int):
        """Handle column removed signal."""
        self.remove_column_action.setEnabled(self.table_widget.columnCount() > 0)

    def _show_status_message(self, message: str):
        """Show a status message (would connect to main window status bar in real implementation)."""
        print(f"Status: {message}")
        # In a real implementation, this would emit a signal to the main window
        # self.statusMessage.emit(message)
