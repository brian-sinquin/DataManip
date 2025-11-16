"""Formula editor dialog for calculated columns.

This dialog provides:
- Formula editor with syntax help
- List of available columns/variables with diminutives
- Easy insertion of column references
- Preview of formula results
- Unit automatic calculation
- Uncertainty propagation toggle
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QCheckBox, QGroupBox,
    QTextEdit, QListWidget, QSplitter, QWidget
)
from PySide6.QtCore import Qt
import re

from .constants import (
    FORMULA_HELP_TEXT,
    INFO_UNCERTAINTY_AUTO_UPDATE,
    INFO_UNCERTAINTY_AUTO_CREATE,
    INFO_UNCERTAINTY_WILL_BE_REMOVED
)
from .models import AdvancedColumnType
from .dialog_utils import populate_formula_columns_list
from .dialog_widgets import FormulaColumnsListWidget


class FormulaEditorDialog(QDialog):
    """Dialog for creating or editing formulas with column reference assistance.
    
    Args:
        parent: Parent widget
        column_index: Index of the column being edited (None for creation)
        table_widget: Reference to the AdvancedDataTableWidget
    """

    def __init__(self, parent, column_index, table_widget):
        super().__init__(parent)
        self.table_widget = table_widget
        self.column_index = column_index
        self.is_create_mode = column_index is None

        # Get current column properties (or defaults for create mode)
        if self.is_create_mode:
            self.current_diminutive = "calc"
            self.current_description = ""
            self.current_unit = ""
            self.current_formula = ""
            self.current_propagate_uncertainty = False
            self.has_uncertainty = False
            self.uncertainty_col_index = None
        else:
            self.current_diminutive = table_widget.getColumnDiminutive(column_index) or f"col{column_index}"
            self.current_description = table_widget.getColumnDescription(column_index) or ""
            self.current_unit = table_widget.getColumnUnit(column_index) or ""
            self.current_formula = table_widget.getColumnFormula(column_index)
            self.current_propagate_uncertainty = table_widget.getColumnPropagateUncertainty(column_index)
            self.has_uncertainty, self.uncertainty_col_index = table_widget.hasUncertaintyColumn(column_index)

        title = "Create Calculated Column" if self.is_create_mode else f"Edit Calculated Column - {self.current_diminutive}"
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(700, 650)

        self._setup_ui()
        self._load_current_values()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Column properties section
        properties_group = QGroupBox("Column Properties")
        properties_layout = QFormLayout()

        self.diminutive_edit = QLineEdit()
        self.diminutive_edit.setPlaceholderText("Short name for formulas (e.g., 'temp')")
        properties_layout.addRow("Diminutive:", self.diminutive_edit)

        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Description shown as tooltip on column header")
        properties_layout.addRow("Description:", self.description_edit)

        # Unit field - READ-ONLY for calculated columns (automatically determined)
        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText("Automatically calculated from formula")
        self.unit_edit.setReadOnly(True)
        self.unit_edit.setStyleSheet("QLineEdit { background-color: #f0f0f0; color: #666; }")
        self.unit_edit.setToolTip("Unit is automatically calculated based on the formula and input column units")
        properties_layout.addRow("Unit (Auto):", self.unit_edit)

        properties_group.setLayout(properties_layout)
        layout.addWidget(properties_group)

        # Formula section
        formula_group = QGroupBox("Formula")
        formula_layout = QVBoxLayout()

        formula_label = QLabel("Formula (use {diminutive} for column references):")
        formula_layout.addWidget(formula_label)

        self.formula_edit = QTextEdit()
        self.formula_edit.setPlainText(self.current_formula or "")
        self.formula_edit.setMaximumHeight(100)
        self.formula_edit.textChanged.connect(self._update_unit_preview)
        formula_layout.addWidget(self.formula_edit)

        formula_group.setLayout(formula_layout)
        layout.addWidget(formula_group)

        # Uncertainty propagation section
        uncertainty_group = QGroupBox("Uncertainty Propagation")
        uncertainty_layout = QVBoxLayout()

        self.uncertainty_checkbox = QCheckBox("Automatically calculate uncertainty for this column")
        self.uncertainty_checkbox.setToolTip(
            "When enabled, uncertainty will be calculated using partial derivatives\n"
            "of the formula with respect to each input variable that has uncertainty."
        )
        self.uncertainty_checkbox.toggled.connect(self._on_uncertainty_toggled)
        uncertainty_layout.addWidget(self.uncertainty_checkbox)

        # Uncertainty info label
        self.uncertainty_info_label = QLabel()
        self.uncertainty_info_label.setWordWrap(True)
        self.uncertainty_info_label.setStyleSheet("color: #666; font-size: 9pt; margin-left: 20px;")
        uncertainty_layout.addWidget(self.uncertainty_info_label)

        uncertainty_group.setLayout(uncertainty_layout)
        layout.addWidget(uncertainty_group)

        # Splitter for column/variable list and help
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Available columns and variables list
        columns_widget = QVBoxLayout()
        columns_label = QLabel("Available Columns & Variables (double-click to insert):")
        columns_widget.addWidget(columns_label)

        self.columns_list = FormulaColumnsListWidget()
        self.columns_list.setTableWidget(self.table_widget, self.column_index)
        self.columns_list.referenceRequested.connect(self._insert_reference_text)
        columns_widget.addWidget(self.columns_list)

        columns_container = QWidget()
        columns_container.setLayout(columns_widget)
        splitter.addWidget(columns_container)

        # Help text
        help_label = QLabel("Formula Help:")
        help_text = QLabel(FORMULA_HELP_TEXT)
        help_text.setWordWrap(True)
        help_text.setAlignment(Qt.AlignmentFlag.AlignTop)

        help_widget = QVBoxLayout()
        help_widget.addWidget(help_label)
        help_widget.addWidget(help_text)
        help_widget.addStretch()

        help_container = QWidget()
        help_container.setLayout(help_widget)
        splitter.addWidget(help_container)

        # Preview section
        preview_group = QGroupBox("Formula Status")
        preview_layout = QVBoxLayout()

        self.preview_label = QLabel("Enter a formula to see unit calculation")
        self.preview_label.setWordWrap(True)
        preview_layout.addWidget(self.preview_label)

        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)

        layout.addLayout(button_layout)

    def _load_current_values(self):
        """Load current values into the form fields."""
        self.diminutive_edit.setText(self.current_diminutive or "")
        self.description_edit.setText(self.current_description)
        self.unit_edit.setText(self.current_unit)
        self.uncertainty_checkbox.setChecked(self.current_propagate_uncertainty)
        self._update_uncertainty_info()
        
        # Trigger unit preview calculation if formula exists
        if self.current_formula:
            self._update_unit_preview()

    def _on_uncertainty_toggled(self, checked):
        """Handle uncertainty checkbox toggle."""
        self._update_uncertainty_info()

    def _update_uncertainty_info(self):
        """Update the uncertainty info label."""
        if self.uncertainty_checkbox.isChecked():
            if self.has_uncertainty:
                self.uncertainty_info_label.setText(
                    INFO_UNCERTAINTY_AUTO_UPDATE.format(index=self.uncertainty_col_index)
                )
            else:
                self.uncertainty_info_label.setText(INFO_UNCERTAINTY_AUTO_CREATE)
        else:
            if self.has_uncertainty:
                self.uncertainty_info_label.setText(
                    INFO_UNCERTAINTY_WILL_BE_REMOVED.format(index=self.uncertainty_col_index)
                )
            else:
                self.uncertainty_info_label.setText("")

    def _insert_reference_text(self, reference: str):
        """Insert a reference (like {varname}) into the formula editor.
        
        Args:
            reference: The reference text to insert (e.g., "{temp}", "{x}")
        """
        cursor = self.formula_edit.textCursor()
        cursor.insertText(reference)

    def _update_unit_preview(self):
        """Update the unit preview based on the current formula."""
        formula = self.formula_edit.toPlainText().strip()
        
        if not formula:
            self.unit_edit.clear()
            self.unit_edit.setPlaceholderText("Automatically calculated from formula")
            self.preview_label.setText("Enter a formula to see unit calculation")
            return
        
        try:
            from .formula_evaluator import SafeFormulaEvaluator
            from .constants import FORMULA_REFERENCE_PATTERN
            
            # Extract diminutive references from formula
            diminutives = re.findall(FORMULA_REFERENCE_PATTERN, formula)
            
            if not diminutives:
                self.unit_edit.setText("dimensionless")
                self.preview_label.setText("✓ Formula is valid (dimensionless)")
                return
            
            # Build a mapping of diminutive -> (dummy_value, unit)
            variables_with_units = {}
            missing_units = []
            
            # First, add global variables
            table_variables = getattr(self.table_widget, '_variables', {})
            for var_name, (var_value, var_unit) in table_variables.items():
                if var_name in diminutives:
                    variables_with_units[var_name] = (1.0, var_unit if var_unit else "dimensionless")
            
            for dim in set(diminutives):
                # Skip if already added as a variable
                if dim in variables_with_units:
                    continue
                    
                # Find the column with this diminutive
                col_idx = None
                for idx in range(self.table_widget.columnCount()):
                    if self.table_widget.getColumnDiminutive(idx) == dim:
                        col_idx = idx
                        break
                
                if col_idx is not None:
                    unit = self.table_widget.getColumnUnit(col_idx)
                    if unit:
                        variables_with_units[dim] = (1.0, unit)  # Use dummy value 1.0
                    else:
                        variables_with_units[dim] = (1.0, "dimensionless")
                        missing_units.append(dim)
                else:
                    # Not found as column or variable
                    variables_with_units[dim] = (1.0, "dimensionless")
                    missing_units.append(dim)
            
            # Replace {placeholder} syntax with plain variable names for evaluation
            eval_formula = formula
            for dim in set(diminutives):
                eval_formula = eval_formula.replace(f"{{{dim}}}", dim)
            
            # Evaluate the formula with units to get the resulting unit
            evaluator = SafeFormulaEvaluator()
            magnitude, result_unit = evaluator.evaluate_with_units(eval_formula, variables_with_units)
            
            # Update the unit field
            self.unit_edit.setText(result_unit)
            
            # Update preview - only show warnings, not redundant unit info
            if missing_units:
                self.preview_label.setText(
                    f"⚠ Note: {', '.join(missing_units)} not found (treated as dimensionless)"
                )
            else:
                self.preview_label.setText("✓ Formula is valid")
                
        except Exception as e:
            # Don't print errors to console - they're expected during typing
            self.unit_edit.setText("")
            self.unit_edit.setPlaceholderText("(invalid formula)")
            # Only show brief error message, not full traceback
            error_msg = str(e).split(':')[-1].strip() if ':' in str(e) else str(e)
            self.preview_label.setText(f"Formula error: {error_msg}")

    def get_results(self):
        """Get all the edited values from the dialog.
        
        Returns:
            dict: Dictionary containing:
                - diminutive: The edited diminutive
                - description: The edited description
                - unit: The edited unit
                - formula: The edited formula
                - propagate_uncertainty: Whether to calculate uncertainty
        """
        return {
            'diminutive': self.diminutive_edit.text().strip(),
            'description': self.description_edit.text().strip(),
            'unit': self.unit_edit.text().strip(),
            'formula': self.formula_edit.toPlainText().strip(),
            'propagate_uncertainty': self.uncertainty_checkbox.isChecked()
        }
