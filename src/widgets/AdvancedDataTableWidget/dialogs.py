"""
Dialog classes for AdvancedDataTableWidget.

This module contains all dialog interfaces for editing column properties:
- DataColumnEditorDialog: Edit data column properties (diminutive, unit, uncertainty)
- FormulaEditorDialog: Edit calculated column formulas
- VariablesDialog: Manage global variables/constants for formulas
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QCheckBox, QGroupBox,
    QComboBox, QTextEdit, QListWidget, QSplitter, QWidget,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt
from typing import Optional

from .models import AdvancedColumnType, COMMON_UNITS
from .formula_evaluator import SafeFormulaEvaluator
from .dialog_utils import populate_formula_columns_list, populate_column_combo_boxes
from .dialog_widgets import FormulaColumnsListWidget, ColumnSelectionComboBox


class DataColumnEditorDialog(QDialog):
    """Dialog for editing data column properties: diminutive, unit, and uncertainty toggle.
    
    This dialog allows users to:
    - Edit the display name of a data column
    - Set or modify the diminutive (short form for formulas)
    - Choose a unit from common units or enter a custom one
    - Enable/disable an associated uncertainty column
    - Preview how the changes will appear
    
    Args:
        parent: Parent widget
        column_index: Index of the column being edited
        table_widget: Reference to the AdvancedDataTableWidget
    """
    
    def __init__(self, parent, column_index, table_widget):
        super().__init__(parent)
        self.table_widget = table_widget
        self.column_index = column_index
        
        # Get current column properties
        self.current_diminutive = table_widget.getColumnDiminutive(column_index)
        self.current_description = table_widget.getColumnDescription(column_index) or ""
        self.current_unit = table_widget.getColumnUnit(column_index) or ""
        self.has_uncertainty, self.uncertainty_col_index = table_widget.hasUncertaintyColumn(column_index)
        
        self.setWindowTitle(f"Edit Data Column - {self.current_diminutive}")
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
        col_type = self.table_widget.getColumnType(self.column_index)
        type_label = QLabel(col_type.value.title())
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
                    f"✓ Uncertainty column already exists (Column {self.uncertainty_col_index})"
                )
            else:
                self.uncertainty_info_label.setText(
                    "ⓘ Will create a new uncertainty column when applied"
                )
        else:
            if self.has_uncertainty:
                self.uncertainty_info_label.setText(
                    f"⚠ Will remove existing uncertainty column (Column {self.uncertainty_col_index})"
                )
            else:
                self.uncertainty_info_label.setText("")
    
    def _update_preview(self):
        """Update the preview labels."""
        # Header preview - use diminutive as base
        unit_text = self.unit_edit.text().strip()
        diminutive_text = self.diminutive_edit.text().strip() or self.current_diminutive
        if unit_text:
            from .advanced_datatable import format_unit_pretty
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


class FormulaEditorDialog(QDialog):
    """Dialog for editing formulas with column reference assistance.
    
    This dialog provides:
    - Formula editor with syntax help
    - List of available columns with their diminutives
    - Easy insertion of column references
    - Preview of formula results
    - Column property editing (display name, diminutive, unit)
    
    Args:
        parent: Parent widget
        column_index: Index of the column being edited
        table_widget: Reference to the AdvancedDataTableWidget
    """

    def __init__(self, parent, column_index, table_widget):
        super().__init__(parent)
        self.table_widget = table_widget
        self.column_index = column_index

        # Get current column properties
        self.current_diminutive = table_widget.getColumnDiminutive(column_index) or f"col{column_index}"
        self.current_description = table_widget.getColumnDescription(column_index) or ""
        self.current_unit = table_widget.getColumnUnit(column_index) or ""
        self.current_formula = table_widget.getColumnFormula(column_index)
        self.current_propagate_uncertainty = table_widget.getColumnPropagateUncertainty(column_index)
        self.has_uncertainty, self.uncertainty_col_index = table_widget.hasUncertaintyColumn(column_index)

        self.setWindowTitle(f"Edit Calculated Column - {self.current_diminutive}")
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
        help_text = QLabel("""
Operators: + - * / ** (power) ( )
Functions: sin, cos, tan, sqrt, log, exp, etc.
Examples:
  {temp} * 1.8 + 32
  {m} * {g}  (mass × gravity)
  ({x} ** 2 + {y} ** 2) ** 0.5
  
Tip: Use "Manage Variables" (right-click menu)
to define constants like {g}, {c}, {pi}
        """)
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
                    f"ⓘ Uncertainty column already exists (Column {self.uncertainty_col_index}).\n"
                    "   It will be automatically updated based on input uncertainties."
                )
            else:
                self.uncertainty_info_label.setText(
                    "ⓘ An uncertainty column will be created automatically.\n"
                    "   Only inputs with uncertainty columns will contribute to the calculation."
                )
        else:
            if self.has_uncertainty:
                self.uncertainty_info_label.setText(
                    f"⚠ Existing uncertainty column (Column {self.uncertainty_col_index}) will be removed."
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

    def _insert_reference(self, item):
        """Insert column or variable reference into formula when double-clicked."""
        text = item.text()
        # Skip header/separator items
        if text.startswith("---") or not text.strip():
            return
        # Extract diminutive from "... → {diminutive}"
        if "→ {" in text and "}" in text:
            start = text.find("→ {") + 2
            end = text.find("}", start) + 1
            reference = text[start:end]

            # Insert at cursor position
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
            # Extract diminutive references from formula
            import re
            diminutive_pattern = r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}'
            diminutives = re.findall(diminutive_pattern, formula)
            
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
            # e.g., "{k_cu} / {k_al}" becomes "k_cu / k_al"
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
            # (incomplete formulas, unclosed braces, etc.)
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


class VariablesDialog(QDialog):
    """Dialog for managing global variables/constants that can be used in formulas.
    
    Variables are defined with:
    - Diminutive: Short name to use in formulas (e.g., 'g', 'c', 'pi')
    - Value: Numeric value
    - Unit: Physical unit (optional)
    
    Example variables:
    - g = 9.81 m/s²
    - c = 299792458 m/s
    - pi = 3.14159 (dimensionless)
    """
    
    def __init__(self, parent, current_variables: Optional[dict] = None):
        """
        Args:
            parent: Parent widget
            current_variables: Dict of {diminutive: (value, unit)}
        """
        super().__init__(parent)
        self.current_variables = current_variables or {}
        
        self.setWindowTitle("Manage Variables")
        self.setModal(True)
        self.resize(600, 400)
        
        self._setup_ui()
        self._load_variables()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Description
        desc_label = QLabel(
            "Define global variables/constants that can be used in formulas.\n"
            "Use the diminutive name in formulas (e.g., {g} for gravity)."
        )
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Variables table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Diminutive", "Value", "Unit"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)
        
        # Buttons for adding/removing rows
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add Variable")
        add_btn.clicked.connect(self._add_variable_row)
        button_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._remove_selected_rows)
        button_layout.addWidget(remove_btn)
        
        # Add some common constants button
        common_btn = QPushButton("Add Common Constants")
        common_btn.clicked.connect(self._add_common_constants)
        button_layout.addWidget(common_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Dialog buttons
        dialog_buttons = QHBoxLayout()
        dialog_buttons.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        dialog_buttons.addWidget(cancel_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self._validate_and_accept)
        ok_btn.setDefault(True)
        dialog_buttons.addWidget(ok_btn)
        
        layout.addLayout(dialog_buttons)
    
    def _load_variables(self):
        """Load current variables into the table."""
        self.table.setRowCount(0)
        for diminutive, (value, unit) in self.current_variables.items():
            self._add_variable_row(diminutive, str(value), unit or "")
    
    def _add_variable_row(self, diminutive: str = "", value: str = "", unit: str = ""):
        """Add a new row to the variables table."""
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        self.table.setItem(row, 0, QTableWidgetItem(diminutive))
        self.table.setItem(row, 1, QTableWidgetItem(value))
        self.table.setItem(row, 2, QTableWidgetItem(unit))
    
    def _remove_selected_rows(self):
        """Remove selected rows from the table."""
        selected_rows = sorted(set(index.row() for index in self.table.selectedIndexes()), reverse=True)
        for row in selected_rows:
            self.table.removeRow(row)
    
    def _add_common_constants(self):
        """Add common physical constants to the table."""
        common_constants = [
            ("g", "9.80665", "m/s²"),
            ("c", "299792458", "m/s"),
            ("pi", "3.14159265", ""),
            ("e", "2.71828183", ""),
            ("h", "6.62607015e-34", "J*s"),
            ("k_B", "1.380649e-23", "J/K"),
        ]
        
        # Check which ones are not already in the table
        existing_diminutives = set()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                existing_diminutives.add(item.text().strip())
        
        added = 0
        for dim, val, unit in common_constants:
            if dim not in existing_diminutives:
                self._add_variable_row(dim, val, unit)
                added += 1
        
        if added > 0:
            QMessageBox.information(self, "Constants Added", f"Added {added} common physical constant(s).")
        else:
            QMessageBox.information(self, "No Constants Added", "All common constants are already defined.")
    
    def _validate_and_accept(self):
        """Validate the variables before accepting."""
        # Check for duplicate diminutives
        diminutives = []
        for row in range(self.table.rowCount()):
            dim_item = self.table.item(row, 0)
            if dim_item:
                dim = dim_item.text().strip()
                if dim:
                    if dim in diminutives:
                        QMessageBox.warning(self, "Duplicate Diminutive", 
                                          f"Diminutive '{dim}' is defined multiple times.")
                        return
                    diminutives.append(dim)
        
        # Validate that values are numeric
        for row in range(self.table.rowCount()):
            dim_item = self.table.item(row, 0)
            val_item = self.table.item(row, 1)
            
            if dim_item and dim_item.text().strip():
                dim = dim_item.text().strip()
                val_text = val_item.text().strip() if val_item else ""
                
                if not val_text:
                    QMessageBox.warning(self, "Missing Value", 
                                      f"Variable '{dim}' has no value.")
                    return
                
                try:
                    float(val_text)
                except ValueError:
                    QMessageBox.warning(self, "Invalid Value", 
                                      f"Value '{val_text}' for variable '{dim}' is not a valid number.")
                    return
        
        self.accept()
    
    def get_variables(self) -> dict:
        """Get the variables as a dictionary.
        
        Returns:
            dict: {diminutive: (value, unit)}
        """
        variables = {}
        for row in range(self.table.rowCount()):
            dim_item = self.table.item(row, 0)
            val_item = self.table.item(row, 1)
            unit_item = self.table.item(row, 2)
            
            if dim_item and dim_item.text().strip():
                dim = dim_item.text().strip()
                val_text = val_item.text().strip() if val_item else ""
                unit = unit_item.text().strip() if unit_item else ""
                
                if val_text:
                    try:
                        value = float(val_text)
                        variables[dim] = (value, unit if unit else None)
                    except ValueError:
                        pass  # Skip invalid values
        
        
        return variables


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
        
        title = f"Edit Derivative Column - {self.current_diminutive}" if column_index is not None else "Add Derivative Column"
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
            "For each row i: result[i] = (y[i+1] - y[i]) / (x[i+1] - x[i])"
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
        self.numerator_combo.setIncludeTypeLabels(False)  # Simpler display
        self.numerator_combo.setIncludeUnits(True)
        self.numerator_combo.setTableWidget(self.table_widget, self.column_index)
        self.numerator_combo.currentIndexChanged.connect(self._update_unit_preview)
        derivative_layout.addRow("Numerator (dy):", self.numerator_combo)
        
        # Denominator (dx)
        self.denominator_combo = ColumnSelectionComboBox()
        self.denominator_combo.setIncludeTypeLabels(False)  # Simpler display
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
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self._validate_and_accept)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)
        
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
        diminutive = self.diminutive_edit.text().strip() or "deriv"
        self.preview_header_label.setText(f"∂ {diminutive} [{result_unit}]")
    
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
        
        self.setWindowTitle("Create Range Column")
        self.setModal(True)
        self.resize(400, 300)
        
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
        self.points_edit.setPlaceholderText("Number of points (e.g., 11)")
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
            
            if points < 2:
                self.preview_label.setText("Number of points must be at least 2")
                return
            
            if points > 1000:
                self.preview_label.setText("Number of points limited to 1000")
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
            if points < 2:
                QMessageBox.warning(self, "Invalid Points", "Number of points must be at least 2.")
                return
            if points > 1000:
                QMessageBox.warning(self, "Too Many Points", "Number of points is limited to 1000.")
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

