"""Column management for AdvancedDataTableWidget.

This module provides centralized column operations including:
- Column creation, validation, and removal
- Column metadata management
- Diminutive-to-index lookups with caching
- Column reference tracking
"""

from typing import List, Optional, Dict, Set
import re

from .models import AdvancedColumnType, AdvancedColumnDataType, ColumnMetadata
from .constants import FORMULA_REFERENCE_PATTERN, BACKWARD_COMPAT_PATTERN
from .exceptions import (
    ColumnNotFoundError,
    DuplicateDiminutiveError,
    InvalidColumnTypeError,
    InvalidColumnIndexError
)


class ColumnManager:
    """Manages column metadata and operations for the data table.
    
    This class centralizes all column-related operations and maintains
    an index cache for fast lookups by diminutive.
    
    Attributes:
        _columns: List of column metadata
        _diminutive_index: Cache mapping diminutive -> column index
    """
    
    def __init__(self):
        """Initialize the column manager."""
        self._columns: List[ColumnMetadata] = []
        self._diminutive_index: Dict[str, int] = {}
    
    def add_column(
        self,
        column_type: AdvancedColumnType,
        data_type: AdvancedColumnDataType,
        diminutive: str,
        description: Optional[str] = None,
        unit: Optional[str] = None,
        formula: Optional[str] = None,
        uncertainty_reference: Optional[int] = None,
        propagate_uncertainty: bool = False,
        derivative_numerator: Optional[int] = None,
        derivative_denominator: Optional[int] = None,
        insert_position: Optional[int] = None
    ) -> int:
        """Add a new column with validation.
        
        Args:
            column_type: Type of column (DATA, CALCULATED, etc.)
            data_type: Data type (NUMERICAL, CATEGORICAL, TEXT)
            diminutive: Short name for formulas
            description: Full description
            unit: Unit of measurement
            formula: Formula for calculated columns
            uncertainty_reference: Reference column for uncertainty
            propagate_uncertainty: Whether to propagate uncertainty
            derivative_numerator: Numerator column for derivatives
            derivative_denominator: Denominator column for derivatives
            insert_position: Position to insert (None = append)
            
        Returns:
            Index of the created column
            
        Raises:
            DuplicateDiminutiveError: If diminutive already exists
            InvalidColumnIndexError: If insert_position is invalid
        """
        # Validate diminutive uniqueness
        if diminutive in self._diminutive_index:
            raise DuplicateDiminutiveError(diminutive)
        
        # Determine position
        if insert_position is None:
            col_index = len(self._columns)
        else:
            if insert_position < 0 or insert_position > len(self._columns):
                raise InvalidColumnIndexError(insert_position, len(self._columns))
            col_index = insert_position
        
        # Create metadata
        metadata = ColumnMetadata(
            column_type=column_type,
            data_type=data_type,
            diminutive=diminutive,
            description=description,
            unit=unit,
            formula=formula,
            uncertainty_reference=uncertainty_reference,
            propagate_uncertainty=propagate_uncertainty,
            derivative_numerator=derivative_numerator,
            derivative_denominator=derivative_denominator
        )
        
        # Insert column
        self._columns.insert(col_index, metadata)
        
        # Update cache and references
        self._rebuild_index_cache()
        self._adjust_references_after_insert(col_index)
        
        return col_index
    
    def remove_column(self, column_index: int) -> ColumnMetadata:
        """Remove a column and update references.
        
        Args:
            column_index: Index of column to remove
            
        Returns:
            Removed column metadata
            
        Raises:
            ColumnNotFoundError: If column index is invalid
        """
        if not self.is_valid_index(column_index):
            raise ColumnNotFoundError(column_index)
        
        # Get metadata before removal
        metadata = self._columns[column_index]
        
        # Remove from list
        del self._columns[column_index]
        
        # Update cache and references
        self._rebuild_index_cache()
        self._adjust_references_after_remove(column_index)
        
        return metadata
    
    def get_column(self, column_index: int) -> ColumnMetadata:
        """Get column metadata by index.
        
        Args:
            column_index: Column index
            
        Returns:
            Column metadata
            
        Raises:
            ColumnNotFoundError: If column index is invalid
        """
        if not self.is_valid_index(column_index):
            raise ColumnNotFoundError(column_index)
        
        return self._columns[column_index]
    
    def find_by_diminutive(self, diminutive: str) -> Optional[int]:
        """Find column index by diminutive (O(1) lookup).
        
        Args:
            diminutive: Column diminutive to search for
            
        Returns:
            Column index or None if not found
        """
        return self._diminutive_index.get(diminutive)
    
    def update_diminutive(self, column_index: int, new_diminutive: str) -> str:
        """Update column diminutive with validation.
        
        Args:
            column_index: Index of column to update
            new_diminutive: New diminutive value
            
        Returns:
            The actual diminutive set (may be modified for uniqueness)
            
        Raises:
            ColumnNotFoundError: If column index is invalid
            DuplicateDiminutiveError: If new diminutive already exists
        """
        if not self.is_valid_index(column_index):
            raise ColumnNotFoundError(column_index)
        
        # Check if already used by another column
        existing_index = self._diminutive_index.get(new_diminutive)
        if existing_index is not None and existing_index != column_index:
            raise DuplicateDiminutiveError(new_diminutive)
        
        # Update
        self._columns[column_index].diminutive = new_diminutive
        self._rebuild_index_cache()
        
        return new_diminutive
    
    def ensure_unique_diminutive(self, base_diminutive: str, exclude_index: Optional[int] = None) -> str:
        """Ensure a diminutive is unique by adding numeric suffix if needed.
        
        Args:
            base_diminutive: Base diminutive to make unique
            exclude_index: Column index to exclude from uniqueness check
            
        Returns:
            Unique diminutive (may have numeric suffix)
        """
        existing_diminutives = {
            metadata.diminutive for idx, metadata in enumerate(self._columns)
            if exclude_index is None or idx != exclude_index
        }
        
        if base_diminutive not in existing_diminutives:
            return base_diminutive
        
        # Add numeric suffix
        counter = 1
        while f"{base_diminutive}{counter}" in existing_diminutives:
            counter += 1
        
        return f"{base_diminutive}{counter}"
    
    def generate_diminutive(self, display_name: str, column_index: int) -> str:
        """Generate a diminutive from a display name.
        
        Args:
            display_name: Full name to generate diminutive from
            column_index: Column index for fallback
            
        Returns:
            Generated diminutive
        """
        # Remove common units and symbols
        clean_name = display_name.lower()
        clean_name = clean_name.replace('(', '').replace(')', '').replace('°', '').replace('%', '')
        clean_name = clean_name.replace('/', '_').replace(' ', '_').replace('-', '_')
        
        # Extract meaningful parts
        words = [word.strip() for word in clean_name.split('_') if word.strip()]
        
        if not words:
            return f"col{column_index}"
        
        # Try to create a meaningful diminutive
        if len(words) == 1:
            word = words[0]
            if len(word) <= 4:
                return word
            elif word in ['temperature', 'temp']:
                return 'temp'
            elif word in ['pressure', 'press']:
                return 'press'
            elif word in ['voltage', 'volt']:
                return 'volt'
            elif word in ['current', 'amp', 'ampere']:
                return 'amp'
            elif word in ['time']:
                return 'time'
            elif word in ['distance', 'dist']:
                return 'dist'
            else:
                # Take first 4 characters
                return word[:4]
        else:
            # Multiple words - take first letter of each
            abbreviation = ''.join(word[0] for word in words if word)
            if len(abbreviation) <= 6:
                return abbreviation
            else:
                return abbreviation[:4]
    
    def get_dependent_columns(self, column_index: int) -> List[int]:
        """Get indices of columns that depend on the specified column.
        
        A column depends on another if:
        - It's an uncertainty column referencing it
        - It's a calculated column with a formula referencing it
        - It's a derivative column using it as numerator/denominator
        
        Args:
            column_index: Index of column to check dependencies for
            
        Returns:
            List of dependent column indices
        """
        if not self.is_valid_index(column_index):
            return []
        
        diminutive = self._columns[column_index].diminutive
        dependents = []
        
        for idx, metadata in enumerate(self._columns):
            # Check uncertainty references
            if (metadata.column_type == AdvancedColumnType.UNCERTAINTY and
                metadata.uncertainty_reference == column_index):
                dependents.append(idx)
            
            # Check formula references
            elif (metadata.column_type == AdvancedColumnType.CALCULATED and
                  metadata.formula and self._formula_references_diminutive(metadata.formula, diminutive)):
                dependents.append(idx)
            
            # Check derivative references
            elif (metadata.column_type == AdvancedColumnType.DERIVATIVE and
                  (metadata.derivative_numerator == column_index or
                   metadata.derivative_denominator == column_index)):
                dependents.append(idx)
        
        return dependents
    
    def has_uncertainty_column(self, data_column_index: int) -> tuple[bool, Optional[int]]:
        """Check if a data column has an associated uncertainty column.
        
        Args:
            data_column_index: Index of the data column
            
        Returns:
            Tuple of (has_uncertainty, uncertainty_column_index)
        """
        for idx, metadata in enumerate(self._columns):
            if (metadata.column_type == AdvancedColumnType.UNCERTAINTY and
                metadata.uncertainty_reference == data_column_index):
                return True, idx
        
        return False, None
    
    def get_columns_by_type(self, *column_types: AdvancedColumnType) -> List[int]:
        """Get indices of all columns of specified types.
        
        Args:
            *column_types: Column types to filter by
            
        Returns:
            List of column indices matching any of the types
        """
        return [
            idx for idx, metadata in enumerate(self._columns)
            if metadata.column_type in column_types
        ]
    
    def is_valid_index(self, column_index: int) -> bool:
        """Check if a column index is valid.
        
        Args:
            column_index: Index to validate
            
        Returns:
            True if valid, False otherwise
        """
        return 0 <= column_index < len(self._columns)
    
    def column_count(self) -> int:
        """Get the total number of columns.
        
        Returns:
            Number of columns
        """
        return len(self._columns)
    
    def clear(self):
        """Remove all columns and clear the cache."""
        self._columns.clear()
        self._diminutive_index.clear()
    
    def _rebuild_index_cache(self):
        """Rebuild the diminutive -> index cache."""
        self._diminutive_index.clear()
        for idx, metadata in enumerate(self._columns):
            if metadata.diminutive:
                self._diminutive_index[metadata.diminutive] = idx
    
    def _adjust_references_after_insert(self, inserted_index: int):
        """Adjust column references after inserting a column.
        
        Args:
            inserted_index: Index where column was inserted
        """
        for metadata in self._columns:
            # Adjust uncertainty references
            if metadata.uncertainty_reference is not None and metadata.uncertainty_reference >= inserted_index:
                metadata.uncertainty_reference += 1
            
            # Adjust derivative references
            if metadata.derivative_numerator is not None and metadata.derivative_numerator >= inserted_index:
                metadata.derivative_numerator += 1
            
            if metadata.derivative_denominator is not None and metadata.derivative_denominator >= inserted_index:
                metadata.derivative_denominator += 1
    
    def _adjust_references_after_remove(self, removed_index: int):
        """Adjust column references after removing a column.
        
        Args:
            removed_index: Index of removed column
        """
        for metadata in self._columns:
            # Adjust uncertainty references
            if metadata.uncertainty_reference is not None:
                if metadata.uncertainty_reference == removed_index:
                    # Reference to removed column - invalidate
                    metadata.uncertainty_reference = None
                elif metadata.uncertainty_reference > removed_index:
                    metadata.uncertainty_reference -= 1
            
            # Adjust derivative references
            if metadata.derivative_numerator is not None:
                if metadata.derivative_numerator == removed_index:
                    metadata.derivative_numerator = None
                elif metadata.derivative_numerator > removed_index:
                    metadata.derivative_numerator -= 1
            
            if metadata.derivative_denominator is not None:
                if metadata.derivative_denominator == removed_index:
                    metadata.derivative_denominator = None
                elif metadata.derivative_denominator > removed_index:
                    metadata.derivative_denominator -= 1
    
    def _formula_references_diminutive(self, formula: str, diminutive: str) -> bool:
        """Check if a formula references a specific diminutive.
        
        Args:
            formula: Formula string
            diminutive: Diminutive to check for
            
        Returns:
            True if formula references the diminutive
        """
        # Check primary format: {diminutive}
        if f"{{{diminutive}}}" in formula:
            return True
        
        # Check backward compatibility: [diminutive]
        if f"[{diminutive}]" in formula:
            return True
        
        return False
    
    def extract_formula_references(self, formula: str) -> Set[str]:
        """Extract all column/variable references from a formula.
        
        Args:
            formula: Formula string
            
        Returns:
            Set of referenced diminutives
        """
        refs = set()
        
        # Primary format: {diminutive}
        refs.update(re.findall(FORMULA_REFERENCE_PATTERN, formula))
        
        # Backward compatibility: [name_or_index]
        refs.update(re.findall(BACKWARD_COMPAT_PATTERN, formula))
        
        return refs
    
    def __len__(self) -> int:
        """Get number of columns."""
        return len(self._columns)
    
    def __getitem__(self, index: int) -> ColumnMetadata:
        """Get column by index."""
        if not self.is_valid_index(index):
            raise ColumnNotFoundError(index)
        return self._columns[index]
    
    def __iter__(self):
        """Iterate over columns."""
        return iter(self._columns)
