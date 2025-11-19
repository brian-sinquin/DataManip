"""
Series metadata for plot widget.

This module defines metadata for plot series, including style, markers,
error bars, and legend configuration.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from PySide6.QtGui import QColor


class PlotStyle(Enum):
    """Plot style types."""
    LINE = "line"
    SCATTER = "scatter"
    LINE_SCATTER = "line+scatter"
    BAR = "bar"
    STEP = "step"
    ERRORBAR = "errorbar"


class MarkerStyle(Enum):
    """Marker styles for scatter plots."""
    CIRCLE = "o"
    SQUARE = "s"
    TRIANGLE = "^"
    DIAMOND = "D"
    PLUS = "+"
    CROSS = "x"
    STAR = "*"
    NONE = ""


class LineStyle(Enum):
    """Line styles."""
    SOLID = "-"
    DASHED = "--"
    DOTTED = ":"
    DASHDOT = "-."
    NONE = ""


@dataclass
class SeriesMetadata:
    """Metadata for a plot series.
    
    Attributes:
        name: Series display name
        x_column: X data column name from DataTable
        y_column: Y data column name from DataTable
        x_error_column: Optional X uncertainty column name
        y_error_column: Optional Y uncertainty column name
        
        # Style properties
        plot_style: Type of plot (line, scatter, etc.)
        color: Series color (hex string or QColor)
        line_style: Line style for line plots
        line_width: Line width in points
        marker_style: Marker style for scatter plots
        marker_size: Marker size in points
        marker_edge_color: Marker edge color
        marker_edge_width: Marker edge width in points
        alpha: Transparency (0.0 = transparent, 1.0 = opaque)
        
        # Error bar properties
        show_error_bars: Whether to display error bars
        error_bar_cap_size: Cap size for error bars
        error_bar_cap_width: Cap width for error bars
        error_bar_line_width: Error bar line width
        
        # Legend properties
        show_in_legend: Whether to show in legend
        legend_label: Custom legend label (uses name if None)
        
        # Display properties
        visible: Whether series is visible
        z_order: Drawing order (higher = drawn on top)
    """
    
    # Core identification
    name: str
    x_column: str
    y_column: str
    x_error_column: Optional[str] = None
    y_error_column: Optional[str] = None
    
    # Style properties
    plot_style: PlotStyle = PlotStyle.LINE_SCATTER
    color: str = "#1f77b4"  # Default matplotlib blue
    line_style: LineStyle = LineStyle.SOLID
    line_width: float = 2.0
    marker_style: MarkerStyle = MarkerStyle.CIRCLE
    marker_size: float = 6.0
    marker_edge_color: str = "auto"  # "auto" means same as fill color
    marker_edge_width: float = 0.5
    alpha: float = 1.0
    
    # Error bar properties
    show_error_bars: bool = True
    error_bar_cap_size: float = 5.0
    error_bar_cap_width: float = 1.5
    error_bar_line_width: float = 1.5
    
    # Legend properties
    show_in_legend: bool = True
    legend_label: Optional[str] = None
    
    # Display properties
    visible: bool = True
    z_order: int = 1
    
    def __post_init__(self):
        """Validate and normalize metadata after initialization."""
        # Convert enum strings to enum objects if needed
        if isinstance(self.plot_style, str):
            self.plot_style = PlotStyle(self.plot_style)
        if isinstance(self.line_style, str):
            self.line_style = LineStyle(self.line_style)
        if isinstance(self.marker_style, str):
            self.marker_style = MarkerStyle(self.marker_style)
        
        # Set default legend label to series name if not provided
        if self.legend_label is None:
            self.legend_label = self.name
    
    def get_matplotlib_format(self) -> str:
        """Generate matplotlib format string.
        
        Returns:
            Format string like 'o-', 's--', etc.
        """
        marker = self.marker_style.value if self.plot_style in (PlotStyle.SCATTER, PlotStyle.LINE_SCATTER) else ""
        line = self.line_style.value if self.plot_style in (PlotStyle.LINE, PlotStyle.LINE_SCATTER) else ""
        return f"{marker}{line}" if marker or line else "-"
    
    def has_error_bars(self) -> bool:
        """Check if series has error bars configured.
        
        Returns:
            True if X or Y error columns are specified
        """
        return self.show_error_bars and (self.x_error_column is not None or self.y_error_column is not None)
    
    def get_marker_edge_color(self) -> str:
        """Get actual marker edge color.
        
        Returns:
            Color string (resolves "auto" to series color)
        """
        return self.color if self.marker_edge_color == "auto" else self.marker_edge_color
    
    def to_dict(self) -> dict:
        """Convert metadata to dictionary for serialization.
        
        Returns:
            Dictionary representation of metadata
        """
        return {
            'name': self.name,
            'x_column': self.x_column,
            'y_column': self.y_column,
            'x_error_column': self.x_error_column,
            'y_error_column': self.y_error_column,
            'plot_style': self.plot_style.value,
            'color': self.color,
            'line_style': self.line_style.value,
            'line_width': self.line_width,
            'marker_style': self.marker_style.value,
            'marker_size': self.marker_size,
            'marker_edge_color': self.marker_edge_color,
            'marker_edge_width': self.marker_edge_width,
            'alpha': self.alpha,
            'show_error_bars': self.show_error_bars,
            'error_bar_cap_size': self.error_bar_cap_size,
            'error_bar_cap_width': self.error_bar_cap_width,
            'error_bar_line_width': self.error_bar_line_width,
            'show_in_legend': self.show_in_legend,
            'legend_label': self.legend_label,
            'visible': self.visible,
            'z_order': self.z_order
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SeriesMetadata':
        """Create SeriesMetadata from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            SeriesMetadata instance
        """
        return cls(**data)


# Preset color palette (matplotlib default colors)
DEFAULT_COLORS = [
    "#1f77b4",  # Blue
    "#ff7f0e",  # Orange
    "#2ca02c",  # Green
    "#d62728",  # Red
    "#9467bd",  # Purple
    "#8c564b",  # Brown
    "#e377c2",  # Pink
    "#7f7f7f",  # Gray
    "#bcbd22",  # Olive
    "#17becf",  # Cyan
]


def get_default_color(index: int) -> str:
    """Get default color for series by index.
    
    Args:
        index: Series index (0-based)
        
    Returns:
        Color hex string
    """
    return DEFAULT_COLORS[index % len(DEFAULT_COLORS)]
