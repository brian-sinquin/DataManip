"""
Tests for file I/O operations (JSON, CSV, Excel).

Tests saving and loading data tables in various formats, verifying
data integrity and metadata preservation.
"""

import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path
from PySide6.QtCore import Qt

from widgets.data_table.model import DataTableModel
from widgets.data_table.column_metadata import ColumnType, DataType


class TestJSONFileIO:
    """Tests for JSON file format."""
    
    def test_save_json_simple_data(self, tmp_path):
        """Test saving simple data table to JSON."""
        model = DataTableModel()
        model.add_data_column("x", data=[1.0, 2.0, 3.0], unit="m")
        model.add_data_column("y", data=[4.0, 5.0, 6.0], unit="s")
        
        filepath = tmp_path / "test.json"
        model.save_to_json(str(filepath))
        
        assert filepath.exists()
        
        # Check file content
        import json
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        assert data["version"] == "2.0.0"
        assert len(data["columns"]) == 2
        assert data["columns"][0]["name"] == "x"
        assert data["columns"][0]["unit"] == "m"
        assert data["data"]["x"] == [1.0, 2.0, 3.0]
    
    def test_save_json_calculated_column(self, tmp_path):
        """Test saving calculated column with formula."""
        model = DataTableModel()
        model.add_data_column("a", data=[1.0, 2.0, 3.0])
        model.add_data_column("b", data=[4.0, 5.0, 6.0])
        model.add_calculated_column("c", formula="{a} + {b}")
        
        filepath = tmp_path / "calc.json"
        model.save_to_json(str(filepath))
        
        import json
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Find calculated column
        calc_col = [c for c in data["columns"] if c["name"] == "c"][0]
        assert calc_col["column_type"] == "calc"
        assert calc_col["formula"] == "{a} + {b}"
    
    def test_save_json_range_column(self, tmp_path):
        """Test saving range column."""
        model = DataTableModel()
        model.add_range_column("t", start=0, end=10, points=11, unit="s")
        
        filepath = tmp_path / "range.json"
        model.save_to_json(str(filepath))
        
        import json
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        col = data["columns"][0]
        assert col["column_type"] == "range"
        assert col["range_start"] == 0
        assert col["range_end"] == 10
        assert col["range_points"] == 11
    
    def test_save_json_derivative_column(self, tmp_path):
        """Test saving derivative column."""
        model = DataTableModel()
        model.add_range_column("t", start=0, end=5, points=6)
        model.add_data_column("x", data=[0, 1, 4, 9, 16, 25])
        model.add_derivative_column("v", "x", "t", method="forward")
        
        filepath = tmp_path / "deriv.json"
        model.save_to_json(str(filepath))
        
        import json
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        deriv_col = [c for c in data["columns"] if c["name"] == "v"][0]
        assert deriv_col["column_type"] == "deriv"
        assert deriv_col["derivative_numerator"] == "x"
        assert deriv_col["derivative_denominator"] == "t"
    
    def test_save_json_with_nan_values(self, tmp_path):
        """Test saving data with NaN values."""
        model = DataTableModel()
        model.add_data_column("x", data=[1.0, np.nan, 3.0])
        
        filepath = tmp_path / "nan.json"
        model.save_to_json(str(filepath))
        
        import json
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        assert data["data"]["x"] == [1.0, None, 3.0]  # NaN -> null in JSON
    
    def test_load_json_simple_data(self, tmp_path):
        """Test loading simple data from JSON."""
        # Create and save
        model1 = DataTableModel()
        model1.add_data_column("x", data=[1.0, 2.0, 3.0], unit="m", description="Position")
        filepath = tmp_path / "test.json"
        model1.save_to_json(str(filepath))
        
        # Load
        model2 = DataTableModel()
        model2.load_from_json(str(filepath))
        
        assert len(model2.get_column_names()) == 1
        assert model2.get_column_names()[0] == "x"
        assert model2.get_column_metadata("x").unit == "m"
        assert model2.get_column_metadata("x").description == "Position"
        
        data = model2.get_column_data("x")
        assert list(data) == [1.0, 2.0, 3.0]
    
    def test_load_json_calculated_column(self, tmp_path):
        """Test loading calculated column - should recalculate."""
        # Create and save
        model1 = DataTableModel()
        model1.add_data_column("a", data=[1.0, 2.0, 3.0])
        model1.add_data_column("b", data=[4.0, 5.0, 6.0])
        model1.add_calculated_column("sum", formula="{a} + {b}")
        
        filepath = tmp_path / "calc.json"
        model1.save_to_json(str(filepath))
        
        # Load
        model2 = DataTableModel()
        model2.load_from_json(str(filepath))
        
        assert "sum" in model2.get_column_names()
        assert model2.get_column_metadata("sum").formula == "{a} + {b}"
        
        # Verify recalculation
        result = model2.get_column_data("sum")
        expected = [5.0, 7.0, 9.0]
        assert list(result) == expected
    
    def test_load_json_derivative_column(self, tmp_path):
        """Test loading derivative column - should recalculate."""
        # Create and save
        model1 = DataTableModel()
        model1.add_range_column("t", start=0, end=2, points=3)
        model1.add_data_column("x", data=[0, 1, 4])
        model1.add_derivative_column("v", "x", "t")
        
        filepath = tmp_path / "deriv.json"
        model1.save_to_json(str(filepath))
        
        # Load
        model2 = DataTableModel()
        model2.load_from_json(str(filepath))
        
        assert "v" in model2.get_column_names()
        meta = model2.get_column_metadata("v")
        assert meta.derivative_numerator == "x"
        assert meta.derivative_denominator == "t"
        
        # Verify recalculation (forward difference)
        result = model2.get_column_data("v")
        # dx/dt = (x[i+1] - x[i]) / (t[i+1] - t[i])
        # [0, 1, 4] -> dy = [1, 3], dt = [1, 1] -> [1, 3, NaN]
        assert not pd.isna(result.iloc[0])
        assert not pd.isna(result.iloc[1])
    
    def test_roundtrip_json(self, tmp_path):
        """Test save->load->save produces identical files."""
        # Create complex table
        model1 = DataTableModel()
        model1.add_range_column("t", start=0, end=5, points=6, unit="s")
        model1.add_data_column("v0", data=[10.0]*6, unit="m/s")
        model1.add_calculated_column("x", formula="{v0} * {t}", unit="m")
        model1.add_derivative_column("v", "x", "t")
        
        filepath1 = tmp_path / "original.json"
        filepath2 = tmp_path / "roundtrip.json"
        
        # Save, load, save again
        model1.save_to_json(str(filepath1))
        
        model2 = DataTableModel()
        model2.load_from_json(str(filepath1))
        model2.save_to_json(str(filepath2))
        
        # Compare files (structure, not exact data due to recalculation)
        import json
        with open(filepath1) as f:
            data1 = json.load(f)
        with open(filepath2) as f:
            data2 = json.load(f)
        
        assert len(data1["columns"]) == len(data2["columns"])
        for col1, col2 in zip(data1["columns"], data2["columns"]):
            assert col1["name"] == col2["name"]
            assert col1["column_type"] == col2["column_type"]
            assert col1.get("formula") == col2.get("formula")


class TestCSVFileIO:
    """Tests for CSV file format."""
    
    def test_save_csv_basic(self, tmp_path):
        """Test saving basic data to CSV."""
        model = DataTableModel()
        model.add_data_column("x", data=[1.0, 2.0, 3.0])
        model.add_data_column("y", data=[4.0, 5.0, 6.0])
        
        filepath = tmp_path / "test.csv"
        model.save_to_csv(str(filepath), include_metadata=False)
        
        assert filepath.exists()
        
        # Read back as plain CSV
        df = pd.read_csv(filepath)
        assert list(df.columns) == ["x", "y"]
        assert list(df["x"]) == [1.0, 2.0, 3.0]
    
    def test_save_csv_with_metadata(self, tmp_path):
        """Test saving CSV with metadata comments."""
        model = DataTableModel()
        model.add_data_column("temp", data=[20.0, 25.0, 30.0], unit="°C")
        model.add_calculated_column("temp_K", formula="{temp} + 273.15", unit="K")
        
        filepath = tmp_path / "test_meta.csv"
        model.save_to_csv(str(filepath), include_metadata=True)
        
        # Check file has comments
        with open(filepath, 'r') as f:
            content = f.read()
        
        assert "# DataTableV2 CSV Export" in content
        assert "# Version: 2.0.0" in content
        assert "temp:" in content
        assert "°C" in content
    
    def test_load_csv_basic(self, tmp_path):
        """Test loading basic CSV."""
        # Create CSV file
        filepath = tmp_path / "data.csv"
        df = pd.DataFrame({
            "a": [1, 2, 3],
            "b": [4.0, 5.0, 6.0],
            "c": ["x", "y", "z"]
        })
        df.to_csv(filepath, index=False)
        
        # Load
        model = DataTableModel()
        model.load_from_csv(str(filepath), has_metadata=False)
        
        assert len(model.get_column_names()) == 3
        assert list(model.get_column_data("a")) == [1, 2, 3]
        assert model.get_column_metadata("a").dtype == DataType.INTEGER
        assert model.get_column_metadata("b").dtype == DataType.FLOAT


class TestExcelFileIO:
    """Tests for Excel file format."""
    
    def test_save_excel_basic(self, tmp_path):
        """Test saving to Excel with two sheets."""
        model = DataTableModel()
        model.add_data_column("x", data=[1.0, 2.0, 3.0], unit="m", description="Position")
        model.add_data_column("y", data=[4.0, 5.0, 6.0], unit="s", description="Time")
        
        filepath = tmp_path / "test.xlsx"
        model.save_to_excel(str(filepath))
        
        assert filepath.exists()
        
        # Read back
        df_data = pd.read_excel(filepath, sheet_name="Data")
        df_meta = pd.read_excel(filepath, sheet_name="Metadata")
        
        assert list(df_data.columns) == ["x", "y"]
        assert list(df_data["x"]) == [1.0, 2.0, 3.0]
        
        assert "Column Name" in df_meta.columns
        assert list(df_meta["Column Name"]) == ["x", "y"]
        assert list(df_meta["Unit"]) == ["m", "s"]
    
    def test_save_excel_with_formulas(self, tmp_path):
        """Test Excel save includes formula metadata."""
        model = DataTableModel()
        model.add_data_column("a", data=[1.0, 2.0])
        model.add_calculated_column("b", formula="{a} * 2")
        
        filepath = tmp_path / "formulas.xlsx"
        model.save_to_excel(str(filepath))
        
        df_meta = pd.read_excel(filepath, sheet_name="Metadata")
        
        # Check formula is in metadata
        b_row = df_meta[df_meta["Column Name"] == "b"].iloc[0]
        assert b_row["Formula"] == "{a} * 2"
    
    def test_load_excel_basic(self, tmp_path):
        """Test loading from Excel."""
        # Create and save
        model1 = DataTableModel()
        model1.add_data_column("x", data=[1.0, 2.0, 3.0], unit="m", description="Test")
        
        filepath = tmp_path / "test.xlsx"
        model1.save_to_excel(str(filepath))
        
        # Load
        model2 = DataTableModel()
        model2.load_from_excel(str(filepath))
        
        assert "x" in model2.get_column_names()
        assert model2.get_column_metadata("x").unit == "m"
        assert model2.get_column_metadata("x").description == "Test"
        assert list(model2.get_column_data("x")) == [1.0, 2.0, 3.0]
    
    def test_excel_roundtrip(self, tmp_path):
        """Test save->load round trip preserves data."""
        model1 = DataTableModel()
        model1.add_data_column("temp", data=[20.0, 25.0, 30.0], unit="°C")
        model1.add_data_column("pressure", data=[101.3, 102.1, 103.5], unit="kPa")
        
        filepath = tmp_path / "roundtrip.xlsx"
        model1.save_to_excel(str(filepath))
        
        model2 = DataTableModel()
        model2.load_from_excel(str(filepath))
        
        assert model2.get_column_names() == model1.get_column_names()
        
        for col in model1.get_column_names():
            data1 = list(model1.get_column_data(col))
            data2 = list(model2.get_column_data(col))
            assert data1 == data2


class TestFileIOEdgeCases:
    """Test edge cases and error handling."""
    
    def test_save_json_empty_model(self, tmp_path):
        """Test saving empty model."""
        model = DataTableModel()
        filepath = tmp_path / "empty.json"
        model.save_to_json(str(filepath))
        
        import json
        with open(filepath) as f:
            data = json.load(f)
        
        assert data["columns"] == []
        assert data["data"] == {}
    
    def test_load_json_nonexistent_file(self):
        """Test loading from nonexistent file raises error."""
        model = DataTableModel()
        with pytest.raises(FileNotFoundError):
            model.load_from_json("/nonexistent/file.json")
    
    def test_load_json_invalid_version(self, tmp_path):
        """Test loading unsupported version raises error."""
        import json
        filepath = tmp_path / "old.json"
        with open(filepath, 'w') as f:
            json.dump({"version": "1.0.0", "columns": [], "data": {}}, f)
        
        model = DataTableModel()
        with pytest.raises(ValueError, match="Unsupported file version"):
            model.load_from_json(str(filepath))
    
    def test_save_load_large_dataset(self, tmp_path):
        """Test handling large datasets efficiently."""
        model1 = DataTableModel()
        n = 10000
        model1.add_range_column("x", start=0, end=n-1, points=n)
        model1.add_calculated_column("x2", formula="{x} ** 2")
        model1.add_calculated_column("x3", formula="{x} ** 3")
        
        filepath = tmp_path / "large.json"
        model1.save_to_json(str(filepath))
        
        model2 = DataTableModel()
        model2.load_from_json(str(filepath))
        
        assert model2.rowCount() == n
        assert model2.columnCount() == 3
        
        # Spot check some values using data() method
        idx_0_1 = model2.index(0, 1)
        idx_10_1 = model2.index(10, 1)
        idx_10_2 = model2.index(10, 2)
        
        assert float(model2.data(idx_0_1, Qt.ItemDataRole.DisplayRole)) == 0  # 0^2
        assert float(model2.data(idx_10_1, Qt.ItemDataRole.DisplayRole)) == 100  # 10^2
        assert float(model2.data(idx_10_2, Qt.ItemDataRole.DisplayRole)) == 1000  # 10^3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
