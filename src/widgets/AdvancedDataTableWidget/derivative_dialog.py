"""Derivative column editor dialog.

This dialog allows creating/editing derivative columns that calculate
discrete differences (numerical derivatives) between two columns.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QGroupBox,
    QComboBox, QMessageBox
)
from typing import Optional

from .constants import DIALOG_EDIT_DERIVATIVE, DIALOG_ADD_DERIVATIVE
from .models import AdvancedColumnType
from .dialog_utils import populate_column_combo_boxes
from .dialog_widgets import ColumnSelectionComboBox


class DerivativeEditorDialog(QDialog):
    """Dialog for creating/editing derivative columns.
    
    A derivative column calculates the discrete differences ratio dy/dx
    between two data columns. This is useful for:
    - Calculating velocities (distance/time)
    - Finding rates of change
    - Computing slopes
    
    The calculation uses discrete differences:
    - For row i: derivative[i] = (y[i+1] - y[i]) / (x[i+1] - x[i])
    - First row gets the forward difference
    - Last row gets the backward difference
    
    Args:
        parent: Parent widget
        column_index: Index of column being edited (None for new column)
        table_widget: Reference to the AdvancedDataTableWidget
    """
    
    def __init__(self, parent, column_index: Optional[int], table_widget):
        super().__init__(parent)
        self.table_widget = table_widget
        self.column_index = column_index
        
        # Get current properties if editing existing derivative column
        if column_index is not None:
            self.current_diminutive = table_widget.getColumnDiminutive(column_index) or f"deriv_{column_index}"
            self.current_description = table_widget.getColumnDescription(column_index) or ""
            self.current_unit = table_widget.getColumnUnit(column_index) or ""
            metadata = table_widget._columns[column_index]
            self.current_numerator = metadata.derivative_numerator
            self.current_denominator = metadata.derivative_denominator
        else:
            self.current_diminutive = ""
            self.current_description = ""
            self.current_unit = ""
            self.current_numerator = None
            self.current_denominator = None
        
        title = DIALOG_EDIT_DERIVATIVE.format(name=self.current_diminutive) if column_index is not None else DIALOG_ADD_DERIVATIVE
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(500, 400)
        
        self._setup_ui()
        self._load_current_values()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Explanation
        explanation = QLabel(
            "A derivative column calculates discrete differences: dy/dx\n"
            "For each row i: result[i] = (y[i+1] - y[i]) / (x[i+1] - x[i])\n\n"
            "You can use DATA, CALCULATED, or even DERIVATIVE columns as inputs.\n"
            "Example: acceleration = d(velocity)/dt where velocity is itself a derivative!"
        )
        explanation.setWordWrap(True)
        explanation.setStyleSheet("color: #666; font-size: 9pt; padding: 5px;")
        layout.addWidget(explanation)
        
        # Column properties
        properties_group = QGroupBox("Column Properties")
        properties_layout = QFormLayout()
        
        self.diminutive_edit = QLineEdit()
        self.diminutive_edit.setPlaceholderText("Short name (e.g., 'v', 'accel', 'slope')")
        properties_layout.addRow("Diminutive:", self.diminutive_edit)
        
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Description shown as tooltip")
        properties_layout.addRow("Description:", self.description_edit)
        
        properties_group.setLayout(properties_layout)
        layout.addWidget(properties_group)
        
        # Derivative configuration
        derivative_group = QGroupBox("Derivative Configuration")
        derivative_layout = QFormLayout()
        
        # Numerator (dy)
        self.numerator_combo = ColumnSelectionComboBox()
        self.numerator_combo.setIncludeTypeLabels(True)
        self.numerator_combo.setIncludeUnits(True)
        self.numerator_combo.setTableWidget(self.table_widget, self.column_index)
        self.numerator_combo.currentIndexChanged.connect(self._update_unit_preview)
        derivative_layout.addRow("Numerator (dy):", self.numerator_combo)
        
        # Denominator (dx)
        self.denominator_combo = ColumnSelectionComboBox()
        self.denominator_combo.setIncludeTypeLabels(True)
        self.denominator_combo.setIncludeUnits(True)
        self.denominator_combo.setTableWidget(self.table_widget, self.column_index)
        self.denominator_combo.currentIndexChanged.connect(self._update_unit_preview)
        derivative_layout.addRow("Denominator (dx):", self.denominator_combo)
        
        derivative_group.setLayout(derivative_layout)
        layout.addWidget(derivative_group)
        
        # Preview (create before populating combos to avoid errors)
        preview_group = QGroupBox("Preview")
        preview_layout = QFormLayout()
        
        self.preview_unit_label = QLabel()
        self.preview_header_label = QLabel()
        
        preview_layout.addRow("Calculated Unit:", self.preview_unit_label)
        preview_layout.addRow("Header:", self.preview_header_label)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Buttons
        button_layout = QVBoxLayout()
        button_layout.addStretch()
        
        from PySide6.QtWidgets import QHBoxLayout
        btn_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self._validate_and_accept)
        ok_btn.setDefault(True)
        btn_layout.addWidget(ok_btn)
        
        button_layout.addLayout(btn_layout)
        layout.addLayout(button_layout)
    
    def _load_current_values(self):
        """Load current values if editing existing column."""
        self.diminutive_edit.setText(self.current_diminutive)
        self.description_edit.setText(self.current_description)
        
        # Set combo box selections
        if self.current_numerator is not None:
            for i in range(self.numerator_combo.count()):
                if self.numerator_combo.itemData(i) == self.current_numerator:
                    self.numerator_combo.setCurrentIndex(i)
                    break
        
        if self.current_denominator is not None:
            for i in range(self.denominator_combo.count()):
                if self.denominator_combo.itemData(i) == self.current_denominator:
                    self.denominator_combo.setCurrentIndex(i)
                    break
        
        self._update_unit_preview()
    
    def _update_unit_preview(self):
        """Update the unit and header preview based on selected columns."""
        num_idx = self.numerator_combo.currentData()
        den_idx = self.denominator_combo.currentData()
        
        if num_idx is None or den_idx is None:
            self.preview_unit_label.setText("Select both columns")
            self.preview_header_label.setText("")
            return
        
        # Get units from selected columns
        num_unit = self.table_widget.getColumnUnit(num_idx) or "dimensionless"
        den_unit = self.table_widget.getColumnUnit(den_idx) or "dimensionless"
        
        # Calculate resulting unit
        if num_unit == "dimensionless" and den_unit == "dimensionless":
            result_unit = "dimensionless"
        elif num_unit == "dimensionless":
            result_unit = f"1/({den_unit})"
        elif den_unit == "dimensionless":
            result_unit = num_unit
        else:
            result_unit = f"({num_unit})/({den_unit})"
        
        self.preview_unit_label.setText(result_unit)
        
        # Preview header
        from .constants import SYMBOL_DERIVATIVE
        diminutive = self.diminutive_edit.text().strip() or "deriv"
        self.preview_header_label.setText(f"{SYMBOL_DERIVATIVE}{diminutive} [{result_unit}]")
    
    def _validate_and_accept(self):
        """Validate inputs before accepting."""
        # Check diminutive
        diminutive = self.diminutive_edit.text().strip()
        if not diminutive:
            QMessageBox.warning(self, "Missing Diminutive", "Please enter a diminutive for the column.")
            return
        
        # Check that both columns are selected
        num_idx = self.numerator_combo.currentData()
        den_idx = self.denominator_combo.currentData()
        
        if num_idx is None:
            QMessageBox.warning(self, "Missing Numerator", "Please select a numerator column (dy).")
            return
        
        if den_idx is None:
            QMessageBox.warning(self, "Missing Denominator", "Please select a denominator column (dx).")
            return
        
        if num_idx == den_idx:
            QMessageBox.warning(self, "Same Column", "Numerator and denominator must be different columns.")
            return
        
        self.accept()
    
    def get_results(self):
        """Get the dialog results.
        
        Returns:
            dict: Dictionary containing:
                - diminutive: The column diminutive
                - description: The column description
                - unit: The calculated unit
                - numerator_index: Index of numerator column
                - denominator_index: Index of denominator column
        """
        num_idx = self.numerator_combo.currentData()
        den_idx = self.denominator_combo.currentData()
        
        # Calculate unit
        num_unit = self.table_widget.getColumnUnit(num_idx) or "dimensionless"
        den_unit = self.table_widget.getColumnUnit(den_idx) or "dimensionless"
        
        if num_unit == "dimensionless" and den_unit == "dimensionless":
            result_unit = "dimensionless"
        elif num_unit == "dimensionless":
            result_unit = f"1/({den_unit})"
        elif den_unit == "dimensionless":
            result_unit = num_unit
        else:
            result_unit = f"({num_unit})/({den_unit})"
        
        return {
            'diminutive': self.diminutive_edit.text().strip(),
            'description': self.description_edit.text().strip(),
            'unit': result_unit,
            'numerator_index': num_idx,
            'denominator_index': den_idx
        }
