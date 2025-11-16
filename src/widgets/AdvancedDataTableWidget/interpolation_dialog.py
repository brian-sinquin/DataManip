"""Interpolation column creation/editing dialog.

This dialog allows creating or editing INTERPOLATION columns that interpolate
values from two source columns (x and y).
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QGroupBox,
    QComboBox, QMessageBox
)

from .models import AdvancedColumnType, AdvancedColumnDataType
from .constants import (
    DIALOG_ADD_INTERPOLATION,
    DIALOG_EDIT_INTERPOLATION,
    INTERPOLATION_METHODS
)
from .dialog_utils import populate_interpolation_column_combos
from .dialog_widgets import InterpolationColumnComboBox


class InterpolationDialog(QDialog):
    """Dialog for creating or editing an interpolation column.
    
    Interpolation columns calculate values by interpolating between points
    defined by two source columns (x and y).
    
    Args:
        parent: Parent widget
        table_widget: Reference to the AdvancedDataTableWidget
        column_index: Column index for editing (None for creation)
    """
    
    def __init__(self, parent, table_widget, column_index=None):
        super().__init__(parent)
        self.table_widget = table_widget
        self.column_index = column_index
        self.is_edit_mode = column_index is not None
        
        title = DIALOG_EDIT_INTERPOLATION if self.is_edit_mode else DIALOG_ADD_INTERPOLATION
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(500, 450)
        
        self._setup_ui()
        
        if self.is_edit_mode:
            self._load_existing_data()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Explanation
        explanation = QLabel(
            "An interpolation column calculates values by interpolating between points.\n"
            "Select source columns for X and Y measurement data, then choose an evaluation\n"
            "X column where the interpolation will be calculated (defaults to source X).\n\n"
            "This allows interpolating sparse measurement data onto a dense evaluation grid."
        )
        explanation.setWordWrap(True)
        explanation.setStyleSheet("color: #666; font-size: 9pt; padding: 5px;")
        layout.addWidget(explanation)
        
        # Source columns
        source_group = QGroupBox("Source Data")
        source_layout = QFormLayout()
        
        self.x_column_combo = InterpolationColumnComboBox()
        self.x_column_combo.setTableWidget(self.table_widget, self.column_index if self.is_edit_mode else None)
        source_layout.addRow("X Column:", self.x_column_combo)
        
        self.y_column_combo = InterpolationColumnComboBox()
        self.y_column_combo.setTableWidget(self.table_widget, self.column_index if self.is_edit_mode else None)
        self.y_column_combo.currentIndexChanged.connect(self._update_unit_preview)
        source_layout.addRow("Y Column:", self.y_column_combo)
        
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)
        
        # Evaluation column
        eval_group = QGroupBox("Evaluation Grid")
        eval_layout = QFormLayout()
        
        self.eval_column_combo = InterpolationColumnComboBox()
        self.eval_column_combo.setTableWidget(self.table_widget, self.column_index if self.is_edit_mode else None)
        eval_layout.addRow("Evaluation X Column:", self.eval_column_combo)
        
        eval_group.setLayout(eval_layout)
        layout.addWidget(eval_group)
        
        # Interpolation method
        method_group = QGroupBox("Interpolation Method")
        method_layout = QFormLayout()
        
        self.method_combo = QComboBox()
        for method_key, method_label in INTERPOLATION_METHODS.items():
            self.method_combo.addItem(method_label, method_key)
        method_layout.addRow("Method:", self.method_combo)
        
        method_group.setLayout(method_layout)
        layout.addWidget(method_group)
        
        # Column properties
        properties_group = QGroupBox("Column Properties")
        properties_layout = QFormLayout()
        
        self.diminutive_edit = QLineEdit()
        self.diminutive_edit.setPlaceholderText("Short name (e.g., 'y_interp', 'f_x')")
        properties_layout.addRow("Diminutive:", self.diminutive_edit)
        
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Description shown as tooltip")
        properties_layout.addRow("Description:", self.description_edit)
        
        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText("Unit (auto-detected from Y column)")
        properties_layout.addRow("Unit:", self.unit_edit)
        
        properties_group.setLayout(properties_layout)
        layout.addWidget(properties_group)
        
        # Unit preview
        self.unit_preview = QLabel("")
        self.unit_preview.setStyleSheet("color: #0066cc; font-style: italic;")
        layout.addWidget(self.unit_preview)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_text = "Update" if self.is_edit_mode else "Create"
        ok_btn = QPushButton(ok_text)
        ok_btn.clicked.connect(self._validate_and_accept)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        
        # Initial unit preview
        self._update_unit_preview()
    
    def _update_unit_preview(self):
        """Update the unit preview based on selected Y column."""
        y_col_idx = self.y_column_combo.currentData()
        if y_col_idx is None:
            self.unit_preview.setText("")
            return
        
        # _columns is a list, not a dict
        if y_col_idx < len(self.table_widget._columns):
            y_metadata = self.table_widget._columns[y_col_idx]
        else:
            y_metadata = None
            
        if y_metadata and y_metadata.unit:
            self.unit_preview.setText(f"💡 Suggested unit from Y column: {y_metadata.unit}")
            if not self.unit_edit.text():
                self.unit_edit.setPlaceholderText(y_metadata.unit)
        else:
            self.unit_preview.setText("")
    
    def _load_existing_data(self):
        """Load data from existing column for editing."""
        metadata = self.table_widget._columns[self.column_index]
        
        self.diminutive_edit.setText(metadata.diminutive)
        if metadata.description:
            self.description_edit.setText(metadata.description)
        if metadata.unit:
            self.unit_edit.setText(metadata.unit)
        
        # Set source columns
        if metadata.interpolation_x_column is not None:
            idx = self.x_column_combo.findData(metadata.interpolation_x_column)
            if idx >= 0:
                self.x_column_combo.setCurrentIndex(idx)
        
        if metadata.interpolation_y_column is not None:
            idx = self.y_column_combo.findData(metadata.interpolation_y_column)
            if idx >= 0:
                self.y_column_combo.setCurrentIndex(idx)
        
        # Set evaluation column
        if metadata.interpolation_evaluation_column is not None:
            idx = self.eval_column_combo.findData(metadata.interpolation_evaluation_column)
            if idx >= 0:
                self.eval_column_combo.setCurrentIndex(idx)
        
        # Set interpolation method
        if metadata.interpolation_method:
            idx = self.method_combo.findData(metadata.interpolation_method)
            if idx >= 0:
                self.method_combo.setCurrentIndex(idx)
    
    def _validate_and_accept(self):
        """Validate inputs before accepting."""
        # Validate diminutive
        diminutive = self.diminutive_edit.text().strip()
        if not diminutive:
            QMessageBox.warning(self, "Missing Diminutive", 
                              "Please enter a diminutive for the column.")
            return
        
        # Check diminutive uniqueness (except for current column in edit mode)
        for col_idx, metadata in enumerate(self.table_widget._columns):
            if self.is_edit_mode and col_idx == self.column_index:
                continue
            if metadata.diminutive == diminutive:
                QMessageBox.warning(self, "Duplicate Diminutive",
                                  f"The diminutive '{diminutive}' is already used by another column.")
                return
        
        # Validate X column selection
        x_col_idx = self.x_column_combo.currentData()
        if x_col_idx is None:
            QMessageBox.warning(self, "Missing X Column",
                              "Please select an X column for interpolation.")
            return
        
        # Validate Y column selection
        y_col_idx = self.y_column_combo.currentData()
        if y_col_idx is None:
            QMessageBox.warning(self, "Missing Y Column",
                              "Please select a Y column for interpolation.")
            return
        
        # Validate Evaluation column selection (optional, defaults to X column)
        eval_col_idx = self.eval_column_combo.currentData()
        if eval_col_idx is None:
            eval_col_idx = x_col_idx  # Default to X column
        
        self.accept()
    
    def get_results(self):
        """Get the dialog results.
        
        Returns:
            dict: Dictionary containing:
                - diminutive: The column diminutive
                - description: The column description
                - unit: The unit
                - interpolation_x_column: X column index
                - interpolation_y_column: Y column index
                - interpolation_method: Interpolation method ('linear', 'cubic', etc.)
        """
        return {
            'diminutive': self.diminutive_edit.text().strip(),
            'description': self.description_edit.text().strip() or None,
            'unit': self.unit_edit.text().strip() or None,
            'interpolation_x_column': self.x_column_combo.currentData(),
            'interpolation_y_column': self.y_column_combo.currentData(),
            'interpolation_evaluation_column': self.eval_column_combo.currentData(),
            'interpolation_method': self.method_combo.currentData()
        }
