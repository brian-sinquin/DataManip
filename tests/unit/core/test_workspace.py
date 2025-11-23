"""
Unit tests for Workspace class.

Tests workspace operations, study management, and constants system.
"""

import unittest
from core.workspace import Workspace
from core.study import Study


class MockStudy(Study):
    """Mock study for testing."""
    
    def get_type(self) -> str:
        return "mock_study"


class TestWorkspaceCreation(unittest.TestCase):
    """Test workspace creation."""
    
    def test_create_workspace(self):
        """Test basic workspace creation."""
        workspace = Workspace("Test Workspace", "numerical")
        
        self.assertEqual(workspace.name, "Test Workspace")
        self.assertEqual(workspace.workspace_type, "numerical")
        self.assertEqual(len(workspace.studies), 0)
        self.assertEqual(len(workspace.constants), 0)
        self.assertEqual(len(workspace.metadata), 0)
    
    def test_workspace_repr(self):
        """Test workspace string representation."""
        workspace = Workspace("Physics Lab", "numerical")
        repr_str = repr(workspace)
        
        self.assertIn("Physics Lab", repr_str)
        self.assertIn("numerical", repr_str)
        self.assertIn("studies=0", repr_str)


class TestStudyManagement(unittest.TestCase):
    """Test study management operations."""
    
    def setUp(self):
        """Set up test workspace."""
        self.workspace = Workspace("Test", "numerical")
    
    def test_add_study(self):
        """Test adding study to workspace."""
        study = MockStudy("Study 1")
        self.workspace.add_study(study)
        
        self.assertEqual(len(self.workspace.studies), 1)
        self.assertIn("Study 1", self.workspace.studies)
        self.assertEqual(self.workspace.studies["Study 1"], study)
    
    def test_add_multiple_studies(self):
        """Test adding multiple studies."""
        study1 = MockStudy("Study 1")
        study2 = MockStudy("Study 2")
        study3 = MockStudy("Study 3")
        
        self.workspace.add_study(study1)
        self.workspace.add_study(study2)
        self.workspace.add_study(study3)
        
        self.assertEqual(len(self.workspace.studies), 3)
        self.assertIn("Study 1", self.workspace.studies)
        self.assertIn("Study 2", self.workspace.studies)
        self.assertIn("Study 3", self.workspace.studies)
    
    def test_get_study(self):
        """Test getting study by name."""
        study = MockStudy("Test Study")
        self.workspace.add_study(study)
        
        retrieved = self.workspace.get_study("Test Study")
        self.assertEqual(retrieved, study)
    
    def test_get_nonexistent_study(self):
        """Test getting nonexistent study returns None."""
        result = self.workspace.get_study("Nonexistent")
        self.assertIsNone(result)
    
    def test_remove_study(self):
        """Test removing study from workspace."""
        study = MockStudy("Study 1")
        self.workspace.add_study(study)
        
        self.assertEqual(len(self.workspace.studies), 1)
        
        self.workspace.remove_study("Study 1")
        self.assertEqual(len(self.workspace.studies), 0)
        self.assertNotIn("Study 1", self.workspace.studies)
    
    def test_remove_nonexistent_study(self):
        """Test removing nonexistent study (should not raise error)."""
        self.workspace.remove_study("Nonexistent")
        self.assertEqual(len(self.workspace.studies), 0)
    
    def test_list_studies(self):
        """Test listing study names."""
        study1 = MockStudy("Study 1")
        study2 = MockStudy("Study 2")
        
        self.workspace.add_study(study1)
        self.workspace.add_study(study2)
        
        studies = self.workspace.list_studies()
        self.assertEqual(len(studies), 2)
        self.assertIn("Study 1", studies)
        self.assertIn("Study 2", studies)
    
    def test_replace_study_same_name(self):
        """Test replacing study with same name."""
        study1 = MockStudy("Study")
        study2 = MockStudy("Study")
        
        self.workspace.add_study(study1)
        self.workspace.add_study(study2)
        
        # Should have replaced, not added
        self.assertEqual(len(self.workspace.studies), 1)
        self.assertEqual(self.workspace.get_study("Study"), study2)


class TestConstantsSystem(unittest.TestCase):
    """Test constants, calculated variables, and functions."""
    
    def setUp(self):
        """Set up test workspace."""
        self.workspace = Workspace("Test", "numerical")
    
    def test_add_numeric_constant(self):
        """Test adding numeric constant."""
        self.workspace.add_constant("g", 9.81, "m/s^2")
        
        info = self.workspace.get_constant_info("g")
        self.assertIsNotNone(info)
        self.assertEqual(info["type"], "constant")
        self.assertEqual(info["value"], 9.81)
        self.assertEqual(info["unit"], "m/s^2")
    
    def test_add_constant_without_unit(self):
        """Test adding constant without unit."""
        self.workspace.add_constant("pi", 3.14159)
        
        info = self.workspace.get_constant_info("pi")
        self.assertEqual(info["type"], "constant")
        self.assertEqual(info["value"], 3.14159)
        self.assertIsNone(info["unit"])
    
    def test_add_calculated_variable(self):
        """Test adding calculated variable."""
        self.workspace.add_calculated_variable("v", "sqrt(2*{g}*{h})", "m/s")
        
        info = self.workspace.get_constant_info("v")
        self.assertIsNotNone(info)
        self.assertEqual(info["type"], "calculated")
        self.assertEqual(info["formula"], "sqrt(2*{g}*{h})")
        self.assertEqual(info["unit"], "m/s")
        self.assertIsNone(info["value"])  # Not calculated yet
    
    def test_add_function(self):
        """Test adding custom function."""
        self.workspace.add_function("distance", "{x}^2 + {y}^2", ["x", "y"], "m")
        
        info = self.workspace.get_constant_info("distance")
        self.assertIsNotNone(info)
        self.assertEqual(info["type"], "function")
        self.assertEqual(info["formula"], "{x}^2 + {y}^2")
        self.assertEqual(info["parameters"], ["x", "y"])
        self.assertEqual(info["unit"], "m")
    
    def test_add_function_without_unit(self):
        """Test adding function without unit."""
        self.workspace.add_function("sum", "{a} + {b}", ["a", "b"])
        
        info = self.workspace.get_constant_info("sum")
        self.assertEqual(info["type"], "function")
        self.assertIsNone(info["unit"])
    
    def test_remove_constant(self):
        """Test removing constant."""
        self.workspace.add_constant("temp", 273.15, "K")
        self.assertEqual(len(self.workspace.constants), 1)
        
        self.workspace.remove_constant("temp")
        self.assertEqual(len(self.workspace.constants), 0)
        self.assertIsNone(self.workspace.get_constant_info("temp"))
    
    def test_remove_nonexistent_constant(self):
        """Test removing nonexistent constant (should not raise error)."""
        self.workspace.remove_constant("nonexistent")
        self.assertEqual(len(self.workspace.constants), 0)
    
    def test_get_nonexistent_constant(self):
        """Test getting nonexistent constant returns None."""
        info = self.workspace.get_constant_info("nonexistent")
        self.assertIsNone(info)
    
    def test_replace_constant(self):
        """Test replacing constant with same name."""
        self.workspace.add_constant("g", 9.8, "m/s^2")
        self.workspace.add_constant("g", 9.81, "m/s^2")
        
        self.assertEqual(len(self.workspace.constants), 1)
        info = self.workspace.get_constant_info("g")
        self.assertEqual(info["value"], 9.81)
    
    def test_multiple_constants(self):
        """Test adding multiple constants of different types."""
        self.workspace.add_constant("g", 9.81, "m/s^2")
        self.workspace.add_constant("pi", 3.14159)
        self.workspace.add_calculated_variable("v", "sqrt(2*{g}*{h})", "m/s")
        self.workspace.add_function("distance", "{x}^2 + {y}^2", ["x", "y"])
        
        self.assertEqual(len(self.workspace.constants), 4)
        self.assertEqual(self.workspace.get_constant_info("g")["type"], "constant")
        self.assertEqual(self.workspace.get_constant_info("pi")["type"], "constant")
        self.assertEqual(self.workspace.get_constant_info("v")["type"], "calculated")
        self.assertEqual(self.workspace.get_constant_info("distance")["type"], "function")


class TestWorkspaceSerialization(unittest.TestCase):
    """Test workspace serialization."""
    
    def test_to_dict_empty(self):
        """Test serializing empty workspace."""
        workspace = Workspace("Test", "numerical")
        data = workspace.to_dict()
        
        self.assertEqual(data["name"], "Test")
        self.assertEqual(data["workspace_type"], "numerical")
        self.assertEqual(len(data["studies"]), 0)
        self.assertEqual(len(data["constants"]), 0)
        self.assertEqual(len(data["metadata"]), 0)
    
    def test_to_dict_with_constants(self):
        """Test serializing workspace with constants."""
        workspace = Workspace("Test", "numerical")
        workspace.add_constant("g", 9.81, "m/s^2")
        workspace.add_calculated_variable("v", "sqrt(2*{g}*{h})", "m/s")
        
        data = workspace.to_dict()
        
        self.assertEqual(len(data["constants"]), 2)
        self.assertIn("g", data["constants"])
        self.assertIn("v", data["constants"])
    
    def test_to_dict_with_metadata(self):
        """Test serializing workspace with metadata."""
        workspace = Workspace("Test", "numerical")
        workspace.metadata["author"] = "Test User"
        workspace.metadata["created"] = "2025-11-23"
        
        data = workspace.to_dict()
        
        self.assertEqual(data["metadata"]["author"], "Test User")
        self.assertEqual(data["metadata"]["created"], "2025-11-23")
    
    def test_from_dict(self):
        """Test deserializing workspace."""
        data = {
            "name": "Test Workspace",
            "workspace_type": "numerical",
            "studies": {},
            "constants": {
                "g": {"type": "constant", "value": 9.81, "unit": "m/s^2"}
            },
            "metadata": {"author": "Test User"}
        }
        
        workspace = Workspace.from_dict(data)
        
        self.assertEqual(workspace.name, "Test Workspace")
        self.assertEqual(workspace.workspace_type, "numerical")
        self.assertEqual(len(workspace.constants), 1)
        self.assertEqual(workspace.metadata["author"], "Test User")
    
    def test_from_dict_minimal(self):
        """Test deserializing minimal workspace data."""
        data = {
            "name": "Minimal",
            "workspace_type": "numerical"
        }
        
        workspace = Workspace.from_dict(data)
        
        self.assertEqual(workspace.name, "Minimal")
        self.assertEqual(workspace.workspace_type, "numerical")
        self.assertEqual(len(workspace.constants), 0)
        self.assertEqual(len(workspace.metadata), 0)
    
    def test_roundtrip_serialization(self):
        """Test serialize then deserialize."""
        original = Workspace("Test", "numerical")
        original.add_constant("g", 9.81, "m/s^2")
        original.add_constant("pi", 3.14159)
        original.metadata["version"] = "0.2.0"
        
        data = original.to_dict()
        restored = Workspace.from_dict(data)
        
        self.assertEqual(restored.name, original.name)
        self.assertEqual(restored.workspace_type, original.workspace_type)
        self.assertEqual(len(restored.constants), len(original.constants))
        self.assertEqual(restored.metadata["version"], original.metadata["version"])


class TestLegacyVariablesCompatibility(unittest.TestCase):
    """Test backward compatibility with legacy variables system."""
    

if __name__ == "__main__":
    unittest.main()
