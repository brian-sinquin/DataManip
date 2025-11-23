"""
Unit tests for column renaming functionality.
"""

import pytest
from pathlib import Path
import sys

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.workspace import Workspace
from studies.data_table_study import DataTableStudy, ColumnType


class TestRenameColumn:
    """Test column renaming in DataTableStudy."""
    
    def setup_method(self):
        """Setup test workspace and data."""
        self.workspace = Workspace("Test", "numerical")
        self.study = DataTableStudy("Test Table", workspace=self.workspace)
        
        # Add test columns
        self.study.add_column("x")
        self.study.add_column("y", formula="{x} * 2")
        self.study.add_column("z", formula="{y} + 1")
        self.study.add_rows(5)
    
    def test_rename_simple_column(self):
        """Test renaming a simple data column."""
        self.study.rename_column("x", "x_new")
        
        assert "x_new" in self.study.table.columns
        assert "x" not in self.study.table.columns
        assert "x_new" in self.study.column_metadata
        assert "x" not in self.study.column_metadata
    
    def test_rename_updates_dependent_formulas(self):
        """Test that renaming updates formulas that reference it."""
        self.study.rename_column("x", "x_renamed")
        
        # Check that y's formula was updated
        y_meta = self.study.column_metadata["y"]
        assert "{x_renamed}" in y_meta["formula"]
        assert "{x}" not in y_meta["formula"]
    
    def test_rename_cascades_through_dependencies(self):
        """Test that renaming cascades through multiple dependencies."""
        self.study.rename_column("y", "y_new")
        
        # Check that z's formula was updated
        z_meta = self.study.column_metadata["z"]
        assert "{y_new}" in z_meta["formula"]
        assert "{y}" not in z_meta["formula"]
        
        # Original formula in y should still reference x
        y_meta = self.study.column_metadata["y_new"]
        assert "{x}" in y_meta["formula"]
