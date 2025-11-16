"""Variables management dialog for global constants.

This dialog allows users to define global variables/constants that can be used
in formulas across all calculated columns.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox
)
from typing import Optional, Dict, Tuple

from .constants import DIALOG_MANAGE_VARIABLES


class VariablesDialog(QDialog):
    """Dialog for managing global variables/constants that can be used in formulas.
    
    Variables are defined with:
    - Diminutive: Short name to use in formulas (e.g., 'g', 'c', 'pi')
    - Value: Numeric value
    - Unit: Physical unit (optional)
    
    Example variables:
    - g = 9.81 m/s²
    - c = 299792458 m/s
    - pi = 3.14159 (dimensionless)
    
    Args:
        parent: Parent widget
        current_variables: Dict of {diminutive: (value, unit)}
    """
    
    def __init__(self, parent, current_variables: Optional[Dict[str, Tuple[float, Optional[str]]]] = None):
        super().__init__(parent)
        self.current_variables = current_variables or {}
        
        self.setWindowTitle(DIALOG_MANAGE_VARIABLES)
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
            "Use the diminutive name in formulas (e.g., {g} for gravity)."
        )
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Variables table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Diminutive", "Value", "Unit"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)
        
        # Buttons for adding/removing rows
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add Variable")
        add_btn.clicked.connect(self._add_variable_row)
        button_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._remove_selected_rows)
        button_layout.addWidget(remove_btn)
        
        # Add some common constants button
        common_btn = QPushButton("Add Common Constants")
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
        for diminutive, (value, unit) in self.current_variables.items():
            self._add_variable_row(diminutive, str(value), unit or "")
    
    def _add_variable_row(self, diminutive: str = "", value: str = "", unit: str = ""):
        """Add a new row to the variables table.
        
        Args:
            diminutive: Variable name
            value: Numeric value
            unit: Physical unit (optional)
        """
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        self.table.setItem(row, 0, QTableWidgetItem(diminutive))
        self.table.setItem(row, 1, QTableWidgetItem(value))
        self.table.setItem(row, 2, QTableWidgetItem(unit))
    
    def _remove_selected_rows(self):
        """Remove selected rows from the table."""
        selected_rows = sorted(set(index.row() for index in self.table.selectedIndexes()), reverse=True)
        for row in selected_rows:
            self.table.removeRow(row)
    
    def _add_common_constants(self):
        """Add common physical constants to the table."""
        common_constants = [
            ("g", "9.80665", "m/s²"),
            ("c", "299792458", "m/s"),
            ("pi", "3.14159265", ""),
            ("e", "2.71828183", ""),
            ("h", "6.62607015e-34", "J*s"),
            ("k_B", "1.380649e-23", "J/K"),
        ]
        
        # Check which ones are not already in the table
        existing_diminutives = set()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                existing_diminutives.add(item.text().strip())
        
        added = 0
        for dim, val, unit in common_constants:
            if dim not in existing_diminutives:
                self._add_variable_row(dim, val, unit)
                added += 1
        
        if added > 0:
            QMessageBox.information(self, "Constants Added", f"Added {added} common physical constant(s).")
        else:
            QMessageBox.information(self, "No Constants Added", "All common constants are already defined.")
    
    def _validate_and_accept(self):
        """Validate the variables before accepting."""
        # Check for duplicate diminutives
        diminutives = []
        for row in range(self.table.rowCount()):
            dim_item = self.table.item(row, 0)
            if dim_item:
                dim = dim_item.text().strip()
                if dim:
                    if dim in diminutives:
                        QMessageBox.warning(self, "Duplicate Diminutive", 
                                          f"Diminutive '{dim}' is defined multiple times.")
                        return
                    diminutives.append(dim)
        
        # Validate that values are numeric
        for row in range(self.table.rowCount()):
            dim_item = self.table.item(row, 0)
            val_item = self.table.item(row, 1)
            
            if dim_item and dim_item.text().strip():
                dim = dim_item.text().strip()
                val_text = val_item.text().strip() if val_item else ""
                
                if not val_text:
                    QMessageBox.warning(self, "Missing Value", 
                                      f"Variable '{dim}' has no value.")
                    return
                
                try:
                    float(val_text)
                except ValueError:
                    QMessageBox.warning(self, "Invalid Value", 
                                      f"Value '{val_text}' for variable '{dim}' is not a valid number.")
                    return
        
        self.accept()
    
    def get_variables(self) -> Dict[str, Tuple[float, Optional[str]]]:
        """Get the variables as a dictionary.
        
        Returns:
            dict: {diminutive: (value, unit)}
        """
        variables = {}
        for row in range(self.table.rowCount()):
            dim_item = self.table.item(row, 0)
            val_item = self.table.item(row, 1)
            unit_item = self.table.item(row, 2)
            
            if dim_item and dim_item.text().strip():
                dim = dim_item.text().strip()
                val_text = val_item.text().strip() if val_item else ""
                unit = unit_item.text().strip() if unit_item else ""
                
                if val_text:
                    try:
                        value = float(val_text)
                        variables[dim] = (value, unit if unit else None)
                    except ValueError:
                        pass  # Skip invalid values
        
        return variables
