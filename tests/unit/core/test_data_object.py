"""Unit tests for core DataObject."""

import pytest
import pandas as pd
import numpy as np
from core.data_object import DataObject


class TestDataObjectCreation:
    """Test DataObject creation methods."""
    
    def test_from_dict(self):
        """Test creating DataObject from dictionary."""
        obj = DataObject.from_dict(
            "test",
            {"x": [1, 2, 3], "y": [4, 5, 6]},
            unit="m"
        )
        
        assert obj.name == "test"
        assert obj.shape == (3, 2)
        assert obj.columns == ["x", "y"]
        assert obj.metadata["unit"] == "m"
    
    def test_from_array_1d(self):
        """Test creating DataObject from 1D array."""
        arr = np.array([1, 2, 3, 4])
        obj = DataObject.from_array("test", arr)
        
        assert obj.shape == (4, 1)
        assert "values" in obj.columns
    
    def test_from_array_2d(self):
        """Test creating DataObject from 2D array."""
        arr = np.array([[1, 2], [3, 4], [5, 6]])
        obj = DataObject.from_array("test", arr)
        
        assert obj.shape == (3, 2)
    
    def test_empty(self):
        """Test creating empty DataObject."""
        obj = DataObject.empty("test", rows=10, columns=["a", "b", "c"])
        
        assert obj.shape == (10, 3)
        assert obj.columns == ["a", "b", "c"]


class TestDataObjectOperations:
    """Test DataObject operations."""
    
    def test_get_set_column(self):
        """Test getting and setting columns."""
        obj = DataObject.from_dict("test", {"x": [1, 2, 3]})
        
        # Get column
        col = obj.get_column("x")
        assert len(col) == 3
        assert col.tolist() == [1, 2, 3]
        
        # Set column
        obj.set_column("x", [10, 20, 30])
        assert obj["x"].tolist() == [10, 20, 30]
    
    def test_add_remove_column(self):
        """Test adding and removing columns."""
        obj = DataObject.empty("test", rows=5)
        
        # Add column
        obj.add_column("a", [1, 2, 3, 4, 5])
        assert "a" in obj.columns
        assert len(obj["a"]) == 5
        
        # Remove column
        obj.remove_column("a")
        assert "a" not in obj.columns
    
    def test_copy(self):
        """Test copying DataObject."""
        obj1 = DataObject.from_dict("test", {"x": [1, 2, 3]})
        obj2 = obj1.copy()
        
        # Modify copy
        obj2.set_column("x", [10, 20, 30])
        
        # Original unchanged
        assert obj1["x"].tolist() == [1, 2, 3]
        assert obj2["x"].tolist() == [10, 20, 30]


class TestDataObjectSerialization:
    """Test DataObject serialization."""
    
    def test_to_dict(self):
        """Test exporting to dictionary."""
        obj = DataObject.from_dict(
            "test",
            {"x": [1, 2, 3], "y": [4, 5, 6]},
            unit="m"
        )
        
        data = obj.to_dict()
        
        assert data["name"] == "test"
        assert "x" in data["data"]
        assert "y" in data["data"]
        assert data["metadata"]["unit"] == "m"
