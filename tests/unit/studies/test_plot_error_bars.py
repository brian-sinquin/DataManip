"""Tests for plot error bar functionality."""

import pytest
import numpy as np
from matplotlib.figure import Figure

from core.workspace import Workspace
from studies.data_table_study import DataTableStudy, ColumnType
from studies.plot_study import PlotStudy


def test_add_series_with_error_bars():
    """Test adding series with error bar columns."""
    workspace = Workspace("test", "numerical")
    
    # Create data table with data and uncertainty columns
    data_study = DataTableStudy("data", workspace)
    data_study.add_column("x", ColumnType.DATA)
    data_study.add_column("y", ColumnType.DATA)
    data_study.add_column("x_err", ColumnType.DATA)
    data_study.add_column("y_err", ColumnType.DATA)
    
    # Add some data
    data_study.add_rows(5)
    x_values = [1.0, 2.0, 3.0, 4.0, 5.0]
    y_values = [2.0, 4.0, 6.0, 8.0, 10.0]
    x_err_values = [0.1, 0.15, 0.1, 0.2, 0.15]
    y_err_values = [0.2, 0.3, 0.25, 0.4, 0.35]
    
    for i in range(5):
        data_study.table.data.loc[i, "x"] = x_values[i]
        data_study.table.data.loc[i, "y"] = y_values[i]
        data_study.table.data.loc[i, "x_err"] = x_err_values[i]
        data_study.table.data.loc[i, "y_err"] = y_err_values[i]
    
    workspace.add_study(data_study)
    
    # Create plot study
    plot_study = PlotStudy("plot", workspace)
    
    # Add series with error bars
    plot_study.add_series(
        study_name="data",
        x_column="x",
        y_column="y",
        xerr_column="x_err",
        yerr_column="y_err",
        label="Data with errors",
        style="both"
    )
    
    assert len(plot_study.series) == 1
    series = plot_study.series[0]
    assert series["xerr_col"] == "x_err"
    assert series["yerr_col"] == "y_err"


def test_get_data_for_series_with_errors():
    """Test retrieving data with error bars."""
    workspace = Workspace("test", "numerical")
    
    # Create data table
    data_study = DataTableStudy("data", workspace)
    data_study.add_column("x", ColumnType.DATA)
    data_study.add_column("y", ColumnType.DATA)
    data_study.add_column("x_err", ColumnType.DATA)
    data_study.add_column("y_err", ColumnType.DATA)
    
    data_study.add_rows(3)
    for i in range(3):
        data_study.table.data.loc[i, "x"] = float(i)
        data_study.table.data.loc[i, "y"] = float(i * 2)
        data_study.table.data.loc[i, "x_err"] = 0.1
        data_study.table.data.loc[i, "y_err"] = 0.2
    
    workspace.add_study(data_study)
    
    # Create plot with error bars
    plot_study = PlotStudy("plot", workspace)
    plot_study.add_series(
        study_name="data",
        x_column="x",
        y_column="y",
        xerr_column="x_err",
        yerr_column="y_err"
    )
    
    # Get data for series
    result = plot_study.get_data_for_series(0)
    assert result is not None
    
    x_data, y_data, x_label, y_label, x_err, y_err = result
    
    # Check data arrays
    assert len(x_data) == 3
    assert len(y_data) == 3
    assert x_err is not None
    assert y_err is not None
    assert len(x_err) == 3
    assert len(y_err) == 3
    
    # Check error values
    np.testing.assert_array_almost_equal(x_err, [0.1, 0.1, 0.1])
    np.testing.assert_array_almost_equal(y_err, [0.2, 0.2, 0.2])


def test_get_data_without_errors():
    """Test retrieving data without error bars (backward compatibility)."""
    workspace = Workspace("test", "numerical")
    
    data_study = DataTableStudy("data", workspace)
    data_study.add_column("x", ColumnType.DATA)
    data_study.add_column("y", ColumnType.DATA)
    data_study.add_rows(2)
    
    workspace.add_study(data_study)
    
    plot_study = PlotStudy("plot", workspace)
    plot_study.add_series(
        study_name="data",
        x_column="x",
        y_column="y"
    )
    
    result = plot_study.get_data_for_series(0)
    assert result is not None
    
    x_data, y_data, x_label, y_label, x_err, y_err = result
    
    # No error bars specified
    assert x_err is None
    assert y_err is None


def test_plot_with_x_error_only():
    """Test plotting with only X error bars."""
    workspace = Workspace("test", "numerical")
    
    data_study = DataTableStudy("data", workspace)
    data_study.add_column("x", ColumnType.DATA)
    data_study.add_column("y", ColumnType.DATA)
    data_study.add_column("x_err", ColumnType.DATA)
    
    data_study.add_rows(3)
    for i in range(3):
        data_study.table.data.loc[i, "x"] = float(i)
        data_study.table.data.loc[i, "y"] = float(i * 2)
        data_study.table.data.loc[i, "x_err"] = 0.1
    
    workspace.add_study(data_study)
    
    plot_study = PlotStudy("plot", workspace)
    plot_study.add_series(
        study_name="data",
        x_column="x",
        y_column="y",
        xerr_column="x_err"
    )
    
    result = plot_study.get_data_for_series(0)
    assert result is not None
    
    x_data, y_data, x_label, y_label, x_err, y_err = result
    assert x_err is not None
    assert y_err is None


def test_plot_with_y_error_only():
    """Test plotting with only Y error bars."""
    workspace = Workspace("test", "numerical")
    
    data_study = DataTableStudy("data", workspace)
    data_study.add_column("x", ColumnType.DATA)
    data_study.add_column("y", ColumnType.DATA)
    data_study.add_column("y_err", ColumnType.DATA)
    
    data_study.add_rows(3)
    for i in range(3):
        data_study.table.data.loc[i, "x"] = float(i)
        data_study.table.data.loc[i, "y"] = float(i * 2)
        data_study.table.data.loc[i, "y_err"] = 0.2
    
    workspace.add_study(data_study)
    
    plot_study = PlotStudy("plot", workspace)
    plot_study.add_series(
        study_name="data",
        x_column="x",
        y_column="y",
        yerr_column="y_err"
    )
    
    result = plot_study.get_data_for_series(0)
    assert result is not None
    
    x_data, y_data, x_label, y_label, x_err, y_err = result
    assert x_err is None
    assert y_err is not None


def test_update_plot_with_error_bars():
    """Test that plot updates correctly with error bars."""
    workspace = Workspace("test", "numerical")
    
    # Create data with uncertainties
    data_study = DataTableStudy("data", workspace)
    data_study.add_column("x", ColumnType.DATA)
    data_study.add_column("y", ColumnType.DATA)
    data_study.add_column("y_err", ColumnType.DATA)
    
    data_study.add_rows(4)
    for i in range(4):
        data_study.table.data.loc[i, "x"] = float(i)
        data_study.table.data.loc[i, "y"] = float(i ** 2)
        data_study.table.data.loc[i, "y_err"] = 0.5
    
    workspace.add_study(data_study)
    
    # Create plot
    plot_study = PlotStudy("plot", workspace)
    plot_study.add_series(
        study_name="data",
        x_column="x",
        y_column="y",
        yerr_column="y_err",
        style="both"
    )
    
    # Update plot
    figure = Figure()
    plot_study.update_plot(figure)
    
    # Verify plot has content
    ax = figure.axes[0]
    assert len(ax.lines) > 0 or len(ax.collections) > 0  # Has plotted data


def test_error_bars_serialization():
    """Test that error bar columns are preserved in to_dict/from_dict."""
    workspace = Workspace("test", "numerical")
    
    plot_study = PlotStudy("plot", workspace)
    plot_study.add_series(
        study_name="data",
        x_column="x",
        y_column="y",
        xerr_column="x_err",
        yerr_column="y_err"
    )
    
    # Serialize
    data = plot_study.to_dict()
    
    # Check serialization
    assert len(data["series"]) == 1
    series = data["series"][0]
    assert series["xerr_col"] == "x_err"
    assert series["yerr_col"] == "y_err"
    
    # Deserialize
    restored = PlotStudy.from_dict(data, workspace)
    assert len(restored.series) == 1
    restored_series = restored.series[0]
    assert restored_series["xerr_col"] == "x_err"
    assert restored_series["yerr_col"] == "y_err"


def test_invalid_error_column():
    """Test handling of non-existent error column."""
    workspace = Workspace("test", "numerical")
    
    data_study = DataTableStudy("data", workspace)
    data_study.add_column("x", ColumnType.DATA)
    data_study.add_column("y", ColumnType.DATA)
    data_study.add_rows(2)
    
    workspace.add_study(data_study)
    
    plot_study = PlotStudy("plot", workspace)
    plot_study.add_series(
        study_name="data",
        x_column="x",
        y_column="y",
        xerr_column="nonexistent",  # Invalid column
        yerr_column="also_invalid"
    )
    
    # Should return None for invalid error columns
    result = plot_study.get_data_for_series(0)
    assert result is not None
    
    x_data, y_data, x_label, y_label, x_err, y_err = result
    assert x_err is None  # Invalid column should be None
    assert y_err is None
