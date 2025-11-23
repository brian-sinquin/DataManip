"""
Tests for clipboard operations (copy/paste/cut/clear).

This module tests clipboard functionality for DataTableV2, including:
- Copy selection to TSV
- Paste from TSV
- Cut operation (copy + clear)
- Clear selection
- Read-only column handling
- Type conversion
- Error handling
"""

import pytest
import pandas as pd
import numpy as np
from PySide6.QtCore import Qt

from widgets.data_table.model import DataTableModel
from widgets.data_table.column_metadata import ColumnType, DataType


class TestCopyToTSV:
    """Test copying selected cells to TSV format."""
    
    def test_copy_single_cell(self):
        """Test copying a single cell."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1.5, 2.5, 3.5]))
        
        selection = [(0, 0)]  # First cell
        tsv = model.copy_selection_to_tsv(selection)
        
        assert tsv == "1.5"
    
    def test_copy_row(self):
        """Test copying an entire row."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1.0, 2.0]))
        model.add_data_column("B", data=pd.Series([10.0, 20.0]))
        model.add_data_column("C", data=pd.Series([100.0, 200.0]))
        
        selection = [(0, 0), (0, 1), (0, 2)]  # First row
        tsv = model.copy_selection_to_tsv(selection)
        
        assert tsv == "1\t10\t100"
    
    def test_copy_column(self):
        """Test copying an entire column."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1.0, 2.0, 3.0]))
        
        selection = [(0, 0), (1, 0), (2, 0)]
        tsv = model.copy_selection_to_tsv(selection)
        
        expected = "1\n2\n3"
        assert tsv == expected
    
    def test_copy_rectangular_range(self):
        """Test copying a rectangular range of cells."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1, 2, 3]))
        model.add_data_column("B", data=pd.Series([10, 20, 30]))
        model.add_data_column("C", data=pd.Series([100, 200, 300]))
        
        # 2x2 range (rows 0-1, cols 1-2)
        selection = [(0, 1), (0, 2), (1, 1), (1, 2)]
        tsv = model.copy_selection_to_tsv(selection)
        
        expected = "10\t100\n20\t200"
        assert tsv == expected
    
    def test_copy_sparse_selection(self):
        """Test copying non-contiguous cells."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1, 2, 3]))
        model.add_data_column("B", data=pd.Series([10, 20, 30]))
        model.add_data_column("C", data=pd.Series([100, 200, 300]))
        
        # Sparse selection with gaps
        selection = [(0, 0), (0, 2)]  # First row, columns 0 and 2
        tsv = model.copy_selection_to_tsv(selection)
        
        # Gaps filled with empty strings
        expected = "1\t\t100"
        assert tsv == expected
    
    def test_copy_empty_selection(self):
        """Test copying empty selection returns empty string."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1, 2, 3]))
        
        selection = []
        tsv = model.copy_selection_to_tsv(selection)
        
        assert tsv == ""
    
    def test_copy_with_nan_values(self):
        """Test copying cells with NaN values."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1.0, np.nan, 3.0]))
        
        selection = [(0, 0), (1, 0), (2, 0)]
        tsv = model.copy_selection_to_tsv(selection)
        
        # NaN displayed as empty string
        expected = "1\n\n3"
        assert tsv == expected
    
    def test_copy_string_data(self):
        """Test copying string data."""
        model = DataTableModel()
        model.add_data_column("Name", dtype=DataType.STRING, data=pd.Series(["Alice", "Bob", "Charlie"]))
        
        selection = [(0, 0), (1, 0), (2, 0)]
        tsv = model.copy_selection_to_tsv(selection)
        
        expected = "Alice\nBob\nCharlie"
        assert tsv == expected


class TestPasteFromTSV:
    """Test pasting TSV data into table."""
    
    def test_paste_single_cell(self):
        """Test pasting into a single cell."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([0.0, 0.0, 0.0]))
        
        tsv = "42.5"
        rows, cells, errors = model.paste_from_tsv(tsv, start_row=1, start_col=0)
        
        assert rows == 1
        assert cells == 1
        assert len(errors) == 0
        
        # Check value was set
        idx = model.index(1, 0)
        assert float(model.data(idx, Qt.ItemDataRole.DisplayRole)) == 42.5
    
    def test_paste_row(self):
        """Test pasting a row of data."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([0.0, 0.0]))
        model.add_data_column("B", data=pd.Series([0.0, 0.0]))
        model.add_data_column("C", data=pd.Series([0.0, 0.0]))
        
        tsv = "1.5\t2.5\t3.5"
        rows, cells, errors = model.paste_from_tsv(tsv, start_row=0, start_col=0)
        
        assert rows == 1
        assert cells == 3
        assert len(errors) == 0
        
        # Check values
        assert float(model.data(model.index(0, 0), Qt.ItemDataRole.DisplayRole)) == 1.5
        assert float(model.data(model.index(0, 1), Qt.ItemDataRole.DisplayRole)) == 2.5
        assert float(model.data(model.index(0, 2), Qt.ItemDataRole.DisplayRole)) == 3.5
    
    def test_paste_column(self):
        """Test pasting a column of data."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([0.0, 0.0, 0.0]))
        
        tsv = "10\n20\n30"
        rows, cells, errors = model.paste_from_tsv(tsv, start_row=0, start_col=0)
        
        assert rows == 3
        assert cells == 3
        assert len(errors) == 0
        
        # Check values
        assert float(model.data(model.index(0, 0), Qt.ItemDataRole.DisplayRole)) == 10
        assert float(model.data(model.index(1, 0), Qt.ItemDataRole.DisplayRole)) == 20
        assert float(model.data(model.index(2, 0), Qt.ItemDataRole.DisplayRole)) == 30
    
    def test_paste_rectangular_range(self):
        """Test pasting a rectangular block."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([0, 0, 0]))
        model.add_data_column("B", data=pd.Series([0, 0, 0]))
        model.add_data_column("C", data=pd.Series([0, 0, 0]))
        
        tsv = "1\t2\n3\t4"
        rows, cells, errors = model.paste_from_tsv(tsv, start_row=1, start_col=1)
        
        assert rows == 2
        assert cells == 4
        assert len(errors) == 0
        
        # Check values were pasted starting at (1, 1)
        assert float(model.data(model.index(1, 1), Qt.ItemDataRole.DisplayRole)) == 1
        assert float(model.data(model.index(1, 2), Qt.ItemDataRole.DisplayRole)) == 2
        assert float(model.data(model.index(2, 1), Qt.ItemDataRole.DisplayRole)) == 3
        assert float(model.data(model.index(2, 2), Qt.ItemDataRole.DisplayRole)) == 4
    
    def test_paste_skips_readonly_columns(self):
        """Test that paste skips read-only columns (CALCULATED, RANGE, DERIVATIVE)."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1.0, 2.0, 3.0]))
        model.add_calculated_column("B", formula="{A} * 2")
        model.add_data_column("C", data=pd.Series([0.0, 0.0, 0.0]))
        
        # Try to paste into all columns
        tsv = "10\t20\t30"
        rows, cells, errors = model.paste_from_tsv(tsv, start_row=0, start_col=0, skip_readonly=True)
        
        # Should only paste into columns A and C (skipping calculated B)
        assert cells == 2
        
        # Check A was updated
        assert float(model.data(model.index(0, 0), Qt.ItemDataRole.DisplayRole)) == 10
        
        # Check B was NOT updated (still calculated value 1*2=2)
        assert float(model.data(model.index(0, 1), Qt.ItemDataRole.DisplayRole)) == 20  # Recalculated from A
        
        # Check C was updated
        assert float(model.data(model.index(0, 2), Qt.ItemDataRole.DisplayRole)) == 30
    
    def test_paste_type_conversion(self):
        """Test automatic type conversion when pasting."""
        model = DataTableModel()
        model.add_data_column("Int", dtype=DataType.INTEGER, data=pd.Series([0, 0, 0], dtype="int64"))
        model.add_data_column("Float", dtype=DataType.FLOAT, data=pd.Series([0.0, 0.0, 0.0]))
        model.add_data_column("String", dtype=DataType.STRING, data=pd.Series(["", "", ""]))
        
        # Paste different types
        tsv = "42\t3.14\tHello"
        rows, cells, errors = model.paste_from_tsv(tsv, start_row=0, start_col=0)
        
        assert cells == 3
        assert len(errors) == 0
        
        # Check type conversion
        assert model.data(model.index(0, 0), Qt.ItemDataRole.DisplayRole) == "42"
        assert float(model.data(model.index(0, 1), Qt.ItemDataRole.DisplayRole)) == 3.14
        assert model.data(model.index(0, 2), Qt.ItemDataRole.DisplayRole) == "Hello"
    
    def test_paste_out_of_bounds_rows(self):
        """Test pasting beyond table bounds."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([0, 0]))  # Only 2 rows
        
        tsv = "1\n2\n3\n4"  # 4 rows
        rows, cells, errors = model.paste_from_tsv(tsv, start_row=1, start_col=0)
        
        # Should paste only valid rows (row 1 is valid, rows 2-4 are out of bounds)
        assert cells == 1  # Only row 1 pasted
        # Note: Error tracking removed with Command pattern implementation
    
    def test_paste_out_of_bounds_columns(self):
        """Test pasting beyond column bounds."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([0, 0]))
        model.add_data_column("B", data=pd.Series([0, 0]))
        
        tsv = "1\t2\t3\t4"  # 4 columns
        rows, cells, errors = model.paste_from_tsv(tsv, start_row=0, start_col=0)
        
        # Should paste only to existing columns (A, B)
        assert cells == 2
        # Note: Error tracking removed with Command pattern implementation
    
    def test_paste_empty_string(self):
        """Test pasting empty string does nothing."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1.0, 2.0]))
        
        tsv = ""
        rows, cells, errors = model.paste_from_tsv(tsv, start_row=0, start_col=0)
        
        assert rows == 0
        assert cells == 0
        assert len(errors) == 0
    
    def test_paste_triggers_recalculation(self):
        """Test that pasting into data column triggers recalculation."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1.0, 2.0, 3.0]))
        model.add_calculated_column("B", formula="{A} * 10")
        
        # Paste new value into A
        tsv = "5.0"
        model.paste_from_tsv(tsv, start_row=0, start_col=0)
        
        # Check that B was recalculated
        idx_b = model.index(0, 1)
        assert float(model.data(idx_b, Qt.ItemDataRole.DisplayRole)) == 50.0  # 5 * 10


class TestClearSelection:
    """Test clearing selected cells."""
    
    def test_clear_single_cell(self):
        """Test clearing a single cell sets it to NaN."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1.0, 2.0, 3.0]))
        
        selection = [(1, 0)]
        cleared = model.clear_selection(selection)
        
        assert cleared == 1
        
        # Check cell is NaN
        idx = model.index(1, 0)
        value = model.data(idx, Qt.ItemDataRole.DisplayRole)
        assert value is None or value == ""  # NaN displayed as empty
    
    def test_clear_multiple_cells(self):
        """Test clearing multiple cells."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1, 2, 3]))
        model.add_data_column("B", data=pd.Series([10, 20, 30]))
        
        selection = [(0, 0), (0, 1), (1, 0), (1, 1)]
        cleared = model.clear_selection(selection)
        
        assert cleared == 4
        
        # All should be NaN/empty
        for row, col in selection:
            value = model.data(model.index(row, col), Qt.ItemDataRole.DisplayRole)
            assert value is None or value == ""
    
    def test_clear_skips_readonly_columns(self):
        """Test clear skips read-only columns."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1.0, 2.0]))
        model.add_calculated_column("B", formula="{A} * 2")
        
        # Try to clear both columns
        selection = [(0, 0), (0, 1)]
        cleared = model.clear_selection(selection)
        
        # Should only clear column A
        assert cleared == 1
        
        # A should be cleared
        assert model.data(model.index(0, 0), Qt.ItemDataRole.DisplayRole) in (None, "")
        
        # B should still have calculated value (now NaN * 2 = NaN)
        # (Actually will be empty since A is now NaN)
    
    def test_clear_string_column(self):
        """Test clearing string column sets to empty string."""
        model = DataTableModel()
        model.add_data_column("Name", dtype=DataType.STRING, data=pd.Series(["Alice", "Bob", "Charlie"]))
        
        selection = [(1, 0)]
        cleared = model.clear_selection(selection)
        
        assert cleared == 1
        assert model.data(model.index(1, 0), Qt.ItemDataRole.DisplayRole) == ""
    
    def test_clear_triggers_recalculation(self):
        """Test that clearing triggers recalculation of dependent columns."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([5.0, 10.0]))
        model.add_calculated_column("B", formula="{A} * 2")
        
        # Clear A[0]
        selection = [(0, 0)]
        model.clear_selection(selection)
        
        # B[0] should be recalculated (NaN * 2 = NaN)
        b_value = model.data(model.index(0, 1), Qt.ItemDataRole.DisplayRole)
        assert b_value in (None, "")  # NaN displayed as empty


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_copy_paste_roundtrip(self):
        """Test that copy followed by paste preserves values."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1.5, 2.5, 3.5]))
        model.add_data_column("B", data=pd.Series([10.0, 20.0, 30.0]))
        
        # Copy first row
        selection = [(0, 0), (0, 1)]
        tsv = model.copy_selection_to_tsv(selection)
        
        # Paste to second row
        model.paste_from_tsv(tsv, start_row=1, start_col=0)
        
        # Check values match
        assert float(model.data(model.index(1, 0), Qt.ItemDataRole.DisplayRole)) == 1.5
        assert float(model.data(model.index(1, 1), Qt.ItemDataRole.DisplayRole)) == 10.0
    
    def test_paste_with_trailing_tabs(self):
        """Test pasting data with trailing tabs."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([0, 0]))
        model.add_data_column("B", data=pd.Series([0, 0]))
        
        # TSV with trailing tabs (empty cells)
        tsv = "1\t2\t\t"
        rows, cells, errors = model.paste_from_tsv(tsv, start_row=0, start_col=0)
        
        # Should paste valid values only
        assert cells == 2
    
    def test_empty_model_copy(self):
        """Test copying from empty model."""
        model = DataTableModel()
        
        selection = []
        tsv = model.copy_selection_to_tsv(selection)
        
        assert tsv == ""
    
    def test_empty_model_paste(self):
        """Test pasting into empty model."""
        model = DataTableModel()
        
        tsv = "1\t2\t3"
        rows, cells, errors = model.paste_from_tsv(tsv, start_row=0, start_col=0)
        
        # Should fail gracefully (no columns to paste into)
        assert cells == 0
        # Note: Error tracking removed with Command pattern implementation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
