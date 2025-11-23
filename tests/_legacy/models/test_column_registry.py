"""
Unit tests for ColumnRegistry class.
"""

import pytest
from models.column_registry import ColumnRegistry
from widgets.data_table.column_metadata import ColumnMetadata, ColumnType, DataType
from utils.exceptions import ColumnExistsError, ColumnNotFoundError


class TestColumnRegistryBasic:
    """Basic column registry tests."""
    
    def test_initialization(self):
        """Test registry initialization."""
        registry = ColumnRegistry()
        assert registry.get_column_count() == 0
        assert registry.get_column_names() == []
    
    def test_add_column(self):
        """Test adding a column."""
        registry = ColumnRegistry()
        metadata = ColumnMetadata(
            name="test_col",
            column_type=ColumnType.DATA,
            dtype=DataType.FLOAT
        )
        
        registry.add_column(metadata)
        
        assert registry.get_column_count() == 1
        assert "test_col" in registry
        assert registry.get_column_names() == ["test_col"]
    
    def test_add_column_duplicate_raises_error(self):
        """Test adding duplicate column raises error."""
        registry = ColumnRegistry()
        metadata = ColumnMetadata(
            name="test_col",
            column_type=ColumnType.DATA,
            dtype=DataType.FLOAT
        )
        
        registry.add_column(metadata)
        
        with pytest.raises(ColumnExistsError):
            registry.add_column(metadata)
    
    def test_add_column_at_position(self):
        """Test adding column at specific position."""
        registry = ColumnRegistry()
        
        # Add three columns
        for i in range(3):
            metadata = ColumnMetadata(
                name=f"col{i}",
                column_type=ColumnType.DATA,
                dtype=DataType.FLOAT
            )
            registry.add_column(metadata)
        
        # Insert at position 1
        metadata = ColumnMetadata(
            name="inserted",
            column_type=ColumnType.DATA,
            dtype=DataType.FLOAT
        )
        registry.add_column(metadata, position=1)
        
        assert registry.get_column_names() == ["col0", "inserted", "col1", "col2"]
    
    def test_remove_column(self):
        """Test removing a column."""
        registry = ColumnRegistry()
        metadata = ColumnMetadata(
            name="test_col",
            column_type=ColumnType.DATA,
            dtype=DataType.FLOAT
        )
        registry.add_column(metadata)
        
        removed = registry.remove_column("test_col")
        
        assert removed.name == "test_col"
        assert registry.get_column_count() == 0
        assert "test_col" not in registry
    
    def test_remove_nonexistent_column_raises_error(self):
        """Test removing nonexistent column raises error."""
        registry = ColumnRegistry()
        
        with pytest.raises(ColumnNotFoundError):
            registry.remove_column("nonexistent")
    
    def test_rename_column(self):
        """Test renaming a column."""
        registry = ColumnRegistry()
        metadata = ColumnMetadata(
            name="old_name",
            column_type=ColumnType.DATA,
            dtype=DataType.FLOAT
        )
        registry.add_column(metadata)
        
        registry.rename_column("old_name", "new_name")
        
        assert "old_name" not in registry
        assert "new_name" in registry
        assert registry.get_column("new_name").name == "new_name"
        assert registry.get_column_names() == ["new_name"]


class TestColumnQueries:
    """Test column query methods."""
    
    def test_has_column(self):
        """Test checking if column exists."""
        registry = ColumnRegistry()
        metadata = ColumnMetadata(
            name="test_col",
            column_type=ColumnType.DATA,
            dtype=DataType.FLOAT
        )
        registry.add_column(metadata)
        
        assert registry.has_column("test_col") is True
        assert registry.has_column("nonexistent") is False
    
    def test_get_column(self):
        """Test getting column metadata."""
        registry = ColumnRegistry()
        metadata = ColumnMetadata(
            name="test_col",
            column_type=ColumnType.DATA,
            dtype=DataType.FLOAT,
            unit="m"
        )
        registry.add_column(metadata)
        
        retrieved = registry.get_column("test_col")
        
        assert retrieved.name == "test_col"
        assert retrieved.unit == "m"
    
    def test_get_column_index(self):
        """Test getting column index."""
        registry = ColumnRegistry()
        
        for i in range(3):
            metadata = ColumnMetadata(
                name=f"col{i}",
                column_type=ColumnType.DATA,
                dtype=DataType.FLOAT
            )
            registry.add_column(metadata)
        
        assert registry.get_column_index("col0") == 0
        assert registry.get_column_index("col1") == 1
        assert registry.get_column_index("col2") == 2
    
    def test_get_column_at_index(self):
        """Test getting column name by index."""
        registry = ColumnRegistry()
        
        for i in range(3):
            metadata = ColumnMetadata(
                name=f"col{i}",
                column_type=ColumnType.DATA,
                dtype=DataType.FLOAT
            )
            registry.add_column(metadata)
        
        assert registry.get_column_at_index(0) == "col0"
        assert registry.get_column_at_index(1) == "col1"
        assert registry.get_column_at_index(2) == "col2"
        assert registry.get_column_at_index(99) is None
        assert registry.get_column_at_index(-1) is None


class TestFilteredQueries:
    """Test filtered query methods."""
    
    def setup_method(self):
        """Set up test registry with various column types."""
        self.registry = ColumnRegistry()
        
        # Add DATA column
        self.registry.add_column(ColumnMetadata(
            name="data1",
            column_type=ColumnType.DATA,
            dtype=DataType.FLOAT
        ))
        
        # Add CALCULATED column
        self.registry.add_column(ColumnMetadata(
            name="calc1",
            column_type=ColumnType.CALCULATED,
            dtype=DataType.FLOAT,
            formula="{data1} * 2"
        ))
        
        # Add DERIVATIVE column
        self.registry.add_column(ColumnMetadata(
            name="deriv1",
            column_type=ColumnType.DERIVATIVE,
            dtype=DataType.FLOAT,
            derivative_numerator="data1",
            derivative_denominator="data1"
        ))
        
        # Add another DATA column
        self.registry.add_column(ColumnMetadata(
            name="data2",
            column_type=ColumnType.DATA,
            dtype=DataType.FLOAT
        ))
    
    def test_get_columns_by_type(self):
        """Test filtering by column type."""
        data_cols = self.registry.get_columns_by_type(ColumnType.DATA)
        calc_cols = self.registry.get_columns_by_type(ColumnType.CALCULATED)
        deriv_cols = self.registry.get_columns_by_type(ColumnType.DERIVATIVE)
        
        assert set(data_cols) == {"data1", "data2"}
        assert calc_cols == ["calc1"]
        assert deriv_cols == ["deriv1"]
    
    def test_get_data_columns(self):
        """Test getting data columns."""
        data_cols = self.registry.get_data_columns()
        assert set(data_cols) == {"data1", "data2"}
    
    def test_get_calculated_columns(self):
        """Test getting calculated columns."""
        calc_cols = self.registry.get_calculated_columns()
        assert calc_cols == ["calc1"]
    
    def test_get_derivative_columns(self):
        """Test getting derivative columns."""
        deriv_cols = self.registry.get_derivative_columns()
        assert deriv_cols == ["deriv1"]
    
    def test_get_editable_columns(self):
        """Test getting editable columns."""
        editable = self.registry.get_editable_columns()
        # Only DATA columns are editable, CALCULATED and DERIVATIVE are not
        assert set(editable) == {"data1", "data2"}
    
    def test_get_columns_with_unit(self):
        """Test filtering by unit."""
        # Add columns with units
        self.registry.add_column(ColumnMetadata(
            name="length1",
            column_type=ColumnType.DATA,
            dtype=DataType.FLOAT,
            unit="m"
        ))
        self.registry.add_column(ColumnMetadata(
            name="length2",
            column_type=ColumnType.DATA,
            dtype=DataType.FLOAT,
            unit="m"
        ))
        self.registry.add_column(ColumnMetadata(
            name="time1",
            column_type=ColumnType.DATA,
            dtype=DataType.FLOAT,
            unit="s"
        ))
        
        length_cols = self.registry.get_columns_with_unit("m")
        time_cols = self.registry.get_columns_with_unit("s")
        
        assert set(length_cols) == {"length1", "length2"}
        assert time_cols == ["time1"]


class TestColumnOrdering:
    """Test column ordering operations."""
    
    def test_move_column(self):
        """Test moving column to new position."""
        registry = ColumnRegistry()
        
        for i in range(4):
            metadata = ColumnMetadata(
                name=f"col{i}",
                column_type=ColumnType.DATA,
                dtype=DataType.FLOAT
            )
            registry.add_column(metadata)
        
        # Move col0 to position 2
        registry.move_column("col0", 2)
        
        assert registry.get_column_names() == ["col1", "col2", "col0", "col3"]
    
    def test_swap_columns(self):
        """Test swapping two columns."""
        registry = ColumnRegistry()
        
        for i in range(4):
            metadata = ColumnMetadata(
                name=f"col{i}",
                column_type=ColumnType.DATA,
                dtype=DataType.FLOAT
            )
            registry.add_column(metadata)
        
        # Swap col1 and col3
        registry.swap_columns("col1", "col3")
        
        assert registry.get_column_names() == ["col0", "col3", "col2", "col1"]


class TestMetadataUpdates:
    """Test metadata update operations."""
    
    def test_update_metadata(self):
        """Test updating metadata fields."""
        registry = ColumnRegistry()
        metadata = ColumnMetadata(
            name="test_col",
            column_type=ColumnType.DATA,
            dtype=DataType.FLOAT,
            unit="m",
            precision=2
        )
        registry.add_column(metadata)
        
        # Update unit and precision
        registry.update_metadata("test_col", unit="km", precision=4)
        
        updated = registry.get_column("test_col")
        assert updated.unit == "km"
        assert updated.precision == 4


class TestValidation:
    """Test validation methods."""
    
    def test_validate_column_name_valid(self):
        """Test validating valid column name."""
        registry = ColumnRegistry()
        
        valid, error = registry.validate_column_name("valid_name")
        
        assert valid is True
        assert error is None
    
    def test_validate_column_name_empty(self):
        """Test validating empty column name."""
        registry = ColumnRegistry()
        
        valid, error = registry.validate_column_name("")
        
        assert valid is False
        assert "cannot be empty" in error
    
    def test_validate_column_name_invalid_chars(self):
        """Test validating column name with invalid characters."""
        registry = ColumnRegistry()
        
        for char in ['{', '}', '[', ']', '(', ')', ',', ';']:
            valid, error = registry.validate_column_name(f"test{char}name")
            assert valid is False
            assert f"cannot contain '{char}'" in error
    
    def test_validate_column_name_duplicate(self):
        """Test validating duplicate column name."""
        registry = ColumnRegistry()
        metadata = ColumnMetadata(
            name="existing",
            column_type=ColumnType.DATA,
            dtype=DataType.FLOAT
        )
        registry.add_column(metadata)
        
        valid, error = registry.validate_column_name("existing")
        
        assert valid is False
        assert "already exists" in error
    
    def test_validate_column_name_with_exclude(self):
        """Test validating with excluded name (for renaming)."""
        registry = ColumnRegistry()
        metadata = ColumnMetadata(
            name="existing",
            column_type=ColumnType.DATA,
            dtype=DataType.FLOAT
        )
        registry.add_column(metadata)
        
        # Should be valid when excluding the same name
        valid, error = registry.validate_column_name("existing", exclude="existing")
        
        assert valid is True
        assert error is None


class TestUtilities:
    """Test utility methods."""
    
    def test_clear(self):
        """Test clearing all columns."""
        registry = ColumnRegistry()
        
        for i in range(3):
            metadata = ColumnMetadata(
                name=f"col{i}",
                column_type=ColumnType.DATA,
                dtype=DataType.FLOAT
            )
            registry.add_column(metadata)
        
        registry.clear()
        
        assert registry.get_column_count() == 0
        assert registry.get_column_names() == []
    
    def test_len(self):
        """Test __len__ method."""
        registry = ColumnRegistry()
        
        assert len(registry) == 0
        
        for i in range(3):
            metadata = ColumnMetadata(
                name=f"col{i}",
                column_type=ColumnType.DATA,
                dtype=DataType.FLOAT
            )
            registry.add_column(metadata)
        
        assert len(registry) == 3
    
    def test_contains(self):
        """Test __contains__ method."""
        registry = ColumnRegistry()
        metadata = ColumnMetadata(
            name="test_col",
            column_type=ColumnType.DATA,
            dtype=DataType.FLOAT
        )
        registry.add_column(metadata)
        
        assert "test_col" in registry
        assert "nonexistent" not in registry
    
    def test_iter(self):
        """Test __iter__ method."""
        registry = ColumnRegistry()
        
        names = ["col0", "col1", "col2"]
        for name in names:
            metadata = ColumnMetadata(
                name=name,
                column_type=ColumnType.DATA,
                dtype=DataType.FLOAT
            )
            registry.add_column(metadata)
        
        assert list(registry) == names
    
    def test_to_dict(self):
        """Test exporting to dictionary."""
        registry = ColumnRegistry()
        metadata = ColumnMetadata(
            name="test_col",
            column_type=ColumnType.DATA,
            dtype=DataType.FLOAT,
            unit="m"
        )
        registry.add_column(metadata)
        
        data = registry.to_dict()
        
        assert "column_order" in data
        assert "metadata" in data
        assert data["column_order"] == ["test_col"]
        assert "test_col" in data["metadata"]
        assert data["metadata"]["test_col"]["unit"] == "m"
