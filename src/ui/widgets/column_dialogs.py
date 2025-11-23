"""Dialogs for column management in DataTable."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QComboBox, QPushButton,
    QLabel, QCheckBox
)
from PySide6.QtCore import Qt

from studies.data_table_study import ColumnType
from .dialog_utils import show_warning, show_info


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
        
        from PySide6.QtWidgets import QSpinBox
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
