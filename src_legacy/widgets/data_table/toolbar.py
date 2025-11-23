"""Toolbar for DataTableV2.

Provides toolbar buttons and actions for common table operations.
"""

from PySide6.QtWidgets import QToolBar, QToolButton, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .view import DataTableView


class DataTableToolbar(QToolBar):
    """Toolbar for DataTableView with common operations."""

    def __init__(self, view: 'DataTableView', parent=None):
        super().__init__("Data Table Tools", parent)
        self.view = view

        # Set toolbar properties
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.setMovable(True)
        self.setFloatable(True)

        self._setup_toolbar()

    def _setup_toolbar(self):
        """Setup toolbar actions and buttons."""
        
        # Add Column dropdown button
        add_column_btn = QToolButton()
        add_column_btn.setText("Add Column")
        add_column_btn.setToolTip("Add a new column of any type")
        
        add_column_menu = QMenu(add_column_btn)
        
        add_data_action = QAction("Data Column...", add_column_btn)
        add_data_action.setToolTip("Add a new data column")
        add_data_action.triggered.connect(self.view._show_add_data_column_dialog)
        add_column_menu.addAction(add_data_action)
        
        add_range_action = QAction("Range Column...", add_column_btn)
        add_range_action.setToolTip("Add a column with evenly spaced values")
        add_range_action.triggered.connect(self.view._show_add_range_column_dialog)
        add_column_menu.addAction(add_range_action)
        
        add_calc_action = QAction("Calculated Column...", add_column_btn)
        add_calc_action.setToolTip("Add a calculated column with formula")
        add_calc_action.triggered.connect(self.view._show_add_calculated_column_dialog)
        add_column_menu.addAction(add_calc_action)
        
        add_deriv_action = QAction("Derivative Column...", add_column_btn)
        add_deriv_action.setToolTip("Add a derivative (dy/dx) column")
        add_deriv_action.triggered.connect(self.view._show_add_derivative_column_dialog)
        add_column_menu.addAction(add_deriv_action)
        
        add_interp_action = QAction("Interpolation Column...", add_column_btn)
        add_interp_action.setToolTip("Add an interpolation column")
        add_interp_action.triggered.connect(self.view._show_add_interpolation_column_dialog)
        add_column_menu.addAction(add_interp_action)
        
        add_uncertainty_action = QAction("Uncertainty Column...", add_column_btn)
        add_uncertainty_action.setToolTip("Add a manual uncertainty column")
        add_uncertainty_action.triggered.connect(self.view._show_add_uncertainty_column_dialog)
        add_column_menu.addAction(add_uncertainty_action)
        
        add_column_btn.setMenu(add_column_menu)
        add_column_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.addWidget(add_column_btn)
        
        self.addSeparator()
        
        # Add Row action
        add_row_action = QAction("Add Row", self)
        add_row_action.setToolTip("Add a new row at the end")
        add_row_action.triggered.connect(self._add_row)
        self.addAction(add_row_action)
        
        self.addSeparator()
        
        # Variables action
        variables_action = QAction("Variables...", self)
        variables_action.setToolTip("Manage global constants (g, pi, etc.)")
        variables_action.triggered.connect(self.view._show_variables_dialog)
        self.addAction(variables_action)
        
        self.addSeparator()
        
        # Auto-resize columns action
        resize_action = QAction("Auto-resize", self)
        resize_action.setToolTip("Auto-resize all columns to fit content")
        resize_action.triggered.connect(self._auto_resize_columns)
        self.addAction(resize_action)
        
        # Add stretch to push everything to the left
        spacer = QToolButton()
        spacer.setEnabled(False)
        spacer.setSizePolicy(
            spacer.sizePolicy().horizontalPolicy(),
            spacer.sizePolicy().verticalPolicy()
        )
        self.addWidget(spacer)
    
    def _add_row(self):
        """Add a new row at the end of the table."""
        if self.view._data_model:
            row_count = self.view._data_model.rowCount()
            self.view._data_model.insertRows(row_count, 1)
    
    def _auto_resize_columns(self):
        """Auto-resize all columns to fit content."""
        self.view.resizeColumnsToContents()
