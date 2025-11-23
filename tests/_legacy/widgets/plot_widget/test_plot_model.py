"""
Unit tests for PlotModel.

Tests the plot model for series management, configuration, and data extraction.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "src"))

import pytest
import numpy as np
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject

from widgets import DataTableWidget
from widgets.plot_widget.plot_model import PlotModel
from widgets.plot_widget.series_metadata import SeriesMetadata, PlotStyle
from widgets.plot_widget.plot_config import PlotConfig, AxisScale


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def datatable(qapp):
    """Create a DataTableWidget with sample data."""
    dt = DataTableWidget()
    model = dt.model()
    
    # Add columns with data
    model.add_data_column("time", unit="s", data=[0.0, 1.0, 2.0, 3.0, 4.0])
    model.add_data_column("position", unit="m", data=[0.0, 5.0, 20.0, 45.0, 80.0])
    model.add_data_column("velocity", unit="m/s", data=[0.0, 10.0, 20.0, 30.0, 40.0])
    
    # Add uncertainty column
    model.add_uncertainty_column("position")
    
    return dt


@pytest.fixture
def plot_model(datatable):
    """Create a PlotModel with datatable."""
    return PlotModel(datatable=datatable)


class TestPlotModelInit:
    """Test PlotModel initialization."""
    
    def test_create_without_datatable(self, qapp):
        """Test creating model without datatable."""
        model = PlotModel()
        
        assert model._datatable is None
        assert len(model.get_series_names()) == 0
        assert isinstance(model.get_config(), PlotConfig)
    
    def test_create_with_datatable(self, plot_model, datatable):
        """Test creating model with datatable."""
        assert plot_model._datatable is datatable
        assert len(plot_model.get_series_names()) == 0


class TestSeriesManagement:
    """Test series add/remove/update operations."""
    
    def test_add_series(self, plot_model):
        """Test adding a series."""
        series = SeriesMetadata(
            name="Test Series",
            x_column="time",
            y_column="position"
        )
        
        plot_model.add_series(series)
        
        assert plot_model.has_series("Test Series")
        assert plot_model.series_count() == 1
        assert "Test Series" in plot_model.get_series_names()
    
    def test_add_series_emits_signal(self, plot_model, qapp):
        """Test that adding series emits signal."""
        signal_received = []
        
        plot_model.seriesAdded.connect(lambda name: signal_received.append(name))
        
        series = SeriesMetadata(name="Test", x_column="time", y_column="position")
        plot_model.add_series(series)
        
        assert len(signal_received) == 1
        assert signal_received[0] == "Test"
    
    def test_add_duplicate_series_raises_error(self, plot_model):
        """Test that adding duplicate series raises error."""
        series1 = SeriesMetadata(name="Test", x_column="time", y_column="position")
        plot_model.add_series(series1)
        
        series2 = SeriesMetadata(name="Test", x_column="time", y_column="velocity")
        
        with pytest.raises(ValueError, match="already exists"):
            plot_model.add_series(series2)
    
    def test_add_series_with_invalid_columns_raises_error(self, plot_model):
        """Test that adding series with invalid columns raises error."""
        series = SeriesMetadata(
            name="Test",
            x_column="nonexistent",
            y_column="position"
        )
        
        with pytest.raises(ValueError, match="Invalid columns"):
            plot_model.add_series(series)
    
    def test_remove_series(self, plot_model):
        """Test removing a series."""
        series = SeriesMetadata(name="Test", x_column="time", y_column="position")
        plot_model.add_series(series)
        
        assert plot_model.has_series("Test")
        
        plot_model.remove_series("Test")
        
        assert not plot_model.has_series("Test")
        assert plot_model.series_count() == 0
    
    def test_remove_nonexistent_series_raises_error(self, plot_model):
        """Test that removing nonexistent series raises error."""
        with pytest.raises(KeyError, match="not found"):
            plot_model.remove_series("Nonexistent")
    
    def test_remove_series_emits_signal(self, plot_model, qapp):
        """Test that removing series emits signal."""
        signal_received = []
        
        series = SeriesMetadata(name="Test", x_column="time", y_column="position")
        plot_model.add_series(series)
        
        plot_model.seriesRemoved.connect(lambda name: signal_received.append(name))
        plot_model.remove_series("Test")
        
        assert len(signal_received) == 1
        assert signal_received[0] == "Test"
    
    def test_update_series(self, plot_model):
        """Test updating a series."""
        original = SeriesMetadata(
            name="Test",
            x_column="time",
            y_column="position",
            color="#ff0000"
        )
        plot_model.add_series(original)
        
        updated = SeriesMetadata(
            name="Test",
            x_column="time",
            y_column="velocity",
            color="#00ff00"
        )
        plot_model.update_series("Test", updated)
        
        result = plot_model.get_series("Test")
        assert result.y_column == "velocity"
        assert result.color == "#00ff00"
    
    def test_update_series_rename(self, plot_model):
        """Test updating series with name change."""
        original = SeriesMetadata(name="Old", x_column="time", y_column="position")
        plot_model.add_series(original)
        
        updated = SeriesMetadata(name="New", x_column="time", y_column="position")
        plot_model.update_series("Old", updated)
        
        assert not plot_model.has_series("Old")
        assert plot_model.has_series("New")
    
    def test_get_series(self, plot_model):
        """Test getting series by name."""
        series = SeriesMetadata(name="Test", x_column="time", y_column="position")
        plot_model.add_series(series)
        
        result = plot_model.get_series("Test")
        
        assert result.name == "Test"
        assert result.x_column == "time"
        assert result.y_column == "position"
    
    def test_get_all_series(self, plot_model):
        """Test getting all series."""
        series1 = SeriesMetadata(name="Series1", x_column="time", y_column="position")
        series2 = SeriesMetadata(name="Series2", x_column="time", y_column="velocity", use_secondary_y_axis=True)
        plot_model.add_series(series1)
        plot_model.add_series(series2)
        all_series = plot_model.get_all_series()
        assert len(all_series) == 2
        assert all_series[0].name == "Series1"
        assert all_series[1].name == "Series2"
    
    def test_clear_all_series(self, plot_model):
        """Test clearing all series."""
        series1 = SeriesMetadata(name="Series1", x_column="time", y_column="position")
        series2 = SeriesMetadata(name="Series2", x_column="time", y_column="velocity", use_secondary_y_axis=True)
        plot_model.add_series(series1)
        plot_model.add_series(series2)
        assert plot_model.series_count() == 2
        plot_model.clear_all_series()
        assert plot_model.series_count() == 0


class TestDataExtraction:
    """Test data extraction from datatable."""
    
    def test_get_series_data(self, plot_model):
        """Test extracting data for a series."""
        series = SeriesMetadata(name="Test", x_column="time", y_column="position")
        plot_model.add_series(series)
        
        x_data, y_data, x_error, y_error = plot_model.get_series_data("Test")
        
        assert isinstance(x_data, np.ndarray)
        assert isinstance(y_data, np.ndarray)
        assert len(x_data) == 5
        assert len(y_data) == 5
        np.testing.assert_array_equal(x_data, [0.0, 1.0, 2.0, 3.0, 4.0])
        np.testing.assert_array_equal(y_data, [0.0, 5.0, 20.0, 45.0, 80.0])
    
    def test_get_series_data_with_errors(self, plot_model, datatable):
        """Test extracting data with error bars."""
        series = SeriesMetadata(
            name="Test",
            x_column="time",
            y_column="position",
            y_error_column="position_u"
        )
        plot_model.add_series(series)
        
        x_data, y_data, x_error, y_error = plot_model.get_series_data("Test")
        
        # Should get data even if uncertainty column has no values yet
        assert x_error is None
        assert isinstance(y_data, np.ndarray)
        # y_error will be None or array depending on whether uncertainty exists
        if y_error is not None:
            assert isinstance(y_error, np.ndarray)
    
    def test_get_all_series_data(self, plot_model):
        """Test extracting data for all series."""
        series1 = SeriesMetadata(name="Series1", x_column="time", y_column="position")
        series2 = SeriesMetadata(name="Series2", x_column="time", y_column="velocity", use_secondary_y_axis=True)
        plot_model.add_series(series1)
        plot_model.add_series(series2)
        all_data = plot_model.get_all_series_data()
        assert len(all_data) == 2
        assert all_data[0][0] == "Series1"  # series name
        assert len(all_data[0][1]) == 5  # x_data
        assert len(all_data[0][2]) == 5  # y_data

    def test_get_all_series_data_respects_visibility(self, plot_model):
        """Test that invisible series are excluded."""
        series1 = SeriesMetadata(name="Visible", x_column="time", y_column="position")
        series2 = SeriesMetadata(
            name="Hidden",
            x_column="time",
            y_column="velocity",
            visible=False,
            use_secondary_y_axis=True
        )
        plot_model.add_series(series1)
        plot_model.add_series(series2)
        all_data = plot_model.get_all_series_data()
        assert len(all_data) == 1
        assert all_data[0][0] == "Visible"


class TestConfiguration:
    """Test configuration management."""
    
    def test_get_config(self, plot_model):
        """Test getting configuration."""
        config = plot_model.get_config()
        
        assert isinstance(config, PlotConfig)
        assert config.x_axis.label == "X-axis"
        assert config.y_axis.label == "Y-axis"
    
    def test_set_config(self, plot_model, qapp):
        """Test setting entire configuration."""
        signal_received = []
        plot_model.configUpdated.connect(lambda: signal_received.append(True))
        
        new_config = PlotConfig(title="New Title", figure_width=12.0)
        plot_model.set_config(new_config)
        
        assert plot_model.get_config().title == "New Title"
        assert plot_model.get_config().figure_width == 12.0
        assert len(signal_received) == 1
    
    def test_update_config(self, plot_model):
        """Test updating specific config attributes."""
        plot_model.update_config(title="Updated Title", dpi=150)
        
        config = plot_model.get_config()
        assert config.title == "Updated Title"
        assert config.dpi == 150
    
    def test_update_x_axis(self, plot_model):
        """Test updating X-axis config."""
        plot_model.update_x_axis(label="Time", unit="s", scale=AxisScale.LOG)
        
        config = plot_model.get_config()
        assert config.x_axis.label == "Time"
        assert config.x_axis.unit == "s"
        assert config.x_axis.scale == AxisScale.LOG
    
    def test_update_y_axis(self, plot_model):
        """Test updating Y-axis config."""
        plot_model.update_y_axis(label="Position", unit="m")
        
        config = plot_model.get_config()
        assert config.y_axis.label == "Position"
        assert config.y_axis.unit == "m"
    
    def test_update_legend(self, plot_model):
        """Test updating legend config."""
        plot_model.update_legend(show=False, ncol=2)
        
        config = plot_model.get_config()
        assert config.legend.show is False
        assert config.legend.ncol == 2


class TestAutoConfiguration:
    """Test automatic configuration from data."""
    
    def test_auto_set_axis_units_on_first_series(self, plot_model):
        """Test that axis units are auto-set when adding first series."""
        series = SeriesMetadata(name="Test", x_column="time", y_column="position")
        plot_model.add_series(series)
        
        config = plot_model.get_config()
        
        assert config.x_axis.label == "time"
        assert config.x_axis.unit == "s"
        assert config.y_axis.label == "position"
        assert config.y_axis.unit == "m"
    
    def test_auto_configure_axes(self, plot_model):
        """Test manual auto-configure from first series."""
        series = SeriesMetadata(name="Test", x_column="time", y_column="velocity")
        plot_model.add_series(series)
        
        # Manually call auto-configure (updates to existing series columns)
        plot_model.auto_configure_axes()
        
        config = plot_model.get_config()
        assert config.x_axis.label == "time"
        assert config.y_axis.label == "velocity"
        assert config.y_axis.unit == "m/s"
    
    def test_suggest_series_name(self, plot_model):
        """Test series name suggestion."""
        name = plot_model.suggest_series_name("position", "time")
        
        assert name == "position vs time"
    
    def test_suggest_series_name_avoids_duplicates(self, plot_model):
        """Test that suggested names avoid duplicates."""
        series1 = SeriesMetadata(
            name="position vs time",
            x_column="time",
            y_column="position"
        )
        plot_model.add_series(series1)
        
        name = plot_model.suggest_series_name("position", "time")
        
        assert name == "position vs time (2)"


class TestUtilities:
    """Test utility methods."""
    
    def test_get_available_columns(self, plot_model):
        """Test getting available columns."""
        columns = plot_model.get_available_columns()
        
        assert len(columns) >= 3
        # Check format is (column_name, display_text)
        assert all(isinstance(col, tuple) and len(col) == 2 for col in columns)
        
        # Find time column
        time_col = [col for col in columns if col[0] == "time"]
        assert len(time_col) == 1
        assert "s" in time_col[0][1]  # Display text includes unit


class TestSerialization:
    """Test serialization and deserialization."""
    
    def test_to_dict(self, plot_model):
        """Test converting model to dictionary."""
        series = SeriesMetadata(name="Test", x_column="time", y_column="position")
        plot_model.add_series(series)
        plot_model.update_config(title="Test Plot")
        
        data = plot_model.to_dict()
        
        assert isinstance(data, dict)
        assert 'series' in data
        assert 'config' in data
        assert len(data['series']) == 1
        assert data['config']['title'] == "Test Plot"
    
    def test_from_dict(self, datatable):
        """Test creating model from dictionary."""
        data = {
            'series': [
                {
                    'name': "Test Series",
                    'x_column': "time",
                    'y_column': "position",
                    'plot_style': "line",
                    'color': "#ff0000"
                }
            ],
            'config': {
                'title': "Restored Plot",
                'x_axis': {'label': "Time", 'unit': "s", 'scale': "linear"},
                'y_axis': {'label': "Position", 'unit': "m", 'scale': "linear"},
                'legend': {'show': True, 'location': "best"},
                'grid_style': "major"
            }
        }
        
        model = PlotModel.from_dict(data, datatable=datatable)
        
        assert model.series_count() == 1
        assert model.has_series("Test Series")
        assert model.get_config().title == "Restored Plot"


class TestDataTableEvents:
    """Test responses to datatable changes."""
    
    def test_column_removed_removes_dependent_series(self, plot_model, datatable, qapp):
        """Test that series are removed when their columns are deleted."""
        series = SeriesMetadata(name="Test", x_column="time", y_column="position")
        plot_model.add_series(series)
        
        assert plot_model.has_series("Test")
        
        # Remove position column
        datatable.model().remove_column("position")
        
        # Series should be removed
        assert not plot_model.has_series("Test")
    
    def test_column_renamed_updates_series(self, plot_model, datatable, qapp):
        """Test that series are updated when columns are renamed."""
        series = SeriesMetadata(name="Test", x_column="time", y_column="position")
        plot_model.add_series(series)
        
        # Rename position to location
        datatable.model().rename_column("position", "location")
        
        # Series should still exist with updated column name
        assert plot_model.has_series("Test")
        updated_series = plot_model.get_series("Test")
        assert updated_series.y_column == "location"
