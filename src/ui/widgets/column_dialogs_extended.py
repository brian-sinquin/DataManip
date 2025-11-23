"""Additional dialogs for derivative and range columns."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QPushButton, QLabel, 
    QSpinBox, QDoubleSpinBox, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt

from constants import (
    DIALOG_MEDIUM_WIDTH, DIALOG_MEDIUM_HEIGHT,
    DIALOG_DERIVATIVE_WIDTH, DIALOG_DERIVATIVE_HEIGHT
)


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
        self.resize(DIALOG_MEDIUM_WIDTH, DIALOG_MEDIUM_HEIGHT)
        
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
        form.addRow("Numerator (y):", self.y_combo)
        
        self.x_combo = QComboBox()
        self.x_combo.addItems(available_columns)
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
        y_col = self.y_combo.currentText()
        x_col = self.x_combo.currentText()
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
        self.resize(DIALOG_DERIVATIVE_WIDTH, DIALOG_DERIVATIVE_HEIGHT)
        
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
        
        # Range parameters group
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
        """Update visible fields based on range type.
        
        Args:
            range_type: Selected range type
        """
        # Show/hide fields based on type
        if range_type == "linspace":
            self.count_spin.setVisible(True)
            self.count_spin.parentWidget().layout().labelForField(self.count_spin).setVisible(True)
            self.step_spin.setVisible(False)
            self.step_spin.parentWidget().layout().labelForField(self.step_spin).setVisible(False)
            
            self.help_label.setText(
                "<small><b>linspace:</b> Generate 'Count' evenly spaced values "
                "from 'Start' to 'Stop' (inclusive).<br>"
                "Example: linspace(0, 10, 11) → [0, 1, 2, ..., 10]</small>"
            )
        
        elif range_type == "arange":
            self.count_spin.setVisible(False)
            self.count_spin.parentWidget().layout().labelForField(self.count_spin).setVisible(False)
            self.step_spin.setVisible(True)
            self.step_spin.parentWidget().layout().labelForField(self.step_spin).setVisible(True)
            
            self.help_label.setText(
                "<small><b>arange:</b> Generate values from 'Start' to 'Stop' "
                "with 'Step' increment (Stop excluded).<br>"
                "Example: arange(0, 5, 0.5) → [0, 0.5, 1.0, ..., 4.5]</small>"
            )
        
        elif range_type == "logspace":
            self.count_spin.setVisible(True)
            self.count_spin.parentWidget().layout().labelForField(self.count_spin).setVisible(True)
            self.step_spin.setVisible(False)
            self.step_spin.parentWidget().layout().labelForField(self.step_spin).setVisible(False)
            
            self.help_label.setText(
                "<small><b>logspace:</b> Generate 'Count' logarithmically spaced values. "
                "'Start' and 'Stop' are exponents (base 10).<br>"
                "Example: logspace(0, 3, 4) → [10⁰, 10¹, 10², 10³] = [1, 10, 100, 1000]</small>"
            )
    
    def get_values(self):
        """Get dialog values.
        
        Returns:
            Dictionary with keys: name, range_type, unit, start, stop, count, step
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
