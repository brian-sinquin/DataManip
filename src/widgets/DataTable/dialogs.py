"""
Dialog classes for DataTableV2.

This module provides enhanced UI dialogs for column creation and editing:
- AddDataColumnDialog: Create new data columns with all properties
- AddCalculatedColumnDialog: Create calculated columns with formula editor and uncertainty propagation
- AddRangeColumnDialog: Create range columns with evenly-spaced values
- VariablesDialog: Manage global constants for formulas (future enhancement)

These dialogs provide a user-friendly interface for the DataTableV2 model,
with validation, preview, and helpful guidance for users.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QCheckBox, QGroupBox,
    QComboBox, QTextEdit, QListWidget, QSplitter, QWidget,
    QMessageBox, QDoubleSpinBox, QSpinBox, QListWidgetItem,
    QDialogButtonBox, QTabWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from typing import Optional, Dict, Any, List, TYPE_CHECKING
import math

from .column_metadata import ColumnType, DataType

if TYPE_CHECKING:
    from .column_metadata import ColumnMetadata


# Common units for quick selection
COMMON_UNITS = [
    "",  # No unit
    # Length
    "m", "cm", "mm", "μm", "nm", "km", "in", "ft",
    # Mass
    "kg", "g", "mg", "μg", "lb", "oz",
    # Time
    "s", "ms", "μs", "ns", "min", "h", "day",
    # Temperature
    "K", "°C", "°F",
    # Pressure
    "Pa", "kPa", "MPa", "bar", "atm", "psi", "mmHg",
    # Volume
    "L", "mL", "μL", "m³", "cm³",
    # Energy
    "J", "kJ", "MJ", "eV", "keV", "MeV", "cal", "kcal",
    # Power
    "W", "kW", "MW", "hp",
    # Electric
    "V", "mV", "A", "mA", "μA", "Ω", "kΩ", "MΩ",
    # Frequency
    "Hz", "kHz", "MHz", "GHz",
    # Other
    "mol", "rad", "deg", "%", "ppm"
]


class AddDataColumnDialog(QDialog):
    """Dialog for creating or editing a data column.
    
    This dialog allows users to:
    - Set column name (used for display and formulas)
    - Choose data type (FLOAT, INTEGER, STRING, etc.)
    - Set unit of measurement
    - Add description/tooltip
    - Set display precision
    - Optionally create an associated uncertainty column
    
    The dialog validates input and provides helpful tooltips and examples.
    
    Supports both creation (column_metadata=None) and editing (column_metadata provided).
    """
    
    def __init__(self, parent=None, existing_names: Optional[List[str]] = None, 
                 column_metadata: Optional['ColumnMetadata'] = None):
        """Initialize the dialog.
        
        Args:
            parent: Parent widget
            existing_names: List of existing column names to prevent duplicates
            column_metadata: If provided, dialog is in edit mode for this column
        """
        super().__init__(parent)
        self.existing_names = existing_names or []
        self.column_metadata = column_metadata
        self.is_edit_mode = column_metadata is not None
        
        # Set appropriate title
        if self.is_edit_mode and column_metadata is not None:
            self.setWindowTitle(f"Edit Data Column - {column_metadata.name}")
        else:
            self.setWindowTitle("Add Data Column")
        
        self.setModal(True)
        self.resize(500, 400)
        
        self._setup_ui()
        
        # Load existing values if in edit mode
        if self.is_edit_mode and column_metadata is not None:
            self._load_existing_values()
        
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel(
            "Create a new data column for entering measured or input values.\n"
            "Data columns can be referenced in formulas and have optional uncertainty."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(instructions)
        
        # Main properties group
        props_group = QGroupBox("Column Properties")
        props_layout = QFormLayout(props_group)
        
        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., temperature, pressure, voltage")
        self.name_edit.textChanged.connect(self._validate_name)
        props_layout.addRow("Name*:", self.name_edit)
        
        self.name_error_label = QLabel()
        self.name_error_label.setStyleSheet("color: red; font-size: 9pt;")
        self.name_error_label.setWordWrap(True)
        props_layout.addRow("", self.name_error_label)
        
        # Data type
        self.dtype_combo = QComboBox()
        for dtype in DataType:
            self.dtype_combo.addItem(dtype.name, dtype)
        self.dtype_combo.setCurrentText("FLOAT")
        self.dtype_combo.currentTextChanged.connect(self._on_dtype_changed)
        props_layout.addRow("Data Type*:", self.dtype_combo)
        
        # Unit (only for numeric types)
        unit_layout = QHBoxLayout()
        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText("e.g., °C, kPa, V, m/s")
        
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(COMMON_UNITS)
        self.unit_combo.currentTextChanged.connect(self._on_unit_combo_changed)
        
        unit_layout.addWidget(self.unit_edit, 2)
        unit_layout.addWidget(QLabel("Quick:"), 0)
        unit_layout.addWidget(self.unit_combo, 1)
        
        self.unit_row_label = QLabel("Unit:")
        props_layout.addRow(self.unit_row_label, unit_layout)
        
        # Description
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Optional: Description shown as tooltip")
        props_layout.addRow("Description:", self.description_edit)
        
        # Precision (only for numeric types)
        self.precision_spin = QSpinBox()
        self.precision_spin.setRange(0, 15)
        self.precision_spin.setValue(6)
        self.precision_spin.setToolTip("Number of decimal places to display")
        self.precision_row_label = QLabel("Precision:")
        props_layout.addRow(self.precision_row_label, self.precision_spin)
        
        layout.addWidget(props_group)
        
        # Uncertainty option
        uncertainty_group = QGroupBox("Uncertainty (Optional)")
        uncertainty_layout = QVBoxLayout(uncertainty_group)
        
        self.create_uncertainty_checkbox = QCheckBox(
            "Create an associated uncertainty column (name_u)"
        )
        self.create_uncertainty_checkbox.setToolTip(
            "Creates a separate column to store measurement uncertainties.\n"
            "Useful for error propagation in calculated columns."
        )
        uncertainty_layout.addWidget(self.create_uncertainty_checkbox)
        
        layout.addWidget(uncertainty_group)
        
        # Preview
        preview_group = QGroupBox("Preview")
        preview_layout = QFormLayout(preview_group)
        
        self.preview_header_label = QLabel("(enter name)")
        self.preview_header_label.setStyleSheet("font-weight: bold;")
        preview_layout.addRow("Header:", self.preview_header_label)
        
        self.preview_formula_label = QLabel("(enter name)")
        self.preview_formula_label.setFont(QFont("Courier New"))
        preview_layout.addRow("In formulas:", self.preview_formula_label)
        
        layout.addWidget(preview_group)
        
        # Connect preview updates
        self.name_edit.textChanged.connect(self._update_preview)
        self.unit_edit.textChanged.connect(self._update_preview)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setEnabled(False)  # Disabled until valid name
        layout.addWidget(button_box)
        
        # Trigger initial validation
        self._on_dtype_changed()
    
    def _validate_name(self):
        """Validate the column name."""
        name = self.name_edit.text().strip()
        
        if not name:
            self.name_error_label.setText("")
            self.ok_button.setEnabled(False)
            return False
        
        # In edit mode, exclude current name from duplicate check
        existing = [n for n in self.existing_names if not (self.is_edit_mode and 
                    self.column_metadata is not None and n == self.column_metadata.name)]
        
        # Check for duplicates
        if name in existing:
            self.name_error_label.setText(f"⚠ Column '{name}' already exists")
            self.ok_button.setEnabled(False)
            return False
        
        # Check for invalid characters
        if not name.replace("_", "").replace("-", "").isalnum():
            self.name_error_label.setText("⚠ Name should only contain letters, numbers, _, -")
            self.ok_button.setEnabled(False)
            return False
        
        # Valid
        self.name_error_label.setText("✓ Valid name")
        self.name_error_label.setStyleSheet("color: green; font-size: 9pt;")
        self.ok_button.setEnabled(True)
        return True
    
    def _load_existing_values(self):
        """Load existing column values when in edit mode."""
        if not self.is_edit_mode or self.column_metadata is None:
            return
        
        meta = self.column_metadata
        
        # Load basic properties
        self.name_edit.setText(meta.name)
        
        # Set data type
        for i in range(self.dtype_combo.count()):
            if self.dtype_combo.itemData(i) == meta.dtype:
                self.dtype_combo.setCurrentIndex(i)
                break
        
        # Load unit and description
        if meta.unit:
            self.unit_edit.setText(meta.unit)
        if meta.description:
            self.description_edit.setText(meta.description)
        
        # Load precision
        self.precision_spin.setValue(meta.precision)
        
        # Note: Uncertainty checkbox is not loaded - creating/removing uncertainty 
        # columns should be done through separate actions
    
    def _on_dtype_changed(self):
        """Handle data type changes - show/hide unit and precision for numeric types."""
        dtype = self.dtype_combo.currentData()
        is_numeric = dtype in (DataType.FLOAT, DataType.INTEGER)
        
        # Show/hide unit fields
        self.unit_edit.setVisible(is_numeric)
        self.unit_combo.setVisible(is_numeric)
        self.unit_row_label.setVisible(is_numeric)
        
        # Show/hide precision
        self.precision_spin.setVisible(dtype == DataType.FLOAT)
        self.precision_row_label.setVisible(dtype == DataType.FLOAT)
        
        # Show/hide uncertainty option (only for numeric)
        self.create_uncertainty_checkbox.setVisible(is_numeric)
    
    def _on_unit_combo_changed(self, unit: str):
        """Update unit edit when combo selection changes."""
        if unit:  # Skip empty selection
            self.unit_edit.setText(unit)
    
    def _update_preview(self):
        """Update the preview labels."""
        name = self.name_edit.text().strip() or "(enter name)"
        unit_text = self.unit_edit.text().strip()
        
        # Header preview
        if unit_text and self.dtype_combo.currentData() in (DataType.FLOAT, DataType.INTEGER):
            header_preview = f"{name} [{unit_text}]"
        else:
            header_preview = name
        
        self.preview_header_label.setText(header_preview)
        
        # Formula reference preview
        self.preview_formula_label.setText(f"{{{name}}}")
    
    def get_results(self) -> Dict[str, Any]:
        """Get the dialog results.
        
        Returns:
            Dictionary containing:
                - name: Column name
                - dtype: DataType enum value
                - unit: Unit string (or None)
                - description: Description string (or None)
                - precision: Display precision (or None for non-float)
                - create_uncertainty: Whether to create uncertainty column
        """
        dtype = self.dtype_combo.currentData()
        
        results = {
            'name': self.name_edit.text().strip(),
            'dtype': dtype,
            'unit': self.unit_edit.text().strip() or None if dtype in (DataType.FLOAT, DataType.INTEGER) else None,
            'description': self.description_edit.text().strip() or None,
            'precision': self.precision_spin.value() if dtype == DataType.FLOAT else None,
            'create_uncertainty': self.create_uncertainty_checkbox.isChecked()
        }
        
        return results


class AddCalculatedColumnDialog(QDialog):
    """Dialog for creating or editing a calculated column with formula and uncertainty propagation.
    
    This dialog provides:
    - Formula editor with syntax help
    - List of available columns for reference
    - Easy insertion of column references with {name} syntax
    - Unit preview (automatically calculated from formula)
    - Uncertainty propagation toggle
    - Column property editing (name, description, precision)
    - Validation and error checking
    
    Supports both creation (column_metadata=None) and editing (column_metadata provided).
    """
    
    def __init__(self, parent=None, model=None, existing_names: Optional[List[str]] = None,
                 column_metadata: Optional['ColumnMetadata'] = None):
        """Initialize the dialog.
        
        Args:
            parent: Parent widget
            model: DataTableModel instance for column reference
            existing_names: List of existing column names to prevent duplicates
            column_metadata: If provided, dialog is in edit mode for this column
        """
        super().__init__(parent)
        self.model = model
        self.existing_names = existing_names or []
        self.column_metadata = column_metadata
        self.is_edit_mode = column_metadata is not None
        
        # Set appropriate title
        if self.is_edit_mode and column_metadata is not None:
            self.setWindowTitle(f"Edit Calculated Column - {column_metadata.name}")
        else:
            self.setWindowTitle("Add Calculated Column")
        
        self.setModal(True)
        self.resize(700, 700)
        
        self._setup_ui()
        
        # Load existing values if in edit mode
        if self.is_edit_mode and column_metadata is not None:
            self._load_existing_values()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel(
            "Create a calculated column using a formula. Reference other columns using {name} syntax.\n"
            "The column values will automatically update when referenced columns change."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(instructions)
        
        # Column properties section
        properties_group = QGroupBox("Column Properties")
        properties_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., velocity, energy, ratio")
        self.name_edit.textChanged.connect(self._validate_name)
        properties_layout.addRow("Name*:", self.name_edit)
        
        self.name_error_label = QLabel()
        self.name_error_label.setStyleSheet("color: red; font-size: 9pt;")
        self.name_error_label.setWordWrap(True)
        properties_layout.addRow("", self.name_error_label)
        
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Optional: Description shown as tooltip")
        properties_layout.addRow("Description:", self.description_edit)
        
        # Unit field - READ-ONLY (automatically calculated from formula)
        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText("Automatically calculated from formula")
        self.unit_edit.setReadOnly(True)
        self.unit_edit.setStyleSheet("QLineEdit { background-color: #f0f0f0; color: #666; }")
        self.unit_edit.setToolTip(
            "Unit is automatically calculated based on the formula and input column units.\n"
            "This feature requires Pint library for unit propagation."
        )
        properties_layout.addRow("Unit (Auto):", self.unit_edit)
        
        self.precision_spin = QSpinBox()
        self.precision_spin.setRange(0, 15)
        self.precision_spin.setValue(6)
        self.precision_spin.setToolTip("Number of decimal places to display")
        properties_layout.addRow("Precision:", self.precision_spin)
        
        properties_group.setLayout(properties_layout)
        layout.addWidget(properties_group)
        
        # Formula section
        formula_group = QGroupBox("Formula")
        formula_layout = QVBoxLayout()
        
        formula_label = QLabel("Formula (use {name} to reference columns):")
        formula_layout.addWidget(formula_label)
        
        self.formula_edit = QTextEdit()
        self.formula_edit.setPlaceholderText(
            "Examples:\n"
            "  {distance} / {time}\n"
            "  {mass} * {velocity}**2 / 2\n"
            "  sqrt({x}**2 + {y}**2)\n"
            "  sin({angle}) * {amplitude}"
        )
        self.formula_edit.setMaximumHeight(120)
        self.formula_edit.textChanged.connect(self._validate_formula)
        formula_layout.addWidget(self.formula_edit)
        
        # Syntax help
        syntax_label = QLabel(
            "<b>Operators:</b> + - * / ** (power) | "
            "<b>Functions:</b> sin, cos, tan, sqrt, log, log10, exp, abs | "
            "<b>Constants:</b> pi, e"
        )
        syntax_label.setWordWrap(True)
        syntax_label.setStyleSheet("font-size: 9pt; color: #666;")
        formula_layout.addWidget(syntax_label)
        
        self.formula_error_label = QLabel()
        self.formula_error_label.setStyleSheet("color: red; font-size: 9pt;")
        self.formula_error_label.setWordWrap(True)
        formula_layout.addWidget(self.formula_error_label)
        
        formula_group.setLayout(formula_layout)
        layout.addWidget(formula_group)
        
        # Uncertainty propagation section
        uncertainty_group = QGroupBox("Uncertainty Propagation")
        uncertainty_layout = QVBoxLayout()
        
        self.propagate_uncertainty_checkbox = QCheckBox(
            "Automatically calculate propagated uncertainty"
        )
        self.propagate_uncertainty_checkbox.setToolTip(
            "When enabled, uncertainty will be calculated using symbolic differentiation\n"
            "of the formula with respect to each input variable that has uncertainty.\n\n"
            "Formula: δf = √(Σ(∂f/∂xᵢ · δxᵢ)²)\n\n"
            "A read-only uncertainty column (name_u) will be created automatically."
        )
        self.propagate_uncertainty_checkbox.toggled.connect(self._on_uncertainty_toggled)
        uncertainty_layout.addWidget(self.propagate_uncertainty_checkbox)
        
        # Uncertainty info label
        self.uncertainty_info_label = QLabel()
        self.uncertainty_info_label.setWordWrap(True)
        self.uncertainty_info_label.setStyleSheet("color: #666; font-size: 9pt; margin-left: 20px;")
        uncertainty_layout.addWidget(self.uncertainty_info_label)
        
        uncertainty_group.setLayout(uncertainty_layout)
        layout.addWidget(uncertainty_group)
        
        # Splitter for column list and preview
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Available columns list (left side)
        columns_widget = QWidget()
        columns_layout = QVBoxLayout(columns_widget)
        columns_layout.setContentsMargins(0, 0, 0, 0)
        
        columns_label = QLabel("Available Columns (double-click to insert):")
        columns_layout.addWidget(columns_label)
        
        self.columns_list = QListWidget()
        self.columns_list.itemDoubleClicked.connect(self._insert_column_reference)
        columns_layout.addWidget(self.columns_list)
        
        # Populate columns list
        if self.model:
            self._populate_columns_list()
        
        splitter.addWidget(columns_widget)
        
        # Preview panel (right side)
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        preview_label = QLabel("Column Preview:")
        preview_layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(100)
        preview_layout.addWidget(self.preview_text)
        
        splitter.addWidget(preview_widget)
        
        # Connect preview update
        self.name_edit.textChanged.connect(self._update_preview)
        self.formula_edit.textChanged.connect(self._update_preview)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setEnabled(False)  # Disabled until valid
        layout.addWidget(button_box)
        
        # Trigger initial update
        self._on_uncertainty_toggled()
    
    def _populate_columns_list(self):
        """Populate the list of available columns."""
        self.columns_list.clear()
        
        if not self.model:
            return
        
        for col_name in self.model.get_column_names():
            metadata = self.model._metadata[col_name]
            
            # Determine icon/symbol
            if metadata.is_data_column():
                symbol = "●"
                type_text = "data"
            elif metadata.is_calculated_column():
                symbol = "ƒ"
                type_text = "calc"
            elif metadata.is_derivative_column():
                symbol = "∂"
                type_text = "deriv"
            elif metadata.is_range_column():
                symbol = "▬"
                type_text = "range"
            elif metadata.is_uncertainty_column():
                symbol = "σ"
                type_text = "unc"
            else:
                symbol = "?"
                type_text = "?"
            
            # Format display text
            unit_text = f" [{metadata.unit}]" if metadata.unit else ""
            display_text = f"{symbol} {col_name}{unit_text}  ({type_text})"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, col_name)  # Store actual name
            self.columns_list.addItem(item)
    
    def _insert_column_reference(self, item: QListWidgetItem):
        """Insert column reference into formula when double-clicked."""
        col_name = item.data(Qt.ItemDataRole.UserRole)
        self.formula_edit.insertPlainText(f"{{{col_name}}}")
        self.formula_edit.setFocus()
    
    def _validate_name(self):
        """Validate the column name."""
        name = self.name_edit.text().strip()
        
        if not name:
            self.name_error_label.setText("")
            self._update_ok_button()
            return False
        
        # In edit mode, exclude current name from duplicate check
        existing = [n for n in self.existing_names if not (self.is_edit_mode and 
                    self.column_metadata is not None and n == self.column_metadata.name)]
        
        # Check for duplicates
        if name in existing:
            self.name_error_label.setText(f"⚠ Column '{name}' already exists")
            self._update_ok_button()
            return False
        
        # Check for invalid characters
        if not name.replace("_", "").replace("-", "").isalnum():
            self.name_error_label.setText("⚠ Name should only contain letters, numbers, _, -")
            self._update_ok_button()
            return False
        
        # Valid
        self.name_error_label.setText("✓ Valid name")
        self.name_error_label.setStyleSheet("color: green; font-size: 9pt;")
        self._update_ok_button()
        return True
    
    def _load_existing_values(self):
        """Load existing column values when in edit mode."""
        if not self.is_edit_mode or self.column_metadata is None:
            return
        
        meta = self.column_metadata
        
        # Load basic properties
        self.name_edit.setText(meta.name)
        if meta.description:
            self.description_edit.setText(meta.description)
        if meta.unit:
            self.unit_edit.setText(meta.unit)
        self.precision_spin.setValue(meta.precision)
        
        # Load formula
        if meta.formula:
            self.formula_edit.setPlainText(meta.formula)
        
        # Load uncertainty propagation setting
        self.propagate_uncertainty_checkbox.setChecked(meta.propagate_uncertainty)
    
    def _validate_formula(self):
        """Validate the formula."""
        formula = self.formula_edit.toPlainText().strip()
        
        if not formula:
            self.formula_error_label.setText("")
            self._update_ok_button()
            return False
        
        # Basic validation - check for balanced braces
        if formula.count('{') != formula.count('}'):
            self.formula_error_label.setText("⚠ Unbalanced { } braces in formula")
            self._update_ok_button()
            return False
        
        # Check if referenced columns exist
        import re
        refs = re.findall(r'\{([^}]+)\}', formula)
        if self.model:
            available_cols = self.model.get_column_names()
            missing_cols = [ref for ref in refs if ref not in available_cols]
            if missing_cols:
                self.formula_error_label.setText(
                    f"⚠ Unknown column(s): {', '.join(missing_cols)}"
                )
                self._update_ok_button()
                return False
        
        # Valid
        self.formula_error_label.setText("✓ Valid formula")
        self.formula_error_label.setStyleSheet("color: green; font-size: 9pt;")
        self._update_ok_button()
        return True
    
    def _update_ok_button(self):
        """Enable OK button only if both name and formula are valid."""
        name_valid = bool(self.name_edit.text().strip()) and "✓" in self.name_error_label.text()
        formula_valid = bool(self.formula_edit.toPlainText().strip()) and "✓" in self.formula_error_label.text()
        self.ok_button.setEnabled(name_valid and formula_valid)
    
    def _on_uncertainty_toggled(self):
        """Handle uncertainty propagation checkbox toggle."""
        if self.propagate_uncertainty_checkbox.isChecked():
            # Show which columns have uncertainties
            if self.model:
                cols_with_unc = []
                for col_name in self.model.get_column_names():
                    if col_name.endswith("_u") or self.model._metadata[col_name].is_uncertainty_column():
                        # This is an uncertainty column, find its reference
                        data_col = col_name.replace("_u", "") if col_name.endswith("_u") else None
                        if data_col and data_col in self.model.get_column_names():
                            cols_with_unc.append(data_col)
                
                if cols_with_unc:
                    self.uncertainty_info_label.setText(
                        f"Columns with uncertainty: {', '.join(cols_with_unc)}\n\n"
                        f"A read-only column '{self.name_edit.text().strip() or 'name'}_u' will be created "
                        f"to store the propagated uncertainty."
                    )
                else:
                    self.uncertainty_info_label.setText(
                        "⚠ No columns currently have uncertainties.\n"
                        "The uncertainty column will be created but will contain zeros.\n"
                        "Add uncertainty columns (name_u) to enable propagation."
                    )
            else:
                self.uncertainty_info_label.setText(
                    f"A read-only column '{self.name_edit.text().strip() or 'name'}_u' will be created "
                    f"to store the propagated uncertainty."
                )
        else:
            self.uncertainty_info_label.setText("")
    
    def _update_preview(self):
        """Update the preview panel."""
        name = self.name_edit.text().strip() or "(enter name)"
        formula = self.formula_edit.toPlainText().strip() or "(enter formula)"
        
        preview_lines = [
            f"<b>Column Name:</b> {name}",
            f"<b>Formula:</b> {formula}",
            f"<b>Type:</b> CALCULATED (read-only)",
        ]
        
        if self.propagate_uncertainty_checkbox.isChecked():
            preview_lines.append(f"<b>Uncertainty Column:</b> {name}_u (auto-calculated, read-only)")
        
        self.preview_text.setHtml("<br>".join(preview_lines))
    
    def get_results(self) -> Dict[str, Any]:
        """Get the dialog results.
        
        Returns:
            Dictionary containing:
                - name: Column name
                - formula: Formula string
                - description: Description (or None)
                - precision: Display precision
                - propagate_uncertainty: Whether to propagate uncertainty
        """
        return {
            'name': self.name_edit.text().strip(),
            'formula': self.formula_edit.toPlainText().strip(),
            'description': self.description_edit.text().strip() or None,
            'precision': self.precision_spin.value(),
            'propagate_uncertainty': self.propagate_uncertainty_checkbox.isChecked()
        }


class AddRangeColumnDialog(QDialog):
    """Dialog for creating or editing a range column with evenly-spaced values.
    
    This dialog allows users to:
    - Set column name
    - Define start and end values
    - Choose number of points or step size
    - Set unit and description
    - Preview the generated values
    
    Supports both creation (column_metadata=None) and editing (column_metadata provided).
    """
    
    def __init__(self, parent=None, existing_names: Optional[List[str]] = None,
                 column_metadata: Optional['ColumnMetadata'] = None):
        """Initialize the dialog.
        
        Args:
            parent: Parent widget
            existing_names: List of existing column names to prevent duplicates
            column_metadata: If provided, dialog is in edit mode for this column
        """
        super().__init__(parent)
        self.existing_names = existing_names or []
        self.column_metadata = column_metadata
        self.is_edit_mode = column_metadata is not None
        
        # Set appropriate title
        if self.is_edit_mode and column_metadata is not None:
            self.setWindowTitle(f"Edit Range Column - {column_metadata.name}")
        else:
            self.setWindowTitle("Add Range Column")
        
        self.setModal(True)
        self.resize(500, 550)
        
        self._setup_ui()
        
        # Load existing values if in edit mode
        if self.is_edit_mode and column_metadata is not None:
            self._load_existing_values()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel(
            "Create a column with evenly-spaced values. Useful for creating x-axis data,\n"
            "time series, or any sequence of regularly-spaced measurements."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(instructions)
        
        # Column properties
        props_group = QGroupBox("Column Properties")
        props_layout = QFormLayout(props_group)
        
        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., time, x, angle")
        self.name_edit.textChanged.connect(self._validate_name)
        props_layout.addRow("Name*:", self.name_edit)
        
        self.name_error_label = QLabel()
        self.name_error_label.setStyleSheet("color: red; font-size: 9pt;")
        self.name_error_label.setWordWrap(True)
        props_layout.addRow("", self.name_error_label)
        
        # Unit
        unit_layout = QHBoxLayout()
        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText("e.g., s, m, deg")
        
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(COMMON_UNITS)
        self.unit_combo.currentTextChanged.connect(self._on_unit_combo_changed)
        
        unit_layout.addWidget(self.unit_edit, 2)
        unit_layout.addWidget(QLabel("Quick:"), 0)
        unit_layout.addWidget(self.unit_combo, 1)
        
        props_layout.addRow("Unit:", unit_layout)
        
        # Description
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Optional: Description shown as tooltip")
        props_layout.addRow("Description:", self.description_edit)
        
        layout.addWidget(props_group)
        
        # Range parameters
        range_group = QGroupBox("Range Parameters")
        range_layout = QFormLayout(range_group)
        
        # Start value
        self.start_spin = QDoubleSpinBox()
        self.start_spin.setRange(-1e15, 1e15)
        self.start_spin.setDecimals(6)
        self.start_spin.setValue(0.0)
        self.start_spin.valueChanged.connect(self._update_preview)
        range_layout.addRow("Start Value*:", self.start_spin)
        
        # End value
        self.end_spin = QDoubleSpinBox()
        self.end_spin.setRange(-1e15, 1e15)
        self.end_spin.setDecimals(6)
        self.end_spin.setValue(10.0)
        self.end_spin.valueChanged.connect(self._update_preview)
        range_layout.addRow("End Value*:", self.end_spin)
        
        # Method selection
        self.method_combo = QComboBox()
        self.method_combo.addItems(["Number of Points", "Step Size"])
        self.method_combo.currentTextChanged.connect(self._on_method_changed)
        range_layout.addRow("Method:", self.method_combo)
        
        # Number of points (default)
        self.points_spin = QSpinBox()
        self.points_spin.setRange(2, 1000000)
        self.points_spin.setValue(11)
        self.points_spin.valueChanged.connect(self._update_preview)
        self.points_row_label = QLabel("Number of Points*:")
        range_layout.addRow(self.points_row_label, self.points_spin)
        
        # Step size (hidden by default)
        self.step_spin = QDoubleSpinBox()
        self.step_spin.setRange(-1e15, 1e15)
        self.step_spin.setDecimals(6)
        self.step_spin.setValue(1.0)
        self.step_spin.setSingleStep(0.1)
        self.step_spin.valueChanged.connect(self._update_preview)
        self.step_row_label = QLabel("Step Size*:")
        range_layout.addRow(self.step_row_label, self.step_spin)
        
        # Hide step initially
        self.step_spin.hide()
        self.step_row_label.hide()
        
        # Precision
        self.precision_spin = QSpinBox()
        self.precision_spin.setRange(0, 15)
        self.precision_spin.setValue(6)
        self.precision_spin.setToolTip("Number of decimal places to display")
        range_layout.addRow("Precision:", self.precision_spin)
        
        layout.addWidget(range_group)
        
        # Preview
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(150)
        preview_layout.addWidget(self.preview_text)
        
        layout.addWidget(preview_group)
        
        # Connect updates
        self.name_edit.textChanged.connect(self._update_preview)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setEnabled(False)
        layout.addWidget(button_box)
        
        # Initial update
        self._update_preview()
    
    def _validate_name(self):
        """Validate the column name."""
        name = self.name_edit.text().strip()
        
        if not name:
            self.name_error_label.setText("")
            self._update_ok_button()
            return False
        
        # In edit mode, exclude current name from duplicate check
        existing = [n for n in self.existing_names if not (self.is_edit_mode and 
                    self.column_metadata is not None and n == self.column_metadata.name)]
        
        # Check for duplicates
        if name in existing:
            self.name_error_label.setText(f"⚠ Column '{name}' already exists")
            self._update_ok_button()
            return False
        
        # Check for invalid characters
        if not name.replace("_", "").replace("-", "").isalnum():
            self.name_error_label.setText("⚠ Name should only contain letters, numbers, _, -")
            self._update_ok_button()
            return False
        
        # Valid
        self.name_error_label.setText("✓ Valid name")
        self.name_error_label.setStyleSheet("color: green; font-size: 9pt;")
        self._update_ok_button()
        return True
    
    def _load_existing_values(self):
        """Load existing column values when in edit mode."""
        if not self.is_edit_mode or self.column_metadata is None:
            return
        
        meta = self.column_metadata
        
        # Load basic properties
        self.name_edit.setText(meta.name)
        if meta.description:
            self.description_edit.setText(meta.description)
        if meta.unit:
            self.unit_edit.setText(meta.unit)
        self.precision_spin.setValue(meta.precision)
        
        # Load range properties
        if meta.range_start is not None:
            self.start_spin.setValue(meta.range_start)
        if meta.range_end is not None:
            self.end_spin.setValue(meta.range_end)
        if meta.range_points is not None:
            self.points_spin.setValue(meta.range_points)
    
    def _update_ok_button(self):
        """Enable OK button only if name is valid."""
        name_valid = bool(self.name_edit.text().strip()) and "✓" in self.name_error_label.text()
        self.ok_button.setEnabled(name_valid)
    
    def _on_method_changed(self):
        """Handle method selection change."""
        is_points = self.method_combo.currentText() == "Number of Points"
        
        # Show/hide appropriate controls
        self.points_spin.setVisible(is_points)
        self.points_row_label.setVisible(is_points)
        self.step_spin.setVisible(not is_points)
        self.step_row_label.setVisible(not is_points)
        
        self._update_preview()
    
    def _on_unit_combo_changed(self, unit: str):
        """Update unit edit when combo selection changes."""
        if unit:
            self.unit_edit.setText(unit)
    
    def _update_preview(self):
        """Update the preview with calculated values."""
        start = self.start_spin.value()
        end = self.end_spin.value()
        
        # Calculate values based on method
        if self.method_combo.currentText() == "Number of Points":
            points = self.points_spin.value()
            if points > 1:
                step = (end - start) / (points - 1)
            else:
                step = 0
        else:
            step = self.step_spin.value()
            if step != 0:
                points = int(abs((end - start) / step)) + 1
            else:
                points = 0
        
        # Generate preview values (max 10 shown)
        preview_lines = [
            f"<b>Range:</b> {start} to {end}",
            f"<b>Points:</b> {points}",
            f"<b>Step:</b> {step:.6g}",
            "",
            f"<b>Values (first 10):</b>",
        ]
        
        if points > 0 and points <= 1000000:
            values = []
            for i in range(min(10, points)):
                val = start + i * step
                values.append(f"  [{i}] {val:.6g}")
            
            preview_lines.extend(values)
            
            if points > 10:
                preview_lines.append(f"  ... ({points - 10} more values)")
        else:
            preview_lines.append("  (invalid range)")
        
        self.preview_text.setHtml("<br>".join(preview_lines))
    
    def get_results(self) -> Dict[str, Any]:
        """Get the dialog results.
        
        Returns:
            Dictionary containing:
                - name: Column name
                - start: Start value
                - end: End value
                - points: Number of points
                - unit: Unit string (or None)
                - description: Description (or None)
                - precision: Display precision
        """
        start = self.start_spin.value()
        end = self.end_spin.value()
        
        # Calculate points based on method
        if self.method_combo.currentText() == "Number of Points":
            points = self.points_spin.value()
        else:
            step = self.step_spin.value()
            if step != 0:
                points = int(abs((end - start) / step)) + 1
            else:
                points = 2
        
        return {
            'name': self.name_edit.text().strip(),
            'start': start,
            'end': end,
            'points': points,
            'unit': self.unit_edit.text().strip() or None,
            'description': self.description_edit.text().strip() or None,
            'precision': self.precision_spin.value()
        }


class AddDerivativeColumnDialog(QDialog):
    """Dialog for creating or editing a derivative column.
    
    A derivative column calculates discrete differences: dy/dx
    Useful for velocities, accelerations, rates of change, slopes.
    
    Supports both creation (column_metadata=None) and editing (column_metadata provided).
    """
    
    def __init__(self, parent=None, model=None, existing_names: Optional[List[str]] = None,
                 column_metadata: Optional['ColumnMetadata'] = None):
        """Initialize the dialog.
        
        Args:
            parent: Parent widget
            model: DataTableModel instance for column reference
            existing_names: List of existing column names to prevent duplicates
            column_metadata: If provided, dialog is in edit mode for this column
        """
        super().__init__(parent)
        self.model = model
        self.existing_names = existing_names or []
        self.column_metadata = column_metadata
        self.is_edit_mode = column_metadata is not None
        
        # Set appropriate title
        if self.is_edit_mode and column_metadata is not None:
            self.setWindowTitle(f"Edit Derivative Column - {column_metadata.name}")
        else:
            self.setWindowTitle("Add Derivative Column")
        
        self.setModal(True)
        self.resize(500, 450)
        
        self._setup_ui()
        
        # Load existing values if in edit mode
        if self.is_edit_mode and column_metadata is not None:
            self._load_existing_values()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Explanation
        explanation = QLabel(
            "A derivative column calculates discrete differences: dy/dx\n"
            "For each row i: result[i] = (y[i+1] - y[i]) / (x[i+1] - x[i])"
        )
        explanation.setWordWrap(True)
        explanation.setStyleSheet("color: #666; font-size: 9pt; padding: 5px; margin-bottom: 10px;")
        layout.addWidget(explanation)
        
        # Column properties
        properties_group = QGroupBox("Column Properties")
        properties_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., velocity, acceleration, slope")
        self.name_edit.textChanged.connect(self._validate_and_update)
        properties_layout.addRow("Name*:", self.name_edit)
        
        self.name_error_label = QLabel()
        self.name_error_label.setStyleSheet("color: red; font-size: 9pt;")
        self.name_error_label.setWordWrap(True)
        properties_layout.addRow("", self.name_error_label)
        
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Optional: Description shown as tooltip")
        properties_layout.addRow("Description:", self.description_edit)
        
        self.precision_spin = QSpinBox()
        self.precision_spin.setRange(0, 15)
        self.precision_spin.setValue(6)
        self.precision_spin.setToolTip("Number of decimal places to display")
        properties_layout.addRow("Precision:", self.precision_spin)
        
        properties_group.setLayout(properties_layout)
        layout.addWidget(properties_group)
        
        # Derivative configuration
        derivative_group = QGroupBox("Derivative Configuration")
        derivative_layout = QFormLayout()
        
        # Numerator (dy)
        self.numerator_combo = QComboBox()
        self.numerator_combo.currentIndexChanged.connect(self._validate_and_update)
        derivative_layout.addRow("Numerator (dy)*:", self.numerator_combo)
        
        # Denominator (dx)
        self.denominator_combo = QComboBox()
        self.denominator_combo.currentIndexChanged.connect(self._validate_and_update)
        derivative_layout.addRow("Denominator (dx)*:", self.denominator_combo)
        
        derivative_group.setLayout(derivative_layout)
        layout.addWidget(derivative_group)
        
        # Populate combos
        self._populate_column_combos()
        
        # Preview
        preview_group = QGroupBox("Preview")
        preview_layout = QFormLayout()
        
        self.preview_unit_label = QLabel("(select columns)")
        preview_layout.addRow("Calculated Unit:", self.preview_unit_label)
        
        self.preview_header_label = QLabel("(enter name)")
        preview_layout.addRow("Header:", self.preview_header_label)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setEnabled(False)
        layout.addWidget(button_box)
    
    def _populate_column_combos(self):
        """Populate the column selection combos."""
        self.numerator_combo.clear()
        self.denominator_combo.clear()
        
        if not self.model:
            return
        
        # Add placeholder
        self.numerator_combo.addItem("-- Select Column --", None)
        self.denominator_combo.addItem("-- Select Column --", None)
        
        # Add all columns
        for col_name in self.model.get_column_names():
            metadata = self.model.get_column_metadata(col_name)
            
            # Get symbol
            symbol = metadata.get_symbol()
            
            # Format display text
            unit_text = f" [{metadata.unit}]" if metadata.unit else ""
            display_text = f"{symbol} {col_name}{unit_text}"
            
            self.numerator_combo.addItem(display_text, col_name)
            self.denominator_combo.addItem(display_text, col_name)
    
    def _validate_and_update(self):
        """Validate inputs and update preview."""
        # Validate name
        name = self.name_edit.text().strip()
        name_valid = False
        
        if not name:
            self.name_error_label.setText("")
        else:
            # In edit mode, exclude current name from duplicate check
            existing = [n for n in self.existing_names if not (self.is_edit_mode and 
                        self.column_metadata is not None and n == self.column_metadata.name)]
            
            if name in existing:
                self.name_error_label.setText(f"⚠ Column '{name}' already exists")
            elif not name.replace("_", "").replace("-", "").isalnum():
                self.name_error_label.setText("⚠ Name should only contain letters, numbers, _, -")
            else:
                self.name_error_label.setText("✓ Valid name")
                self.name_error_label.setStyleSheet("color: green; font-size: 9pt;")
                name_valid = True
        
        # Validate column selections
        num_col = self.numerator_combo.currentData()
        den_col = self.denominator_combo.currentData()
        
        cols_valid = num_col is not None and den_col is not None and num_col != den_col
        
        # Update preview
        if cols_valid and self.model:
            num_meta = self.model.get_column_metadata(num_col)
            den_meta = self.model.get_column_metadata(den_col)
            
            # Calculate unit
            num_unit = num_meta.unit or "dimensionless"
            den_unit = den_meta.unit or "dimensionless"
            
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
            preview_name = name or "(enter name)"
            self.preview_header_label.setText(f"∂ {preview_name} [{result_unit}]")
        else:
            self.preview_unit_label.setText("(select columns)")
            self.preview_header_label.setText("(enter name)")
        
        # Enable OK button
        self.ok_button.setEnabled(name_valid and cols_valid)
    
    def _load_existing_values(self):
        """Load existing column values when in edit mode."""
        if not self.is_edit_mode or self.column_metadata is None:
            return
        
        meta = self.column_metadata
        
        # Load basic properties
        self.name_edit.setText(meta.name)
        if meta.description:
            self.description_edit.setText(meta.description)
        self.precision_spin.setValue(meta.precision)
        
        # Load derivative configuration
        if meta.derivative_numerator:
            for i in range(self.numerator_combo.count()):
                if self.numerator_combo.itemData(i) == meta.derivative_numerator:
                    self.numerator_combo.setCurrentIndex(i)
                    break
        
        if meta.derivative_denominator:
            for i in range(self.denominator_combo.count()):
                if self.denominator_combo.itemData(i) == meta.derivative_denominator:
                    self.denominator_combo.setCurrentIndex(i)
                    break
    
    def get_results(self) -> Dict[str, Any]:
        """Get the dialog results.
        
        Returns:
            Dictionary containing:
                - name: Column name
                - numerator_column: Name of numerator column
                - denominator_column: Name of denominator column
                - description: Description (or None)
                - precision: Display precision
        """
        return {
            'name': self.name_edit.text().strip(),
            'numerator_column': self.numerator_combo.currentData(),
            'denominator_column': self.denominator_combo.currentData(),
            'description': self.description_edit.text().strip() or None,
            'precision': self.precision_spin.value()
        }


class AddInterpolationColumnDialog(QDialog):
    """Dialog for creating or editing an interpolation column.
    
    Interpolation columns calculate values by interpolating between data points.
    Useful for: sparse data interpolation, resampling, curve fitting.
    
    Supports both creation (column_metadata=None) and editing (column_metadata provided).
    """
    
    def __init__(self, parent=None, model=None, existing_names: Optional[List[str]] = None,
                 column_metadata: Optional['ColumnMetadata'] = None):
        """Initialize the dialog.
        
        Args:
            parent: Parent widget
            model: DataTableModel instance for column reference
            existing_names: List of existing column names to prevent duplicates
            column_metadata: If provided, dialog is in edit mode for this column
        """
        super().__init__(parent)
        self.model = model
        self.existing_names = existing_names or []
        self.column_metadata = column_metadata
        self.is_edit_mode = column_metadata is not None
        
        # Set appropriate title
        if self.is_edit_mode and column_metadata is not None:
            self.setWindowTitle(f"Edit Interpolation Column - {column_metadata.name}")
        else:
            self.setWindowTitle("Add Interpolation Column")
        
        self.setModal(True)
        self.resize(550, 550)
        
        self._setup_ui()
        
        # Load existing values if in edit mode
        if self.is_edit_mode and column_metadata is not None:
            self._load_existing_values()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Explanation
        explanation = QLabel(
            "Interpolation columns calculate values by interpolating between data points.\n"
            "Define source X and Y columns, then specify where to evaluate the interpolation."
        )
        explanation.setWordWrap(True)
        explanation.setStyleSheet("color: #666; font-size: 9pt; padding: 5px; margin-bottom: 10px;")
        layout.addWidget(explanation)
        
        # Column properties
        properties_group = QGroupBox("Column Properties")
        properties_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., interpolated_temp, fitted_curve")
        self.name_edit.textChanged.connect(self._validate_and_update)
        properties_layout.addRow("Name*:", self.name_edit)
        
        self.name_error_label = QLabel()
        self.name_error_label.setStyleSheet("color: red; font-size: 9pt;")
        self.name_error_label.setWordWrap(True)
        properties_layout.addRow("", self.name_error_label)
        
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Optional: Description shown as tooltip")
        properties_layout.addRow("Description:", self.description_edit)
        
        self.precision_spin = QSpinBox()
        self.precision_spin.setRange(0, 15)
        self.precision_spin.setValue(6)
        self.precision_spin.setToolTip("Number of decimal places to display")
        properties_layout.addRow("Precision:", self.precision_spin)
        
        properties_group.setLayout(properties_layout)
        layout.addWidget(properties_group)
        
        # Source data configuration
        source_group = QGroupBox("Source Data for Interpolation")
        source_layout = QFormLayout()
        
        # X column (independent variable)
        self.x_column_combo = QComboBox()
        self.x_column_combo.currentIndexChanged.connect(self._validate_and_update)
        source_layout.addRow("X Column (data)*:", self.x_column_combo)
        
        # Y column (dependent variable)
        self.y_column_combo = QComboBox()
        self.y_column_combo.currentIndexChanged.connect(self._validate_and_update)
        source_layout.addRow("Y Column (data)*:", self.y_column_combo)
        
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)
        
        # Interpolation method
        method_group = QGroupBox("Interpolation Method")
        method_layout = QFormLayout()
        
        self.method_combo = QComboBox()
        self.method_combo.addItem("Linear", "linear")
        self.method_combo.addItem("Cubic Spline", "cubic")
        self.method_combo.addItem("Quadratic", "quadratic")
        self.method_combo.addItem("Nearest Neighbor", "nearest")
        method_layout.addRow("Method*:", self.method_combo)
        
        method_group.setLayout(method_layout)
        layout.addWidget(method_group)
        
        # Populate combos
        self._populate_column_combos()
        
        # Preview
        preview_group = QGroupBox("Preview")
        preview_layout = QFormLayout()
        
        self.preview_unit_label = QLabel("(select Y column)")
        preview_layout.addRow("Unit (from Y):", self.preview_unit_label)
        
        self.preview_header_label = QLabel("(enter name)")
        preview_layout.addRow("Header:", self.preview_header_label)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setEnabled(False)
        layout.addWidget(button_box)
    
    def _populate_column_combos(self):
        """Populate the column selection combos."""
        self.x_column_combo.clear()
        self.y_column_combo.clear()
        
        if not self.model:
            return
        
        # Add placeholder
        self.x_column_combo.addItem("-- Select Column --", None)
        self.y_column_combo.addItem("-- Select Column --", None)
        
        # Add all numeric columns
        for col_name in self.model.get_column_names():
            metadata = self.model.get_column_metadata(col_name)
            
            # Only add numeric columns
            if metadata.dtype not in (DataType.FLOAT, DataType.INTEGER):
                continue
            
            # Get symbol
            symbol = metadata.get_symbol()
            
            # Format display text
            unit_text = f" [{metadata.unit}]" if metadata.unit else ""
            display_text = f"{symbol} {col_name}{unit_text}"
            
            self.x_column_combo.addItem(display_text, col_name)
            self.y_column_combo.addItem(display_text, col_name)
    
    def _validate_and_update(self):
        """Validate inputs and update preview."""
        # Validate name
        name = self.name_edit.text().strip()
        name_valid = False
        
        if not name:
            self.name_error_label.setText("")
        else:
            # In edit mode, exclude current name from duplicate check
            existing = [n for n in self.existing_names if not (self.is_edit_mode and 
                        self.column_metadata is not None and n == self.column_metadata.name)]
            
            if name in existing:
                self.name_error_label.setText(f"⚠ Column '{name}' already exists")
            elif not name.replace("_", "").replace("-", "").isalnum():
                self.name_error_label.setText("⚠ Name should only contain letters, numbers, _, -")
            else:
                self.name_error_label.setText("✓ Valid name")
                self.name_error_label.setStyleSheet("color: green; font-size: 9pt;")
                name_valid = True
        
        # Validate column selections
        x_col = self.x_column_combo.currentData()
        y_col = self.y_column_combo.currentData()
        
        cols_valid = x_col is not None and y_col is not None
        
        # Update preview
        if cols_valid and y_col and self.model:
            y_meta = self.model.get_column_metadata(y_col)
            unit = y_meta.unit or "dimensionless"
            
            self.preview_unit_label.setText(unit)
            
            # Preview header
            preview_name = name or "(enter name)"
            self.preview_header_label.setText(f"⌇ {preview_name} [{unit}]")
        else:
            self.preview_unit_label.setText("(select Y column)")
            self.preview_header_label.setText("(enter name)")
        
        # Enable OK button
        self.ok_button.setEnabled(name_valid and cols_valid)
    
    def _load_existing_values(self):
        """Load existing column values when in edit mode."""
        if not self.is_edit_mode or self.column_metadata is None:
            return
        
        meta = self.column_metadata
        
        # Load basic properties
        self.name_edit.setText(meta.name)
        if meta.description:
            self.description_edit.setText(meta.description)
        self.precision_spin.setValue(meta.precision)
        
        # Load interpolation configuration
        if meta.interp_x_column:
            for i in range(self.x_column_combo.count()):
                if self.x_column_combo.itemData(i) == meta.interp_x_column:
                    self.x_column_combo.setCurrentIndex(i)
                    break
        
        if meta.interp_y_column:
            for i in range(self.y_column_combo.count()):
                if self.y_column_combo.itemData(i) == meta.interp_y_column:
                    self.y_column_combo.setCurrentIndex(i)
                    break
        
        if meta.interp_method:
            for i in range(self.method_combo.count()):
                if self.method_combo.itemData(i) == meta.interp_method:
                    self.method_combo.setCurrentIndex(i)
                    break
    
    def get_results(self) -> Dict[str, Any]:
        """Get the dialog results.
        
        Returns:
            Dictionary containing:
                - name: Column name
                - x_column: Name of X column
                - y_column: Name of Y column
                - method: Interpolation method
                - description: Description (or None)
                - precision: Display precision
        """
        y_col = self.y_column_combo.currentData()
        unit = None
        if y_col and self.model:
            y_meta = self.model.get_column_metadata(y_col)
            unit = y_meta.unit
        
        return {
            'name': self.name_edit.text().strip(),
            'x_column': self.x_column_combo.currentData(),
            'y_column': self.y_column_combo.currentData(),
            'method': self.method_combo.currentData(),
            'unit': unit,
            'description': self.description_edit.text().strip() or None,
            'precision': self.precision_spin.value()
        }


class AddUncertaintyColumnDialog(QDialog):
    """Dialog for adding a manual uncertainty column."""
    
    def __init__(self, model: 'DataTableModel', column_name: Optional[str] = None, parent=None):
        """Initialize the dialog.
        
        Args:
            model: DataTableModel instance
            column_name: Name of existing column to edit (for edit mode)
            parent: Parent widget
        """
        super().__init__(parent)
        self.model = model
        self.column_name = column_name
        self.is_edit_mode = column_name is not None
        
        self.setWindowTitle("Edit Uncertainty Column" if self.is_edit_mode else "Add Uncertainty Column")
        self.setModal(True)
        
        # Create form layout
        form_layout = QFormLayout()
        
        # Column name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., Temperature_u, Pressure_u")
        form_layout.addRow("Column Name:", self.name_edit)
        
        # Reference column dropdown
        self.ref_column_combo = QComboBox()
        self.ref_column_combo.currentIndexChanged.connect(self._on_ref_column_changed)
        form_layout.addRow("Reference Column:", self.ref_column_combo)
        
        # Unit (auto-populated from reference column)
        self.unit_edit = QLineEdit()
        self.unit_edit.setReadOnly(True)
        self.unit_edit.setPlaceholderText("Auto-populated from reference column")
        form_layout.addRow("Unit:", self.unit_edit)
        
        # Description
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Optional description")
        form_layout.addRow("Description:", self.description_edit)
        
        # Precision
        self.precision_spin = QSpinBox()
        self.precision_spin.setRange(0, 10)
        self.precision_spin.setValue(2)
        form_layout.addRow("Display Precision:", self.precision_spin)
        
        # Add info label
        info_label = QLabel("This creates an editable uncertainty column where you can manually enter uncertainty values.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; font-size: 9pt;")
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Main layout
        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(info_label)
        layout.addWidget(button_box)
        self.setLayout(layout)
        
        # Populate fields
        self._populate_reference_columns()
        if self.is_edit_mode:
            self._load_existing_column()
    
    def _populate_reference_columns(self):
        """Populate the reference column dropdown with data columns."""
        self.ref_column_combo.clear()
        
        for col_name in self.model.get_column_names():
            meta = self.model.get_column_metadata(col_name)
            # Only allow DATA and CALCULATED columns as references
            if meta.column_type in [ColumnType.DATA, ColumnType.CALCULATED]:
                display_text = f"{col_name}"
                if meta.unit:
                    display_text += f" ({meta.unit})"
                self.ref_column_combo.addItem(display_text, col_name)
    
    def _on_ref_column_changed(self, index: int):
        """Update unit when reference column changes."""
        if index >= 0:
            ref_col = self.ref_column_combo.currentData()
            if ref_col:
                meta = self.model.get_column_metadata(ref_col)
                self.unit_edit.setText(meta.unit or "")
                
                # Auto-suggest name if not in edit mode and name is empty
                if not self.is_edit_mode and not self.name_edit.text():
                    self.name_edit.setText(f"{ref_col}_u")
    
    def _load_existing_column(self):
        """Load existing column data for editing."""
        meta = self.model.get_column_metadata(self.column_name)
        self.name_edit.setText(self.column_name)
        self.name_edit.setReadOnly(True)  # Can't change name in edit mode
        
        # Set reference column
        if meta.uncertainty_reference is not None:
            ref_name = self.model.get_column_names()[meta.uncertainty_reference]
            for i in range(self.ref_column_combo.count()):
                if self.ref_column_combo.itemData(i) == ref_name:
                    self.ref_column_combo.setCurrentIndex(i)
                    break
        
        if meta.description:
            self.description_edit.setText(meta.description)
        
        self.precision_spin.setValue(meta.precision)
    
    def get_results(self) -> Dict[str, Any]:
        """Get the dialog results.
        
        Returns:
            Dictionary containing:
                - name: Column name
                - reference_column: Name of reference column
                - unit: Unit (from reference column)
                - description: Description (or None)
                - precision: Display precision
        """
        return {
            'name': self.name_edit.text().strip(),
            'reference_column': self.ref_column_combo.currentData(),
            'unit': self.unit_edit.text() or None,
            'description': self.description_edit.text().strip() or None,
            'precision': self.precision_spin.value()
        }


