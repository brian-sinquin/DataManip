"""
Plot view for rendering plots using matplotlib.

This module implements the view layer for plotting, handling canvas
rendering, user interaction, and matplotlib integration.
"""

from typing import Optional
import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, Signal, Slot
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from .plot_model import PlotModel
from .series_metadata import PlotStyle, SeriesMetadata
from .plot_config import GridStyle


class PlotView(QWidget):
    """View for rendering plots from PlotModel.
    
    This widget handles:
    - Matplotlib canvas creation and management
    - Rendering series from PlotModel
    - Navigation toolbar
    - User interaction events
    
    Signals:
        plotClicked: Emitted when plot is clicked (x, y)
        selectionChanged: Emitted when data selection changes
    """
    
    # Signals
    plotClicked = Signal(float, float)
    selectionChanged = Signal()
    
    def __init__(self, plot_model: Optional[PlotModel] = None, parent=None):
        """Initialize plot view.
        
        Args:
            plot_model: PlotModel instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._plot_model = plot_model
        self._setup_ui()
        
        # Connect to model signals
        if self._plot_model:
            self._connect_model_signals()
    
    def _setup_ui(self):
        """Set up UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        # Get initial config for figure size
        config = self._plot_model.get_config() if self._plot_model else None
        figsize = config.get_figure_size() if config else (8, 6)
        dpi = config.dpi if config else 100
        
        # Create matplotlib figure and canvas
        self.figure = Figure(figsize=figsize, dpi=dpi)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Create axes
        self.ax = self.figure.add_subplot(111)
        
        # Add navigation toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
        # Initial empty plot
        self._render_empty_plot()
    
    def _connect_model_signals(self):
        """Connect to plot model signals."""
        if not self._plot_model:
            return
        
        self._plot_model.seriesAdded.connect(self._on_series_changed)
        self._plot_model.seriesRemoved.connect(self._on_series_changed)
        self._plot_model.seriesUpdated.connect(self._on_series_changed)
        self._plot_model.configUpdated.connect(self._on_config_changed)
        self._plot_model.dataChanged.connect(self._on_data_changed)
    
    def set_model(self, plot_model: PlotModel):
        """Set or update the plot model.
        
        Args:
            plot_model: PlotModel instance
        """
        # Disconnect old signals
        if self._plot_model:
            try:
                self._plot_model.seriesAdded.disconnect(self._on_series_changed)
                self._plot_model.seriesRemoved.disconnect(self._on_series_changed)
                self._plot_model.seriesUpdated.disconnect(self._on_series_changed)
                self._plot_model.configUpdated.disconnect(self._on_config_changed)
                self._plot_model.dataChanged.disconnect(self._on_data_changed)
            except Exception:
                pass
        
        # Set new model
        self._plot_model = plot_model
        
        # Connect new signals
        if self._plot_model:
            self._connect_model_signals()
        
        # Re-render
        self.render()
    
    def get_model(self) -> Optional[PlotModel]:
        """Get the current plot model.
        
        Returns:
            PlotModel instance or None
        """
        return self._plot_model
    
    # ========================================================================
    # Rendering
    # ========================================================================
    
    def render(self):
        """Render the complete plot from model."""
        if not self._plot_model:
            self._render_empty_plot()
            return
        
        # Get configuration
        config = self._plot_model.get_config()
        
        # Clear axes
        self.ax.clear()
        
        # Get all series data
        all_series_data = self._plot_model.get_all_series_data()
        
        if not all_series_data:
            self._render_empty_plot()
            return
        
        # Render each series
        for series_name, x_data, y_data, x_error, y_error in all_series_data:
            series = self._plot_model.get_series(series_name)
            self._render_series(series, x_data, y_data, x_error, y_error)
        
        # Apply configuration
        self._apply_config(config)
        
        # Update canvas
        self.figure.tight_layout() if config.tight_layout else self.figure.subplots_adjust()
        self.canvas.draw()
    
    def _render_series(self, series: SeriesMetadata, x_data: np.ndarray, y_data: np.ndarray,
                       x_error: Optional[np.ndarray], y_error: Optional[np.ndarray]):
        """Render a single series.
        
        Args:
            series: SeriesMetadata instance
            x_data: X data array
            y_data: Y data array
            x_error: X error array (or None)
            y_error: Y error array (or None)
        """
        # Determine plot style
        plot_style = series.plot_style
        
        # Common plot parameters
        plot_kwargs = {
            'color': series.color,
            'alpha': series.alpha,
            'label': series.legend_label if series.show_in_legend else None,
            'zorder': series.z_order
        }
        
        # Render based on plot style
        if plot_style == PlotStyle.LINE:
            self._render_line(x_data, y_data, series, plot_kwargs)
        
        elif plot_style == PlotStyle.SCATTER:
            self._render_scatter(x_data, y_data, series, plot_kwargs)
        
        elif plot_style == PlotStyle.LINE_SCATTER:
            self._render_line_scatter(x_data, y_data, series, plot_kwargs)
        
        elif plot_style == PlotStyle.BAR:
            self._render_bar(x_data, y_data, series, plot_kwargs)
        
        elif plot_style == PlotStyle.STEP:
            self._render_step(x_data, y_data, series, plot_kwargs)
        
        elif plot_style == PlotStyle.ERRORBAR:
            self._render_errorbar(x_data, y_data, x_error, y_error, series, plot_kwargs)
        
        # Add error bars if configured
        if series.has_error_bars() and plot_style != PlotStyle.ERRORBAR:
            self._add_error_bars(x_data, y_data, x_error, y_error, series)
    
    def _render_line(self, x_data: np.ndarray, y_data: np.ndarray,
                     series: SeriesMetadata, plot_kwargs: dict):
        """Render line plot."""
        self.ax.plot(
            x_data, y_data,
            linestyle=series.line_style.value,
            linewidth=series.line_width,
            **plot_kwargs
        )
    
    def _render_scatter(self, x_data: np.ndarray, y_data: np.ndarray,
                        series: SeriesMetadata, plot_kwargs: dict):
        """Render scatter plot."""
        self.ax.scatter(
            x_data, y_data,
            marker=series.marker_style.value,
            s=series.marker_size**2,  # s is area, not diameter
            edgecolors=series.get_marker_edge_color(),
            linewidths=series.marker_edge_width,
            **plot_kwargs
        )
    
    def _render_line_scatter(self, x_data: np.ndarray, y_data: np.ndarray,
                             series: SeriesMetadata, plot_kwargs: dict):
        """Render combined line + scatter plot."""
        # Draw line
        self.ax.plot(
            x_data, y_data,
            linestyle=series.line_style.value,
            linewidth=series.line_width,
            marker=series.marker_style.value,
            markersize=series.marker_size,
            markeredgecolor=series.get_marker_edge_color(),
            markeredgewidth=series.marker_edge_width,
            **plot_kwargs
        )
    
    def _render_bar(self, x_data: np.ndarray, y_data: np.ndarray,
                    series: SeriesMetadata, plot_kwargs: dict):
        """Render bar plot."""
        # Calculate bar width (80% of spacing)
        if len(x_data) > 1:
            width = np.min(np.diff(x_data)) * 0.8
        else:
            width = 0.8
        
        self.ax.bar(
            x_data, y_data,
            width=width,
            edgecolor=series.get_marker_edge_color(),
            linewidth=series.marker_edge_width,
            **plot_kwargs
        )
    
    def _render_step(self, x_data: np.ndarray, y_data: np.ndarray,
                     series: SeriesMetadata, plot_kwargs: dict):
        """Render step plot."""
        self.ax.step(
            x_data, y_data,
            where='mid',
            linewidth=series.line_width,
            **plot_kwargs
        )
    
    def _render_errorbar(self, x_data: np.ndarray, y_data: np.ndarray,
                         x_error: Optional[np.ndarray], y_error: Optional[np.ndarray],
                         series: SeriesMetadata, plot_kwargs: dict):
        """Render errorbar plot."""
        self.ax.errorbar(
            x_data, y_data,
            xerr=x_error,
            yerr=y_error,
            fmt=series.get_matplotlib_format(),
            linewidth=series.line_width,
            markersize=series.marker_size,
            capsize=series.error_bar_cap_size,
            capthick=series.error_bar_cap_width,
            elinewidth=series.error_bar_line_width,
            **plot_kwargs
        )
    
    def _add_error_bars(self, x_data: np.ndarray, y_data: np.ndarray,
                        x_error: Optional[np.ndarray], y_error: Optional[np.ndarray],
                        series: SeriesMetadata):
        """Add error bars to existing plot."""
        self.ax.errorbar(
            x_data, y_data,
            xerr=x_error,
            yerr=y_error,
            fmt='none',
            ecolor=series.color,
            elinewidth=series.error_bar_line_width,
            capsize=series.error_bar_cap_size,
            capthick=series.error_bar_cap_width,
            alpha=series.alpha,
            zorder=series.z_order
        )
    
    def _apply_config(self, config):
        """Apply plot configuration to axes.
        
        Args:
            config: PlotConfig instance
        """
        # Title
        if config.title:
            self.ax.set_title(config.title, fontsize=config.title_fontsize)
        
        # X-axis
        self.ax.set_xlabel(config.x_axis.get_full_label(), fontsize=12)
        self.ax.set_xscale(config.x_axis.scale.value)
        if not config.x_axis.auto_range:
            self.ax.set_xlim(config.x_axis.min_value, config.x_axis.max_value)
        if config.x_axis.invert:
            self.ax.invert_xaxis()
        
        # Y-axis
        self.ax.set_ylabel(config.y_axis.get_full_label(), fontsize=12)
        self.ax.set_yscale(config.y_axis.scale.value)
        if not config.y_axis.auto_range:
            self.ax.set_ylim(config.y_axis.min_value, config.y_axis.max_value)
        if config.y_axis.invert:
            self.ax.invert_yaxis()
        
        # Grid
        if config.grid_style != GridStyle.NONE:
            which = config.grid_style.value
            self.ax.grid(
                True,
                which=which if which != 'none' else 'major',
                color=config.grid_color,
                linewidth=config.grid_line_width,
                alpha=config.x_axis.grid_alpha
            )
        else:
            self.ax.grid(False)
        
        # Legend
        if config.legend.show:
            # Check if any series should be in legend
            handles, labels = self.ax.get_legend_handles_labels()
            if handles:
                self.ax.legend(
                    loc=config.legend.location.value,
                    frameon=config.legend.frameon,
                    framealpha=config.legend.frame_alpha,
                    shadow=config.legend.shadow,
                    ncol=config.legend.ncol,
                    fontsize=config.legend.fontsize,
                    title=config.legend.title
                )
        
        # Background color
        self.figure.patch.set_facecolor(config.background_color)
        self.ax.set_facecolor(config.background_color)
    
    def _render_empty_plot(self):
        """Render empty plot with default message."""
        self.ax.clear()
        self.ax.set_xlabel("X-axis", fontsize=12)
        self.ax.set_ylabel("Y-axis", fontsize=12)
        self.ax.set_title("No Data", fontsize=14)
        self.ax.grid(True, alpha=0.3)
        self.ax.text(
            0.5, 0.5, "Add series to plot data",
            horizontalalignment='center',
            verticalalignment='center',
            transform=self.ax.transAxes,
            fontsize=14,
            color='gray'
        )
        self.canvas.draw()
    
    # ========================================================================
    # Public Methods
    # ========================================================================
    
    def clear(self):
        """Clear the plot."""
        self.ax.clear()
        self._render_empty_plot()
    
    def refresh(self):
        """Refresh the plot (alias for render)."""
        self.render()
    
    def export_image(self, filepath: str, dpi: Optional[int] = None):
        """Export plot to image file.
        
        Args:
            filepath: Output file path
            dpi: DPI for export (uses config default if None)
        """
        if not self._plot_model:
            return
        
        config = self._plot_model.get_config()
        export_dpi = dpi if dpi else config.export_dpi
        
        self.figure.savefig(filepath, dpi=export_dpi, bbox_inches='tight')
    
    def get_figure(self) -> Figure:
        """Get matplotlib figure.
        
        Returns:
            Matplotlib Figure instance
        """
        return self.figure
    
    def get_axes(self):
        """Get matplotlib axes.
        
        Returns:
            Matplotlib Axes instance
        """
        return self.ax
    
    # ========================================================================
    # Event Handlers
    # ========================================================================
    
    @Slot()
    def _on_series_changed(self):
        """Handle series added/removed/updated."""
        self.render()
    
    @Slot()
    def _on_config_changed(self):
        """Handle configuration changes."""
        if not self._plot_model:
            return
        
        # Update figure size if changed
        config = self._plot_model.get_config()
        self.figure.set_size_inches(config.get_figure_size())
        self.figure.set_dpi(config.dpi)
        
        # Re-render
        self.render()
    
    @Slot()
    def _on_data_changed(self):
        """Handle underlying data changes."""
        # Could add debouncing here to avoid excessive re-renders
        self.render()


class PlotWidget(PlotView):
    """All-in-one plot widget with built-in PlotModel.
    
    This is a convenience class that creates its own PlotModel.
    For more control, use PlotView with a separate PlotModel.
    """
    
    def __init__(self, datatable=None, parent=None):
        """Initialize widget with built-in model.
        
        Args:
            datatable: Optional DataTableWidget reference
            parent: Parent widget
        """
        # Create internal model
        self._internal_model = PlotModel(datatable=datatable)
        
        # Initialize view with model
        super().__init__(plot_model=self._internal_model, parent=parent)
    
    def model(self) -> PlotModel:
        """Get the internal plot model.
        
        Returns:
            PlotModel instance
        """
        return self._internal_model
    
    # Convenience methods that delegate to model
    
    def add_series(self, *args, **kwargs):
        """Add a series. See PlotModel.add_series()."""
        return self._internal_model.add_series(*args, **kwargs)
    
    def remove_series(self, *args, **kwargs):
        """Remove a series. See PlotModel.remove_series()."""
        return self._internal_model.remove_series(*args, **kwargs)
    
    def update_series(self, *args, **kwargs):
        """Update a series. See PlotModel.update_series()."""
        return self._internal_model.update_series(*args, **kwargs)
    
    def get_series(self, *args, **kwargs):
        """Get series metadata. See PlotModel.get_series()."""
        return self._internal_model.get_series(*args, **kwargs)
    
    def get_all_series(self):
        """Get all series. See PlotModel.get_all_series()."""
        return self._internal_model.get_all_series()
    
    def get_config(self):
        """Get plot config. See PlotModel.get_config()."""
        return self._internal_model.get_config()
    
    def set_config(self, *args, **kwargs):
        """Set plot config. See PlotModel.set_config()."""
        return self._internal_model.set_config(*args, **kwargs)
    
    def set_datatable(self, *args, **kwargs):
        """Set datatable. See PlotModel.set_datatable()."""
        return self._internal_model.set_datatable(*args, **kwargs)
