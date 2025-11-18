"""
Unit tests for ColumnMetadata.

Tests the column metadata dataclass and validation logic.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

import pytest
from widgets.DataTable.column_metadata import ColumnType, ColumnMetadata


class TestColumnType:
    """Test ColumnType enum."""
    
    def test_column_types_exist(self):
        """Test that all expected column types exist."""
        assert ColumnType.DATA
        assert ColumnType.CALCULATED
        assert ColumnType.DERIVATIVE
        assert ColumnType.RANGE
        assert ColumnType.INTERPOLATION
        assert ColumnType.UNCERTAINTY
    
    def test_column_type_values(self):
        """Test that column types have correct string values."""
        assert ColumnType.DATA.value == "data"
        assert ColumnType.CALCULATED.value == "calc"
        assert ColumnType.DERIVATIVE.value == "deriv"
        assert ColumnType.RANGE.value == "range"
        assert ColumnType.INTERPOLATION.value == "interp"
        assert ColumnType.UNCERTAINTY.value == "unc"


class TestColumnMetadata:
    """Test ColumnMetadata dataclass."""
    
    def test_basic_creation(self):
        """Test creating a basic DATA column."""
        col = ColumnMetadata(name="time", column_type=ColumnType.DATA, unit="s")
        
        assert col.name == "time"
        assert col.column_type == ColumnType.DATA
        assert col.unit == "s"
        assert col.description is None
        assert col.editable is True
    
    def test_calculated_column(self):
        """Test creating a CALCULATED column."""
        col = ColumnMetadata(
            name="position",
            column_type=ColumnType.CALCULATED,
            unit="m",
            formula="{velocity} * {time}"
        )
        
        assert col.name == "position"
        assert col.column_type == ColumnType.CALCULATED
        assert col.formula == "{velocity} * {time}"
        assert col.editable is False
    
    def test_derivative_column(self):
        """Test creating a DERIVATIVE column."""
        col = ColumnMetadata(
            name="velocity",
            column_type=ColumnType.DERIVATIVE,
            unit="m/s",
            derivative_numerator="position",
            derivative_denominator="time"
        )
        
        assert col.name == "velocity"
        assert col.column_type == ColumnType.DERIVATIVE
        assert col.derivative_numerator == "position"
        assert col.derivative_denominator == "time"
        assert col.editable is False
    
    def test_range_column(self):
        """Test creating a RANGE column."""
        col = ColumnMetadata(
            name="time",
            column_type=ColumnType.RANGE,
            unit="s",
            range_start=0.0,
            range_end=10.0,
            range_points=11
        )
        
        assert col.name == "time"
        assert col.column_type == ColumnType.RANGE
        assert col.range_start == 0.0
        assert col.range_end == 10.0
        assert col.range_points == 11
        assert col.editable is False  # RANGE columns are read-only (auto-generated)
    
    def test_uncertainty_column(self):
        """Test creating an UNCERTAINTY column."""
        col = ColumnMetadata(
            name="time_unc",
            column_type=ColumnType.UNCERTAINTY,
            unit="s",
            uncertainty_reference="time"
        )
        
        assert col.name == "time_unc"
        assert col.column_type == ColumnType.UNCERTAINTY
        assert col.uncertainty_reference == "time"
        assert col.editable is False  # Propagated uncertainties are read-only
    
    def test_manual_uncertainty_column(self):
        """Test creating a manual UNCERTAINTY column (no reference)."""
        col = ColumnMetadata(
            name="manual_unc",
            column_type=ColumnType.UNCERTAINTY,
            unit="s"
            # No uncertainty_reference - this is a manually entered uncertainty
        )
        
        assert col.name == "manual_unc"
        assert col.column_type == ColumnType.UNCERTAINTY
        assert col.uncertainty_reference is None
        assert col.editable is True  # Manual uncertainties are editable
    
    def test_editability(self):
        """Test that editable property is set correctly."""
        data_col = ColumnMetadata(name="x", column_type=ColumnType.DATA)
        calc_col = ColumnMetadata(name="y", column_type=ColumnType.CALCULATED, formula="{x}**2")
        prop_unc_col = ColumnMetadata(name="y_u", column_type=ColumnType.UNCERTAINTY, uncertainty_reference="y")
        manual_unc_col = ColumnMetadata(name="x_u", column_type=ColumnType.UNCERTAINTY)  # No reference
        
        assert data_col.editable is True
        assert calc_col.editable is False
        assert prop_unc_col.editable is False  # Propagated uncertainty is read-only
        assert manual_unc_col.editable is True  # Manual uncertainty is editable
    
    def test_is_methods(self):
        """Test the is_* helper methods."""
        data_col = ColumnMetadata(name="x", column_type=ColumnType.DATA)
        calc_col = ColumnMetadata(name="y", column_type=ColumnType.CALCULATED, formula="{x}")
        deriv_col = ColumnMetadata(
            name="dydx", column_type=ColumnType.DERIVATIVE,
            derivative_numerator="y", derivative_denominator="x"
        )
        
        assert data_col.is_data_column() is True
        assert data_col.is_calculated_column() is False
        
        assert calc_col.is_calculated_column() is True
        assert calc_col.is_data_column() is False
        
        assert deriv_col.is_derivative_column() is True
        assert deriv_col.is_data_column() is False
    
    def test_get_display_header_with_unit(self):
        """Test display header formatting with unit."""
        col = ColumnMetadata(name="time", column_type=ColumnType.DATA, unit="s")
        assert col.get_display_header() == "time [s]"
    
    def test_get_display_header_without_unit(self):
        """Test display header formatting without unit."""
        col = ColumnMetadata(name="count", column_type=ColumnType.DATA)
        assert col.get_display_header() == "count"
    
    def test_get_symbol(self):
        """Test that correct symbols are returned for each type."""
        data_col = ColumnMetadata(name="x", column_type=ColumnType.DATA)
        calc_col = ColumnMetadata(name="y", column_type=ColumnType.CALCULATED, formula="{x}")
        deriv_col = ColumnMetadata(
            name="dy", column_type=ColumnType.DERIVATIVE,
            derivative_numerator="y", derivative_denominator="x"
        )
        
        assert data_col.get_symbol() == "●"
        assert calc_col.get_symbol() == "ƒ"
        assert deriv_col.get_symbol() == "∂"
    
    def test_validation_calculated_missing_formula(self):
        """Test that CALCULATED column without formula fails validation."""
        col = ColumnMetadata(name="y", column_type=ColumnType.CALCULATED)
        is_valid, error = col.validate()
        
        assert is_valid is False
        assert error is not None
        assert "formula" in error.lower()
    
    def test_validation_calculated_with_formula(self):
        """Test that CALCULATED column with formula passes validation."""
        col = ColumnMetadata(name="y", column_type=ColumnType.CALCULATED, formula="{x}**2")
        is_valid, error = col.validate()
        
        assert is_valid is True
        assert error is None
    
    def test_validation_derivative_missing_columns(self):
        """Test that DERIVATIVE column without num/denom fails validation."""
        col = ColumnMetadata(name="dydx", column_type=ColumnType.DERIVATIVE)
        is_valid, error = col.validate()
        
        assert is_valid is False
        assert error is not None
        assert "numerator" in error.lower() or "denominator" in error.lower()
    
    def test_validation_derivative_complete(self):
        """Test that DERIVATIVE column with num/denom passes validation."""
        col = ColumnMetadata(
            name="dydx",
            column_type=ColumnType.DERIVATIVE,
            derivative_numerator="y",
            derivative_denominator="x"
        )
        is_valid, error = col.validate()
        
        assert is_valid is True
        assert error is None
    
    def test_validation_range_missing_params(self):
        """Test that RANGE column without params fails validation."""
        col = ColumnMetadata(name="t", column_type=ColumnType.RANGE)
        is_valid, error = col.validate()
        
        assert is_valid is False
    
    def test_validation_range_too_few_points(self):
        """Test that RANGE column with <2 points fails validation."""
        col = ColumnMetadata(
            name="t",
            column_type=ColumnType.RANGE,
            range_start=0.0,
            range_end=1.0,
            range_points=1
        )
        is_valid, error = col.validate()
        
        assert is_valid is False
        assert error is not None
        assert "2 points" in error.lower()
    
    def test_validation_range_complete(self):
        """Test that RANGE column with valid params passes validation."""
        col = ColumnMetadata(
            name="t",
            column_type=ColumnType.RANGE,
            range_start=0.0,
            range_end=10.0,
            range_points=11
        )
        is_valid, error = col.validate()
        
        assert is_valid is True
        assert error is None
    
    def test_validation_uncertainty_missing_reference(self):
        """Test that UNCERTAINTY column without reference fails validation."""
        col = ColumnMetadata(name="x_u", column_type=ColumnType.UNCERTAINTY)
        is_valid, error = col.validate()
        
        assert is_valid is False
        assert error is not None
        assert "reference" in error.lower()
    
    def test_validation_uncertainty_complete(self):
        """Test that UNCERTAINTY column with reference passes validation."""
        col = ColumnMetadata(
            name="x_u",
            column_type=ColumnType.UNCERTAINTY,
            uncertainty_reference="x"
        )
        is_valid, error = col.validate()
        
        assert is_valid is True
        assert error is None
    
    def test_precision_default(self):
        """Test that default precision is 6."""
        col = ColumnMetadata(name="x", column_type=ColumnType.DATA)
        assert col.precision == 6
    
    def test_precision_custom(self):
        """Test setting custom precision."""
        col = ColumnMetadata(name="x", column_type=ColumnType.DATA, precision=3)
        assert col.precision == 3
