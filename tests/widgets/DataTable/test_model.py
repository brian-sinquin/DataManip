"""
Unit tests for DataTableModel.

Tests the core data model functionality including data storage, retrieval,
and Qt model interface implementation.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

import pytest
import pandas as pd
import numpy as np
from PySide6.QtCore import Qt, QModelIndex
from widgets.DataTable.model import DataTableModel, ColumnExistsError, ColumnNotFoundError
from widgets.DataTable.column_metadata import ColumnType


class TestDataTableModelBasics:
    """Test basic model creation and properties."""
    
    def test_create_empty_model(self):
        """Test creating an empty model."""
        model = DataTableModel()
        
        assert model.rowCount() == 0
        assert model.columnCount() == 0
        assert model.get_column_names() == []
    
    def test_add_single_data_column_no_data(self):
        """Test adding a DATA column without initial data."""
        model = DataTableModel()
        model.add_data_column("time", unit="s", description="Time values")
        
        assert model.columnCount() == 1
        assert model.rowCount() == 0
        assert "time" in model.get_column_names()
    
    def test_add_single_data_column_with_data(self):
        """Test adding a DATA column with initial data."""
        model = DataTableModel()
        data = [0, 1, 2, 3, 4]
        model.add_data_column("time", unit="s", data=data)
        
        assert model.columnCount() == 1
        assert model.rowCount() == 5
        
        # Verify data
        col_data = model.get_column_data("time")
        assert len(col_data) == 5
        assert list(col_data) == data
    
    def test_add_multiple_columns(self):
        """Test adding multiple columns."""
        model = DataTableModel()
        model.add_data_column("time", unit="s", data=[0, 1, 2])
        model.add_data_column("position", unit="m", data=[0, 5, 10])
        model.add_data_column("velocity", unit="m/s", data=[5, 5, 5])
        
        assert model.columnCount() == 3
        assert model.rowCount() == 3
        assert model.get_column_names() == ["time", "position", "velocity"]
    
    def test_duplicate_column_name_raises_error(self):
        """Test that adding duplicate column name raises ColumnExistsError."""
        model = DataTableModel()
        model.add_data_column("time", unit="s")
        
        with pytest.raises(ColumnExistsError, match="already exists"):
            model.add_data_column("time", unit="ms")
    
    def test_get_nonexistent_column_raises_error(self):
        """Test that getting non-existent column raises ColumnNotFoundError."""
        model = DataTableModel()
        
        with pytest.raises(ColumnNotFoundError):
            model.get_column_data("nonexistent")
    
    def test_column_order_preserved(self):
        """Test that column order is preserved."""
        model = DataTableModel()
        model.add_data_column("c")
        model.add_data_column("a")
        model.add_data_column("b")
        
        assert model.get_column_names() == ["c", "a", "b"]


class TestDataTableModelQtInterface:
    """Test Qt model interface methods."""
    
    def test_data_display_role(self):
        """Test getting data with DisplayRole."""
        model = DataTableModel()
        model.add_data_column("values", data=[1.234567, 2.345678, 3.456789])
        
        # Get first cell
        index = model.index(0, 0)
        value = model.data(index, Qt.ItemDataRole.DisplayRole)
        
        # Should be formatted with precision
        assert value == "1.23457"  # Default precision = 6
    
    def test_data_edit_role(self):
        """Test getting data with EditRole."""
        model = DataTableModel()
        model.add_data_column("values", data=[1.234567])
        
        index = model.index(0, 0)
        value = model.data(index, Qt.ItemDataRole.EditRole)
        
        # Should return raw value
        assert value == 1.234567
    
    def test_data_invalid_index(self):
        """Test that invalid index returns None."""
        model = DataTableModel()
        model.add_data_column("values", data=[1, 2, 3])
        
        # Out of bounds index
        index = model.index(10, 0)
        value = model.data(index, Qt.ItemDataRole.DisplayRole)
        
        assert value is None
    
    def test_data_nan_displayed_as_empty(self):
        """Test that NaN values are displayed as empty string."""
        model = DataTableModel()
        model.add_data_column("values", data=[1.0, np.nan, 3.0])
        
        index = model.index(1, 0)
        value = model.data(index, Qt.ItemDataRole.DisplayRole)
        
        assert value == ""
    
    def test_setData_valid(self):
        """Test setting data in an editable column."""
        model = DataTableModel()
        model.add_data_column("values", data=[1.0, 2.0, 3.0])
        
        index = model.index(1, 0)
        success = model.setData(index, 10.5, Qt.ItemDataRole.EditRole)
        
        assert success is True
        
        # Verify data was updated
        col_data = model.get_column_data("values")
        assert col_data.iloc[1] == 10.5
    
    def test_setData_string_to_float_conversion(self):
        """Test that string values are converted to float."""
        model = DataTableModel()
        model.add_data_column("values", data=[1.0, 2.0])
        
        index = model.index(0, 0)
        success = model.setData(index, "3.14", Qt.ItemDataRole.EditRole)
        
        assert success is True
        col_data = model.get_column_data("values")
        assert col_data.iloc[0] == 3.14
    
    def test_setData_empty_string_to_nan(self):
        """Test that empty string is converted to NaN."""
        model = DataTableModel()
        model.add_data_column("values", data=[1.0, 2.0])
        
        index = model.index(0, 0)
        success = model.setData(index, "", Qt.ItemDataRole.EditRole)
        
        assert success is True
        col_data = model.get_column_data("values")
        assert pd.isna(col_data.iloc[0])
    
    def test_setData_invalid_value(self):
        """Test that invalid values are rejected."""
        model = DataTableModel()
        model.add_data_column("values", data=[1.0, 2.0])
        
        index = model.index(0, 0)
        success = model.setData(index, "not a number", Qt.ItemDataRole.EditRole)
        
        assert success is False
    
    def test_headerData_horizontal(self):
        """Test getting horizontal header data (column headers)."""
        model = DataTableModel()
        model.add_data_column("time", unit="s", description="Time values")
        
        header = model.headerData(0, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        
        # Should include symbol and unit
        assert "●" in header  # DATA symbol
        assert "time" in header
        assert "[s]" in header
    
    def test_headerData_vertical(self):
        """Test getting vertical header data (row numbers)."""
        model = DataTableModel()
        model.add_data_column("values", data=[1, 2, 3])
        
        header = model.headerData(0, Qt.Orientation.Vertical, Qt.ItemDataRole.DisplayRole)
        
        assert header == "1"  # Row numbers start at 1
    
    def test_flags_editable_column(self):
        """Test that DATA columns have editable flag."""
        model = DataTableModel()
        model.add_data_column("values", data=[1, 2, 3])
        
        index = model.index(0, 0)
        flags = model.flags(index)
        
        assert flags & Qt.ItemFlag.ItemIsEditable
        assert flags & Qt.ItemFlag.ItemIsEnabled
        assert flags & Qt.ItemFlag.ItemIsSelectable
    
    def test_flags_invalid_index(self):
        """Test that invalid index has no flags."""
        model = DataTableModel()
        model.add_data_column("values", data=[1, 2, 3])
        
        invalid_index = QModelIndex()
        flags = model.flags(invalid_index)
        
        assert flags == Qt.ItemFlag.NoItemFlags


class TestDataTableModelData:
    """Test data manipulation methods."""
    
    def test_get_column_data_returns_copy(self):
        """Test that get_column_data returns a copy, not reference."""
        model = DataTableModel()
        model.add_data_column("values", data=[1, 2, 3])
        
        data1 = model.get_column_data("values")
        data2 = model.get_column_data("values")
        
        # Modify one copy
        data1.iloc[0] = 999
        
        # Other copy should be unchanged
        assert data2.iloc[0] == 1
    
    def test_get_column_metadata(self):
        """Test getting column metadata."""
        model = DataTableModel()
        model.add_data_column("time", unit="s", description="Time values", precision=3)
        
        metadata = model.get_column_metadata("time")
        
        assert metadata.name == "time"
        assert metadata.unit == "s"
        assert metadata.description == "Time values"
        assert metadata.precision == 3
        assert metadata.column_type == ColumnType.DATA
    
    def test_to_dataframe_empty(self):
        """Test converting empty model to DataFrame."""
        model = DataTableModel()
        
        df = model.to_dataframe()
        
        assert isinstance(df, pd.DataFrame)
        assert df.empty
    
    def test_to_dataframe_with_data(self):
        """Test converting model with data to DataFrame."""
        model = DataTableModel()
        model.add_data_column("time", data=[0, 1, 2])
        model.add_data_column("position", data=[0, 5, 10])
        
        df = model.to_dataframe()
        
        assert isinstance(df, pd.DataFrame)
        assert df.shape == (3, 2)
        assert list(df.columns) == ["time", "position"]
        assert list(df["time"]) == [0, 1, 2]
        assert list(df["position"]) == [0, 5, 10]
    
    def test_custom_precision(self):
        """Test that custom precision affects display."""
        model = DataTableModel()
        model.add_data_column("values", data=[1.23456789], precision=2)
        
        index = model.index(0, 0)
        value = model.data(index, Qt.ItemDataRole.DisplayRole)
        
        # Should be formatted with 2 significant figures
        assert value == "1.2"
    
    def test_numpy_array_as_data(self):
        """Test that NumPy arrays can be used as initial data."""
        model = DataTableModel()
        data = np.array([1.0, 2.0, 3.0, 4.0])
        model.add_data_column("values", data=data)
        
        col_data = model.get_column_data("values")
        assert len(col_data) == 4
        np.testing.assert_array_equal(col_data.values, data)
    
    def test_pandas_series_as_data(self):
        """Test that Pandas Series can be used as initial data."""
        model = DataTableModel()
        data = pd.Series([10, 20, 30])
        model.add_data_column("values", data=data)
        
        col_data = model.get_column_data("values")
        assert len(col_data) == 3
        assert list(col_data) == [10, 20, 30]


class TestColumnOperations:
    """Test remove, rename, and reorder operations."""
    
    def test_remove_column(self):
        """Test removing a column."""
        model = DataTableModel()
        model.add_data_column("col1", data=[1, 2, 3])
        model.add_data_column("col2", data=[4, 5, 6])
        model.add_data_column("col3", data=[7, 8, 9])
        
        assert model.columnCount() == 3
        model.remove_column("col2")
        
        assert model.columnCount() == 2
        assert model.get_column_names() == ["col1", "col3"]
    
    def test_rename_column(self):
        """Test renaming a column."""
        model = DataTableModel()
        model.add_data_column("old_name", data=[1, 2, 3], unit="m")
        
        model.rename_column("old_name", "new_name")
        
        assert "new_name" in model.get_column_names()
        assert "old_name" not in model.get_column_names()
        metadata = model.get_column_metadata("new_name")
        assert metadata.unit == "m"


class TestDependencyTracking:
    """Test dependency graph for calculated columns."""
    
    def test_dependency_registration(self):
        """Test registering and retrieving dependencies."""
        model = DataTableModel()
        model.add_data_column("x", data=[1, 2, 3])
        model.add_data_column("y", data=[4, 5, 6])
        
        model._register_dependency("result", "x")
        model._register_dependency("result", "y")
        
        assert model._dependencies["result"] == {"x", "y"}
        assert "result" in model._dependents["x"]
    
    def test_circular_dependency_detection(self):
        """Test that circular dependencies are detected."""
        model = DataTableModel()
        model.add_data_column("a", data=[1, 2, 3])
        
        model._register_dependency("b", "a")
        model._register_dependency("c", "b")
        model._register_dependency("a", "c")
        
        with pytest.raises(ValueError, match="Circular dependency"):
            model._get_recalculation_order("a")
