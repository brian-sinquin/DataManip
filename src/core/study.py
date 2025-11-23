"""
Base class for all study types.

A study is a container for related data objects and analysis results.
Examples: DataTable, Visualization, Statistics, Fitting, etc.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from .data_object import DataObject


class Study(ABC):
    """Abstract base class for all study types.
    
    A study contains:
    - Data objects (tables, arrays, images)
    - Analysis results
    - Configuration/settings
    
    Each study type (DataTable, Visualization, etc.) implements
    its specific logic while sharing a common interface.
    
    Attributes:
        name: Human-readable study name
        data_objects: Dictionary of DataObjects in this study
        metadata: Study-specific settings and configuration
    """
    
    def __init__(self, name: str):
        """Initialize study.
        
        Args:
            name: Study name
        """
        self.name = name
        self.data_objects: Dict[str, DataObject] = {}
        self.metadata: Dict[str, Any] = {}
    
    def add_data_object(self, data_object: DataObject):
        """Add data object to study.
        
        Args:
            data_object: DataObject to add
        """
        self.data_objects[data_object.name] = data_object
    
    def remove_data_object(self, name: str):
        """Remove data object from study.
        
        Args:
            name: DataObject name
        """
        if name in self.data_objects:
            del self.data_objects[name]
    
    def get_data_object(self, name: str) -> Optional[DataObject]:
        """Get data object by name.
        
        Args:
            name: DataObject name
            
        Returns:
            DataObject or None if not found
        """
        return self.data_objects.get(name)
    
    def list_data_objects(self) -> List[str]:
        """Get list of data object names.
        
        Returns:
            List of DataObject names
        """
        return list(self.data_objects.keys())
    
    @abstractmethod
    def get_type(self) -> str:
        """Get study type identifier.
        
        Returns:
            Study type string (e.g., "data_table", "visualization")
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Export study to dictionary format.
        
        Returns:
            Dictionary representation of study
        """
        return {
            "name": self.name,
            "type": self.get_type(),
            "data_objects": {
                name: obj.to_dict() for name, obj in self.data_objects.items()
            },
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Study:
        """Create study from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            Study instance
        """
        study = cls(name=data["name"])
        study.metadata = data.get("metadata", {})
        
        # Restore data objects
        for name, obj_data in data.get("data_objects", {}).items():
            data_object = DataObject.from_dict(
                name=obj_data["name"],
                data_dict=obj_data["data"],
                **obj_data.get("metadata", {})
            )
            study.add_data_object(data_object)
        
        return study
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', objects={len(self.data_objects)})"
