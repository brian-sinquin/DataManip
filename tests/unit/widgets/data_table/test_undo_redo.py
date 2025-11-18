"""
Tests for undo/redo functionality.

This module tests the command pattern implementation for undoable/redoable
operations, including:
- Undo/redo single cell edits
- Undo/redo paste operations
- Undo/redo clear operations
- Command history limits
- Redo stack clearing
"""

import pytest
import pandas as pd
import numpy as np
from PySide6.QtCore import Qt

from widgets.data_table.model import DataTableModel
from widgets.data_table.column_metadata import ColumnType, DataType


class TestUndoRedoSingleCellEdit:
    """Test undo/redo for single cell edits."""
    
    def test_undo_single_cell_edit(self):
        """Test undoing a single cell edit."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1.0, 2.0, 3.0]))
        
        # Edit a cell
        idx = model.index(1, 0)
        model.setData(idx, 99.0, Qt.ItemDataRole.EditRole)
        
        # Verify new value
        assert float(model.data(idx, Qt.ItemDataRole.DisplayRole)) == 99.0
        
        # Undo
        assert model.can_undo()
        model.undo()
        
        # Verify old value restored
        assert float(model.data(idx, Qt.ItemDataRole.DisplayRole)) == 2.0
    
    def test_redo_single_cell_edit(self):
        """Test redoing a single cell edit."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1.0, 2.0, 3.0]))
        
        # Edit and undo
        idx = model.index(1, 0)
        model.setData(idx, 99.0, Qt.ItemDataRole.EditRole)
        model.undo()
        
        # Redo
        assert model.can_redo()
        model.redo()
        
        # Verify new value restored
        assert float(model.data(idx, Qt.ItemDataRole.DisplayRole)) == 99.0
    
    def test_multiple_undos(self):
        """Test undoing multiple edits in sequence."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1.0, 2.0, 3.0]))
        
        # Make 3 edits
        idx0 = model.index(0, 0)
        idx1 = model.index(1, 0)
        idx2 = model.index(2, 0)
        
        model.setData(idx0, 10.0, Qt.ItemDataRole.EditRole)
        model.setData(idx1, 20.0, Qt.ItemDataRole.EditRole)
        model.setData(idx2, 30.0, Qt.ItemDataRole.EditRole)
        
        # Undo all 3
        model.undo()
        assert float(model.data(idx2, Qt.ItemDataRole.DisplayRole)) == 3.0
        
        model.undo()
        assert float(model.data(idx1, Qt.ItemDataRole.DisplayRole)) == 2.0
        
        model.undo()
        assert float(model.data(idx0, Qt.ItemDataRole.DisplayRole)) == 1.0
        
        # Nothing left to undo
        assert not model.can_undo()
    
    def test_multiple_redos(self):
        """Test redoing multiple edits in sequence."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1.0, 2.0, 3.0]))
        
        # Make 3 edits and undo all
        idx0 = model.index(0, 0)
        idx1 = model.index(1, 0)
        idx2 = model.index(2, 0)
        
        model.setData(idx0, 10.0, Qt.ItemDataRole.EditRole)
        model.setData(idx1, 20.0, Qt.ItemDataRole.EditRole)
        model.setData(idx2, 30.0, Qt.ItemDataRole.EditRole)
        
        model.undo()
        model.undo()
        model.undo()
        
        # Redo all 3
        model.redo()
        assert float(model.data(idx0, Qt.ItemDataRole.DisplayRole)) == 10.0
        
        model.redo()
        assert float(model.data(idx1, Qt.ItemDataRole.DisplayRole)) == 20.0
        
        model.redo()
        assert float(model.data(idx2, Qt.ItemDataRole.DisplayRole)) == 30.0
        
        # Nothing left to redo
        assert not model.can_redo()
    
    def test_new_edit_clears_redo_stack(self):
        """Test that new edit clears redo stack."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1.0, 2.0, 3.0]))
        
        # Edit, undo, then make new edit
        idx = model.index(0, 0)
        model.setData(idx, 10.0, Qt.ItemDataRole.EditRole)
        model.undo()
        
        # Should be able to redo
        assert model.can_redo()
        
        # Make new edit
        model.setData(idx, 20.0, Qt.ItemDataRole.EditRole)
        
        # Redo stack should be cleared
        assert not model.can_redo()


class TestUndoRedoPaste:
    """Test undo/redo for paste operations."""
    
    def test_undo_paste(self):
        """Test undoing a paste operation."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1, 2, 3]))
        model.add_data_column("B", data=pd.Series([10, 20, 30]))
        
        # Paste some data
        tsv = "100\t200\n300\t400"
        model.paste_from_tsv(tsv, start_row=0, start_col=0)
        
        # Verify pasted values
        assert float(model.data(model.index(0, 0), Qt.ItemDataRole.DisplayRole)) == 100
        assert float(model.data(model.index(0, 1), Qt.ItemDataRole.DisplayRole)) == 200
        assert float(model.data(model.index(1, 0), Qt.ItemDataRole.DisplayRole)) == 300
        assert float(model.data(model.index(1, 1), Qt.ItemDataRole.DisplayRole)) == 400
        
        # Undo
        model.undo()
        
        # Verify original values restored
        assert float(model.data(model.index(0, 0), Qt.ItemDataRole.DisplayRole)) == 1
        assert float(model.data(model.index(0, 1), Qt.ItemDataRole.DisplayRole)) == 10
        assert float(model.data(model.index(1, 0), Qt.ItemDataRole.DisplayRole)) == 2
        assert float(model.data(model.index(1, 1), Qt.ItemDataRole.DisplayRole)) == 20
    
    def test_redo_paste(self):
        """Test redoing a paste operation."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1, 2, 3]))
        model.add_data_column("B", data=pd.Series([10, 20, 30]))
        
        # Paste and undo
        tsv = "100\t200"
        model.paste_from_tsv(tsv, start_row=0, start_col=0)
        model.undo()
        
        # Redo
        model.redo()
        
        # Verify pasted values restored
        assert float(model.data(model.index(0, 0), Qt.ItemDataRole.DisplayRole)) == 100
        assert float(model.data(model.index(0, 1), Qt.ItemDataRole.DisplayRole)) == 200
    
    def test_paste_skips_readonly_columns(self):
        """Test that paste with undo skips read-only columns."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1, 2, 3]))
        model.add_calculated_column("B", formula="{A} * 10")
        model.add_data_column("C", data=pd.Series([100, 200, 300]))
        
        # Try to paste into all columns
        tsv = "10\t20\t30"
        model.paste_from_tsv(tsv, start_row=0, start_col=0)
        
        # A and C should be updated, B should still be calculated
        assert float(model.data(model.index(0, 0), Qt.ItemDataRole.DisplayRole)) == 10
        assert float(model.data(model.index(0, 1), Qt.ItemDataRole.DisplayRole)) == 100  # 10 * 10
        assert float(model.data(model.index(0, 2), Qt.ItemDataRole.DisplayRole)) == 30
        
        # Undo should restore A and C
        model.undo()
        assert float(model.data(model.index(0, 0), Qt.ItemDataRole.DisplayRole)) == 1
        assert float(model.data(model.index(0, 2), Qt.ItemDataRole.DisplayRole)) == 100


class TestUndoRedoClear:
    """Test undo/redo for clear operations."""
    
    def test_undo_clear(self):
        """Test undoing a clear operation."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1.0, 2.0, 3.0]))
        
        # Clear cells
        selection = [(0, 0), (1, 0)]
        model.clear_selection(selection)
        
        # Verify cells are cleared (NaN displayed as empty)
        assert model.data(model.index(0, 0), Qt.ItemDataRole.DisplayRole) in (None, "")
        assert model.data(model.index(1, 0), Qt.ItemDataRole.DisplayRole) in (None, "")
        
        # Undo
        model.undo()
        
        # Verify values restored
        assert float(model.data(model.index(0, 0), Qt.ItemDataRole.DisplayRole)) == 1.0
        assert float(model.data(model.index(1, 0), Qt.ItemDataRole.DisplayRole)) == 2.0
    
    def test_redo_clear(self):
        """Test redoing a clear operation."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1.0, 2.0, 3.0]))
        
        # Clear and undo
        selection = [(0, 0), (1, 0)]
        model.clear_selection(selection)
        model.undo()
        
        # Redo
        model.redo()
        
        # Verify cells are cleared again
        assert model.data(model.index(0, 0), Qt.ItemDataRole.DisplayRole) in (None, "")
        assert model.data(model.index(1, 0), Qt.ItemDataRole.DisplayRole) in (None, "")
    
    def test_clear_string_column(self):
        """Test clear/undo/redo on string column."""
        model = DataTableModel()
        model.add_data_column("Name", dtype=DataType.STRING, data=pd.Series(["Alice", "Bob", "Charlie"]))
        
        # Clear
        selection = [(1, 0)]
        model.clear_selection(selection)
        assert model.data(model.index(1, 0), Qt.ItemDataRole.DisplayRole) == ""
        
        # Undo
        model.undo()
        assert model.data(model.index(1, 0), Qt.ItemDataRole.DisplayRole) == "Bob"
        
        # Redo
        model.redo()
        assert model.data(model.index(1, 0), Qt.ItemDataRole.DisplayRole) == ""


class TestCommandHistory:
    """Test command history management."""
    
    def test_history_limit(self):
        """Test that history is limited to max_history."""
        # Create model with small history limit
        model = DataTableModel()
        model._command_manager.max_history = 5
        model.add_data_column("A", data=pd.Series([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))
        
        # Make 10 edits
        for i in range(10):
            idx = model.index(i, 0)
            model.setData(idx, i + 1, Qt.ItemDataRole.EditRole)
        
        # Should only be able to undo 5 times
        undo_count = 0
        while model.can_undo():
            model.undo()
            undo_count += 1
        
        assert undo_count == 5
    
    def test_clear_history(self):
        """Test clearing command history."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1, 2, 3]))
        
        # Make some edits
        idx = model.index(0, 0)
        model.setData(idx, 10, Qt.ItemDataRole.EditRole)
        model.setData(idx, 20, Qt.ItemDataRole.EditRole)
        
        # Clear history
        model.clear_undo_history()
        
        # Should not be able to undo
        assert not model.can_undo()
        assert not model.can_redo()
    
    def test_can_undo_can_redo(self):
        """Test can_undo() and can_redo() methods."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1, 2, 3]))
        
        # Initially nothing to undo/redo
        assert not model.can_undo()
        assert not model.can_redo()
        
        # After edit, can undo but not redo
        idx = model.index(0, 0)
        model.setData(idx, 10, Qt.ItemDataRole.EditRole)
        assert model.can_undo()
        assert not model.can_redo()
        
        # After undo, can redo but not undo (nothing left)
        model.undo()
        assert not model.can_undo()
        assert model.can_redo()
        
        # After redo, can undo but not redo
        model.redo()
        assert model.can_undo()
        assert not model.can_redo()
    
    def test_undo_description(self):
        """Test getting undo description."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1, 2, 3]))
        
        # Edit a cell
        idx = model.index(1, 2)  # Row 1, Col 2 (doesn't exist, but testing description)
        idx_valid = model.index(1, 0)
        model.setData(idx_valid, 99, Qt.ItemDataRole.EditRole)
        
        # Get description
        desc = model.get_undo_description()
        assert desc is not None
        assert "Edit Cell" in desc or "1" in desc  # Should mention cell edit
    
    def test_redo_description(self):
        """Test getting redo description."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1, 2, 3]))
        model.add_data_column("B", data=pd.Series([10, 20, 30]))
        
        # Paste and undo
        tsv = "100\t200"
        model.paste_from_tsv(tsv, start_row=0, start_col=0)
        model.undo()
        
        # Get redo description
        desc = model.get_redo_description()
        assert desc is not None
        assert "Paste" in desc or "cells" in desc


class TestUndoRedoWithCalculatedColumns:
    """Test undo/redo interactions with calculated columns."""
    
    def test_undo_triggers_recalculation(self):
        """Test that undo triggers recalculation of dependent columns."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([5.0, 10.0]))
        model.add_calculated_column("B", formula="{A} * 2")
        
        # Edit A
        idx = model.index(0, 0)
        model.setData(idx, 20.0, Qt.ItemDataRole.EditRole)
        
        # B should be recalculated
        idx_b = model.index(0, 1)
        assert float(model.data(idx_b, Qt.ItemDataRole.DisplayRole)) == 40.0
        
        # Undo
        model.undo()
        
        # B should be recalculated again
        assert float(model.data(idx_b, Qt.ItemDataRole.DisplayRole)) == 10.0
    
    def test_redo_triggers_recalculation(self):
        """Test that redo triggers recalculation."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([5.0, 10.0]))
        model.add_calculated_column("B", formula="{A} * 2")
        
        # Edit, undo, redo
        idx = model.index(0, 0)
        model.setData(idx, 20.0, Qt.ItemDataRole.EditRole)
        model.undo()
        model.redo()
        
        # B should be recalculated
        idx_b = model.index(0, 1)
        assert float(model.data(idx_b, Qt.ItemDataRole.DisplayRole)) == 40.0


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_undo_when_nothing_to_undo(self):
        """Test undo returns False when nothing to undo."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1, 2, 3]))
        
        assert not model.undo()
    
    def test_redo_when_nothing_to_redo(self):
        """Test redo returns False when nothing to redo."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1, 2, 3]))
        
        assert not model.redo()
    
    def test_undo_redo_with_empty_model(self):
        """Test undo/redo with empty model."""
        model = DataTableModel()
        
        assert not model.can_undo()
        assert not model.can_redo()
        assert not model.undo()
        assert not model.redo()
    
    def test_mixed_operations_undo_redo(self):
        """Test undo/redo with mixed edit, paste, clear operations."""
        model = DataTableModel()
        model.add_data_column("A", data=pd.Series([1, 2, 3]))
        model.add_data_column("B", data=pd.Series([10, 20, 30]))
        
        # 1. Edit a cell
        idx = model.index(0, 0)
        model.setData(idx, 100, Qt.ItemDataRole.EditRole)
        
        # 2. Paste
        tsv = "200\t300"
        model.paste_from_tsv(tsv, start_row=1, start_col=0)
        
        # 3. Clear
        model.clear_selection([(2, 0)])
        
        # Undo all 3 operations
        model.undo()  # Undo clear
        assert float(model.data(model.index(2, 0), Qt.ItemDataRole.DisplayRole)) == 3
        
        model.undo()  # Undo paste
        assert float(model.data(model.index(1, 0), Qt.ItemDataRole.DisplayRole)) == 2
        assert float(model.data(model.index(1, 1), Qt.ItemDataRole.DisplayRole)) == 20
        
        model.undo()  # Undo edit
        assert float(model.data(model.index(0, 0), Qt.ItemDataRole.DisplayRole)) == 1
        
        # Redo all 3
        model.redo()  # Redo edit
        assert float(model.data(model.index(0, 0), Qt.ItemDataRole.DisplayRole)) == 100
        
        model.redo()  # Redo paste
        assert float(model.data(model.index(1, 0), Qt.ItemDataRole.DisplayRole)) == 200
        
        model.redo()  # Redo clear
        assert model.data(model.index(2, 0), Qt.ItemDataRole.DisplayRole) in (None, "")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
