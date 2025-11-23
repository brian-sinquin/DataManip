"""
Constants & Functions widget for managing workspace-level values.

Supports three types:
1. Constants: Numeric values (e.g., g = 9.81 m/s^2)
2. Calculated Variables: Formula-based (e.g., v = sqrt(2*g*h))
3. Functions: Named, parameterized (e.g., f(x, y) = x^2 + y^2)
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLineEdit, QLabel, QToolBar, QComboBox,
    QDialog, QDialogButtonBox, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from typing import Dict, Any, Optional

from constants import (
    DIALOG_CONSTANTS_WIDTH, DIALOG_CONSTANTS_HEIGHT,
    FORMULA_INPUT_MAX_HEIGHT
)
from .shared.dialog_utils import show_warning, show_info, confirm_action


class AddConstantDialog(QDialog):
    """Dialog for adding/editing constants, variables, or functions."""
    
    def __init__(self, parent=None, edit_mode=False, existing_data=None):
        """Initialize dialog.
        
        Args:
            parent: Parent widget
            edit_mode: True if editing existing entry
            existing_data: Existing constant data (for edit mode)
        """
        super().__init__(parent)
        
        self.setWindowTitle("Edit Constant" if edit_mode else "Add Constant")
        self.resize(DIALOG_CONSTANTS_WIDTH, DIALOG_CONSTANTS_HEIGHT)
        
        layout = QVBoxLayout(self)
        
        # Type selector
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Constant", "Calculated Variable", "Function"])
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)
        
        # Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., g, velocity, distance")
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Value (for constants)
        self.value_layout = QHBoxLayout()
        self.value_layout.addWidget(QLabel("Value:"))
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("e.g., 9.81")
        self.value_layout.addWidget(self.value_input)
        layout.addLayout(self.value_layout)
        
        # Formula (for calculated variables and functions)
        self.formula_widget = QWidget()
        formula_layout = QVBoxLayout(self.formula_widget)
        formula_layout.setContentsMargins(0, 0, 0, 0)
        formula_layout.addWidget(QLabel("Formula:"))
        self.formula_input = QTextEdit()
        self.formula_input.setPlaceholderText(
            "Examples:\n"
            "  Calculated: 2 * pi * r\n"
            "  Function: x^2 + y^2"
        )
        self.formula_input.setMaximumHeight(100)
        formula_layout.addWidget(self.formula_input)
        layout.addWidget(self.formula_widget)
        self.formula_widget.hide()
        
        # Parameters (for functions)
        self.params_widget = QWidget()
        params_layout = QVBoxLayout(self.params_widget)
        params_layout.setContentsMargins(0, 0, 0, 0)
        params_layout.addWidget(QLabel("Parameters (comma-separated):"))
        self.params_input = QLineEdit()
        self.params_input.setPlaceholderText("e.g., x, y, z")
        params_layout.addWidget(self.params_input)
        layout.addWidget(self.params_widget)
        self.params_widget.hide()
        
        # Unit
        unit_layout = QHBoxLayout()
        unit_layout.addWidget(QLabel("Unit:"))
        self.unit_input = QLineEdit()
        self.unit_input.setPlaceholderText("Optional (e.g., m/s, kg)")
        unit_layout.addWidget(self.unit_input)
        layout.addLayout(unit_layout)
        
        # Help text
        self.help_label = QLabel()
        self.help_label.setWordWrap(True)
        # Use default Qt styling
        layout.addWidget(self.help_label)
        self._update_help_text()
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Load existing data
        if edit_mode and existing_data:
            self._load_data(existing_data)
    
    def _on_type_changed(self):
        """Handle type selection change."""
        const_type = self.type_combo.currentText()
        
        # Show/hide appropriate fields
        if const_type == "Constant":
            self.value_layout.setEnabled(True)
            self.value_input.setEnabled(True)
            self.formula_widget.hide()
            self.params_widget.hide()
        elif const_type == "Calculated Variable":
            self.value_layout.setEnabled(False)
            self.value_input.setEnabled(False)
            self.formula_widget.show()
            self.params_widget.hide()
        else:  # Function
            self.value_layout.setEnabled(False)
            self.value_input.setEnabled(False)
            self.formula_widget.show()
            self.params_widget.show()
        
        self._update_help_text()
    
    def _update_help_text(self):
        """Update help text based on type."""
        const_type = self.type_combo.currentText()
        
        if const_type == "Constant":
            text = "Define a numeric constant value."
        elif const_type == "Calculated Variable":
            text = "Define a variable calculated from a formula. Can reference other constants."
        else:  # Function
            text = "Define a custom function with parameters. Can be called from formulas."
        
        self.help_label.setText(text)
    
    def _load_data(self, data: Dict[str, Any]):
        """Load existing data for editing."""
        self.name_input.setText(data.get("name", ""))
        
        const_type = data.get("type", "constant")
        if const_type == "constant":
            self.type_combo.setCurrentText("Constant")
            self.value_input.setText(str(data.get("value", "")))
        elif const_type == "calculated":
            self.type_combo.setCurrentText("Calculated Variable")
            self.formula_input.setPlainText(data.get("formula", ""))
        else:  # function
            self.type_combo.setCurrentText("Function")
            self.formula_input.setPlainText(data.get("formula", ""))
            params = data.get("parameters", [])
            self.params_input.setText(", ".join(params))
        
        self.unit_input.setText(data.get("unit", "") or "")
    
    def get_data(self) -> Optional[Dict[str, Any]]:
        """Get dialog data.
        
        Returns:
            Dictionary with constant data or None if invalid
        """
        name = self.name_input.text().strip()
        if not name:
            show_warning(self, "Error", "Name is required")
            return None
        
        const_type = self.type_combo.currentText()
        unit = self.unit_input.text().strip() or None
        
        if const_type == "Constant":
            value_str = self.value_input.text().strip()
            if not value_str:
                show_warning(self, "Error", "Value is required")
                return None
            try:
                value = float(value_str)
            except ValueError:
                show_warning(self, "Error", "Value must be a number")
                return None
            
            return {
                "name": name,
                "type": "constant",
                "value": value,
                "unit": unit
            }
        
        elif const_type == "Calculated Variable":
            formula = self.formula_input.toPlainText().strip()
            if not formula:
                show_warning(self, "Error", "Formula is required")
                return None
            
            return {
                "name": name,
                "type": "calculated",
                "formula": formula,
                "unit": unit
            }
        
        else:  # Function
            formula = self.formula_input.toPlainText().strip()
            if not formula:
                show_warning(self, "Error", "Formula is required")
                return None
            
            params_str = self.params_input.text().strip()
            if not params_str:
                show_warning(self, "Error", "Parameters are required")
                return None
            
            params = [p.strip() for p in params_str.split(",")]
            
            return {
                "name": name,
                "type": "function",
                "formula": formula,
                "parameters": params,
                "unit": unit
            }


class ConstantsWidget(QWidget):
    """Widget for managing workspace constants, variables, and functions.
    
    Features:
    - Table view of all constants/variables/functions
    - Add/remove/edit entries
    - Three types: constants, calculated variables, functions
    
    Signals:
        constants_changed: Emitted when constants are modified
    """
    
    constants_changed = Signal()
    
    def __init__(self, workspace, parent=None):
        """Initialize widget.
        
        Args:
            workspace: Workspace containing constants
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
        
        # Search bar
        self.search_bar = self._create_search_bar()
        layout.addWidget(self.search_bar)
        self.search_bar.hide()  # Hidden by default
        
        # Description
        desc = QLabel(
            "Define constants, calculated variables, and custom functions. "
            "Use {name} in formulas to reference them."
        )
        desc.setWordWrap(True)
        # Use default Qt styling
        layout.addWidget(desc)
        
        # Constants table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Type", "Name", "Value/Formula", "Parameters", "Unit"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.doubleClicked.connect(self._edit_selected)
        layout.addWidget(self.table)
        
        # Quick add button
        add_btn_layout = QHBoxLayout()
        add_btn_layout.addStretch()
        add_btn = QPushButton("Add New...")
        add_btn.clicked.connect(self._add_constant)
        add_btn_layout.addWidget(add_btn)
        layout.addLayout(add_btn_layout)
        
        # Load existing constants
        self._load_constants()
    
    def _create_toolbar(self) -> QToolBar:
        """Create toolbar.
        
        Returns:
            QToolBar instance
        """
        toolbar = QToolBar()
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)  # type: ignore
        
        # Add new
        add_action = QAction("Add", self)
        add_action.setShortcut("Ctrl+N")
        add_action.setToolTip("Add new constant, variable, or function (Ctrl+N)")
        add_action.triggered.connect(self._add_constant)
        toolbar.addAction(add_action)
        
        # Edit selected
        edit_action = QAction("Edit", self)
        edit_action.setShortcut("Ctrl+E")
        edit_action.setToolTip("Edit selected entry (Ctrl+E)")
        edit_action.triggered.connect(self._edit_selected)
        toolbar.addAction(edit_action)
        
        # Remove selected
        remove_action = QAction("Remove", self)
        remove_action.setShortcut("Delete")
        remove_action.setToolTip("Remove selected entry(ies) (Delete)")
        remove_action.triggered.connect(self._remove_selected)
        toolbar.addAction(remove_action)
        
        toolbar.addSeparator()
        
        # Search toggle
        self.search_action = QAction("🔍 Search", self)
        self.search_action.setShortcut("Ctrl+F")
        self.search_action.setCheckable(True)
        self.search_action.setToolTip("Toggle search bar (Ctrl+F)")
        self.search_action.triggered.connect(self._toggle_search)
        toolbar.addAction(self.search_action)
        
        # Refresh
        refresh_action = QAction("🔄 Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.setToolTip("Refresh table (F5)")
        refresh_action.triggered.connect(self._load_constants)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        # Common constants
        common_action = QAction("📊 Add Common", self)
        common_action.setToolTip("Add common physics/math constants (g, pi, e, etc.)")
        common_action.triggered.connect(self._add_common_constants)
        toolbar.addAction(common_action)
        
        # Clear all
        clear_action = QAction("🗑️ Clear All", self)
        clear_action.setToolTip("Remove all constants, variables, and functions")
        clear_action.triggered.connect(self._clear_all)
        toolbar.addAction(clear_action)
        
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
        if not text:
            # Show all rows
            for row in range(self.table.rowCount()):
                self.table.setRowHidden(row, False)
            return
        
        text_lower = text.lower()
        for row in range(self.table.rowCount()):
            match_found = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and text_lower in item.text().lower():
                    match_found = True
                    break
            
            self.table.setRowHidden(row, not match_found)
    
    def _load_constants(self):
        """Load constants from workspace into table."""
        self.table.setRowCount(0)
        
        # Get all constants
        all_constants = self.workspace.constants
        
        # Populate table
        for name, data in sorted(all_constants.items()):
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Type
            const_type = data.get("type", "constant")
            type_map = {
                "constant": "Constant",
                "calculated": "Calculated",
                "function": "Function"
            }
            type_item = QTableWidgetItem(type_map.get(const_type, "?"))
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, type_item)
            
            # Name
            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, name_item)
            
            # Value/Formula
            if const_type == "constant":
                value_str = str(data.get("value", ""))
            else:
                value_str = data.get("formula", "")
            value_item = QTableWidgetItem(value_str)
            value_item.setFlags(value_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, value_item)
            
            # Parameters
            params = data.get("parameters", [])
            params_item = QTableWidgetItem(", ".join(params) if params else "")
            params_item.setFlags(params_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 3, params_item)
            
            # Unit
            unit = data.get("unit", "")
            unit_item = QTableWidgetItem(unit or "")
            unit_item.setFlags(unit_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 4, unit_item)
    
    def _add_constant(self):
        """Add new constant."""
        dialog = AddConstantDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data:
                name = data["name"]
                const_type = data["type"]
                
                # Add to workspace
                if const_type == "constant":
                    self.workspace.add_constant(
                        name, data["value"], data.get("unit")
                    )
                elif const_type == "calculated":
                    self.workspace.add_calculated_variable(
                        name, data["formula"], data.get("unit")
                    )
                else:  # function
                    self.workspace.add_function(
                        name, data["formula"], data["parameters"], data.get("unit")
                    )
                
                # Reload table
                self._load_constants()
                
                # Notify
                self.constants_changed.emit()
    
    def _edit_selected(self):
        """Edit selected constant."""
        current_row = self.table.currentRow()
        if current_row < 0:
            show_warning(self, "Error", "No constant selected")
            return
        
        name = self.table.item(current_row, 1).text()
        data = self.workspace.get_constant_info(name)
        
        if not data:
            return
        
        # Prepare data for dialog
        edit_data = data.copy()
        edit_data["name"] = name
        
        dialog = AddConstantDialog(self, edit_mode=True, existing_data=edit_data)
        if dialog.exec() == QDialog.Accepted:
            new_data = dialog.get_data()
            if new_data:
                # Remove old
                self.workspace.remove_constant(name)
                
                # Add new
                new_name = new_data["name"]
                const_type = new_data["type"]
                
                if const_type == "constant":
                    self.workspace.add_constant(
                        new_name, new_data["value"], new_data.get("unit")
                    )
                elif const_type == "calculated":
                    self.workspace.add_calculated_variable(
                        new_name, new_data["formula"], new_data.get("unit")
                    )
                else:  # function
                    self.workspace.add_function(
                        new_name, new_data["formula"], new_data["parameters"], new_data.get("unit")
                    )
                
                # Reload table
                self._load_constants()
                
                # Notify
                self.constants_changed.emit()
    
    def _remove_selected(self):
        """Remove selected constant."""
        current_row = self.table.currentRow()
        if current_row < 0:
            show_warning(self, "Error", "No constant selected")
            return
        
        name = self.table.item(current_row, 1).text()
        
        if confirm_action(
            self,
            "Remove Constant",
            f"Remove '{name}'?"
        ):
            self.workspace.remove_constant(name)
            
            # Reload table
            self._load_constants()
            
            # Notify
            self.constants_changed.emit()
    
    def _clear_all(self):
        """Clear all constants."""
        if confirm_action(
            self,
            "Clear All Constants",
            "Remove all constants, variables, and functions?"
        ):
            self.workspace.constants.clear()
            
            # Reload table
            self._load_constants()
            
            # Notify
            self.constants_changed.emit()
    
    def _add_common_constants(self):
        """Add common physics/math constants."""
        constants = {
            "g": {"type": "constant", "value": 9.81, "unit": "m/s^2"},
            "pi": {"type": "constant", "value": 3.14159265359, "unit": None},
            "e": {"type": "constant", "value": 2.71828182846, "unit": None},
            "c": {"type": "constant", "value": 299792458, "unit": "m/s"},
            "h": {"type": "constant", "value": 6.62607015e-34, "unit": "J·s"},
            "k_B": {"type": "constant", "value": 1.380649e-23, "unit": "J/K"},
        }
        
        # Add to workspace
        for name, data in constants.items():
            self.workspace.add_constant(name, data["value"], data.get("unit"))
        
        self._load_constants()
        self.constants_changed.emit()
        
        show_info(
            self,
            "Constants Added",
            f"Added {len(constants)} common constants:\n" +
            ", ".join(constants.keys())
        )
