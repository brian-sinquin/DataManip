"""
Plot widget for DataTable.

This module provides advanced plotting capabilities with:
- Model-view separation (PlotModel, PlotView)
- Multi-series support with customizable styles
- Comprehensive configuration (axes, legend, grid)
- Error bar support
- Export functionality
"""

# New enhanced architecture
from .plot_model import PlotModel
from .plot_view import PlotView, PlotWidget
from .series_metadata import (
    SeriesMetadata, PlotStyle, MarkerStyle, LineStyle,
    get_default_color, DEFAULT_COLORS
)
from .plot_config import (
    PlotConfig, AxisConfig, LegendConfig,
    GridStyle, LegendLocation, AxisScale
)
from .plot_toolbar import PlotToolbar
from .plot_dialogs import (
    AddSeriesDialog, AxisConfigDialog, PlotConfigDialog
)

# Legacy support (old implementation)
from .plot_widget import AdvancedDataTablePlotWidget

__all__ = [
    # Core classes
    "PlotModel",
    "PlotView",
    "PlotWidget",
    
    # Metadata and configuration
    "SeriesMetadata",
    "PlotConfig",
    "AxisConfig",
    "LegendConfig",
    
    # Enums
    "PlotStyle",
    "MarkerStyle",
    "LineStyle",
    "GridStyle",
    "LegendLocation",
    "AxisScale",
    
    # UI components
    "PlotToolbar",
    "AddSeriesDialog",
    "AxisConfigDialog",
    "PlotConfigDialog",
    
    # Utilities
    "get_default_color",
    "DEFAULT_COLORS",
    
    # Legacy
    "AdvancedDataTablePlotWidget",
]
