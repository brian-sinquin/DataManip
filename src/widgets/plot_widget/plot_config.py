"""
Plot configuration for plot widget.

This module defines configuration for plot appearance, axes, grid,
legend, and export settings.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple


class GridStyle(Enum):
    """Grid line styles."""
    NONE = "none"
    MAJOR = "major"
    MINOR = "minor"
    BOTH = "both"


class LegendLocation(Enum):
    """Legend location options."""
    BEST = "best"
    UPPER_RIGHT = "upper right"
    UPPER_LEFT = "upper left"
    LOWER_LEFT = "lower left"
    LOWER_RIGHT = "lower right"
    RIGHT = "right"
    CENTER_LEFT = "center left"
    CENTER_RIGHT = "center right"
    LOWER_CENTER = "lower center"
    UPPER_CENTER = "upper center"
    CENTER = "center"


class AxisScale(Enum):
    """Axis scale types."""
    LINEAR = "linear"
    LOG = "log"
    SYMLOG = "symlog"
    LOGIT = "logit"


@dataclass
class AxisConfig:
    """Configuration for a plot axis.
    
    Attributes:
        label: Axis label text
        unit: Unit of measurement (automatically added to label)
        scale: Axis scale (linear, log, etc.)
        auto_range: Whether to auto-calculate range from data
        min_value: Minimum value (if not auto_range)
        max_value: Maximum value (if not auto_range)
        invert: Whether to invert axis direction
        show_grid: Whether to show grid lines
        grid_alpha: Grid line transparency
    """
    
    label: str = ""
    unit: Optional[str] = None
    scale: AxisScale = AxisScale.LINEAR
    auto_range: bool = True
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    invert: bool = False
    show_grid: bool = True
    grid_alpha: float = 0.3
    
    def get_full_label(self) -> str:
        """Get axis label with unit.
        
        Returns:
            Label string with unit in brackets if specified
        """
        if self.unit:
            return f"{self.label} [{self.unit}]" if self.label else f"[{self.unit}]"
        return self.label
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'label': self.label,
            'unit': self.unit,
            'scale': self.scale.value,
            'auto_range': self.auto_range,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'invert': self.invert,
            'show_grid': self.show_grid,
            'grid_alpha': self.grid_alpha
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AxisConfig':
        """Create AxisConfig from dictionary."""
        if 'scale' in data and isinstance(data['scale'], str):
            data['scale'] = AxisScale(data['scale'])
        return cls(**data)


@dataclass
class LegendConfig:
    """Configuration for plot legend.
    
    Attributes:
        show: Whether to show legend
        location: Legend location
        frameon: Whether to draw legend frame
        frame_alpha: Legend frame transparency
        shadow: Whether to add shadow to legend
        ncol: Number of columns in legend
        fontsize: Legend font size
        title: Legend title (optional)
    """
    
    show: bool = True
    location: LegendLocation = LegendLocation.BEST
    frameon: bool = True
    frame_alpha: float = 0.9
    shadow: bool = False
    ncol: int = 1
    fontsize: int = 10
    title: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'show': self.show,
            'location': self.location.value,
            'frameon': self.frameon,
            'frame_alpha': self.frame_alpha,
            'shadow': self.shadow,
            'ncol': self.ncol,
            'fontsize': self.fontsize,
            'title': self.title
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'LegendConfig':
        """Create LegendConfig from dictionary."""
        if 'location' in data and isinstance(data['location'], str):
            data['location'] = LegendLocation(data['location'])
        return cls(**data)


@dataclass
class PlotConfig:
    """Configuration for entire plot appearance.
    
    Attributes:
        title: Plot title
        title_fontsize: Title font size
        
        # Axes
        x_axis: X-axis configuration
        y_axis: Y-axis configuration
        
        # Grid
        grid_style: Grid line style
        grid_color: Grid line color
        grid_line_width: Grid line width
        
        # Legend
        legend: Legend configuration
        
        # Figure properties
        figure_width: Figure width in inches
        figure_height: Figure height in inches
        dpi: Dots per inch for rendering
        background_color: Figure background color
        tight_layout: Whether to use tight layout
        
        # Export settings
        export_dpi: DPI for exported images
        export_format: Default export format
    """
    
    # Title
    title: str = ""
    title_fontsize: int = 14
    
    # Axes
    x_axis: AxisConfig = field(default_factory=lambda: AxisConfig(label="X-axis"))
    y_axis: AxisConfig = field(default_factory=lambda: AxisConfig(label="Y-axis"))
    
    # Grid
    grid_style: GridStyle = GridStyle.MAJOR
    grid_color: str = "#cccccc"
    grid_line_width: float = 0.5
    
    # Legend
    legend: LegendConfig = field(default_factory=LegendConfig)
    
    # Figure properties
    figure_width: float = 8.0
    figure_height: float = 6.0
    dpi: int = 100
    background_color: str = "#ffffff"
    tight_layout: bool = True
    
    # Export settings
    export_dpi: int = 300
    export_format: str = "png"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation of configuration
        """
        return {
            'title': self.title,
            'title_fontsize': self.title_fontsize,
            'x_axis': self.x_axis.to_dict(),
            'y_axis': self.y_axis.to_dict(),
            'grid_style': self.grid_style.value,
            'grid_color': self.grid_color,
            'grid_line_width': self.grid_line_width,
            'legend': self.legend.to_dict(),
            'figure_width': self.figure_width,
            'figure_height': self.figure_height,
            'dpi': self.dpi,
            'background_color': self.background_color,
            'tight_layout': self.tight_layout,
            'export_dpi': self.export_dpi,
            'export_format': self.export_format
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PlotConfig':
        """Create PlotConfig from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            PlotConfig instance
        """
        # Convert nested configs
        if 'x_axis' in data:
            data['x_axis'] = AxisConfig.from_dict(data['x_axis'])
        if 'y_axis' in data:
            data['y_axis'] = AxisConfig.from_dict(data['y_axis'])
        if 'legend' in data:
            data['legend'] = LegendConfig.from_dict(data['legend'])
        if 'grid_style' in data and isinstance(data['grid_style'], str):
            data['grid_style'] = GridStyle(data['grid_style'])
        
        return cls(**data)
    
    def get_figure_size(self) -> Tuple[float, float]:
        """Get figure size as tuple.
        
        Returns:
            (width, height) in inches
        """
        return (self.figure_width, self.figure_height)
