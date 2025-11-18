"""
Column metadata registry and ordering management.

This module provides Qt-independent column metadata management with
ordering, validation, and efficient lookups.
"""

from typing import List, Optional, Dict, Set
from widgets.data_table.column_metadata import ColumnMetadata, ColumnType, DataType
from utils.exceptions import ColumnExistsError, ColumnNotFoundError


class ColumnRegistry:
    """Registry for managing column metadata and ordering.
    
    Provides centralized management of column metadata with efficient
    lookups, ordering, and validation.
    
    Attributes:
        _metadata: Maps column names to their metadata
        _column_order: Ordered list of column names
    """
    
    def __init__(self):
        """Initialize column registry."""
        self._metadata: Dict[str, ColumnMetadata] = {}
        self._column_order: List[str] = []
    
    # ========================================================================
    # Column Registration
    # ========================================================================
    
    def add_column(
        self,
        metadata: ColumnMetadata,
        position: Optional[int] = None
    ) -> None:
        """Add a column to the registry.
        
        Args:
            metadata: Column metadata
            position: Optional position to insert at (None = append)
            
        Raises:
            ColumnExistsError: If column name already exists
        """
        if metadata.name in self._metadata:
            raise ColumnExistsError(metadata.name)
        
        # Add metadata
        self._metadata[metadata.name] = metadata
        
        # Add to order
        if position is not None and 0 <= position <= len(self._column_order):
            self._column_order.insert(position, metadata.name)
        else:
            self._column_order.append(metadata.name)
    
    def remove_column(self, name: str) -> ColumnMetadata:
        """Remove a column from the registry.
        
        Args:
            name: Column name
            
        Returns:
            Removed column's metadata
            
        Raises:
            ColumnNotFoundError: If column doesn't exist
        """
        if name not in self._metadata:
            raise ColumnNotFoundError(name, self.get_column_names())
        
        # Get metadata before removal
        metadata = self._metadata[name]
        
        # Remove from metadata and order
        del self._metadata[name]
        self._column_order.remove(name)
        
        return metadata
    
    def rename_column(self, old_name: str, new_name: str) -> None:
        """Rename a column.
        
        Args:
            old_name: Current column name
            new_name: New column name
            
        Raises:
            ColumnNotFoundError: If old_name doesn't exist
            ColumnExistsError: If new_name already exists
        """
        if old_name not in self._metadata:
            raise ColumnNotFoundError(old_name, self.get_column_names())
        
        if new_name in self._metadata:
            raise ColumnExistsError(new_name)
        
        # Get metadata and update name
        metadata = self._metadata[old_name]
        metadata.name = new_name
        
        # Update metadata dictionary
        self._metadata[new_name] = metadata
        del self._metadata[old_name]
        
        # Update order
        idx = self._column_order.index(old_name)
        self._column_order[idx] = new_name
    
    # ========================================================================
    # Column Queries
    # ========================================================================
    
    def has_column(self, name: str) -> bool:
        """Check if a column exists.
        
        Args:
            name: Column name
            
        Returns:
            True if column exists
        """
        return name in self._metadata
    
    def get_column(self, name: str) -> ColumnMetadata:
        """Get metadata for a column.
        
        Args:
            name: Column name
            
        Returns:
            ColumnMetadata object
            
        Raises:
            ColumnNotFoundError: If column doesn't exist
        """
        if name not in self._metadata:
            raise ColumnNotFoundError(name, self.get_column_names())
        return self._metadata[name]
    
    def get_column_names(self) -> List[str]:
        """Get list of all column names in order.
        
        Returns:
            List of column names
        """
        return self._column_order.copy()
    
    def get_column_count(self) -> int:
        """Get number of columns.
        
        Returns:
            Number of registered columns
        """
        return len(self._column_order)
    
    def get_column_index(self, name: str) -> int:
        """Get index position of a column.
        
        Args:
            name: Column name
            
        Returns:
            Zero-based index of column
            
        Raises:
            ColumnNotFoundError: If column doesn't exist
        """
        if name not in self._metadata:
            raise ColumnNotFoundError(name, self.get_column_names())
        return self._column_order.index(name)
    
    def get_column_at_index(self, index: int) -> Optional[str]:
        """Get column name at a specific index.
        
        Args:
            index: Zero-based column index
            
        Returns:
            Column name or None if index out of range
        """
        if 0 <= index < len(self._column_order):
            return self._column_order[index]
        return None
    
    # ========================================================================
    # Filtered Queries
    # ========================================================================
    
    def get_columns_by_type(self, column_type: ColumnType) -> List[str]:
        """Get all columns of a specific type.
        
        Args:
            column_type: Type to filter by
            
        Returns:
            List of column names matching the type
        """
        return [
            name for name in self._column_order
            if self._metadata[name].column_type == column_type
        ]
    
    def get_data_columns(self) -> List[str]:
        """Get all user-editable data columns.
        
        Returns:
            List of DATA column names
        """
        return self.get_columns_by_type(ColumnType.DATA)
    
    def get_calculated_columns(self) -> List[str]:
        """Get all calculated formula columns.
        
        Returns:
            List of CALCULATED column names
        """
        return self.get_columns_by_type(ColumnType.CALCULATED)
    
    def get_derivative_columns(self) -> List[str]:
        """Get all derivative columns.
        
        Returns:
            List of DERIVATIVE column names
        """
        return self.get_columns_by_type(ColumnType.DERIVATIVE)
    
    def get_editable_columns(self) -> List[str]:
        """Get all editable columns (excludes calculated/uncertainty).
        
        Returns:
            List of editable column names
        """
        return [
            name for name in self._column_order
            if self._metadata[name].editable
        ]
    
    def get_columns_with_unit(self, unit: str) -> List[str]:
        """Get all columns with a specific unit.
        
        Args:
            unit: Unit string (e.g., "m", "s", "kg")
            
        Returns:
            List of column names with matching unit
        """
        return [
            name for name in self._column_order
            if self._metadata[name].unit == unit
        ]
    
    # ========================================================================
    # Column Ordering
    # ========================================================================
    
    def move_column(self, name: str, new_position: int) -> None:
        """Move a column to a new position.
        
        Args:
            name: Column name
            new_position: New zero-based index position
            
        Raises:
            ColumnNotFoundError: If column doesn't exist
            IndexError: If position out of range
        """
        if name not in self._metadata:
            raise ColumnNotFoundError(name, self.get_column_names())
        
        if new_position < 0 or new_position >= len(self._column_order):
            raise IndexError(f"Position {new_position} out of range")
        
        # Remove from current position
        self._column_order.remove(name)
        
        # Insert at new position
        self._column_order.insert(new_position, name)
    
    def swap_columns(self, name1: str, name2: str) -> None:
        """Swap positions of two columns.
        
        Args:
            name1: First column name
            name2: Second column name
            
        Raises:
            ColumnNotFoundError: If either column doesn't exist
        """
        if name1 not in self._metadata:
            raise ColumnNotFoundError(name1, self.get_column_names())
        if name2 not in self._metadata:
            raise ColumnNotFoundError(name2, self.get_column_names())
        
        idx1 = self._column_order.index(name1)
        idx2 = self._column_order.index(name2)
        
        self._column_order[idx1], self._column_order[idx2] = \
            self._column_order[idx2], self._column_order[idx1]
    
    # ========================================================================
    # Metadata Updates
    # ========================================================================
    
    def update_metadata(self, name: str, **kwargs) -> None:
        """Update specific metadata fields for a column.
        
        Args:
            name: Column name
            **kwargs: Metadata fields to update (unit, description, precision, etc.)
            
        Raises:
            ColumnNotFoundError: If column doesn't exist
        """
        if name not in self._metadata:
            raise ColumnNotFoundError(name, self.get_column_names())
        
        metadata = self._metadata[name]
        
        # Update allowed fields
        for key, value in kwargs.items():
            if hasattr(metadata, key):
                setattr(metadata, key, value)
    
    # ========================================================================
    # Validation
    # ========================================================================
    
    def validate_column_name(self, name: str, exclude: Optional[str] = None) -> tuple[bool, Optional[str]]:
        """Validate a column name.
        
        Args:
            name: Column name to validate
            exclude: Optional column name to exclude from existence check (for renaming)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if empty
        if not name or not name.strip():
            return False, "Column name cannot be empty"
        
        # Check for invalid characters
        invalid_chars = ['{', '}', '[', ']', '(', ')', ',', ';']
        for char in invalid_chars:
            if char in name:
                return False, f"Column name cannot contain '{char}'"
        
        # Check if already exists (unless it's the excluded one)
        if name != exclude and name in self._metadata:
            return False, f"Column '{name}' already exists"
        
        return True, None
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def clear(self) -> None:
        """Clear all columns."""
        self._metadata.clear()
        self._column_order.clear()
    
    def get_all_metadata(self) -> Dict[str, ColumnMetadata]:
        """Get all column metadata.
        
        Returns:
            Dictionary mapping column names to metadata
        """
        return self._metadata.copy()
    
    def to_dict(self) -> Dict[str, any]:
        """Export registry to dictionary.
        
        Returns:
            Dictionary with metadata and ordering
        """
        return {
            'column_order': self._column_order.copy(),
            'metadata': {
                name: {
                    'name': meta.name,
                    'column_type': meta.column_type.value,
                    'dtype': meta.dtype.value,
                    'unit': meta.unit,
                    'description': meta.description,
                    'precision': meta.precision,
                    'formula': meta.formula,
                    'propagate_uncertainty': meta.propagate_uncertainty,
                    'derivative_numerator': meta.derivative_numerator,
                    'derivative_denominator': meta.derivative_denominator,
                    'range_start': meta.range_start,
                    'range_end': meta.range_end,
                    'range_points': meta.range_points,
                    'interp_x_column': meta.interp_x_column,
                    'interp_y_column': meta.interp_y_column,
                    'interp_method': meta.interp_method,
                    'uncertainty_reference': meta.uncertainty_reference,
                }
                for name, meta in self._metadata.items()
            }
        }
    
    def __len__(self) -> int:
        """Get number of columns."""
        return len(self._column_order)
    
    def __contains__(self, name: str) -> bool:
        """Check if column exists."""
        return name in self._metadata
    
    def __iter__(self):
        """Iterate over column names in order."""
        return iter(self._column_order)
