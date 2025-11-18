"""
Test that propagated uncertainty columns are read-only.

This ensures that automatically calculated uncertainty columns cannot be
manually edited, while manually-created uncertainty columns remain editable.
"""

import pytest
import pandas as pd
from PySide6.QtCore import Qt, QModelIndex

from widgets.data_table.model import DataTableModel
from widgets.data_table.column_metadata import ColumnType


class TestPropagatedUncertaintyReadOnly:
    """Test that propagated uncertainty columns are read-only."""
    
    def test_propagated_uncertainty_is_read_only(self):
        """Propagated uncertainty columns should not be editable."""
        model = DataTableModel()
        
        # Create data column with uncertainty
        model.add_data_column("x", data=pd.Series([1.0, 2.0, 3.0]))
        model.add_data_column("x_u", data=pd.Series([0.1, 0.2, 0.3]))
        
        # Create calculated column with uncertainty propagation
        model.add_calculated_column(
            "y",
            formula="{x}**2",
            propagate_uncertainty=True
        )
        
        # y_u should exist
        assert "y_u" in model.get_column_names()
        
        # y_u metadata should indicate it's not editable
        y_u_metadata = model._metadata["y_u"]
        assert y_u_metadata.column_type == ColumnType.UNCERTAINTY
        assert y_u_metadata.uncertainty_reference == "y"
        assert y_u_metadata.editable is False
        
        # Try to edit y_u through setData - should fail
        y_u_col_idx = model.get_column_names().index("y_u")
        index = model.index(0, y_u_col_idx)
        result = model.setData(index, 999.0, Qt.ItemDataRole.EditRole)
        
        # Should return False (edit rejected)
        assert result is False
        
        # Value should remain unchanged
        assert model.get_column_data("y_u").iloc[0] == pytest.approx(0.2, abs=0.01)
    
    def test_manual_uncertainty_column_is_editable(self):
        """Manually-created uncertainty columns (DATA type) should be editable."""
        model = DataTableModel()
        
        # Create data column
        model.add_data_column("x", data=pd.Series([1.0, 2.0, 3.0]))
        
        # Create manual uncertainty column (as DATA type)
        model.add_data_column("x_u", data=pd.Series([0.1, 0.2, 0.3]))
        
        # x_u should be editable (it's a DATA column)
        x_u_metadata = model._metadata["x_u"]
        assert x_u_metadata.column_type == ColumnType.DATA
        assert x_u_metadata.editable is True
        
        # Try to edit x_u - should succeed
        x_u_col_idx = model.get_column_names().index("x_u")
        index = model.index(0, x_u_col_idx)
        result = model.setData(index, 0.5, Qt.ItemDataRole.EditRole)
        
        # Should return True (edit accepted)
        assert result is True
        
        # Value should be changed
        assert model.get_column_data("x_u").iloc[0] == 0.5
    
    def test_calculated_column_is_read_only(self):
        """Calculated columns should not be editable."""
        model = DataTableModel()
        
        # Create data column
        model.add_data_column("x", data=pd.Series([1.0, 2.0, 3.0]))
        
        # Create calculated column
        model.add_calculated_column("y", formula="{x}**2")
        
        # y should not be editable
        y_metadata = model._metadata["y"]
        assert y_metadata.column_type == ColumnType.CALCULATED
        assert y_metadata.editable is False
        
        # Try to edit y - should fail
        y_col_idx = model.get_column_names().index("y")
        index = model.index(0, y_col_idx)
        result = model.setData(index, 999.0, Qt.ItemDataRole.EditRole)
        
        # Should return False (edit rejected)
        assert result is False
        
        # Value should remain unchanged
        assert model.get_column_data("y").iloc[0] == 1.0
    
    def test_data_column_is_editable(self):
        """DATA columns should be editable."""
        model = DataTableModel()
        
        # Create data column
        model.add_data_column("x", data=pd.Series([1.0, 2.0, 3.0]))
        
        # x should be editable
        x_metadata = model._metadata["x"]
        assert x_metadata.column_type == ColumnType.DATA
        assert x_metadata.editable is True
        
        # Try to edit x - should succeed
        x_col_idx = model.get_column_names().index("x")
        index = model.index(0, x_col_idx)
        result = model.setData(index, 5.0, Qt.ItemDataRole.EditRole)
        
        # Should return True (edit accepted)
        assert result is True
        
        # Value should be changed
        assert model.get_column_data("x").iloc[0] == 5.0
    
    def test_flags_reflect_editability(self):
        """Qt flags should correctly indicate which columns are editable."""
        model = DataTableModel()
        
        # Create columns
        model.add_data_column("x", data=pd.Series([1.0, 2.0]))
        model.add_data_column("x_u", data=pd.Series([0.1, 0.2]))
        model.add_calculated_column("y", formula="{x}**2", propagate_uncertainty=True)
        
        # Get column indices
        x_idx = model.get_column_names().index("x")
        x_u_idx = model.get_column_names().index("x_u")
        y_idx = model.get_column_names().index("y")
        y_u_idx = model.get_column_names().index("y_u")
        
        # Check flags for first row
        x_flags = model.flags(model.index(0, x_idx))
        x_u_flags = model.flags(model.index(0, x_u_idx))
        y_flags = model.flags(model.index(0, y_idx))
        y_u_flags = model.flags(model.index(0, y_u_idx))
        
        # DATA column (x) should be editable
        assert x_flags & Qt.ItemFlag.ItemIsEditable
        
        # Manual uncertainty column (x_u) should be editable
        assert x_u_flags & Qt.ItemFlag.ItemIsEditable
        
        # Calculated column (y) should NOT be editable
        assert not (y_flags & Qt.ItemFlag.ItemIsEditable)
        
        # Propagated uncertainty column (y_u) should NOT be editable
        assert not (y_u_flags & Qt.ItemFlag.ItemIsEditable)
