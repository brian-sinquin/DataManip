"""
Unit tests for SeriesMetadata.

Tests the series metadata dataclass and style configuration.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "src"))

import pytest
from widgets.plot_widget.series_metadata import (
    SeriesMetadata, PlotStyle, MarkerStyle, LineStyle,
    get_default_color, DEFAULT_COLORS
)


class TestPlotStyle:
    """Test PlotStyle enum."""
    
    def test_plot_styles_exist(self):
        """Test that all expected plot styles exist."""
        assert PlotStyle.LINE
        assert PlotStyle.SCATTER
        assert PlotStyle.LINE_SCATTER
        assert PlotStyle.BAR
        assert PlotStyle.STEP
        assert PlotStyle.ERRORBAR
    
    def test_plot_style_values(self):
        """Test that plot styles have correct string values."""
        assert PlotStyle.LINE.value == "line"
        assert PlotStyle.SCATTER.value == "scatter"
        assert PlotStyle.LINE_SCATTER.value == "line+scatter"
        assert PlotStyle.BAR.value == "bar"


class TestMarkerStyle:
    """Test MarkerStyle enum."""
    
    def test_marker_styles_exist(self):
        """Test that all expected marker styles exist."""
        assert MarkerStyle.CIRCLE
        assert MarkerStyle.SQUARE
        assert MarkerStyle.TRIANGLE
        assert MarkerStyle.DIAMOND
        assert MarkerStyle.PLUS
        assert MarkerStyle.CROSS
        assert MarkerStyle.STAR
        assert MarkerStyle.NONE
    
    def test_marker_style_values(self):
        """Test marker style matplotlib codes."""
        assert MarkerStyle.CIRCLE.value == "o"
        assert MarkerStyle.SQUARE.value == "s"
        assert MarkerStyle.TRIANGLE.value == "^"
        assert MarkerStyle.DIAMOND.value == "D"


class TestLineStyle:
    """Test LineStyle enum."""
    
    def test_line_styles_exist(self):
        """Test that all expected line styles exist."""
        assert LineStyle.SOLID
        assert LineStyle.DASHED
        assert LineStyle.DOTTED
        assert LineStyle.DASHDOT
        assert LineStyle.NONE
    
    def test_line_style_values(self):
        """Test line style matplotlib codes."""
        assert LineStyle.SOLID.value == "-"
        assert LineStyle.DASHED.value == "--"
        assert LineStyle.DOTTED.value == ":"
        assert LineStyle.DASHDOT.value == "-."


class TestSeriesMetadata:
    """Test SeriesMetadata dataclass."""
    
    def test_basic_creation(self):
        """Test creating a basic series."""
        series = SeriesMetadata(
            name="Test Series",
            x_column="time",
            y_column="position"
        )
        
        assert series.name == "Test Series"
        assert series.x_column == "time"
        assert series.y_column == "position"
        assert series.x_error_column is None
        assert series.y_error_column is None
        assert series.visible is True
    
    def test_default_style_values(self):
        """Test that default style values are set correctly."""
        series = SeriesMetadata(
            name="Test",
            x_column="x",
            y_column="y"
        )
        
        assert series.plot_style == PlotStyle.LINE_SCATTER
        assert series.color == "#1f77b4"  # Default matplotlib blue
        assert series.line_style == LineStyle.SOLID
        assert series.line_width == 2.0
        assert series.marker_style == MarkerStyle.CIRCLE
        assert series.marker_size == 6.0
        assert series.alpha == 1.0
    
    def test_with_error_bars(self):
        """Test series with error columns."""
        series = SeriesMetadata(
            name="Test",
            x_column="x",
            y_column="y",
            x_error_column="x_u",
            y_error_column="y_u",
            show_error_bars=True
        )
        
        assert series.x_error_column == "x_u"
        assert series.y_error_column == "y_u"
        assert series.show_error_bars is True
        assert series.has_error_bars() is True
    
    def test_has_error_bars(self):
        """Test has_error_bars() method."""
        # No error columns
        series1 = SeriesMetadata(name="Test", x_column="x", y_column="y")
        assert series1.has_error_bars() is False
        
        # Has error columns but disabled
        series2 = SeriesMetadata(
            name="Test", x_column="x", y_column="y",
            y_error_column="y_u", show_error_bars=False
        )
        assert series2.has_error_bars() is False
        
        # Has error columns and enabled
        series3 = SeriesMetadata(
            name="Test", x_column="x", y_column="y",
            y_error_column="y_u", show_error_bars=True
        )
        assert series3.has_error_bars() is True
    
    def test_get_matplotlib_format(self):
        """Test matplotlib format string generation."""
        # Line only
        series1 = SeriesMetadata(
            name="Test", x_column="x", y_column="y",
            plot_style=PlotStyle.LINE,
            line_style=LineStyle.DASHED
        )
        assert series1.get_matplotlib_format() == "--"
        
        # Scatter only
        series2 = SeriesMetadata(
            name="Test", x_column="x", y_column="y",
            plot_style=PlotStyle.SCATTER,
            marker_style=MarkerStyle.SQUARE
        )
        assert series2.get_matplotlib_format() == "s"
        
        # Line + scatter
        series3 = SeriesMetadata(
            name="Test", x_column="x", y_column="y",
            plot_style=PlotStyle.LINE_SCATTER,
            marker_style=MarkerStyle.CIRCLE,
            line_style=LineStyle.SOLID
        )
        assert series3.get_matplotlib_format() == "o-"
    
    def test_get_marker_edge_color(self):
        """Test marker edge color resolution."""
        # Auto (uses series color)
        series1 = SeriesMetadata(
            name="Test", x_column="x", y_column="y",
            color="#ff0000", marker_edge_color="auto"
        )
        assert series1.get_marker_edge_color() == "#ff0000"
        
        # Custom color
        series2 = SeriesMetadata(
            name="Test", x_column="x", y_column="y",
            color="#ff0000", marker_edge_color="#0000ff"
        )
        assert series2.get_marker_edge_color() == "#0000ff"
    
    def test_legend_label(self):
        """Test legend label handling."""
        # Default (uses series name)
        series1 = SeriesMetadata(
            name="My Series", x_column="x", y_column="y"
        )
        assert series1.legend_label == "My Series"
        
        # Custom label
        series2 = SeriesMetadata(
            name="My Series", x_column="x", y_column="y",
            legend_label="Custom Label"
        )
        assert series2.legend_label == "Custom Label"
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        series = SeriesMetadata(
            name="Test",
            x_column="time",
            y_column="position",
            color="#ff0000"
        )
        
        data = series.to_dict()
        
        assert isinstance(data, dict)
        assert data['name'] == "Test"
        assert data['x_column'] == "time"
        assert data['y_column'] == "position"
        assert data['color'] == "#ff0000"
        assert data['plot_style'] == "line+scatter"
    
    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            'name': "Test",
            'x_column': "time",
            'y_column': "position",
            'plot_style': "line",
            'color': "#00ff00"
        }
        
        series = SeriesMetadata.from_dict(data)
        
        assert series.name == "Test"
        assert series.x_column == "time"
        assert series.y_column == "position"
        assert series.plot_style == PlotStyle.LINE
        assert series.color == "#00ff00"
    
    def test_enum_string_conversion(self):
        """Test that enum strings are converted on init."""
        series = SeriesMetadata(
            name="Test",
            x_column="x",
            y_column="y",
            plot_style="scatter",
            line_style="--",
            marker_style="^"
        )
        
        assert series.plot_style == PlotStyle.SCATTER
        assert series.line_style == LineStyle.DASHED
        assert series.marker_style == MarkerStyle.TRIANGLE


class TestDefaultColors:
    """Test default color utilities."""
    
    def test_default_colors_list(self):
        """Test that DEFAULT_COLORS has expected length."""
        assert len(DEFAULT_COLORS) == 10
        assert all(isinstance(c, str) for c in DEFAULT_COLORS)
        assert all(c.startswith('#') for c in DEFAULT_COLORS)
    
    def test_get_default_color(self):
        """Test get_default_color function."""
        # First 10 colors
        for i in range(10):
            color = get_default_color(i)
            assert color == DEFAULT_COLORS[i]
        
        # Wraps around after 10
        assert get_default_color(10) == DEFAULT_COLORS[0]
        assert get_default_color(11) == DEFAULT_COLORS[1]
        assert get_default_color(25) == DEFAULT_COLORS[5]  # 25 % 10 = 5
