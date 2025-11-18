"""
Tests for DataTableV2 dialog classes.

These tests verify the dialog functionality without requiring GUI interaction
by directly manipulating dialog widgets programmatically.
"""

import pytest
from PySide6.QtWidgets import QApplication, QDialogButtonBox
from PySide6.QtCore import Qt
import pandas as pd

from widgets.data_table.column_dialogs import (
    AddDataColumnDialog,
    AddCalculatedColumnDialog,
    AddRangeColumnDialog
)
from widgets.data_table.model import DataTableModel
from widgets.data_table.column_metadata import DataType


@pytest.fixture
def app():
    """Create QApplication instance for tests."""
    return QApplication.instance() or QApplication([])


class TestAddDataColumnDialog:
    """Test AddDataColumnDialog functionality."""
    
    def test_dialog_creation(self, app):
        """Test dialog can be created without errors."""
        dialog = AddDataColumnDialog()
        assert dialog is not None
        assert dialog.windowTitle() == "Add Data Column"
    
    def test_name_validation_empty(self, app):
        """Test that empty name is invalid."""
        dialog = AddDataColumnDialog()
        dialog.name_edit.setText("")
        assert not dialog.ok_button.isEnabled()
    
    def test_name_validation_duplicate(self, app):
        """Test that duplicate names are rejected."""
        dialog = AddDataColumnDialog(existing_names=["x", "y", "z"])
        
        dialog.name_edit.setText("x")
        assert not dialog.ok_button.isEnabled()
        assert "already exists" in dialog.name_error_label.text()
    
    def test_name_validation_valid(self, app):
        """Test that valid names are accepted."""
        dialog = AddDataColumnDialog(existing_names=["x"])
        
        dialog.name_edit.setText("temperature")
        assert dialog.ok_button.isEnabled()
        assert "✓" in dialog.name_error_label.text()
    
    def test_name_validation_invalid_chars(self, app):
        """Test that invalid characters are rejected."""
        dialog = AddDataColumnDialog()
        
        dialog.name_edit.setText("temp@value")  # @ is invalid
        assert not dialog.ok_button.isEnabled()
    
    def test_dtype_changes_show_hide_fields(self, app):
        """Test that changing data type shows/hides relevant fields."""
        dialog = AddDataColumnDialog()
        dialog.show()  # Show dialog to ensure widgets are visible
        
        # FLOAT should show unit and precision
        dialog.dtype_combo.setCurrentText("FLOAT")
        app.processEvents()  # Process Qt events
        assert dialog.unit_edit.isVisible()
        assert dialog.precision_spin.isVisible()
        
        # STRING should hide unit and precision
        dialog.dtype_combo.setCurrentText("STRING")
        app.processEvents()
        assert not dialog.unit_edit.isVisible()
        assert not dialog.precision_spin.isVisible()
        
        # INTEGER should show unit but hide precision
        dialog.dtype_combo.setCurrentText("INTEGER")
        app.processEvents()
        assert dialog.unit_edit.isVisible()
        assert not dialog.precision_spin.isVisible()
        
        dialog.close()
    
    def test_get_results_basic(self, app):
        """Test getting basic results from dialog."""
        dialog = AddDataColumnDialog()
        
        dialog.name_edit.setText("temperature")
        dialog.dtype_combo.setCurrentText("FLOAT")
        dialog.unit_edit.setText("°C")
        dialog.description_edit.setText("Sample temperature")
        dialog.precision_spin.setValue(2)
        
        results = dialog.get_results()
        
        assert results['name'] == "temperature"
        assert results['dtype'] == DataType.FLOAT
        assert results['unit'] == "°C"
        assert results['description'] == "Sample temperature"
        assert results['precision'] == 2
        assert results['create_uncertainty'] == False
    
    def test_get_results_with_uncertainty(self, app):
        """Test results include uncertainty flag."""
        dialog = AddDataColumnDialog()
        
        dialog.name_edit.setText("pressure")
        dialog.create_uncertainty_checkbox.setChecked(True)
        
        results = dialog.get_results()
        assert results['create_uncertainty'] == True
    
    def test_preview_updates(self, app):
        """Test that preview updates when fields change."""
        dialog = AddDataColumnDialog()
        
        dialog.name_edit.setText("time")
        dialog.unit_edit.setText("s")
        
        # Preview should show name with unit
        preview_text = dialog.preview_header_label.text()
        assert "time" in preview_text
        assert "s" in preview_text
        
        # Formula reference should use {name}
        formula_text = dialog.preview_formula_label.text()
        assert "{time}" in formula_text


class TestAddCalculatedColumnDialog:
    """Test AddCalculatedColumnDialog functionality."""
    
    def test_dialog_creation(self, app):
        """Test dialog can be created without errors."""
        dialog = AddCalculatedColumnDialog()
        assert dialog is not None
        assert dialog.windowTitle() == "Add Calculated Column"
    
    def test_name_validation(self, app):
        """Test name validation works correctly."""
        dialog = AddCalculatedColumnDialog(existing_names=["x"])
        
        # Empty name
        dialog.name_edit.setText("")
        assert not dialog.ok_button.isEnabled()
        
        # Duplicate name
        dialog.name_edit.setText("x")
        assert not dialog.ok_button.isEnabled()
        
        # Valid name (but formula still empty, so OK still disabled)
        dialog.name_edit.setText("result")
        # OK button requires both name AND formula to be valid
        assert not dialog.ok_button.isEnabled()
    
    def test_formula_validation_empty(self, app):
        """Test that empty formula is invalid."""
        dialog = AddCalculatedColumnDialog()
        
        dialog.name_edit.setText("result")
        dialog.formula_edit.setPlainText("")
        
        assert not dialog.ok_button.isEnabled()
    
    def test_formula_validation_unbalanced_braces(self, app):
        """Test that unbalanced braces are detected."""
        dialog = AddCalculatedColumnDialog()
        
        dialog.name_edit.setText("result")
        dialog.formula_edit.setPlainText("{x + {y}")  # Unbalanced
        
        assert not dialog.ok_button.isEnabled()
        assert "Unbalanced" in dialog.formula_error_label.text()
    
    def test_formula_validation_valid(self, app):
        """Test that valid formula is accepted."""
        model = DataTableModel()
        model.add_data_column("x", data=pd.Series([1, 2, 3]))
        model.add_data_column("y", data=pd.Series([4, 5, 6]))
        
        dialog = AddCalculatedColumnDialog(model=model)
        
        dialog.name_edit.setText("result")
        dialog.formula_edit.setPlainText("{x} + {y}")
        
        # Both name and formula valid, OK should be enabled
        assert dialog.ok_button.isEnabled()
        assert "✓" in dialog.formula_error_label.text()
    
    def test_formula_validation_unknown_column(self, app):
        """Test that unknown column references are detected."""
        model = DataTableModel()
        model.add_data_column("x", data=pd.Series([1, 2, 3]))
        
        dialog = AddCalculatedColumnDialog(model=model)
        
        dialog.name_edit.setText("result")
        dialog.formula_edit.setPlainText("{x} + {unknown}")
        
        assert not dialog.ok_button.isEnabled()
        assert "Unknown column" in dialog.formula_error_label.text()
    
    def test_columns_list_populated(self, app):
        """Test that columns list is populated from model."""
        model = DataTableModel()
        model.add_data_column("x", data=pd.Series([1, 2, 3]), unit="m")
        model.add_data_column("y", data=pd.Series([4, 5, 6]), unit="s")
        model.add_calculated_column("z", formula="{x} + {y}")
        
        dialog = AddCalculatedColumnDialog(model=model)
        
        # Should have 3 items in list
        assert dialog.columns_list.count() == 3
        
        # Check that symbols are present
        item_texts = [dialog.columns_list.item(i).text() for i in range(3)]
        assert any("●" in text for text in item_texts)  # DATA symbol
        assert any("ƒ" in text for text in item_texts)  # CALCULATED symbol
    
    def test_insert_column_reference(self, app):
        """Test double-clicking column inserts reference."""
        model = DataTableModel()
        model.add_data_column("temperature", data=pd.Series([1, 2, 3]))
        
        dialog = AddCalculatedColumnDialog(model=model)
        
        # Simulate double-click
        item = dialog.columns_list.item(0)
        dialog._insert_column_reference(item)
        
        # Should insert {temperature}
        formula_text = dialog.formula_edit.toPlainText()
        assert "{temperature}" in formula_text
    
    def test_uncertainty_toggle_updates_info(self, app):
        """Test that uncertainty checkbox updates info label."""
        dialog = AddCalculatedColumnDialog()
        
        dialog.propagate_uncertainty_checkbox.setChecked(False)
        assert dialog.uncertainty_info_label.text() == ""
        
        dialog.name_edit.setText("result")
        dialog.propagate_uncertainty_checkbox.setChecked(True)
        assert "result_u" in dialog.uncertainty_info_label.text()
    
    def test_get_results(self, app):
        """Test getting results from dialog."""
        model = DataTableModel()
        model.add_data_column("x", data=pd.Series([1, 2, 3]))
        
        dialog = AddCalculatedColumnDialog(model=model)
        
        dialog.name_edit.setText("x_squared")
        dialog.formula_edit.setPlainText("{x}**2")
        dialog.description_edit.setText("Square of x")
        dialog.precision_spin.setValue(4)
        dialog.propagate_uncertainty_checkbox.setChecked(True)
        
        results = dialog.get_results()
        
        assert results['name'] == "x_squared"
        assert results['formula'] == "{x}**2"
        assert results['description'] == "Square of x"
        assert results['precision'] == 4
        assert results['propagate_uncertainty'] == True


class TestAddRangeColumnDialog:
    """Test AddRangeColumnDialog functionality."""
    
    def test_dialog_creation(self, app):
        """Test dialog can be created without errors."""
        dialog = AddRangeColumnDialog()
        assert dialog is not None
        assert dialog.windowTitle() == "Add Range Column"
    
    def test_name_validation(self, app):
        """Test name validation works."""
        dialog = AddRangeColumnDialog(existing_names=["x"])
        
        # Valid name
        dialog.name_edit.setText("time")
        assert dialog.ok_button.isEnabled()
        
        # Duplicate name
        dialog.name_edit.setText("x")
        assert not dialog.ok_button.isEnabled()
    
    def test_method_switching(self, app):
        """Test switching between points and step size methods."""
        dialog = AddRangeColumnDialog()
        dialog.show()  # Show dialog to ensure widgets are visible
        app.processEvents()
        
        # Initially on "Number of Points"
        assert dialog.points_spin.isVisible()
        assert not dialog.step_spin.isVisible()
        
        # Switch to "Step Size"
        dialog.method_combo.setCurrentText("Step Size")
        app.processEvents()
        assert not dialog.points_spin.isVisible()
        assert dialog.step_spin.isVisible()
        
        dialog.close()
    
    def test_preview_updates_points_method(self, app):
        """Test preview updates with points method."""
        dialog = AddRangeColumnDialog()
        
        dialog.start_spin.setValue(0.0)
        dialog.end_spin.setValue(10.0)
        dialog.points_spin.setValue(11)
        
        preview_text = dialog.preview_text.toPlainText()
        assert "0 to 10" in preview_text
        assert "11" in preview_text  # Number of points
    
    def test_preview_updates_step_method(self, app):
        """Test preview updates with step size method."""
        dialog = AddRangeColumnDialog()
        
        dialog.method_combo.setCurrentText("Step Size")
        dialog.start_spin.setValue(0.0)
        dialog.end_spin.setValue(5.0)
        dialog.step_spin.setValue(0.5)
        
        preview_text = dialog.preview_text.toPlainText()
        assert "0 to 5" in preview_text
        assert "11" in preview_text  # Calculated points (5 / 0.5 + 1)
    
    def test_get_results_points_method(self, app):
        """Test getting results with points method."""
        dialog = AddRangeColumnDialog()
        
        dialog.name_edit.setText("time")
        dialog.start_spin.setValue(0.0)
        dialog.end_spin.setValue(10.0)
        dialog.points_spin.setValue(101)
        dialog.unit_edit.setText("s")
        dialog.description_edit.setText("Time values")
        dialog.precision_spin.setValue(3)
        
        results = dialog.get_results()
        
        assert results['name'] == "time"
        assert results['start'] == 0.0
        assert results['end'] == 10.0
        assert results['points'] == 101
        assert results['unit'] == "s"
        assert results['description'] == "Time values"
        assert results['precision'] == 3
    
    def test_get_results_step_method(self, app):
        """Test getting results with step size method."""
        dialog = AddRangeColumnDialog()
        
        dialog.name_edit.setText("angle")
        dialog.method_combo.setCurrentText("Step Size")
        dialog.start_spin.setValue(0.0)
        dialog.end_spin.setValue(360.0)
        dialog.step_spin.setValue(10.0)
        
        results = dialog.get_results()
        
        assert results['name'] == "angle"
        assert results['start'] == 0.0
        assert results['end'] == 360.0
        assert results['points'] == 37  # 360 / 10 + 1
    
    def test_negative_range(self, app):
        """Test that negative ranges work correctly."""
        dialog = AddRangeColumnDialog()
        
        dialog.start_spin.setValue(-5.0)
        dialog.end_spin.setValue(5.0)
        dialog.points_spin.setValue(11)
        
        results = dialog.get_results()
        assert results['start'] == -5.0
        assert results['end'] == 5.0
        assert results['points'] == 11
