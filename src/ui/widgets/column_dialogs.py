"""Dialogs for column management in DataTable."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QComboBox, QPushButton,
    QLabel, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox
)
from PySide6.QtCore import Qt

from studies.data_table_study import ColumnType
from .shared.dialog_utils import show_warning, show_info


class AddDataColumnDialog(QDialog):
    """Dialog for adding a data column."""
    
    def __init__(self, parent=None):
        """Initialize dialog."""
        super().__init__(parent)
        
        self.setWindowTitle("Add Data Column")
        self.setModal(True)
        self.resize(400, 200)
        
        # Setup UI
        layout = QVBoxLayout(self)
        
        # Form
        form = QFormLayout()
        
        self.name_edit = QLineEdit()
        form.addRow("Column Name:", self.name_edit)
        
        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText("e.g., m, s, kg, m/s^2")
        form.addRow("Unit (optional):", self.unit_edit)
        
        layout.addLayout(form)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
    
    def get_values(self):
        """Get dialog values.
        
        Returns:
            Tuple of (name, unit)
        """
        name = self.name_edit.text().strip()
        unit = self.unit_edit.text().strip() or None
        return name, unit


class AddCalculatedColumnDialog(QDialog):
    """Dialog for adding a calculated column."""
    
    def __init__(self, available_columns, available_variables, parent=None):
        """Initialize dialog.
        
        Args:
            available_columns: List of available column names
            available_variables: List of available variable names
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.available_columns = available_columns
        self.available_variables = available_variables
        
        self.setWindowTitle("Add Calculated Column")
        self.setModal(True)
        self.resize(500, 400)
        
        # Setup UI
        layout = QVBoxLayout(self)
        
        # Form
        form = QFormLayout()
        
        self.name_edit = QLineEdit()
        form.addRow("Column Name:", self.name_edit)
        
        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText("e.g., m, s, kg, m/s^2")
        form.addRow("Unit (optional):", self.unit_edit)
        
        layout.addLayout(form)
        
        # Formula section
        layout.addWidget(QLabel("Formula:"))
        
        self.formula_edit = QTextEdit()
        self.formula_edit.setPlaceholderText("Enter formula using {column} or {variable} syntax\nExample: {x} * 2 + {y}")
        self.formula_edit.setMaximumHeight(100)
        layout.addWidget(self.formula_edit)
        
        # Help text
        help_text = QLabel(
            "<b>Available:</b><br>"
            f"Columns: {', '.join(available_columns) if available_columns else 'none'}<br>"
            f"Variables: {', '.join(available_variables) if available_variables else 'none'}<br><br>"
            "<b>Functions:</b> sqrt, sin, cos, tan, exp, log, log10, abs, arcsin, arccos, arctan, pi, e<br>"
            "<b>Operators:</b> +, -, *, /, **, %, //<br>"
            "<b>Use np. prefix for numpy functions</b> (e.g., np.mean, np.sum)"
        )
        help_text.setWordWrap(True)
        # Use default Qt styling
        layout.addWidget(help_text)
        
        # Uncertainty propagation
        self.uncertainty_checkbox = QCheckBox("Automatically propagate uncertainty")
        self.uncertainty_checkbox.setToolTip(
            "When enabled, an uncertainty column (δname) will be automatically created\n"
            "using symbolic differentiation: δf = √(Σ(∂f/∂xᵢ · δxᵢ)²)\n\n"
            "Requires uncertainty columns ([name]_u) for dependencies."
        )
        layout.addWidget(self.uncertainty_checkbox)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        validate_btn = QPushButton("Validate Formula")
        validate_btn.clicked.connect(self._validate_formula)
        button_layout.addWidget(validate_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self._accept)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
    
    def _validate_formula(self):
        """Validate formula syntax."""
        formula = self.formula_edit.toPlainText().strip()
        
        if not formula:
            show_warning(self, "Validation", "Formula is empty")
            return
        
        # Import here to avoid circular dependency
        from core.formula_engine import FormulaEngine
        
        engine = FormulaEngine()
        available = self.available_columns + self.available_variables
        
        valid, error = engine.validate_formula(formula, available)
        
        if valid:
            show_info(self, "Validation", "Formula is valid!")
        else:
            show_warning(self, "Validation Error", error or "Unknown error")
    
    def _accept(self):
        """Accept dialog with validation."""
        name = self.name_edit.text().strip()
        formula = self.formula_edit.toPlainText().strip()
        
        if not name:
            show_warning(self, "Error", "Column name is required")
            return
        
        if not formula:
            show_warning(self, "Error", "Formula is required")
            return
        
        self.accept()
    
    def get_values(self):
        """Get dialog values.
        
        Returns:
            Tuple of (name, formula, unit, propagate_uncertainty)
        """
        name = self.name_edit.text().strip()
        formula = self.formula_edit.toPlainText().strip()
        unit = self.unit_edit.text().strip() or None
        propagate_uncertainty = self.uncertainty_checkbox.isChecked()
        return name, formula, unit, propagate_uncertainty

class AddDerivativeColumnDialog(QDialog):
    """Dialog for adding a derivative column."""
    
    def __init__(self, available_columns, parent=None):
        """Initialize dialog.
        
        Args:
            available_columns: List of available column names
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.available_columns = available_columns
        
        self.setWindowTitle("Add Derivative Column")
        self.setModal(True)
        self.resize(450, 300)
        
        # Setup UI
        layout = QVBoxLayout(self)
        
        # Description
        desc = QLabel(
            "Create a column with numerical derivative: dy/dx\n"
            "Uses numpy.gradient for centered differences."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Form
        form = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., velocity, acceleration")
        form.addRow("Column Name:", self.name_edit)
        
        self.y_combo = QComboBox()
        self.y_combo.addItems(available_columns)
        if available_columns:
            self.y_combo.setCurrentIndex(0)
        form.addRow("Numerator (y):", self.y_combo)
        
        self.x_combo = QComboBox()
        self.x_combo.addItems(available_columns)
        if len(available_columns) > 1:
            self.x_combo.setCurrentIndex(1)
        elif available_columns:
            self.x_combo.setCurrentIndex(0)
        form.addRow("Denominator (x):", self.x_combo)
        
        self.order_spin = QSpinBox()
        self.order_spin.setMinimum(1)
        self.order_spin.setMaximum(3)
        self.order_spin.setValue(1)
        form.addRow("Derivative Order:", self.order_spin)
        
        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText("e.g., m/s, m/s^2")
        form.addRow("Unit (optional):", self.unit_edit)
        
        layout.addLayout(form)
        
        # Help text
        help_text = QLabel(
            "<small>"
            "<b>Examples:</b><br>"
            "• Velocity: dy/dt with y=position, x=time<br>"
            "• Acceleration: dv/dt with y=velocity, x=time, order=1<br>"
            "• Or: d²y/dt² with y=position, x=time, order=2"
            "</small>"
        )
        help_text.setWordWrap(True)
        layout.addWidget(help_text)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
    
    def get_values(self):
        """Get dialog values.
        
        Returns:
            Tuple of (name, y_col, x_col, order, unit)
        """
        name = self.name_edit.text().strip()
        y_col = self.y_combo.currentText().strip()
        x_col = self.x_combo.currentText().strip()
        order = self.order_spin.value()
        unit = self.unit_edit.text().strip() or None
        return name, y_col, x_col, order, unit


class AddRangeColumnDialog(QDialog):
    """Dialog for adding a range column (auto-generated sequence)."""
    
    def __init__(self, parent=None):
        """Initialize dialog."""
        super().__init__(parent)
        
        self.setWindowTitle("Add Range Column")
        self.setModal(True)
        self.resize(450, 400)
        
        # Setup UI
        layout = QVBoxLayout(self)
        
        # Description
        desc = QLabel(
            "Create a column with auto-generated sequence.\n"
            "Perfect for time series or independent variables."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Basic info
        form = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., time, frequency")
        form.addRow("Column Name:", self.name_edit)
        
        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText("e.g., s, Hz, m")
        form.addRow("Unit (optional):", self.unit_edit)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["linspace", "arange", "logspace"])
        self.type_combo.currentTextChanged.connect(self._update_fields)
        form.addRow("Range Type:", self.type_combo)
        
        layout.addLayout(form)
        
        # Range parameters
        from PySide6.QtWidgets import QGroupBox, QSpinBox, QDoubleSpinBox
        self.params_group = QGroupBox("Range Parameters")
        params_layout = QFormLayout()
        
        self.start_spin = QDoubleSpinBox()
        self.start_spin.setMinimum(-1e9)
        self.start_spin.setMaximum(1e9)
        self.start_spin.setDecimals(6)
        self.start_spin.setValue(0.0)
        params_layout.addRow("Start:", self.start_spin)
        
        self.stop_spin = QDoubleSpinBox()
        self.stop_spin.setMinimum(-1e9)
        self.stop_spin.setMaximum(1e9)
        self.stop_spin.setDecimals(6)
        self.stop_spin.setValue(10.0)
        params_layout.addRow("Stop:", self.stop_spin)
        
        self.count_spin = QSpinBox()
        self.count_spin.setMinimum(2)
        self.count_spin.setMaximum(100000)
        self.count_spin.setValue(101)
        params_layout.addRow("Count:", self.count_spin)
        
        self.step_spin = QDoubleSpinBox()
        self.step_spin.setMinimum(1e-9)
        self.step_spin.setMaximum(1e9)
        self.step_spin.setDecimals(6)
        self.step_spin.setValue(1.0)
        params_layout.addRow("Step:", self.step_spin)
        
        self.params_group.setLayout(params_layout)
        layout.addWidget(self.params_group)
        
        # Help text
        self.help_label = QLabel()
        self.help_label.setWordWrap(True)
        layout.addWidget(self.help_label)
        
        self._update_fields("linspace")
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
    
    def _update_fields(self, range_type: str):
        """Update visible fields based on range type."""
        # Get form layout
        params_form = self.params_group.layout()
        
        if range_type == "linspace":
            self.count_spin.setVisible(True)
            params_form.labelForField(self.count_spin).setVisible(True)
            self.step_spin.setVisible(False)
            params_form.labelForField(self.step_spin).setVisible(False)
            
            self.help_label.setText(
                "<small><b>linspace:</b> Generate 'Count' evenly spaced values "
                "from 'Start' to 'Stop' (inclusive).<br>"
                "Example: linspace(0, 10, 11) → [0, 1, 2, ..., 10]</small>"
            )
        
        elif range_type == "arange":
            self.count_spin.setVisible(False)
            params_form.labelForField(self.count_spin).setVisible(False)
            self.step_spin.setVisible(True)
            params_form.labelForField(self.step_spin).setVisible(True)
            
            self.help_label.setText(
                "<small><b>arange:</b> Generate values from 'Start' to 'Stop' "
                "with 'Step' increment (Stop excluded).<br>"
                "Example: arange(0, 5, 0.5) → [0, 0.5, 1.0, ..., 4.5]</small>"
            )
        
        elif range_type == "logspace":
            self.count_spin.setVisible(True)
            params_form.labelForField(self.count_spin).setVisible(True)
            self.step_spin.setVisible(False)
            params_form.labelForField(self.step_spin).setVisible(False)
            
            self.help_label.setText(
                "<small><b>logspace:</b> Generate 'Count' logarithmically spaced values. "
                "'Start' and 'Stop' are exponents (base 10).<br>"
                "Example: logspace(0, 3, 4) → [10⁰, 10¹, 10², 10³] = [1, 10, 100, 1000]</small>"
            )
    
    def get_values(self):
        """Get dialog values.
        
        Returns:
            Dictionary with range parameters
        """
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


class EditDataColumnDialog(QDialog):
    """Dialog for editing data column properties."""
    
    def __init__(self, col_name: str, unit: str = None, parent=None):
        """Initialize dialog.
        
        Args:
            col_name: Current column name
            unit: Current unit (optional)
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.original_name = col_name
        
        self.setWindowTitle(f"Edit Column: {col_name}")
        self.setModal(True)
        self.resize(400, 180)
        
        # Setup UI
        layout = QVBoxLayout(self)
        
        # Form
        form = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setText(col_name)
        form.addRow("Column Name:", self.name_edit)
        
        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText("e.g., m, s, kg, m/s^2")
        if unit:
            self.unit_edit.setText(unit)
        form.addRow("Unit (optional):", self.unit_edit)
        
        layout.addLayout(form)
        
        # Info
        info = QLabel(
            "<small><i>Note: Renaming will update all formulas referencing this column.</i></small>"
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self._accept)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
    
    def _accept(self):
        """Accept dialog with validation."""
        name = self.name_edit.text().strip()
        
        if not name:
            show_warning(self, "Error", "Column name cannot be empty")
            return
        
        self.accept()
    
    def get_values(self):
        """Get dialog values.
        
        Returns:
            Tuple of (name, unit)
        """
        name = self.name_edit.text().strip()
        unit = self.unit_edit.text().strip() or None
        return name, unit


class CSVImportDialog(QDialog):
    """Advanced CSV import dialog with preview and configuration options."""
    
    def __init__(self, filepath: str, parent=None):
        """Initialize dialog.
        
        Args:
            filepath: Path to CSV file
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.filepath = filepath
        
        import os
        filename = os.path.basename(filepath)
        self.setWindowTitle(f"Import CSV: {filename}")
        self.setModal(True)
        self.resize(800, 600)
        
        # Setup UI
        layout = QVBoxLayout(self)
        
        # Configuration section
        config_group = QLabel("<b>Import Configuration</b>")
        layout.addWidget(config_group)
        
        form = QFormLayout()
        
        # Delimiter
        self.delimiter_combo = QComboBox()
        self.delimiter_combo.addItems(["Comma (,)", "Semicolon (;)", "Tab", "Space", "Custom"])
        self.delimiter_combo.currentIndexChanged.connect(self._on_config_changed)
        form.addRow("Delimiter:", self.delimiter_combo)
        
        self.custom_delimiter_edit = QLineEdit()
        self.custom_delimiter_edit.setMaximumWidth(50)
        self.custom_delimiter_edit.setVisible(False)
        self.custom_delimiter_edit.textChanged.connect(self._on_config_changed)
        form.addRow("Custom Delimiter:", self.custom_delimiter_edit)
        
        # Header row
        self.header_row_spin = QSpinBox()
        self.header_row_spin.setMinimum(0)
        self.header_row_spin.setMaximum(100)
        self.header_row_spin.setValue(0)
        self.header_row_spin.setToolTip("Row number to use as column headers (0-indexed). Set to -1 for no header.")
        self.header_row_spin.setSpecialValueText("No header")
        self.header_row_spin.setMinimum(-1)
        self.header_row_spin.valueChanged.connect(self._on_config_changed)
        form.addRow("Header Row:", self.header_row_spin)
        
        # Skip rows
        self.skip_rows_spin = QSpinBox()
        self.skip_rows_spin.setMinimum(0)
        self.skip_rows_spin.setMaximum(1000)
        self.skip_rows_spin.setValue(0)
        self.skip_rows_spin.setToolTip("Number of rows to skip at the beginning (before header)")
        self.skip_rows_spin.valueChanged.connect(self._on_config_changed)
        form.addRow("Skip Rows:", self.skip_rows_spin)
        
        # Encoding
        self.encoding_combo = QComboBox()
        self.encoding_combo.addItems(["utf-8", "latin-1", "cp1252", "iso-8859-1", "ascii"])
        self.encoding_combo.setToolTip("File encoding (use utf-8 for most modern files)")
        self.encoding_combo.currentTextChanged.connect(self._on_config_changed)
        form.addRow("Encoding:", self.encoding_combo)
        
        # Decimal separator
        self.decimal_combo = QComboBox()
        self.decimal_combo.addItems(["Period (.)", "Comma (,)"])
        self.decimal_combo.setToolTip("Decimal separator for numbers")
        self.decimal_combo.currentIndexChanged.connect(self._on_config_changed)
        form.addRow("Decimal:", self.decimal_combo)
        
        layout.addLayout(form)
        
        # Metadata checkbox
        self.has_metadata_checkbox = QCheckBox("File contains metadata comments (#)")
        self.has_metadata_checkbox.setChecked(True)
        self.has_metadata_checkbox.setToolTip("Check if CSV has metadata in comment lines starting with #")
        layout.addWidget(self.has_metadata_checkbox)
        
        # Preview section
        layout.addWidget(QLabel("<b>Preview</b>"))
        
        self.preview_table = QTableWidget()
        self.preview_table.setMaximumHeight(300)
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        layout.addWidget(self.preview_table)
        
        # Status label
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        refresh_btn = QPushButton("Refresh Preview")
        refresh_btn.clicked.connect(self._update_preview)
        button_layout.addWidget(refresh_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        import_btn = QPushButton("Import")
        import_btn.setDefault(True)
        import_btn.clicked.connect(self.accept)
        button_layout.addWidget(import_btn)
        
        layout.addLayout(button_layout)
        
        # Connect custom delimiter visibility
        self.delimiter_combo.currentIndexChanged.connect(self._toggle_custom_delimiter)
        
        # Initial preview
        self._update_preview()
    
    def _toggle_custom_delimiter(self):
        """Show/hide custom delimiter input."""
        is_custom = self.delimiter_combo.currentText() == "Custom"
        self.custom_delimiter_edit.setVisible(is_custom)
    
    def _on_config_changed(self):
        """Auto-refresh preview when config changes."""
        # Debounce rapid changes
        pass  # User can click Refresh button
    
    def _get_delimiter(self) -> str:
        """Get current delimiter setting."""
        delim_text = self.delimiter_combo.currentText()
        if delim_text == "Comma (,)":
            return ","
        elif delim_text == "Semicolon (;)":
            return ";"
        elif delim_text == "Tab":
            return "\t"
        elif delim_text == "Space":
            return " "
        else:  # Custom
            return self.custom_delimiter_edit.text() or ","
    
    def _get_decimal(self) -> str:
        """Get decimal separator."""
        return "." if self.decimal_combo.currentIndex() == 0 else ","
    
    def _update_preview(self):
        """Update preview table."""
        import pandas as pd
        
        try:
            # Get settings
            delimiter = self._get_delimiter()
            encoding = self.encoding_combo.currentText()
            decimal = self._get_decimal()
            skip_rows = self.skip_rows_spin.value()
            header_row = self.header_row_spin.value()
            
            # Adjust header for pandas (None means no header)
            header = None if header_row < 0 else header_row
            
            # Read CSV with settings
            df = pd.read_csv(
                self.filepath,
                delimiter=delimiter,
                encoding=encoding,
                decimal=decimal,
                skiprows=skip_rows if skip_rows > 0 else None,
                header=header,
                nrows=20,  # Preview first 20 rows
                comment='#' if self.has_metadata_checkbox.isChecked() else None
            )
            
            # If no header, generate column names
            if header is None:
                df.columns = [f"Column_{i}" for i in range(len(df.columns))]
            
            # Update preview table
            self.preview_table.clear()
            self.preview_table.setRowCount(len(df))
            self.preview_table.setColumnCount(len(df.columns))
            self.preview_table.setHorizontalHeaderLabels([str(col) for col in df.columns])
            
            for i, row in df.iterrows():
                for j, value in enumerate(row):
                    item = QTableWidgetItem(str(value))
                    self.preview_table.setItem(i, j, item)
            
            # Update status
            self.status_label.setText(
                f"<span style='color: green;'>✓ Preview loaded: {len(df)} rows × {len(df.columns)} columns (showing first 20 rows)</span>"
            )
            
        except Exception as e:
            self.status_label.setText(
                f"<span style='color: red;'>✗ Error loading preview: {str(e)}</span>"
            )
            self.preview_table.clear()
    
    def get_import_settings(self):
        """Get import configuration.
        
        Returns:
            Dictionary with import settings
        """
        header_row = self.header_row_spin.value()
        
        return {
            "delimiter": self._get_delimiter(),
            "encoding": self.encoding_combo.currentText(),
            "decimal": self._get_decimal(),
            "skip_rows": self.skip_rows_spin.value(),
            "header": None if header_row < 0 else header_row,
            "has_metadata": self.has_metadata_checkbox.isChecked()
        }
