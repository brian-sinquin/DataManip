"""
Unit tests for PlotConfig.

Tests plot configuration dataclasses (AxisConfig, LegendConfig, PlotConfig).
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "src"))

import pytest
from widgets.plot_widget.plot_config import (
    AxisConfig, LegendConfig, PlotConfig,
    GridStyle, LegendLocation, AxisScale
)


class TestGridStyle:
    """Test GridStyle enum."""
    
    def test_grid_styles_exist(self):
        """Test that all expected grid styles exist."""
        assert GridStyle.NONE
        assert GridStyle.MAJOR
        assert GridStyle.MINOR
        assert GridStyle.BOTH
    
    def test_grid_style_values(self):
        """Test grid style values."""
        assert GridStyle.NONE.value == "none"
        assert GridStyle.MAJOR.value == "major"
        assert GridStyle.MINOR.value == "minor"
        assert GridStyle.BOTH.value == "both"


class TestLegendLocation:
    """Test LegendLocation enum."""
    
    def test_legend_locations_exist(self):
        """Test that common legend locations exist."""
        assert LegendLocation.BEST
        assert LegendLocation.UPPER_RIGHT
        assert LegendLocation.UPPER_LEFT
        assert LegendLocation.LOWER_LEFT
        assert LegendLocation.LOWER_RIGHT
        assert LegendLocation.CENTER
    
    def test_legend_location_values(self):
        """Test legend location values match matplotlib."""
        assert LegendLocation.BEST.value == "best"
        assert LegendLocation.UPPER_RIGHT.value == "upper right"
        assert LegendLocation.CENTER.value == "center"


class TestAxisScale:
    """Test AxisScale enum."""
    
    def test_axis_scales_exist(self):
        """Test that all expected axis scales exist."""
        assert AxisScale.LINEAR
        assert AxisScale.LOG
        assert AxisScale.SYMLOG
        assert AxisScale.LOGIT
    
    def test_axis_scale_values(self):
        """Test axis scale values."""
        assert AxisScale.LINEAR.value == "linear"
        assert AxisScale.LOG.value == "log"


class TestAxisConfig:
    """Test AxisConfig dataclass."""
    
    def test_basic_creation(self):
        """Test creating a basic axis config."""
        axis = AxisConfig()
        
        assert axis.label == ""
        assert axis.unit is None
        assert axis.scale == AxisScale.LINEAR
        assert axis.auto_range is True
        assert axis.invert is False
        assert axis.show_grid is True
    
    def test_with_label_and_unit(self):
        """Test axis with label and unit."""
        axis = AxisConfig(label="Time", unit="s")
        
        assert axis.label == "Time"
        assert axis.unit == "s"
        assert axis.get_full_label() == "Time [s]"
    
    def test_get_full_label_no_unit(self):
        """Test full label without unit."""
        axis = AxisConfig(label="Temperature")
        assert axis.get_full_label() == "Temperature"
    
    def test_get_full_label_unit_only(self):
        """Test full label with unit but no label."""
        axis = AxisConfig(unit="°C")
        assert axis.get_full_label() == "[°C]"
    
    def test_manual_range(self):
        """Test axis with manual range."""
        axis = AxisConfig(
            auto_range=False,
            min_value=0.0,
            max_value=10.0
        )
        
        assert axis.auto_range is False
        assert axis.min_value == 0.0
        assert axis.max_value == 10.0
    
    def test_log_scale(self):
        """Test axis with log scale."""
        axis = AxisConfig(scale=AxisScale.LOG)
        assert axis.scale == AxisScale.LOG
    
    def test_inverted_axis(self):
        """Test inverted axis."""
        axis = AxisConfig(invert=True)
        assert axis.invert is True
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        axis = AxisConfig(
            label="Pressure",
            unit="kPa",
            scale=AxisScale.LOG,
            auto_range=False,
            min_value=1.0,
            max_value=100.0
        )
        
        data = axis.to_dict()
        
        assert isinstance(data, dict)
        assert data['label'] == "Pressure"
        assert data['unit'] == "kPa"
        assert data['scale'] == "log"
        assert data['auto_range'] is False
        assert data['min_value'] == 1.0
        assert data['max_value'] == 100.0
    
    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            'label': "Temperature",
            'unit': "K",
            'scale': "linear",
            'auto_range': True
        }
        
        axis = AxisConfig.from_dict(data)
        
        assert axis.label == "Temperature"
        assert axis.unit == "K"
        assert axis.scale == AxisScale.LINEAR
        assert axis.auto_range is True


class TestLegendConfig:
    """Test LegendConfig dataclass."""
    
    def test_basic_creation(self):
        """Test creating a basic legend config."""
        legend = LegendConfig()
        
        assert legend.show is True
        assert legend.location == LegendLocation.BEST
        assert legend.frameon is True
        assert legend.frame_alpha == 0.9
        assert legend.shadow is False
        assert legend.ncol == 1
        assert legend.fontsize == 10
    
    def test_custom_location(self):
        """Test legend with custom location."""
        legend = LegendConfig(location=LegendLocation.UPPER_LEFT)
        assert legend.location == LegendLocation.UPPER_LEFT
    
    def test_multi_column_legend(self):
        """Test legend with multiple columns."""
        legend = LegendConfig(ncol=3)
        assert legend.ncol == 3
    
    def test_legend_with_title(self):
        """Test legend with title."""
        legend = LegendConfig(title="Data Series")
        assert legend.title == "Data Series"
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        legend = LegendConfig(
            show=True,
            location=LegendLocation.LOWER_RIGHT,
            ncol=2,
            fontsize=12
        )
        
        data = legend.to_dict()
        
        assert data['show'] is True
        assert data['location'] == "lower right"
        assert data['ncol'] == 2
        assert data['fontsize'] == 12
    
    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            'show': False,
            'location': "upper right",
            'ncol': 1
        }
        
        legend = LegendConfig.from_dict(data)
        
        assert legend.show is False
        assert legend.location == LegendLocation.UPPER_RIGHT
        assert legend.ncol == 1


class TestPlotConfig:
    """Test PlotConfig dataclass."""
    
    def test_basic_creation(self):
        """Test creating a basic plot config."""
        config = PlotConfig()
        
        assert config.title == ""
        assert config.title_fontsize == 14
        assert isinstance(config.x_axis, AxisConfig)
        assert isinstance(config.y_axis, AxisConfig)
        assert isinstance(config.legend, LegendConfig)
        assert config.grid_style == GridStyle.MAJOR
        assert config.figure_width == 8.0
        assert config.figure_height == 6.0
        assert config.dpi == 100
    
    def test_default_axis_labels(self):
        """Test that default axes have appropriate labels."""
        config = PlotConfig()
        
        assert config.x_axis.label == "X-axis"
        assert config.y_axis.label == "Y-axis"
    
    def test_custom_title(self):
        """Test plot with custom title."""
        config = PlotConfig(title="My Plot", title_fontsize=16)
        
        assert config.title == "My Plot"
        assert config.title_fontsize == 16
    
    def test_get_figure_size(self):
        """Test get_figure_size method."""
        config = PlotConfig(figure_width=10.0, figure_height=8.0)
        
        size = config.get_figure_size()
        
        assert size == (10.0, 8.0)
        assert isinstance(size, tuple)
    
    def test_custom_grid_style(self):
        """Test plot with custom grid style."""
        config = PlotConfig(grid_style=GridStyle.BOTH)
        assert config.grid_style == GridStyle.BOTH
    
    def test_export_settings(self):
        """Test export-related settings."""
        config = PlotConfig(
            export_dpi=300,
            export_format="pdf"
        )
        
        assert config.export_dpi == 300
        assert config.export_format == "pdf"
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        config = PlotConfig(
            title="Test Plot",
            figure_width=12.0,
            figure_height=9.0,
            dpi=150
        )
        
        data = config.to_dict()
        
        assert isinstance(data, dict)
        assert data['title'] == "Test Plot"
        assert data['figure_width'] == 12.0
        assert data['figure_height'] == 9.0
        assert data['dpi'] == 150
        assert 'x_axis' in data
        assert 'y_axis' in data
        assert 'legend' in data
    
    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            'title': "Restored Plot",
            'title_fontsize': 18,
            'x_axis': {
                'label': "Time",
                'unit': "s",
                'scale': "linear"
            },
            'y_axis': {
                'label': "Position",
                'unit': "m",
                'scale': "linear"
            },
            'legend': {
                'show': True,
                'location': "best"
            },
            'grid_style': "major",
            'figure_width': 10.0,
            'figure_height': 7.0
        }
        
        config = PlotConfig.from_dict(data)
        
        assert config.title == "Restored Plot"
        assert config.title_fontsize == 18
        assert config.x_axis.label == "Time"
        assert config.x_axis.unit == "s"
        assert config.y_axis.label == "Position"
        assert config.y_axis.unit == "m"
        assert config.legend.show is True
        assert config.grid_style == GridStyle.MAJOR
    
    def test_tight_layout(self):
        """Test tight layout setting."""
        config = PlotConfig(tight_layout=False)
        assert config.tight_layout is False
    
    def test_background_color(self):
        """Test background color setting."""
        config = PlotConfig(background_color="#f0f0f0")
        assert config.background_color == "#f0f0f0"
