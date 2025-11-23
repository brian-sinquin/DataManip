"""
Universal data container for all data types.

DataObject wraps pandas DataFrame as the universal representation
for numerical data, images, and other data types.
"""

from __future__ import annotations
from typing import Optional, Any, Dict
from dataclasses import dataclass, field
import pandas as pd
import numpy as np


@dataclass
class DataObject:
    """Universal data container.
    
    All data in DataManip is represented as a DataObject wrapping a
    pandas DataFrame. This provides a consistent API for numerical
    tables, images (as 2D/3D arrays), and other data types.
    
    Attributes:
        name: Human-readable name
        data: Pandas DataFrame containing the actual data
        metadata: Additional information (units, uncertainty, etc.)
    """
    
    name: str
    data: pd.DataFrame
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate data object after initialization."""
        if not isinstance(self.data, pd.DataFrame):
            raise TypeError("data must be a pandas DataFrame")
    
    @classmethod
    def from_dict(cls, name: str, data_dict: Dict[str, Any], **metadata) -> DataObject:
        """Create DataObject from dictionary.
        
        Args:
            name: Object name
            data_dict: Dictionary mapping column names to values
            **metadata: Additional metadata
            
        Returns:
            New DataObject instance
        """
        df = pd.DataFrame(data_dict)
        return cls(name=name, data=df, metadata=metadata)
    
    @classmethod
    def from_array(cls, name: str, array: np.ndarray, **metadata) -> DataObject:
        """Create DataObject from numpy array.
        
        Args:
            name: Object name
            array: Numpy array (1D, 2D, or 3D)
            **metadata: Additional metadata
            
        Returns:
            New DataObject instance
        """
        if array.ndim == 1:
            # 1D array -> single column
            df = pd.DataFrame({"values": array})
        elif array.ndim == 2:
            # 2D array -> multiple columns or image
            df = pd.DataFrame(array)
        elif array.ndim == 3:
            # 3D array -> store as single column of 2D arrays (for images)
            df = pd.DataFrame({"frames": [array[i] for i in range(array.shape[0])]})
        else:
            raise ValueError(f"Arrays with {array.ndim} dimensions not supported")
        
        return cls(name=name, data=df, metadata=metadata)
    
    @classmethod
    def empty(cls, name: str, rows: int = 0, columns: Optional[list[str]] = None) -> DataObject:
        """Create empty DataObject.
        
        Args:
            name: Object name
            rows: Number of rows
            columns: Column names (default: empty)
            
        Returns:
            New empty DataObject
        """
        if columns:
            df = pd.DataFrame({col: [None] * rows for col in columns})
        else:
            df = pd.DataFrame(index=range(rows))
        
        return cls(name=name, data=df)
    
    @property
    def shape(self) -> tuple[int, int]:
        """Get shape of data (rows, columns)."""
        return self.data.shape
    
    @property
    def columns(self) -> list[str]:
        """Get list of column names."""
        return self.data.columns.tolist()
    
    def __getitem__(self, key: str) -> pd.Series:
        """Get column by name."""
        return self.data[key]
    
    def __setitem__(self, key: str, value: Any):
        """Set column data."""
        self.data[key] = value
    
    def get_column(self, name: str) -> pd.Series:
        """Get column data.
        
        Args:
            name: Column name
            
        Returns:
            Pandas Series
        """
        return self.data[name].copy()
    
    def set_column(self, name: str, data: pd.Series | np.ndarray | list):
        """Set column data.
        
        Args:
            name: Column name
            data: Column values
        """
        self.data[name] = data
    
    def add_column(self, name: str, data: Optional[pd.Series | np.ndarray | list] = None):
        """Add new column.
        
        Args:
            name: Column name
            data: Optional initial data (default: None)
        """
        if data is None:
            self.data[name] = None
        else:
            self.data[name] = data
    
    def remove_column(self, name: str):
        """Remove column.
        
        Args:
            name: Column name
        """
        self.data.drop(columns=[name], inplace=True)
    
    def copy(self) -> DataObject:
        """Create deep copy of this DataObject."""
        return DataObject(
            name=self.name,
            data=self.data.copy(),
            metadata=self.metadata.copy()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary format."""
        return {
            "name": self.name,
            "data": self.data.to_dict(orient="list"),
            "metadata": self.metadata
        }
    
    def __repr__(self) -> str:
        return f"DataObject(name='{self.name}', shape={self.shape})"
