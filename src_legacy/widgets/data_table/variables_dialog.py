"""Variables management dialog for global constants in DataTableV2.

This dialog allows users to define global variables/constants that can be used
in formulas across all calculated columns.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox
)
from typing import Optional, Dict, Tuple


class VariablesDialog(QDialog):
    """Dialog for managing global variables/constants that can be used in formulas.
    
    Variables are defined with:
    - Name: Short name to use in formulas (e.g., 'g', 'c', 'pi')
    - Value: Numeric value
    - Unit: Physical unit (optional)
    
    Example variables:
    - g = 9.81 m/s²
    - c = 299792458 m/s
    - pi = 3.14159 (dimensionless)
    
    Args:
        parent: Parent widget
        current_variables: Dict of {name: (value, unit)}
    """
    
    def __init__(self, parent=None, current_variables: Optional[Dict[str, Tuple[float, Optional[str]]]] = None):
        super().__init__(parent)
        self.current_variables = current_variables or {}
        
        self.setWindowTitle("Manage Global Variables")
        self.setModal(True)
        self.resize(600, 400)
        
        self._setup_ui()
        self._load_variables()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Description
        desc_label = QLabel(
            "Define global variables/constants that can be used in formulas.\n"
            "Use the variable name in formulas (e.g., {g} for gravity, {pi} for π)."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; font-size: 9pt; padding: 5px; margin-bottom: 10px;")
        layout.addWidget(desc_label)
        
        # Variables table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "Value", "Unit"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
        # Buttons for adding/removing rows
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ Add Variable")
        add_btn.clicked.connect(self._add_variable_row)
        button_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("➖ Remove Selected")
        remove_btn.clicked.connect(self._remove_selected_rows)
        button_layout.addWidget(remove_btn)
        
        # Add some common constants button
        common_btn = QPushButton("📚 Add Common Constants")
        common_btn.clicked.connect(self._add_common_constants)
        button_layout.addWidget(common_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Dialog buttons
        dialog_buttons = QHBoxLayout()
        dialog_buttons.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        dialog_buttons.addWidget(cancel_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self._validate_and_accept)
        ok_btn.setDefault(True)
        dialog_buttons.addWidget(ok_btn)
        
        layout.addLayout(dialog_buttons)
    
    def _load_variables(self):
        """Load current variables into the table."""
        self.table.setRowCount(0)
        for name, (value, unit) in sorted(self.current_variables.items()):
            self._add_variable_row(name, str(value), unit or "")
    
    def _add_variable_row(self, name: str = "", value: str = "", unit: str = ""):
        """Add a new row to the variables table.
        
        Args:
            name: Variable name
            value: Numeric value
            unit: Physical unit (optional)
        """
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        self.table.setItem(row, 0, QTableWidgetItem(name))
        self.table.setItem(row, 1, QTableWidgetItem(value))
        self.table.setItem(row, 2, QTableWidgetItem(unit))
    
    def _remove_selected_rows(self):
        """Remove selected rows from the table."""
        selected_rows = sorted(set(index.row() for index in self.table.selectedIndexes()), reverse=True)
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select one or more rows to remove.")
            return
        
        for row in selected_rows:
            self.table.removeRow(row)
    
    def _add_common_constants(self):
        """Add common physical and mathematical constants to the table."""
        common_constants = [
            # Mathematical constants
            ("pi", "3.14159265358979", ""),
            ("e", "2.71828182845905", ""),
            
            # Physical constants
            ("c", "299792458", "m/s"),           # Speed of light
            ("g", "9.80665", "m/s²"),            # Standard gravity
            ("h", "6.62607015e-34", "J·s"),      # Planck constant
            ("k_B", "1.380649e-23", "J/K"),      # Boltzmann constant
            ("N_A", "6.02214076e23", "1/mol"),   # Avogadro constant
            ("R", "8.314462618", "J/(mol·K)"),   # Gas constant
            ("e0", "8.8541878128e-12", "F/m"),   # Vacuum permittivity
            ("mu0", "1.25663706212e-6", "H/m"),  # Vacuum permeability
        ]
        
        # Check which ones are not already in the table
        existing_names = set()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                existing_names.add(item.text().strip())
        
        added = 0
        for name, val, unit in common_constants:
            if name not in existing_names:
                self._add_variable_row(name, val, unit)
                added += 1
        
        if added > 0:
            QMessageBox.information(self, "Constants Added", 
                                  f"Added {added} common constant(s).\n\n"
                                  f"You can now use them in formulas like {{pi}}, {{g}}, etc.")
        else:
            QMessageBox.information(self, "No Constants Added", 
                                  "All common constants are already defined.")
    
    def _validate_and_accept(self):
        """Validate the variables before accepting."""
        # Check for duplicate names
        names = []
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            if name_item:
                name = name_item.text().strip()
                if name:
                    if name in names:
                        QMessageBox.warning(self, "Duplicate Name", 
                                          f"Variable name '{name}' is defined multiple times.\n"
                                          f"Each variable must have a unique name.")
                        return
                    names.append(name)
        
        # Validate that values are numeric
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            val_item = self.table.item(row, 1)
            
            if name_item and name_item.text().strip():
                name = name_item.text().strip()
                val_text = val_item.text().strip() if val_item else ""
                
                # Check name is valid (alphanumeric + underscore)
                if not name.replace("_", "").isalnum():
                    QMessageBox.warning(self, "Invalid Name", 
                                      f"Variable name '{name}' contains invalid characters.\n"
                                      f"Only letters, numbers, and underscores are allowed.")
                    return
                
                if not val_text:
                    QMessageBox.warning(self, "Missing Value", 
                                      f"Variable '{name}' has no value.")
                    return
                
                try:
                    float(val_text)
                except ValueError:
                    QMessageBox.warning(self, "Invalid Value", 
                                      f"Value '{val_text}' for variable '{name}' is not a valid number.\n"
                                      f"Scientific notation (e.g., 1.23e-4) is supported.")
                    return
        
        self.accept()
    
    def get_variables(self) -> Dict[str, Tuple[float, Optional[str]]]:
        """Get the variables as a dictionary.
        
        Returns:
            dict: {name: (value, unit)}
        """
        variables = {}
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            val_item = self.table.item(row, 1)
            unit_item = self.table.item(row, 2)
            
            if name_item and name_item.text().strip():
                name = name_item.text().strip()
                val_text = val_item.text().strip() if val_item else ""
                unit = unit_item.text().strip() if unit_item else ""
                
                if val_text:
                    try:
                        value = float(val_text)
                        variables[name] = (value, unit if unit else None)
                    except ValueError:
                        pass  # Skip invalid values
        
        return variables
