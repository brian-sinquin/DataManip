"""
Pure data storage using Pandas/NumPy backend.

This module provides Qt-independent data storage and manipulation.
It can be used in CLI tools, web APIs, or any non-GUI context.
"""

from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np

from widgets.data_table.column_metadata import ColumnMetadata, ColumnType, DataType
from utils.exceptions import ColumnExistsError, ColumnNotFoundError


class DataStore:
    """Pure data storage layer using Pandas Series.
    
    Manages columnar data storage, metadata, and basic operations
    without any Qt dependencies.
    
    Attributes:
        _columns: Dictionary mapping column names to Pandas Series
        _metadata: Dictionary mapping column names to ColumnMetadata
        _column_order: Ordered list of column names
        _row_count: Current number of rows
    """
    
    def __init__(self):
        """Initialize empty data store."""
        self._columns: Dict[str, pd.Series] = {}
        self._metadata: Dict[str, ColumnMetadata] = {}
        self._column_order: List[str] = []
        self._row_count: int = 0
    
    # ========================================================================
    # Basic Properties
    # ========================================================================
    
    @property
    def row_count(self) -> int:
        """Get current row count."""
        return self._row_count
    
    @property
    def column_count(self) -> int:
        """Get current column count."""
        return len(self._column_order)
    
    @property
    def column_names(self) -> List[str]:
        """Get ordered list of column names."""
        return self._column_order.copy()
    
    def has_column(self, name: str) -> bool:
        """Check if column exists."""
        return name in self._columns
    
    # ========================================================================
    # Column Management
    # ========================================================================
    
    def add_column(self, metadata: ColumnMetadata, data: Optional[pd.Series] = None) -> None:
        """Add a new column to the store.
        
        Args:
            metadata: Column metadata
            data: Optional initial data (will be resized to match row count)
            
        Raises:
            ColumnExistsError: If column name already exists
        """
        if metadata.name in self._columns:
            raise ColumnExistsError(f"Column '{metadata.name}' already exists")
        
        # Create empty or initialize with data
        if data is None:
            series = pd.Series([None] * self._row_count, dtype=self._get_pandas_dtype(metadata.dtype))
        else:
            series = data.copy()
            # Resize to match current row count
            if len(series) < self._row_count:
                series = series.reindex(range(self._row_count))
            elif len(series) > self._row_count:
                self._row_count = len(series)
                # Extend existing columns
                for col_name in self._column_order:
                    if len(self._columns[col_name]) < self._row_count:
                        self._columns[col_name] = self._columns[col_name].reindex(range(self._row_count))
        
        self._columns[metadata.name] = series
        self._metadata[metadata.name] = metadata
        self._column_order.append(metadata.name)
    
    def remove_column(self, name: str) -> None:
        """Remove a column from the store.
        
        Args:
            name: Column name
            
        Raises:
            ColumnNotFoundError: If column doesn't exist
        """
        if name not in self._columns:
            raise ColumnNotFoundError(f"Column '{name}' not found")
        
        del self._columns[name]
        del self._metadata[name]
        self._column_order.remove(name)
    
    def get_column(self, name: str) -> pd.Series:
        """Get column data.
        
        Args:
            name: Column name
            
        Returns:
            Pandas Series with column data
            
        Raises:
            ColumnNotFoundError: If column doesn't exist
        """
        if name not in self._columns:
            raise ColumnNotFoundError(f"Column '{name}' not found")
        return self._columns[name].copy()
    
    def set_column(self, name: str, data: pd.Series) -> None:
        """Set column data.
        
        Args:
            name: Column name
            data: New column data
            
        Raises:
            ColumnNotFoundError: If column doesn't exist
        """
        if name not in self._columns:
            raise ColumnNotFoundError(f"Column '{name}' not found")
        
        # Resize if needed
        if len(data) != self._row_count:
            data = data.reindex(range(self._row_count))
        
        self._columns[name] = data
    
    def get_metadata(self, name: str) -> ColumnMetadata:
        """Get column metadata.
        
        Args:
            name: Column name
            
        Returns:
            Column metadata
            
        Raises:
            ColumnNotFoundError: If column doesn't exist
        """
        if name not in self._metadata:
            raise ColumnNotFoundError(f"Column '{name}' not found")
        return self._metadata[name]
    
    def update_metadata(self, name: str, metadata: ColumnMetadata) -> None:
        """Update column metadata.
        
        Args:
            name: Column name
            metadata: New metadata
            
        Raises:
            ColumnNotFoundError: If column doesn't exist
        """
        if name not in self._metadata:
            raise ColumnNotFoundError(f"Column '{name}' not found")
        self._metadata[name] = metadata
    
    # ========================================================================
    # Cell Operations
    # ========================================================================
    
    def get_cell(self, row: int, column_name: str) -> Any:
        """Get value of a specific cell.
        
        Args:
            row: Row index (0-based)
            column_name: Column name
            
        Returns:
            Cell value
            
        Raises:
            ColumnNotFoundError: If column doesn't exist
            IndexError: If row index is out of bounds
        """
        if column_name not in self._columns:
            raise ColumnNotFoundError(f"Column '{column_name}' not found")
        if row < 0 or row >= self._row_count:
            raise IndexError(f"Row {row} out of bounds [0, {self._row_count})")
        
        return self._columns[column_name].iloc[row]
    
    def set_cell(self, row: int, column_name: str, value: Any) -> None:
        """Set value of a specific cell.
        
        Args:
            row: Row index (0-based)
            column_name: Column name
            value: New value
            
        Raises:
            ColumnNotFoundError: If column doesn't exist
            IndexError: If row index is out of bounds
        """
        if column_name not in self._columns:
            raise ColumnNotFoundError(f"Column '{column_name}' not found")
        if row < 0 or row >= self._row_count:
            raise IndexError(f"Row {row} out of bounds [0, {self._row_count})")
        
        self._columns[column_name].iloc[row] = value
    
    # ========================================================================
    # Row Operations
    # ========================================================================
    
    def insert_rows(self, row: int, count: int) -> None:
        """Insert empty rows at specified position.
        
        Args:
            row: Starting row index
            count: Number of rows to insert
        """
        if row < 0 or row > self._row_count:
            raise IndexError(f"Row {row} out of bounds [0, {self._row_count}]")
        
        for col_name in self._column_order:
            series = self._columns[col_name]
            # Create new index
            new_index = list(range(row)) + list(range(row, row + count)) + list(range(row, self._row_count))
            # Create new values with NaN for inserted rows
            new_values = list(series.iloc[:row]) + [None] * count + list(series.iloc[row:])
            self._columns[col_name] = pd.Series(new_values, dtype=series.dtype)
        
        self._row_count += count
    
    def remove_rows(self, row: int, count: int) -> None:
        """Remove rows at specified position.
        
        Args:
            row: Starting row index
            count: Number of rows to remove
        """
        if row < 0 or row >= self._row_count:
            raise IndexError(f"Row {row} out of bounds [0, {self._row_count})")
        if row + count > self._row_count:
            count = self._row_count - row
        
        for col_name in self._column_order:
            series = self._columns[col_name]
            # Remove rows
            mask = pd.Series([True] * self._row_count)
            mask.iloc[row:row+count] = False
            self._columns[col_name] = series[mask].reset_index(drop=True)
        
        self._row_count -= count
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def _get_pandas_dtype(self, dtype: DataType) -> str:
        """Convert DataType enum to pandas dtype string.
        
        Args:
            dtype: DataType enum value
            
        Returns:
            Pandas dtype string
        """
        return dtype.value
    
    def clear(self) -> None:
        """Clear all data and metadata."""
        self._columns.clear()
        self._metadata.clear()
        self._column_order.clear()
        self._row_count = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Export data store to dictionary format.
        
        Returns:
            Dictionary with columns, metadata, and row count
        """
        return {
            'columns': {name: self._columns[name].tolist() for name in self._column_order},
            'metadata': {name: self._metadata[name].__dict__ for name in self._column_order},
            'column_order': self._column_order.copy(),
            'row_count': self._row_count
        }
