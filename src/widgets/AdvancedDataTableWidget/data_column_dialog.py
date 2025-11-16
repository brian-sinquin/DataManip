"""Data column editor dialog for AdvancedDataTableWidget.

This dialog allows editing properties of DATA columns:
- Diminutive (short name for formulas)
- Description (tooltip text)
- Unit of measurement
- Enable/disable uncertainty column
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QCheckBox, QGroupBox,
    QComboBox, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt
from typing import Optional

from .constants import COMMON_UNITS, INFO_UNCERTAINTY_EXISTS, INFO_UNCERTAINTY_WILL_CREATE, INFO_UNCERTAINTY_WILL_REMOVE


class DataColumnEditorDialog(QDialog):
    """Dialog for creating or editing data column properties.
    
    Args:
        parent: Parent widget
        column_index: Index of the column being edited (None for creation)
        table_widget: Reference to the AdvancedDataTableWidget
    """
    
    def __init__(self, parent, column_index: Optional[int], table_widget):
        super().__init__(parent)
        self.table_widget = table_widget
        self.column_index = column_index
        self.is_create_mode = column_index is None
        
        # Get current column properties (or defaults for create mode)
        if self.is_create_mode:
            self.current_diminutive = "new_col"
            self.current_description = ""
            self.current_unit = ""
            self.has_uncertainty = False
            self.uncertainty_col_index = None
        else:
            self.current_diminutive = table_widget.getColumnDiminutive(column_index)
            self.current_description = table_widget.getColumnDescription(column_index) or ""
            self.current_unit = table_widget.getColumnUnit(column_index) or ""
            self.has_uncertainty, self.uncertainty_col_index = table_widget.hasUncertaintyColumn(column_index)
        
        title = "Create Data Column" if self.is_create_mode else f"Edit Data Column - {self.current_diminutive}"
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(400, 300)
        
        self._setup_ui()
        self._load_current_values()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Column info group
        info_group = QGroupBox("Column Information")
        info_layout = QFormLayout(info_group)
        
        # Column type info
        if not self.is_create_mode:
            col_type = self.table_widget.getColumnType(self.column_index)
            type_label = QLabel(col_type.value.title())
            info_layout.addRow("Type:", type_label)
        else:
            type_label = QLabel("Data")
            info_layout.addRow("Type:", type_label)
        
        layout.addWidget(info_group)
        
        # Editable properties group
        props_group = QGroupBox("Editable Properties")
        props_layout = QFormLayout(props_group)
        
        # Diminutive editor
        self.diminutive_edit = QLineEdit()
        self.diminutive_edit.setPlaceholderText("Short form for formulas (e.g., 'temp', 'press')")
        props_layout.addRow("Diminutive:", self.diminutive_edit)
        
        # Description editor
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Description shown as tooltip on column header")
        props_layout.addRow("Description:", self.description_edit)
        
        # Unit editor with common units dropdown
        unit_layout = QHBoxLayout()
        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText("e.g., °C, kPa, V, A, m/s")
        
        self.unit_combo = QComboBox()
        self.unit_combo.setEditable(False)
        self.unit_combo.addItems(COMMON_UNITS)
        self.unit_combo.currentTextChanged.connect(self._on_unit_combo_changed)
        
        unit_layout.addWidget(self.unit_edit, 2)
        unit_layout.addWidget(self.unit_combo, 1)
        props_layout.addRow("Unit:", unit_layout)
        
        layout.addWidget(props_group)
        
        # Uncertainty group
        uncertainty_group = QGroupBox("Uncertainty Column")
        uncertainty_layout = QVBoxLayout(uncertainty_group)
        
        self.uncertainty_checkbox = QCheckBox("Enable uncertainty column for this data column")
        self.uncertainty_checkbox.toggled.connect(self._on_uncertainty_toggled)
        uncertainty_layout.addWidget(self.uncertainty_checkbox)
        
        # Uncertainty info label
        self.uncertainty_info_label = QLabel()
        self.uncertainty_info_label.setWordWrap(True)
        self.uncertainty_info_label.setStyleSheet("color: #666; font-size: 9pt;")
        uncertainty_layout.addWidget(self.uncertainty_info_label)
        
        layout.addWidget(uncertainty_group)
        
        # Preview group
        preview_group = QGroupBox("Preview")
        preview_layout = QFormLayout(preview_group)
        
        self.preview_header_label = QLabel()
        self.preview_formula_label = QLabel()
        
        preview_layout.addRow("Header:", self.preview_header_label)
        preview_layout.addRow("Formula Reference:", self.preview_formula_label)
        
        layout.addWidget(preview_group)
        
        # Connect preview updates
        self.diminutive_edit.textChanged.connect(self._update_preview)
        self.unit_edit.textChanged.connect(self._update_preview)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.accept)
        apply_btn.setDefault(True)
        button_layout.addWidget(apply_btn)
        
        layout.addLayout(button_layout)
    
    def _load_current_values(self):
        """Load current values into the form."""
        self.diminutive_edit.setText(self.current_diminutive or "")
        self.description_edit.setText(self.current_description)
        self.unit_edit.setText(self.current_unit)
        self.uncertainty_checkbox.setChecked(self.has_uncertainty)
        self._update_uncertainty_info()
        self._update_preview()
    
    def _on_unit_combo_changed(self, text):
        """Handle unit combo selection."""
        if text and text != "-- Common Units --":
            current_text = self.unit_edit.text()
            if not current_text:
                self.unit_edit.setText(text)
            else:
                # Ask if they want to replace
                reply = QMessageBox.question(
                    self, "Replace Unit?",
                    f"Replace current unit '{current_text}' with '{text}'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.unit_edit.setText(text)
    
    def _on_uncertainty_toggled(self, checked):
        """Handle uncertainty checkbox toggle."""
        self._update_uncertainty_info()
        self._update_preview()
    
    def _update_uncertainty_info(self):
        """Update the uncertainty info label."""
        if self.uncertainty_checkbox.isChecked():
            if self.has_uncertainty:
                self.uncertainty_info_label.setText(
                    INFO_UNCERTAINTY_EXISTS.format(index=self.uncertainty_col_index)
                )
                self.uncertainty_info_label.setStyleSheet("color: #666; font-size: 9pt;")
            else:
                self.uncertainty_info_label.setText(INFO_UNCERTAINTY_WILL_CREATE)
                self.uncertainty_info_label.setStyleSheet("color: #666; font-size: 9pt;")
        else:
            if self.has_uncertainty:
                # Warning style when about to remove existing uncertainty column
                self.uncertainty_info_label.setText(
                    f"⚠️ Will remove existing uncertainty column (index {self.uncertainty_col_index})"
                )
                self.uncertainty_info_label.setStyleSheet("color: #d32f2f; font-size: 9pt; font-weight: bold;")
            else:
                self.uncertainty_info_label.setText("")
                self.uncertainty_info_label.setStyleSheet("color: #666; font-size: 9pt;")
    
    def _update_preview(self):
        """Update the preview labels."""
        from utils.units import format_unit_pretty
        
        # Header preview - use diminutive as base
        unit_text = self.unit_edit.text().strip()
        diminutive_text = self.diminutive_edit.text().strip() or self.current_diminutive
        if unit_text:
            pretty_unit = format_unit_pretty(unit_text, use_dot=True, use_superscript=True)
            header_preview = f"{diminutive_text} [{pretty_unit}]"
        else:
            header_preview = diminutive_text
        
        self.preview_header_label.setText(header_preview)
        
        # Formula reference preview
        if diminutive_text:
            self.preview_formula_label.setText(f"{{{diminutive_text}}}")
        else:
            self.preview_formula_label.setText("(auto-generated)")
    
    def get_results(self):
        """Get the dialog results.
        
        Returns:
            dict: Dictionary containing:
                - diminutive: The edited diminutive (or None)
                - description: The edited description (or None)
                - unit: The edited unit (or None)
                - enable_uncertainty: Whether to enable uncertainty column
        """
        return {
            'diminutive': self.diminutive_edit.text().strip() or None,
            'description': self.description_edit.text().strip() or None,
            'unit': self.unit_edit.text().strip() or None,
            'enable_uncertainty': self.uncertainty_checkbox.isChecked()
        }
