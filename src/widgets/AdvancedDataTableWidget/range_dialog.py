"""Range column creation dialog.

This dialog allows creating a DATA column populated with evenly spaced values.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QGroupBox,
    QMessageBox
)

from .constants import (
    DIALOG_ADD_RANGE,
    MAX_RANGE_POINTS,
    MIN_RANGE_POINTS,
    ERR_TOO_MANY_POINTS
)


class RangeColumnDialog(QDialog):
    """Dialog for creating a data column with a range of values.
    
    Allows user to specify:
    - Start value (a)
    - End value (b)
    - Number of points (N)
    - Column name/diminutive
    - Unit
    
    The column will be populated with N evenly spaced values from a to b.
    
    Args:
        parent: Parent widget
        table_widget: Reference to the AdvancedDataTableWidget
    """
    
    def __init__(self, parent, table_widget):
        super().__init__(parent)
        self.table_widget = table_widget
        
        self.setWindowTitle(DIALOG_ADD_RANGE)
        self.setModal(True)
        self.resize(400, 350)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Explanation
        explanation = QLabel(
            "Create a data column with evenly spaced values from a to b."
        )
        explanation.setWordWrap(True)
        explanation.setStyleSheet("color: #666; font-size: 9pt; padding: 5px;")
        layout.addWidget(explanation)
        
        # Range parameters
        range_group = QGroupBox("Range Parameters")
        range_layout = QFormLayout()
        
        self.start_edit = QLineEdit()
        self.start_edit.setPlaceholderText("Starting value (e.g., 0)")
        range_layout.addRow("Start (a):", self.start_edit)
        
        self.end_edit = QLineEdit()
        self.end_edit.setPlaceholderText("Ending value (e.g., 100)")
        range_layout.addRow("End (b):", self.end_edit)
        
        self.points_edit = QLineEdit()
        self.points_edit.setPlaceholderText(f"Number of points (e.g., 11, max {MAX_RANGE_POINTS})")
        range_layout.addRow("Number of points (N):", self.points_edit)
        
        range_group.setLayout(range_layout)
        layout.addWidget(range_group)
        
        # Column properties
        properties_group = QGroupBox("Column Properties")
        properties_layout = QFormLayout()
        
        self.diminutive_edit = QLineEdit()
        self.diminutive_edit.setPlaceholderText("Short name (e.g., 'x', 't', 'V')")
        properties_layout.addRow("Diminutive:", self.diminutive_edit)
        
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Description shown as tooltip")
        properties_layout.addRow("Description:", self.description_edit)
        
        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText("Unit (e.g., 'm', 's', 'V')")
        properties_layout.addRow("Unit:", self.unit_edit)
        
        properties_group.setLayout(properties_layout)
        layout.addWidget(properties_group)
        
        # Preview
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_label = QLabel("Enter values to see preview")
        self.preview_label.setWordWrap(True)
        self.preview_label.setStyleSheet("font-family: monospace; font-size: 9pt;")
        preview_layout.addWidget(self.preview_label)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Connect preview updates
        self.start_edit.textChanged.connect(self._update_preview)
        self.end_edit.textChanged.connect(self._update_preview)
        self.points_edit.textChanged.connect(self._update_preview)
        
        # Buttons
        from PySide6.QtWidgets import QHBoxLayout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("Create")
        ok_btn.clicked.connect(self._validate_and_accept)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
    
    def _update_preview(self):
        """Update the preview of the range."""
        try:
            start = float(self.start_edit.text())
            end = float(self.end_edit.text())
            points = int(self.points_edit.text())
            
            if points < MIN_RANGE_POINTS:
                self.preview_label.setText(f"Number of points must be at least {MIN_RANGE_POINTS}")
                return
            
            if points > MAX_RANGE_POINTS:
                self.preview_label.setText(f"Number of points limited to {MAX_RANGE_POINTS}")
                return
            
            # Calculate step
            step = (end - start) / (points - 1) if points > 1 else 0
            
            # Show first few and last few values
            preview_text = f"Step: {step:.6g}\n\n"
            
            if points <= 10:
                # Show all values
                for i in range(points):
                    value = start + i * step
                    preview_text += f"[{i}] {value:.6g}\n"
            else:
                # Show first 4 and last 4
                for i in range(4):
                    value = start + i * step
                    preview_text += f"[{i}] {value:.6g}\n"
                preview_text += f"...\n"
                for i in range(points - 4, points):
                    value = start + i * step
                    preview_text += f"[{i}] {value:.6g}\n"
            
            self.preview_label.setText(preview_text)
            
        except ValueError:
            self.preview_label.setText("Enter valid numbers to see preview")
    
    def _validate_and_accept(self):
        """Validate inputs before accepting."""
        # Validate diminutive
        diminutive = self.diminutive_edit.text().strip()
        if not diminutive:
            QMessageBox.warning(self, "Missing Diminutive", "Please enter a diminutive for the column.")
            return
        
        # Validate start value
        try:
            start = float(self.start_edit.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Start Value", "Please enter a valid number for the start value.")
            return
        
        # Validate end value
        try:
            end = float(self.end_edit.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid End Value", "Please enter a valid number for the end value.")
            return
        
        # Validate number of points
        try:
            points = int(self.points_edit.text())
            if points < MIN_RANGE_POINTS:
                QMessageBox.warning(self, "Invalid Points", f"Number of points must be at least {MIN_RANGE_POINTS}.")
                return
            if points > MAX_RANGE_POINTS:
                QMessageBox.warning(self, "Too Many Points", ERR_TOO_MANY_POINTS)
                return
        except ValueError:
            QMessageBox.warning(self, "Invalid Points", "Please enter a valid integer for the number of points.")
            return
        
        self.accept()
    
    def get_results(self):
        """Get the dialog results.
        
        Returns:
            dict: Dictionary containing:
                - diminutive: The column diminutive
                - description: The column description
                - unit: The unit
                - start: Start value
                - end: End value
                - points: Number of points
        """
        return {
            'diminutive': self.diminutive_edit.text().strip(),
            'description': self.description_edit.text().strip(),
            'unit': self.unit_edit.text().strip() or None,
            'start': float(self.start_edit.text()),
            'end': float(self.end_edit.text()),
            'points': int(self.points_edit.text())
        }
