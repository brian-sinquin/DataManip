"""Tests for interpolation column functionality in DataTableV2."""

import pytest
import numpy as np
from PySide6.QtCore import Qt
from widgets.data_table.model import DataTableModel
from widgets.data_table.column_metadata import ColumnType


class TestInterpolationBasics:
    """Test basic interpolation column creation."""
    
    def test_linear_interpolation(self):
        """Test linear interpolation method."""
        model = DataTableModel()
        
        # Add sparse data points
        x_data = [0.0, 1.0, 2.0, 3.0]
        y_data = [0.0, 2.0, 4.0, 6.0]  # y = 2*x
        
        model.add_data_column("x", data=x_data)
        model.add_data_column("y", data=y_data)
        
        # Add interpolation column
        model.add_interpolation_column(
            name="y_interp",
            x_column="x",
            y_column="y",
            method="linear"
        )
        
        # Check values
        result = model.get_column_data("y_interp")
        np.testing.assert_array_almost_equal(result, y_data)
    
    def test_cubic_interpolation(self):
        """Test cubic spline interpolation."""
        model = DataTableModel()
        
        # Add sparse data points for x^2
        x_data = [0.0, 1.0, 2.0, 3.0, 4.0]
        y_data = [0.0, 1.0, 4.0, 9.0, 16.0]
        
        model.add_data_column("x", data=x_data)
        model.add_data_column("y", data=y_data)
        
        # Add interpolation column
        model.add_interpolation_column(
            name="y_interp",
            x_column="x",
            y_column="y",
            method="cubic"
        )
        
        # Cubic spline should match the data points
        result = model.get_column_data("y_interp")
        np.testing.assert_array_almost_equal(result, y_data)
    
    def test_quadratic_interpolation(self):
        """Test quadratic interpolation method."""
        model = DataTableModel()
        
        # Add data points
        x_data = [0.0, 1.0, 2.0, 3.0]
        y_data = [1.0, 2.0, 3.0, 4.0]
        
        model.add_data_column("x", data=x_data)
        model.add_data_column("y", data=y_data)
        
        # Add interpolation column
        model.add_interpolation_column(
            name="y_interp",
            x_column="x",
            y_column="y",
            method="quadratic"
        )
        
        # Should match at data points
        result = model.get_column_data("y_interp")
        np.testing.assert_array_almost_equal(result, y_data)
    
    def test_nearest_interpolation(self):
        """Test nearest neighbor interpolation."""
        model = DataTableModel()
        
        # Add sparse data points
        x_data = [0.0, 2.0, 4.0]
        y_data = [10.0, 20.0, 30.0]
        
        model.add_data_column("x", data=x_data)
        model.add_data_column("y", data=y_data)
        
        # Add interpolation column
        model.add_interpolation_column(
            name="y_interp",
            x_column="x",
            y_column="y",
            method="nearest"
        )
        
        # Should match at data points
        result = model.get_column_data("y_interp")
        np.testing.assert_array_almost_equal(result, y_data)


class TestInterpolationWithEvalColumn:
    """Test interpolation with separate evaluation column."""
    
    def test_interpolate_to_dense_grid(self):
        """Test interpolating sparse data to dense grid."""
        model = DataTableModel()
        
        # Sparse data
        x_sparse = [0.0, 5.0, 10.0]
        y_sparse = [0.0, 25.0, 100.0]  # y = x^2
        
        model.add_data_column("x_sparse", data=x_sparse)
        model.add_data_column("y_sparse", data=y_sparse)
        
        # Dense grid for evaluation
        model.add_range_column("x_dense", start=0, end=10, points=11)
        
        # Interpolate to dense grid
        model.add_interpolation_column(
            name="y_interp",
            x_column="x_sparse",
            y_column="y_sparse",
            eval_column="x_dense",
            method="linear"
        )
        
        # Check that we have 11 interpolated values
        result = model.get_column_data("y_interp")
        assert len(result) == 11
        
        # Check boundary values
        assert result.iloc[0] == pytest.approx(0.0)
        assert result.iloc[-1] == pytest.approx(100.0)
    
    def test_extrapolation_returns_nan(self):
        """Test that values outside data range are NaN."""
        model = DataTableModel()
        
        # Data from 2 to 8
        x_data = [2.0, 4.0, 6.0, 8.0]
        y_data = [10.0, 20.0, 30.0, 40.0]
        
        model.add_data_column("x_data", data=x_data)
        model.add_data_column("y_data", data=y_data)
        
        # Evaluation from 0 to 10 (extends beyond data range)
        model.add_range_column("x_eval", start=0, end=10, points=11)
        
        # Interpolate
        model.add_interpolation_column(
            name="y_interp",
            x_column="x_data",
            y_column="y_data",
            eval_column="x_eval",
            method="linear"
        )
        
        result = model.get_column_data("y_interp")
        
        # First two points (0, 1) should be NaN (below data range)
        assert np.isnan(result.iloc[0])
        assert np.isnan(result.iloc[1])
        
        # Last two points (9, 10) should be NaN (above data range)
        assert np.isnan(result.iloc[-1])
        assert np.isnan(result.iloc[-2])
        
        # Middle values should be valid
        assert not np.isnan(result.iloc[5])


class TestInterpolationUnits:
    """Test unit handling in interpolation columns."""
    
    def test_unit_inherited_from_y_column(self):
        """Test that unit is inherited from Y column."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0, 1, 2], unit="s")
        model.add_data_column("y", data=[0, 10, 20], unit="m")
        
        model.add_interpolation_column(
            name="y_interp",
            x_column="x",
            y_column="y",
            method="linear"
        )
        
        meta = model.get_column_metadata("y_interp")
        assert meta.unit == "m"
    
    def test_manual_unit_override(self):
        """Test manual unit specification."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0, 1, 2])
        model.add_data_column("y", data=[0, 10, 20], unit="m")
        
        model.add_interpolation_column(
            name="y_interp",
            x_column="x",
            y_column="y",
            method="linear",
            unit="cm"  # Override
        )
        
        meta = model.get_column_metadata("y_interp")
        assert meta.unit == "cm"


class TestInterpolationErrors:
    """Test error handling in interpolation columns."""
    
    def test_duplicate_name_raises_error(self):
        """Test that duplicate column name raises error."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0, 1, 2])
        model.add_data_column("y", data=[0, 1, 2])
        model.add_interpolation_column("interp", x_column="x", y_column="y")
        
        with pytest.raises(Exception):
            model.add_interpolation_column("interp", x_column="x", y_column="y")
    
    def test_x_column_not_found_raises_error(self):
        """Test that missing X column raises error."""
        model = DataTableModel()
        
        model.add_data_column("y", data=[0, 1, 2])
        
        with pytest.raises(Exception):
            model.add_interpolation_column("interp", x_column="missing", y_column="y")
    
    def test_y_column_not_found_raises_error(self):
        """Test that missing Y column raises error."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0, 1, 2])
        
        with pytest.raises(Exception):
            model.add_interpolation_column("interp", x_column="x", y_column="missing")
    
    def test_invalid_method_raises_error(self):
        """Test that invalid interpolation method raises error."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0, 1, 2])
        model.add_data_column("y", data=[0, 1, 2])
        
        with pytest.raises(ValueError, match="Invalid method"):
            model.add_interpolation_column("interp", x_column="x", y_column="y", method="invalid")
    
    def test_non_numeric_x_column_raises_error(self):
        """Test that non-numeric X column raises error."""
        model = DataTableModel()
        
        model.add_data_column("x", data=["a", "b", "c"])
        model.add_data_column("y", data=[0, 1, 2])
        
        with pytest.raises(ValueError, match="must be numeric"):
            model.add_interpolation_column("interp", x_column="x", y_column="y")
    
    def test_non_numeric_y_column_raises_error(self):
        """Test that non-numeric Y column raises error."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0, 1, 2])
        model.add_data_column("y", data=["a", "b", "c"])
        
        with pytest.raises(ValueError, match="must be numeric"):
            model.add_interpolation_column("interp", x_column="x", y_column="y")
    
    def test_too_few_points_raises_error(self):
        """Test that insufficient data points raises error."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[1.0])
        model.add_data_column("y", data=[2.0])
        
        with pytest.raises(ValueError, match="at least 2 valid data points"):
            model.add_interpolation_column("interp", x_column="x", y_column="y")
    
    def test_duplicate_x_values_raises_error(self):
        """Test that duplicate X values raise error."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[1.0, 2.0, 2.0, 3.0])  # Duplicate 2.0
        model.add_data_column("y", data=[10.0, 20.0, 25.0, 30.0])
        
        with pytest.raises(ValueError, match="duplicate values"):
            model.add_interpolation_column("interp", x_column="x", y_column="y")


class TestInterpolationDependencies:
    """Test dependency tracking for interpolation columns."""
    
    def test_dependency_registration(self):
        """Test that dependencies are registered correctly."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0, 1, 2])
        model.add_data_column("y", data=[0, 10, 20])
        model.add_interpolation_column("y_interp", x_column="x", y_column="y")
        
        deps = model._dependencies.get("y_interp", set())
        assert "x" in deps
        assert "y" in deps
    
    def test_recalculation_when_x_changes(self):
        """Test that interpolation recalculates when X data changes."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0.0, 1.0, 2.0])
        model.add_data_column("y", data=[0.0, 10.0, 20.0])
        model.add_interpolation_column("y_interp", x_column="x", y_column="y")
        
        # Modify X data
        model.setData(model.index(1, 0), "1.5", Qt.ItemDataRole.EditRole)
        
        # Interpolation should have recalculated
        result = model.get_column_data("y_interp")
        # After change, x = [0, 1.5, 2], y = [0, 10, 20]
        # Linear interpolation should give different values
        assert result.iloc[1] == pytest.approx(10.0)
    
    def test_recalculation_when_y_changes(self):
        """Test that interpolation recalculates when Y data changes."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0.0, 1.0, 2.0])
        model.add_data_column("y", data=[0.0, 10.0, 20.0])
        model.add_interpolation_column("y_interp", x_column="x", y_column="y")
        
        original = model.get_column_data("y_interp").copy()
        
        # Modify Y data
        model.setData(model.index(1, 1), "15.0", Qt.ItemDataRole.EditRole)
        
        # Interpolation should have recalculated
        result = model.get_column_data("y_interp")
        assert result.iloc[1] == pytest.approx(15.0)
        assert not np.array_equal(result, original)


class TestInterpolationIntegration:
    """Test integration with other column types."""
    
    def test_interpolation_in_formula(self):
        """Test using interpolated column in formulas."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0, 1, 2, 3])
        model.add_data_column("y", data=[0, 2, 4, 6])
        model.add_interpolation_column("y_interp", x_column="x", y_column="y")
        
        # Use interpolation in a formula
        model.add_calculated_column("scaled", formula="{y_interp} * 2")
        
        result = model.get_column_data("scaled")
        expected = np.array([0, 4, 8, 12])
        np.testing.assert_array_almost_equal(result, expected)
    
    def test_interpolation_of_calculated_column(self):
        """Test interpolating a calculated column."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0, 1, 2, 3])
        model.add_calculated_column("x_squared", formula="{x}**2")
        
        # Interpolate the calculated column
        model.add_interpolation_column(
            "x_squared_interp",
            x_column="x",
            y_column="x_squared"
        )
        
        result = model.get_column_data("x_squared_interp")
        expected = np.array([0, 1, 4, 9])
        np.testing.assert_array_almost_equal(result, expected)
    
    def test_with_range_column(self):
        """Test interpolation with range column."""
        model = DataTableModel()
        
        # Sparse data
        model.add_data_column("x_sparse", data=[0, 5, 10])
        model.add_data_column("y_sparse", data=[0, 50, 200])
        
        # Dense range
        model.add_range_column("x_dense", start=0, end=10, points=21)
        
        # Interpolate to dense grid
        model.add_interpolation_column(
            "y_dense",
            x_column="x_sparse",
            y_column="y_sparse",
            eval_column="x_dense",
            method="linear"
        )
        
        result = model.get_column_data("y_dense")
        assert len(result) == 21
        assert result.iloc[0] == pytest.approx(0.0)
        assert result.iloc[10] == pytest.approx(50.0)
        assert result.iloc[20] == pytest.approx(200.0)


class TestInterpolationEdgeCases:
    """Test edge cases for interpolation columns."""
    
    def test_with_nan_values(self):
        """Test that NaN values are handled correctly."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0.0, 1.0, np.nan, 3.0, 4.0])
        model.add_data_column("y", data=[0.0, 10.0, 20.0, np.nan, 40.0])
        
        # Should skip NaN values and interpolate remaining
        model.add_interpolation_column("y_interp", x_column="x", y_column="y")
        
        result = model.get_column_data("y_interp")
        
        # NaN positions should remain NaN in result
        assert np.isnan(result.iloc[2])
        assert np.isnan(result.iloc[3])
        
        # Valid positions should have values
        assert result.iloc[0] == pytest.approx(0.0)
        assert result.iloc[1] == pytest.approx(10.0)
        assert result.iloc[4] == pytest.approx(40.0)
    
    def test_metadata_properties(self):
        """Test that metadata is set correctly."""
        model = DataTableModel()
        
        # Use 4 points for cubic interpolation (minimum requirement)
        model.add_data_column("x", data=[0, 1, 2, 3])
        model.add_data_column("y", data=[0, 10, 20, 30], unit="m")
        
        model.add_interpolation_column(
            "y_interp",
            x_column="x",
            y_column="y",
            method="cubic",
            description="Test interpolation",
            precision=4
        )
        
        meta = model.get_column_metadata("y_interp")
        assert meta.column_type == ColumnType.INTERPOLATION
        assert meta.interp_x_column == "x"
        assert meta.interp_y_column == "y"
        assert meta.interp_method == "cubic"
        assert meta.unit == "m"
        assert meta.description == "Test interpolation"
        assert meta.precision == 4
        assert not meta.editable  # Interpolation columns are read-only
    
    def test_custom_precision(self):
        """Test custom display precision."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0, 1, 2])
        model.add_data_column("y", data=[0.123456789, 1.123456789, 2.123456789])
        
        model.add_interpolation_column(
            "y_interp",
            x_column="x",
            y_column="y",
            precision=2
        )
        
        meta = model.get_column_metadata("y_interp")
        assert meta.precision == 2


class TestEditInterpolationColumn:
    """Test editing interpolation column properties."""
    
    def test_edit_method(self):
        """Test changing interpolation method."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0, 1, 2, 3])
        model.add_data_column("y", data=[0, 1, 4, 9])
        
        model.add_interpolation_column("y_interp", x_column="x", y_column="y", method="linear")
        
        original = model.get_column_data("y_interp").copy()
        
        # Change to cubic
        model.edit_interpolation_column("y_interp", method="cubic")
        
        meta = model.get_column_metadata("y_interp")
        assert meta.interp_method == "cubic"
        
        # Values should have recalculated
        result = model.get_column_data("y_interp")
        # For quadratic data, cubic should match better than linear
        np.testing.assert_array_almost_equal(result, [0, 1, 4, 9])
    
    def test_edit_columns(self):
        """Test changing source columns."""
        model = DataTableModel()
        
        model.add_data_column("x1", data=[0, 1, 2])
        model.add_data_column("x2", data=[0, 1, 2])
        model.add_data_column("y1", data=[0, 10, 20])
        model.add_data_column("y2", data=[0, 5, 10])
        
        model.add_interpolation_column("interp", x_column="x1", y_column="y1")
        
        # Change to use different columns
        model.edit_interpolation_column("interp", x_column="x2", y_column="y2")
        
        meta = model.get_column_metadata("interp")
        assert meta.interp_x_column == "x2"
        assert meta.interp_y_column == "y2"
        
        # Values should reflect new Y column
        result = model.get_column_data("interp")
        np.testing.assert_array_almost_equal(result, [0, 5, 10])
    
    def test_rename(self):
        """Test renaming interpolation column."""
        model = DataTableModel()
        
        model.add_data_column("x", data=[0, 1, 2])
        model.add_data_column("y", data=[0, 10, 20])
        model.add_interpolation_column("old_name", x_column="x", y_column="y")
        
        model.edit_interpolation_column("old_name", new_name="new_name")
        
        assert "new_name" in model.get_column_names()
        assert "old_name" not in model.get_column_names()
