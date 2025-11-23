"""
Unit tests for DataTableStudy class - Basic API Tests.

Tests core study operations that match the actual implementation.
"""

import unittest
import numpy as np
from studies.data_table_study import DataTableStudy, ColumnType


class TestDataTableStudyCreation(unittest.TestCase):
    """Test study creation."""
    
    def test_create_study(self):
        """Test basic study creation."""
        study = DataTableStudy("Test Study")
        
        self.assertEqual(study.name, "Test Study")
        self.assertEqual(len(study.table.columns), 0)
        self.assertEqual(len(study.table.data), 0)
    
    def test_get_type(self):
        """Test study type."""
        study = DataTableStudy("Test")
        self.assertEqual(study.get_type(), "data_table")


class TestColumnManagement(unittest.TestCase):
    """Test column operations."""
    
    def setUp(self):
        """Set up test study."""
        self.study = DataTableStudy("Test")
    
    def test_add_data_column(self):
        """Test adding data column."""
        self.study.add_column("x", unit="m")
        
        self.assertIn("x", self.study.table.columns)
        self.assertEqual(self.study.get_column_type("x"), ColumnType.DATA)
        self.assertEqual(self.study.get_column_unit("x"), "m")
    
    def test_add_data_column_without_unit(self):
        """Test adding column without unit."""
        self.study.add_column("count")
        
        self.assertIn("count", self.study.table.columns)
        self.assertIsNone(self.study.get_column_unit("count"))
    
    def test_add_calculated_column(self):
        """Test adding calculated column."""
        self.study.add_column("x", unit="m")
        self.study.add_column("y", ColumnType.CALCULATED, formula="{x} * 2", unit="m")
        
        self.assertIn("y", self.study.table.columns)
        self.assertEqual(self.study.get_column_type("y"), ColumnType.CALCULATED)
        self.assertEqual(self.study.get_column_formula("y"), "{x} * 2")
    
    def test_add_multiple_columns(self):
        """Test adding multiple columns."""
        self.study.add_column("a")
        self.study.add_column("b")
        self.study.add_column("c")
        
        self.assertEqual(len(self.study.table.columns), 3)
        self.assertIn("a", self.study.table.columns)
        self.assertIn("b", self.study.table.columns)
        self.assertIn("c", self.study.table.columns)
    
    def test_remove_column(self):
        """Test removing column."""
        self.study.add_column("x")
        self.assertEqual(len(self.study.table.columns), 1)
        
        self.study.remove_column("x")
        self.assertEqual(len(self.study.table.columns), 0)
    
    def test_remove_calculated_column_clears_metadata(self):
        """Test removing calculated column clears metadata."""
        self.study.add_column("x")
        self.study.add_column("y", ColumnType.CALCULATED, formula="{x} * 2")
        
        self.study.remove_column("y")
        self.assertNotIn("y", self.study.column_metadata)


class TestRowManagement(unittest.TestCase):
    """Test row operations."""
    
    def setUp(self):
        """Set up test study."""
        self.study = DataTableStudy("Test")
        self.study.add_column("x")
        self.study.add_column("y")
    
    def test_add_rows(self):
        """Test adding rows."""
        self.study.add_rows(5)
        self.assertEqual(len(self.study.table.data), 5)
    
    def test_remove_multiple_rows(self):
        """Test removing multiple rows."""
        self.study.add_rows(10)
        self.study.remove_rows([0, 2, 4])
        
        self.assertEqual(len(self.study.table.data), 7)


class TestDataManipulation(unittest.TestCase):
    """Test data operations."""
    
    def setUp(self):
        """Set up test study."""
        self.study = DataTableStudy("Test")
        self.study.add_column("x")
        self.study.add_column("y")
        self.study.add_rows(5)
    
    def test_get_column_data(self):
        """Test getting column data."""
        self.study.table.data["x"] = [10, 20, 30, 40, 50]
        result = self.study.table["x"]
        
        expected = np.array([10, 20, 30, 40, 50])
        np.testing.assert_array_equal(result, expected)
    
    def test_set_column_data(self):
        """Test setting column data."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        self.study.table.data["x"] = data
        
        result = self.study.table["x"]
        np.testing.assert_array_equal(result, data)


class TestVariables(unittest.TestCase):
    """Test variable management."""
    
    def setUp(self):
        """Set up test study with workspace."""
        from core.workspace import Workspace
        self.workspace = Workspace("Test", "numerical")
        self.study = DataTableStudy("Test", workspace=self.workspace)
    
    def test_add_constant_to_workspace(self):
        """Test adding constant at workspace level."""
        self.workspace.add_constant("g", 9.81, "m/s^2")
        
        self.assertIn("g", self.workspace.constants)
        self.assertEqual(self.workspace.constants["g"]["value"], 9.81)
        self.assertEqual(self.workspace.constants["g"]["unit"], "m/s^2")
    
    def test_add_constant_without_unit(self):
        """Test adding constant without unit."""
        self.workspace.add_constant("pi", 3.14159, None)
        
        self.assertIn("pi", self.workspace.constants)
        self.assertEqual(self.workspace.constants["pi"]["value"], 3.14159)
        self.assertIsNone(self.workspace.constants["pi"]["unit"])
    
    def test_remove_constant(self):
        """Test removing constant from workspace."""
        self.workspace.add_constant("temp", 273.15, "K")
        del self.workspace.constants["temp"]
        
        self.assertNotIn("temp", self.workspace.constants)


class TestSerialization(unittest.TestCase):
    """Test study serialization."""
    
    def test_to_dict_empty(self):
        """Test serializing empty study."""
        study = DataTableStudy("Test")
        data = study.to_dict()
        
        self.assertEqual(data["name"], "Test")
        self.assertEqual(data["type"], "data_table")
    
    def test_to_dict_constants_at_workspace_level(self):
        """Test that constants are not serialized in study (workspace-level only)."""
        from core.workspace import Workspace
        workspace = Workspace("Test", "numerical")
        workspace.add_constant("g", 9.81, "m/s^2")
        
        study = DataTableStudy("Test", workspace=workspace)
        data = study.to_dict()
        
        # Constants should NOT be in study serialization
        self.assertNotIn("variables", data)


class TestColumnTypes(unittest.TestCase):
    """Test column type handling."""
    
    def test_data_column_type(self):
        """Test DATA column type."""
        study = DataTableStudy("Test")
        study.add_column("x", ColumnType.DATA)
        
        self.assertEqual(study.get_column_type("x"), ColumnType.DATA)
    
    def test_calculated_column_type(self):
        """Test CALCULATED column type."""
        study = DataTableStudy("Test")
        study.add_column("x")
        study.add_column("y", ColumnType.CALCULATED, formula="{x} * 2")
        
        self.assertEqual(study.get_column_type("y"), ColumnType.CALCULATED)
        self.assertEqual(study.get_column_formula("y"), "{x} * 2")


if __name__ == "__main__":
    unittest.main()
