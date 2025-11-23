"""
Visualization study for plotting data.

Provides 2D plotting capabilities using matplotlib backend.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from core.study import Study


class PlotStudy(Study):
    """Study for 2D data visualization.
    
    Features:
    - Multiple series on same plot
    - Line, scatter, and mixed plots
    - Axis labels and legend
    - Data references to DataTable studies
    
    Attributes:
        figure: Matplotlib Figure object
        series: List of plot series configurations
    """
    
    def __init__(self, name: str, workspace=None):
        """Initialize PlotStudy.
        
        Args:
            name: Study name
            workspace: Reference to parent workspace
        """
        super().__init__(name)
        self.workspace = workspace
        
        # Plot configuration
        self.title = name
        self.xlabel = "X"
        self.ylabel = "Y"
        self.grid = True
        self.legend = True
        
        # Series: [{study: str, x_col: str, y_col: str, label: str, style: str}]
        self.series: List[Dict[str, Any]] = []
        
        # Matplotlib figure
        self.figure: Optional[Figure] = None
    
    def get_type(self) -> str:
        """Get study type identifier."""
        return "plot"
    
    def add_series(
        self,
        study_name: str,
        x_column: str,
        y_column: str,
        label: Optional[str] = None,
        style: str = "line",  # "line", "scatter", "both"
        color: Optional[str] = None,
        marker: str = "o",
        linestyle: str = "-"
    ):
        """Add data series to plot.
        
        Args:
            study_name: Name of DataTable study containing data
            x_column: Column name for X data
            y_column: Column name for Y data
            label: Series label for legend
            style: Plot style (line, scatter, both)
            color: Line/marker color
            marker: Marker style
            linestyle: Line style
        """
        series = {
            "study": study_name,
            "x_col": x_column,
            "y_col": y_column,
            "label": label or f"{y_column} vs {x_column}",
            "style": style,
            "color": color,
            "marker": marker,
            "linestyle": linestyle
        }
        self.series.append(series)
    
    def remove_series(self, index: int):
        """Remove series by index.
        
        Args:
            index: Series index to remove
        """
        if 0 <= index < len(self.series):
            del self.series[index]
    
    def clear_series(self):
        """Remove all series."""
        self.series.clear()
    
    def get_data_for_series(self, series_index: int):
        """Get X and Y data arrays for a series.
        
        Args:
            series_index: Index of series
            
        Returns:
            Tuple of (x_data, y_data, x_label, y_label) or None if not found
        """
        if not (0 <= series_index < len(self.series)):
            return None
        
        series = self.series[series_index]
        
        # Get study from workspace
        if not self.workspace:
            return None
        
        study = self.workspace.get_study(series["study"])
        if not study:
            return None
        
        # Get DataTable study
        from studies.data_table_study import DataTableStudy
        if not isinstance(study, DataTableStudy):
            return None
        
        # Get column data
        try:
            x_data = study.table.get_column(series["x_col"]).values
            y_data = study.table.get_column(series["y_col"]).values
            
            # Get units for labels
            x_unit = study.get_column_unit(series["x_col"])
            y_unit = study.get_column_unit(series["y_col"])
            
            x_label = f"{series['x_col']}" + (f" [{x_unit}]" if x_unit else "")
            y_label = f"{series['y_col']}" + (f" [{y_unit}]" if y_unit else "")
            
            return x_data, y_data, x_label, y_label
        except Exception:
            return None
    
    def update_plot(self, figure: Figure):
        """Update matplotlib figure with current data.
        
        Args:
            figure: Matplotlib Figure to update
        """
        self.figure = figure
        figure.clear()
        
        ax = figure.add_subplot(111)
        
        # Plot each series
        for i, series in enumerate(self.series):
            data = self.get_data_for_series(i)
            if not data:
                continue
            
            x_data, y_data, x_label, y_label = data
            
            # Set default labels if not already set
            if self.xlabel == "X" and x_label:
                self.xlabel = x_label
            if self.ylabel == "Y" and y_label:
                self.ylabel = y_label
            
            # Plot based on style
            style = series["style"]
            color = series["color"]
            label = series["label"]
            
            if style == "scatter":
                ax.scatter(x_data, y_data, label=label, color=color, 
                          marker=series["marker"], alpha=0.7)
            elif style == "line":
                ax.plot(x_data, y_data, label=label, color=color,
                       linestyle=series["linestyle"])
            elif style == "both":
                ax.plot(x_data, y_data, label=label, color=color,
                       linestyle=series["linestyle"], marker=series["marker"],
                       markersize=4)
        
        # Configure plot
        ax.set_xlabel(self.xlabel)
        ax.set_ylabel(self.ylabel)
        ax.set_title(self.title)
        
        if self.grid:
            ax.grid(True, alpha=0.3)
        
        if self.legend and self.series:
            ax.legend()
        
        figure.tight_layout()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize study to dictionary."""
        data = super().to_dict()
        data.update({
            "title": self.title,
            "xlabel": self.xlabel,
            "ylabel": self.ylabel,
            "grid": self.grid,
            "legend": self.legend,
            "series": self.series
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], workspace=None) -> PlotStudy:
        """Deserialize study from dictionary.
        
        Args:
            data: Dictionary representation
            workspace: Parent workspace reference
        """
        study = cls(data["name"], workspace=workspace)
        study.title = data.get("title", study.name)
        study.xlabel = data.get("xlabel", "X")
        study.ylabel = data.get("ylabel", "Y")
        study.grid = data.get("grid", True)
        study.legend = data.get("legend", True)
        study.series = data.get("series", [])
        return study
