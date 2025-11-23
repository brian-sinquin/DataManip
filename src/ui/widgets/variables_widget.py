"""
Variables widget for managing workspace-level constants.

Provides a dedicated tab for viewing and editing global variables
that can be used across all studies.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLineEdit, QLabel, QToolBar
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from typing import Dict, Tuple, Optional

from .shared.dialog_utils import show_warning, show_info, confirm_action


class VariablesWidget(QWidget):
    """Widget for managing workspace variables.
    
    Features:
    - Table view of all variables
    - Add/remove/edit variables
    - Variables are workspace-level (shared across studies)
    
    Signals:
        variables_changed: Emitted when variables are modified
    """
    
    variables_changed = Signal()
    
    def __init__(self, workspace, parent=None):
        """Initialize widget.
        
        Args:
            workspace: Workspace containing variables
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.workspace = workspace
        
        # Setup UI
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # Description
        desc = QLabel(
            "Global variables available to all studies. "
            "Use {variable_name} in formulas."
        )
        desc.setWordWrap(True)
        # Use default Qt styling
        layout.addWidget(desc)
        
        # Variables table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "Value", "Unit"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)
        
        # Add variable controls
        add_layout = QHBoxLayout()
        add_layout.addWidget(QLabel("Add Variable:"))
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Name (e.g., g, pi, m)")
        add_layout.addWidget(self.name_input)
        
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("Value (e.g., 9.81)")
        add_layout.addWidget(self.value_input)
        
        self.unit_input = QLineEdit()
        self.unit_input.setPlaceholderText("Unit (optional)")
        add_layout.addWidget(self.unit_input)
        
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_variable)
        add_layout.addWidget(add_btn)
        
        layout.addLayout(add_layout)
        
        # Load existing variables
        self._load_variables()
    
    def _create_toolbar(self) -> QToolBar:
        """Create toolbar.
        
        Returns:
            QToolBar instance
        """
        toolbar = QToolBar()
        
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self._load_variables)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        remove_action = QAction("Remove Selected", self)
        remove_action.triggered.connect(self._remove_selected)
        toolbar.addAction(remove_action)
        
        clear_action = QAction("Clear All", self)
        clear_action.triggered.connect(self._clear_all)
        toolbar.addAction(clear_action)
        
        toolbar.addSeparator()
        
        common_action = QAction("Add Common Constants", self)
        common_action.triggered.connect(self._add_common_constants)
        toolbar.addAction(common_action)
        
        return toolbar
    
    def _load_variables(self):
        """Load variables from workspace into table."""
        self.table.setRowCount(0)
        
        # Load from workspace constants (only constant type)
        all_vars = {name: (data["value"], data.get("unit"))
                    for name, data in self.workspace.constants.items()
                    if data.get("type") == "constant"}
        
        # Populate table
        for name, (value, unit) in sorted(all_vars.items()):
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(str(value)))
            self.table.setItem(row, 2, QTableWidgetItem(unit or ""))
            
            # Make cells editable
            for col in range(3):
                item = self.table.item(row, col)
                item.setFlags(item.flags() | Qt.ItemIsEditable)
        
        # Connect cell changed signal
        self.table.cellChanged.connect(self._on_cell_changed)
    
    def _add_variable(self):
        """Add new variable."""
        name = self.name_input.text().strip()
        value_str = self.value_input.text().strip()
        unit = self.unit_input.text().strip() or None
        
        if not name:
            show_warning(self, "Error", "Variable name is required")
            return
        
        if not value_str:
            show_warning(self, "Error", "Variable value is required")
            return
        
        try:
            value = float(value_str)
        except ValueError:
            show_warning(self, "Error", "Value must be a number")
            return
        
        # Add to workspace constants
        self.workspace.add_constant(name, value, unit)
        
        # Clear inputs
        self.name_input.clear()
        self.value_input.clear()
        self.unit_input.clear()
        
        # Reload table
        self._load_variables()
        
        # Notify
        self.variables_changed.emit()
        self.statusBar().showMessage(f"Added variable '{name}'") if hasattr(self, 'statusBar') else None
    
    def _remove_selected(self):
        """Remove selected variable."""
        current_row = self.table.currentRow()
        if current_row < 0:
            show_warning(self, "Error", "No variable selected")
            return
        
        name = self.table.item(current_row, 0).text()
        
        if confirm_action(
            self,
            "Remove Variable",
            f"Remove variable '{name}'?"
        ):
            # Remove from workspace
            if name in self.workspace.constants:
                del self.workspace.constants[name]
            
            # Reload table
            self._load_variables()
            
            # Notify
            self.variables_changed.emit()
    
    def _clear_all(self):
        """Clear all variables."""
        if confirm_action(
            self,
            "Clear All Variables",
            "Remove all variables?"
        ):
            # Clear workspace constants (only constant type)
            const_names = [name for name, data in self.workspace.constants.items()
                          if data.get("type") == "constant"]
            for name in const_names:
                del self.workspace.constants[name]
            
            # Reload table
            self._load_variables()
            
            # Notify
            self.variables_changed.emit()
    
    def _add_common_constants(self):
        """Add common physics/math constants."""
        constants = {
            "g": (9.81, "m/s^2"),
            "pi": (3.14159265359, None),
            "e": (2.71828182846, None),
            "c": (299792458, "m/s"),
            "h": (6.62607015e-34, "J·s"),
            "k_B": (1.380649e-23, "J/K"),
        }
        
        # Add to workspace
        for name, (value, unit) in constants.items():
            self.workspace.add_constant(name, value, unit)
        
        self._load_variables()
        self.variables_changed.emit()
        
        show_info(
            self,
            "Constants Added",
            f"Added {len(constants)} common constants:\n" +
            ", ".join(constants.keys())
        )
    
    def _on_cell_changed(self, row: int, col: int):
        """Handle cell edit.
        
        Args:
            row: Row index
            col: Column index
        """
        # Disconnect to avoid recursion
        self.table.cellChanged.disconnect(self._on_cell_changed)
        
        try:
            name = self.table.item(row, 0).text().strip()
            value_str = self.table.item(row, 1).text().strip()
            unit = self.table.item(row, 2).text().strip() or None
            
            if not name or not value_str:
                return
            
            try:
                value = float(value_str)
            except ValueError:
                show_warning(self, "Error", "Value must be a number")
                self._load_variables()  # Reset
                return
            
            # Update in workspace
            const_keys = [name for name, data in self.workspace.constants.items()
                         if data.get("type") == "constant"]
            old_name = const_keys[row] if row < len(const_keys) else None
            if old_name and old_name != name:
                del self.workspace.constants[old_name]
            self.workspace.add_constant(name, value, unit)
            
            # Notify
            self.variables_changed.emit()
        
        finally:
            # Reconnect
            self.table.cellChanged.connect(self._on_cell_changed)
