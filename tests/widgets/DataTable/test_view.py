"""
Tests for DataTableV2 view layer.

Tests cover:
- View creation and model connection
- Cell selection
- Delegates and formatting
- Basic UI functionality
"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from src.widgets.DataTable.model import DataTableModel
from src.widgets.DataTable.view import DataTableView, DataTableWidget
from src.widgets.DataTable.column_metadata import DataType


# Qt application fixture
@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def model():
    """Create a fresh model for each test."""
    return DataTableModel()


@pytest.fixture
def view(qapp):
    """Create a fresh view for each test."""
    return DataTableView()


@pytest.fixture
def widget(qapp):
    """Create a fresh widget for each test."""
    return DataTableWidget()


class TestDataTableViewBasics:
    """Test basic view functionality."""
    
    def test_create_view(self, view):
        """Test creating a view without model."""
        assert view is not None
        assert view._data_model is None
    
    def test_set_model(self, view, model):
        """Test setting a model on the view."""
        view.setModel(model)
        assert view._data_model is model
        assert view.model() is model
    
    def test_view_with_data(self, view, model):
        """Test view displays data correctly."""
        # Add data to model
        model.add_data_column("x", data=[1, 2, 3, 4, 5])
        model.add_data_column("y", data=[10, 20, 30, 40, 50])
        
        # Set model on view
        view.setModel(model)
        
        # Check dimensions
        assert view.model().rowCount() == 5
        assert view.model().columnCount() == 2
        
        # Check data display
        idx = model.index(0, 0)
        assert model.data(idx, Qt.ItemDataRole.DisplayRole) == "1"
        
        idx = model.index(2, 1)
        assert model.data(idx, Qt.ItemDataRole.DisplayRole) == "30"


class TestDataTableWidget:
    """Test all-in-one widget."""
    
    def test_create_widget(self, widget):
        """Test creating widget with internal model."""
        assert widget is not None
        assert widget.model() is not None
        assert isinstance(widget.model(), DataTableModel)
    
    def test_add_column_convenience_method(self, widget):
        """Test convenience methods delegate to model."""
        widget.add_data_column("test", data=[1, 2, 3])
        
        assert "test" in widget.model().get_column_names()
        assert len(widget.model().get_column_data("test")) == 3
    
    def test_multiple_column_types(self, widget):
        """Test widget with different column types."""
        widget.add_data_column("x", data=[1, 2, 3, 4])
        widget.add_calculated_column("y", "{x} * 2")
        widget.add_range_column("t", start=0, end=3, points=4)
        widget.add_derivative_column("dydx", "y", "x")
        
        assert widget.model().columnCount() == 4


class TestSelection:
    """Test cell selection functionality."""
    
    def test_select_single_cell(self, view, model):
        """Test selecting a single cell."""
        model.add_data_column("x", data=[1, 2, 3])
        view.setModel(model)
        
        view.select_cell(0, 0)
        
        selected = view.get_selected_cells()
        assert len(selected) == 1
        assert selected[0] == (0, 0)
    
    def test_select_row(self, view, model):
        """Test selecting an entire row."""
        model.add_data_column("x", data=[1, 2, 3])
        model.add_data_column("y", data=[4, 5, 6])
        view.setModel(model)
        
        view.select_row(1)
        
        rows = view.get_selected_rows()
        assert len(rows) == 1
        assert rows[0] == 1
    
    def test_select_column(self, view, model):
        """Test selecting an entire column."""
        model.add_data_column("x", data=[1, 2, 3])
        model.add_data_column("y", data=[4, 5, 6])
        view.setModel(model)
        
        view.select_column(0)
        
        cols = view.get_selected_columns()
        assert len(cols) == 1
        assert cols[0] == 0
    
    def test_clear_selection(self, view, model):
        """Test clearing selection."""
        model.add_data_column("x", data=[1, 2, 3])
        view.setModel(model)
        
        view.select_cell(0, 0)
        assert len(view.get_selected_cells()) > 0
        
        view.clear_selection()
        assert len(view.get_selected_cells()) == 0


class TestDelegates:
    """Test delegate creation and formatting."""
    
    def test_numeric_delegate_formatting(self, view, model):
        """Test numeric delegate formats floats correctly."""
        model.add_data_column("x", data=[1.23456789, 2.0, 3.141592])
        view.setModel(model)
        
        # Check display (default precision is 6)
        idx = model.index(0, 0)
        display = model.data(idx, Qt.ItemDataRole.DisplayRole)
        # Should be formatted with precision
        assert "1.23457" in display or "1.2346" in display
    
    def test_integer_delegate_formatting(self, view, model):
        """Test integer delegate formats integers correctly."""
        model.add_data_column("count", dtype=DataType.INTEGER, data=[1, 2, 3])
        view.setModel(model)
        
        idx = model.index(0, 0)
        display = model.data(idx, Qt.ItemDataRole.DisplayRole)
        assert display == "1"
    
    def test_string_delegate(self, view, model):
        """Test string delegate."""
        model.add_data_column("label", dtype=DataType.STRING, data=["a", "b", "c"])
        view.setModel(model)
        
        idx = model.index(0, 0)
        display = model.data(idx, Qt.ItemDataRole.DisplayRole)
        assert display == "a"
    
    def test_boolean_delegate(self, view, model):
        """Test boolean delegate."""
        model.add_data_column("flag", dtype=DataType.BOOLEAN, data=[True, False, True])
        view.setModel(model)
        
        idx = model.index(0, 0)
        display = model.data(idx, Qt.ItemDataRole.DisplayRole)
        assert display in ("True", "False", "1", "0")


class TestDynamicUpdates:
    """Test view updates when model changes."""
    
    def test_add_column_updates_view(self, widget):
        """Test adding column updates view."""
        initial_cols = widget.model().columnCount()
        
        widget.add_data_column("new_col", data=[1, 2, 3])
        
        assert widget.model().columnCount() == initial_cols + 1
    
    def test_remove_column_updates_view(self, widget):
        """Test removing column updates view."""
        widget.add_data_column("temp", data=[1, 2, 3])
        widget.add_data_column("keep", data=[4, 5, 6])
        
        initial_cols = widget.model().columnCount()
        widget.remove_column("temp")
        
        assert widget.model().columnCount() == initial_cols - 1
    
    def test_data_change_updates_view(self, widget):
        """Test changing data updates view display."""
        widget.add_data_column("x", data=[1, 2, 3])
        
        # Change a value
        idx = widget.model().index(0, 0)
        widget.model().setData(idx, 999, Qt.ItemDataRole.EditRole)
        
        # Check updated
        new_val = widget.model().data(idx, Qt.ItemDataRole.DisplayRole)
        assert new_val == "999"


class TestViewConfiguration:
    """Test view configuration options."""
    
    def test_alternating_row_colors(self, view):
        """Test alternating row colors is enabled."""
        assert view.alternatingRowColors() is True
    
    def test_selection_mode(self, view):
        """Test selection mode is set correctly."""
        assert view.selectionMode() == view.SelectionMode.ExtendedSelection
    
    def test_selection_behavior(self, view):
        """Test selection behavior is items."""
        assert view.selectionBehavior() == view.SelectionBehavior.SelectItems
