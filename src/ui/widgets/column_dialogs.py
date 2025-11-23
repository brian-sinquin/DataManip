"""Unified column management dialogs using base classes.

Consolidates column_dialogs.py and column_dialogs_extended.py,
eliminating duplication while maintaining all functionality.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QComboBox, QPushButton,
    QLabel, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QSpinBox, QDoubleSpinBox, QGroupBox
)
from PySide6.QtCore import Qt

from studies.data_table_study import ColumnType
from .shared.base_dialog import BaseDialog, BaseColumnDialog
from .shared.dialog_utils import show_warning, show_info


class AddDataColumnDialog(BaseColumnDialog):
    """Dialog for adding a data column."""
    
    def __init__(self, existing_columns=None, parent=None):
        super().__init__(
            title="Add Data Column",
            description=None,
            parent=parent,
            width=400,
            height=200,
            existing_columns=existing_columns or []
        )
        
        # Customize unit placeholder
        self.unit_edit.setPlaceholderText("e.g., m, s, kg, m/s^2")
    
    def get_values(self):
        """Get dialog values."""
        return self.name_edit.text().strip(), self.unit_edit.text().strip() or None


class AddUncertaintyColumnDialog(BaseColumnDialog):
    """Dialog for adding an uncertainty column."""
    
    def __init__(self, available_columns, existing_columns=None, parent=None):
        super().__init__(
            title="Add Uncertainty Column",
            description=(
                "Create a column for manual uncertainty values.\n"
                "For automatic uncertainty propagation, use the checkbox\n"
                "in the Calculated Column dialog instead."
            ),
            parent=parent,
            width=400,
            height=250,
            existing_columns=existing_columns or []
        )
        
        self.available_columns = available_columns
        
        # Customize name placeholder
        self.name_edit.setPlaceholderText("e.g., velocity_u, mass_u")
        
        # Add reference column selector
        self.reference_combo = QComboBox()
        self.reference_combo.addItem("(none)", None)
        for col in available_columns:
            self.reference_combo.addItem(col, col)
        self.add_form_row("References column:", self.reference_combo)
    
    def get_values(self):
        """Get dialog values."""
        name = self.name_edit.text().strip()
        unit = self.unit_edit.text().strip() or None
        ref_col = self.reference_combo.currentData()
        return name, unit, ref_col


class AddCalculatedColumnDialog(BaseColumnDialog):
    """Dialog for adding a calculated column."""
    
    def __init__(self, available_columns, available_variables, existing_columns=None, parent=None):
        super().__init__(
            title="Add Calculated Column",
            description=None,
            parent=parent,
            width=500,
            height=450,
            existing_columns=existing_columns or []
        )
        
        self.available_columns = available_columns
        self.available_variables = available_variables
        
        # Formula section
        formula_label = QLabel("<b>Formula:</b>")
        self.add_widget(formula_label)
        
        self.formula_edit = QTextEdit()
        self.formula_edit.setPlaceholderText(
            "Enter formula using {column} or {variable} syntax\n"
            "Example: {x} * 2 + {y}"
        )
        self.formula_edit.setMaximumHeight(100)
        self.add_widget(self.formula_edit)
        
        # Help text
        help_text = (
            f"<b>Available:</b><br>"
            f"Columns: {', '.join(available_columns) if available_columns else 'none'}<br>"
            f"Variables: {', '.join(available_variables) if available_variables else 'none'}<br><br>"
            f"<b>Functions:</b> sqrt, sin, cos, tan, exp, log, log10, abs, arcsin, arccos, arctan, pi, e<br>"
            f"<b>Operators:</b> +, -, *, /, **, %, //<br>"
            f"<b>Use np. prefix for numpy functions</b> (e.g., np.mean, np.sum)"
        )
        self.add_help_text(help_text)
        
        # Uncertainty propagation
        self.uncertainty_checkbox = QCheckBox("Automatically propagate uncertainty")
        self.uncertainty_checkbox.setToolTip(
            "Auto-creates uncertainty column: [name]_u\n\n"
            "Uses symbolic differentiation: δf = √(Σ(∂f/∂xᵢ · δxᵢ)²)\n\n"
            "Requires uncertainty columns ([var]_u) for each variable.\n"
            "Example: If formula uses {mass} and {velocity},\n"
            "you need mass_u and velocity_u columns."
        )
        self.add_widget(self.uncertainty_checkbox)
        
        # Add validate button before OK button
        self.validate_btn = QPushButton("Validate Formula")
        self.validate_btn.clicked.connect(self._validate_formula)
        self.button_layout.insertWidget(self.button_layout.count() - 2, self.validate_btn)
    
    def _validate_formula(self):
        """Validate formula syntax."""
        formula = self.formula_edit.toPlainText().strip()
        
        if not formula:
            show_warning(self, "Validation", "Formula is empty")
            return
        
        from core.formula_engine import FormulaEngine
        
        engine = FormulaEngine()
        available = self.available_columns + self.available_variables
        
        valid, error = engine.validate_formula(formula, available)
        
        if valid:
            show_info(self, "Validation", "Formula is valid!")
        else:
            show_warning(self, "Validation Error", error or "Unknown error")
    
    def validate(self) -> bool:
        """Validate form."""
        if not super().validate():
            return False
        
        formula = self.formula_edit.toPlainText().strip()
        if not formula:
            show_warning(self, "Error", "Formula is required")
            return False
        
        return True
    
    def get_values(self):
        """Get dialog values."""
        name = self.name_edit.text().strip()
        formula = self.formula_edit.toPlainText().strip()
        unit = self.unit_edit.text().strip() or None
        propagate_uncertainty = self.uncertainty_checkbox.isChecked()
        return name, formula, unit, propagate_uncertainty


class AddDerivativeColumnDialog(BaseColumnDialog):
    """Dialog for adding a derivative column."""
    
    def __init__(self, available_columns, existing_columns=None, parent=None):
        super().__init__(
            title="Add Derivative Column",
            description=(
                "Create a column with numerical derivative: dy/dx\n"
                "Uses numpy.gradient for centered differences."
            ),
            parent=parent,
            width=450,
            height=350,
            existing_columns=existing_columns or []
        )
        
        self.available_columns = available_columns
        
        # Customize name placeholder
        self.name_edit.setPlaceholderText("e.g., velocity, acceleration")
        
        # Add derivative-specific fields
        self.y_combo = QComboBox()
        self.y_combo.addItems(available_columns)
        self.add_form_row("Numerator (y):", self.y_combo)
        
        self.x_combo = QComboBox()
        self.x_combo.addItems(available_columns)
        if len(available_columns) > 1:
            self.x_combo.setCurrentIndex(1)
        self.add_form_row("Denominator (x):", self.x_combo)
        
        self.order_spin = QSpinBox()
        self.order_spin.setMinimum(1)
        self.order_spin.setMaximum(3)
        self.order_spin.setValue(1)
        self.add_form_row("Derivative Order:", self.order_spin)
        
        # Help text
        help_text = (
            "<b>Examples:</b><br>"
            "• Velocity: dy/dt with y=position, x=time<br>"
            "• Acceleration: dv/dt with y=velocity, x=time, order=1<br>"
            "• Or: d²y/dt² with y=position, x=time, order=2"
        )
        self.add_help_text(help_text)
    
    def get_values(self):
        """Get dialog values."""
        name = self.name_edit.text().strip()
        y_col = self.y_combo.currentText().strip()
        x_col = self.x_combo.currentText().strip()
        order = self.order_spin.value()
        unit = self.unit_edit.text().strip() or None
        return name, y_col, x_col, order, unit


class AddRangeColumnDialog(BaseColumnDialog):
    """Dialog for adding a range column (auto-generated sequence)."""
    
    def __init__(self, existing_columns=None, parent=None):
        super().__init__(
            title="Add Range Column",
            description=(
                "Create a column with auto-generated sequence.\n"
                "Perfect for time series or independent variables."
            ),
            parent=parent,
            width=450,
            height=400,
            existing_columns=existing_columns or []
        )
        
        # Customize name placeholder
        self.name_edit.setPlaceholderText("e.g., time, frequency")
        self.unit_edit.setPlaceholderText("e.g., s, Hz, m")
        
        # Range type selector
        self.type_combo = QComboBox()
        self.type_combo.addItems(["linspace", "arange", "logspace"])
        self.type_combo.currentTextChanged.connect(self._update_fields)
        self.add_form_row("Range Type:", self.type_combo)
        
        # Range parameters in a group box
        self.params_group = QGroupBox("Range Parameters")
        params_layout = QFormLayout()
        
        self.start_spin = QDoubleSpinBox()
        self.start_spin.setRange(-1e9, 1e9)
        self.start_spin.setDecimals(6)
        self.start_spin.setValue(0.0)
        params_layout.addRow("Start:", self.start_spin)
        
        self.stop_spin = QDoubleSpinBox()
        self.stop_spin.setRange(-1e9, 1e9)
        self.stop_spin.setDecimals(6)
        self.stop_spin.setValue(10.0)
        params_layout.addRow("Stop:", self.stop_spin)
        
        self.count_spin = QSpinBox()
        self.count_spin.setRange(2, 100000)
        self.count_spin.setValue(101)
        params_layout.addRow("Count:", self.count_spin)
        
        self.step_spin = QDoubleSpinBox()
        self.step_spin.setRange(1e-9, 1e9)
        self.step_spin.setDecimals(6)
        self.step_spin.setValue(1.0)
        params_layout.addRow("Step:", self.step_spin)
        
        self.params_group.setLayout(params_layout)
        self.add_widget(self.params_group)
        
        # Help text
        self.help_label = QLabel()
        self.help_label.setWordWrap(True)
        self.add_widget(self.help_label)
        
        self._update_fields("linspace")
    
    def _update_fields(self, range_type: str):
        """Update visible fields based on range type."""
        params_layout = self.params_group.layout()
        
        if range_type == "linspace":
            self.count_spin.setVisible(True)
            params_layout.labelForField(self.count_spin).setVisible(True)
            self.step_spin.setVisible(False)
            params_layout.labelForField(self.step_spin).setVisible(False)
            
            self.help_label.setText(
                "<small><b>linspace:</b> Generate 'Count' evenly spaced values "
                "from 'Start' to 'Stop' (inclusive).<br>"
                "Example: linspace(0, 10, 11) → [0, 1, 2, ..., 10]</small>"
            )
        
        elif range_type == "arange":
            self.count_spin.setVisible(False)
            params_layout.labelForField(self.count_spin).setVisible(False)
            self.step_spin.setVisible(True)
            params_layout.labelForField(self.step_spin).setVisible(True)
            
            self.help_label.setText(
                "<small><b>arange:</b> Generate values from 'Start' to 'Stop' "
                "with 'Step' increment (Stop excluded).<br>"
                "Example: arange(0, 5, 0.5) → [0, 0.5, 1.0, ..., 4.5]</small>"
            )
        
        elif range_type == "logspace":
            self.count_spin.setVisible(True)
            params_layout.labelForField(self.count_spin).setVisible(True)
            self.step_spin.setVisible(False)
            params_layout.labelForField(self.step_spin).setVisible(False)
            
            self.help_label.setText(
                "<small><b>logspace:</b> Generate 'Count' logarithmically spaced values. "
                "'Start' and 'Stop' are exponents (base 10).<br>"
                "Example: logspace(0, 3, 4) → [10⁰, 10¹, 10², 10³] = [1, 10, 100, 1000]</small>"
            )
    
    def get_values(self):
        """Get dialog values."""
        range_type = self.type_combo.currentText()
        
        result = {
            "name": self.name_edit.text().strip(),
            "range_type": range_type,
            "unit": self.unit_edit.text().strip() or None,
            "start": self.start_spin.value(),
            "stop": self.stop_spin.value(),
        }
        
        if range_type in ["linspace", "logspace"]:
            result["count"] = self.count_spin.value()
            result["step"] = None
        else:  # arange
            result["count"] = None
            result["step"] = self.step_spin.value()
        
        return result


class EditDataColumnDialog(BaseColumnDialog):
    """Dialog for editing data column properties."""
    
    def __init__(self, col_name: str, unit: str | None = None, existing_columns=None, parent=None):
        super().__init__(
            title=f"Edit Column: {col_name}",
            description=None,
            parent=parent,
            width=400,
            height=200,
            existing_columns=existing_columns or []
        )
        
        self.original_name = col_name
        
        # Pre-fill values
        self.name_edit.setText(col_name)
        if unit:
            self.unit_edit.setText(unit)
        
        # Add info message
        info = QLabel(
            "<small><i>Note: Renaming will update all formulas referencing this column.</i></small>"
        )
        info.setWordWrap(True)
        self.add_widget(info)
    
    def get_values(self):
        """Get dialog values."""
        return self.name_edit.text().strip(), self.unit_edit.text().strip() or None


class EditUncertaintyColumnDialog(BaseColumnDialog):
    """Dialog for editing uncertainty column properties."""
    
    def __init__(self, col_name: str, current_unit: str, current_ref: str,
                 available_columns, existing_columns=None, parent=None):
        super().__init__(
            title=f"Edit Uncertainty Column: {col_name}",
            description=(
                "Edit manual uncertainty column properties.\n"
                "Auto-propagated uncertainty columns cannot change their reference."
            ),
            parent=parent,
            width=400,
            height=250,
            existing_columns=existing_columns or []
        )
        
        # Pre-fill values
        self.name_edit.setText(col_name)
        if current_unit:
            self.unit_edit.setText(current_unit)
        
        # Add reference column selector
        self.reference_combo = QComboBox()
        self.reference_combo.addItem("(none)", None)
        for col in available_columns:
            self.reference_combo.addItem(col, col)
        if current_ref:
            idx = self.reference_combo.findData(current_ref)
            if idx >= 0:
                self.reference_combo.setCurrentIndex(idx)
        self.add_form_row("References column:", self.reference_combo)
    
    def get_values(self):
        """Get dialog values."""
        name = self.name_edit.text().strip()
        unit = self.unit_edit.text().strip() or None
        ref_col = self.reference_combo.currentData()
        return name, unit, ref_col


class CSVImportDialog(BaseDialog):
    """Advanced CSV import dialog with preview and configuration options."""
    
    def __init__(self, filepath: str, parent=None):
        import os
        filename = os.path.basename(filepath)
        
        super().__init__(
            title=f"Import CSV: {filename}",
            description=None,
            parent=parent,
            width=800,
            height=600
        )
        
        self.filepath = filepath
        
        # Override buttons for custom layout
        self.cancel_btn.setVisible(False)
        self.ok_btn.setVisible(False)
        
        # Configuration section
        config_label = QLabel("<b>Import Configuration</b>")
        self.add_widget(config_label)
        
        # Delimiter
        self.delimiter_combo = QComboBox()
        self.delimiter_combo.addItems(["Comma (,)", "Semicolon (;)", "Tab", "Space", "Custom"])
        self.delimiter_combo.currentIndexChanged.connect(self._toggle_custom_delimiter)
        self.add_form_row("Delimiter:", self.delimiter_combo)
        
        self.custom_delimiter_edit = QLineEdit(",")
        self.custom_delimiter_edit.setMaximumWidth(100)
        self.custom_delimiter_edit.setVisible(False)
        self.add_form_row("Custom Delimiter:", self.custom_delimiter_edit)
        
        # Header row
        self.header_row_spin = QSpinBox()
        self.header_row_spin.setRange(-1, 100)
        self.header_row_spin.setValue(0)
        self.header_row_spin.setSpecialValueText("No header")
        self.header_row_spin.setToolTip("Row number to use as column headers (0-indexed). Set to -1 for no header.")
        self.add_form_row("Header Row:", self.header_row_spin)
        
        # Skip rows
        self.skip_rows_spin = QSpinBox()
        self.skip_rows_spin.setRange(0, 1000)
        self.skip_rows_spin.setValue(0)
        self.skip_rows_spin.setToolTip("Number of rows to skip at the beginning (before header)")
        self.add_form_row("Skip Rows:", self.skip_rows_spin)
        
        # Encoding
        self.encoding_combo = QComboBox()
        self.encoding_combo.addItems(["utf-8", "latin-1", "cp1252", "iso-8859-1", "ascii"])
        self.encoding_combo.setToolTip("File encoding (use utf-8 for most modern files)")
        self.add_form_row("Encoding:", self.encoding_combo)
        
        # Decimal separator
        self.decimal_combo = QComboBox()
        self.decimal_combo.addItems(["Period (.)", "Comma (,)"])
        self.decimal_combo.setToolTip("Decimal separator for numbers")
        self.add_form_row("Decimal:", self.decimal_combo)
        
        # Metadata checkbox
        self.has_metadata_checkbox = QCheckBox("File contains metadata comments (#)")
        self.has_metadata_checkbox.setChecked(True)
        self.has_metadata_checkbox.setToolTip("Check if CSV has metadata in comment lines starting with #")
        self.add_widget(self.has_metadata_checkbox)
        
        # Preview section
        preview_label = QLabel("<b>Preview</b>")
        self.add_widget(preview_label)
        
        self.preview_table = QTableWidget()
        self.preview_table.setMaximumHeight(300)
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.add_widget(self.preview_table)
        
        # Status label
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.add_widget(self.status_label)
        
        # Custom buttons
        custom_layout = QHBoxLayout()
        custom_layout.addStretch()
        
        refresh_btn = QPushButton("Refresh Preview")
        refresh_btn.clicked.connect(self._update_preview)
        custom_layout.addWidget(refresh_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        custom_layout.addWidget(cancel_btn)
        
        import_btn = QPushButton("Import")
        import_btn.setDefault(True)
        import_btn.clicked.connect(self.accept)
        custom_layout.addWidget(import_btn)
        
        self.main_layout.addLayout(custom_layout)
        
        # Initial preview
        self._update_preview()
    
    def _toggle_custom_delimiter(self):
        """Show/hide custom delimiter input."""
        is_custom = self.delimiter_combo.currentText() == "Custom"
        self.custom_delimiter_edit.setVisible(is_custom)
        self.form_layout.labelForField(self.custom_delimiter_edit).setVisible(is_custom)
    
    def _get_delimiter(self) -> str:
        """Get current delimiter setting."""
        delim_map = {
            "Comma (,)": ",",
            "Semicolon (;)": ";",
            "Tab": "\t",
            "Space": " ",
            "Custom": self.custom_delimiter_edit.text() or ","
        }
        return delim_map[self.delimiter_combo.currentText()]
    
    def _get_decimal(self) -> str:
        """Get decimal separator."""
        return "." if self.decimal_combo.currentIndex() == 0 else ","
    
    def _update_preview(self):
        """Update preview table."""
        import pandas as pd
        
        try:
            delimiter = self._get_delimiter()
            encoding = self.encoding_combo.currentText()
            decimal = self._get_decimal()
            skip_rows = self.skip_rows_spin.value()
            header_row = self.header_row_spin.value()
            header = None if header_row < 0 else header_row
            
            df = pd.read_csv(
                self.filepath,
                delimiter=delimiter,
                encoding=encoding,
                decimal=decimal,
                skiprows=skip_rows if skip_rows > 0 else None,
                header=header,
                nrows=20,
                comment='#' if self.has_metadata_checkbox.isChecked() else None
            )
            
            if header is None:
                df.columns = [f"Column_{i}" for i in range(len(df.columns))]
            
            self.preview_table.clear()
            self.preview_table.setRowCount(len(df))
            self.preview_table.setColumnCount(len(df.columns))
            self.preview_table.setHorizontalHeaderLabels([str(col) for col in df.columns])
            
            for i, row in df.iterrows():
                for j, value in enumerate(row):
                    item = QTableWidgetItem(str(value))
                    self.preview_table.setItem(i, j, item)
            
            self.status_label.setText(
                f"<span style='color: green;'>✓ Preview loaded: {len(df)} rows × {len(df.columns)} columns (showing first 20 rows)</span>"
            )
            
        except Exception as e:
            self.status_label.setText(
                f"<span style='color: red;'>✗ Error loading preview: {str(e)}</span>"
            )
            self.preview_table.clear()
    
    def get_import_settings(self):
        """Get import configuration."""
        header_row = self.header_row_spin.value()
        
        return {
            "delimiter": self._get_delimiter(),
            "encoding": self.encoding_combo.currentText(),
            "decimal": self._get_decimal(),
            "skip_rows": self.skip_rows_spin.value(),
            "header": None if header_row < 0 else header_row,
            "has_metadata": self.has_metadata_checkbox.isChecked()
        }
