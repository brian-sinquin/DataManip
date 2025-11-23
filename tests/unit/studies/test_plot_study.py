"""
Unit tests for PlotStudy.
"""

import pytest
from pathlib import Path
import sys
import numpy as np
import pandas as pd

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.workspace import Workspace
from studies.data_table_study import DataTableStudy, ColumnType
from studies.plot_study import PlotStudy


class TestPlotStudy:
    """Test PlotStudy functionality."""
    
    def setup_method(self):
        """Setup test workspace and data."""
        self.workspace = Workspace("Test", "numerical")
        
        # Create data table
        self.data_study = DataTableStudy("Data", workspace=self.workspace)
        self.workspace.add_study(self.data_study)
        
        # Add simple x/y data
        self.data_study.add_column("x", unit="m")
        self.data_study.add_column("y", unit="m")
        
        x_data = np.linspace(0, 10, 11)
        y_data = x_data ** 2
        
        self.data_study.table.set_column("x", pd.Series(x_data))
        self.data_study.table.set_column("y", pd.Series(y_data))
    
    def test_create_plot_study(self):
        """Test creating plot study."""
        plot = PlotStudy("Test Plot", workspace=self.workspace)
        
        assert plot.name == "Test Plot"
        assert plot.get_type() == "plot"
        assert plot.workspace == self.workspace
        assert len(plot.series) == 0
    
    def test_add_series(self):
        """Test adding series to plot."""
        plot = PlotStudy("Test Plot", workspace=self.workspace)
        self.workspace.add_study(plot)
        
        plot.add_series(
            study_name="Data",
            x_column="x",
            y_column="y",
            label="y vs x",
            style="line",
            color="blue"
        )
        
        assert len(plot.series) == 1
        assert plot.series[0]["study"] == "Data"
        assert plot.series[0]["x_col"] == "x"
        assert plot.series[0]["y_col"] == "y"
        assert plot.series[0]["label"] == "y vs x"
        assert plot.series[0]["style"] == "line"
        assert plot.series[0]["color"] == "blue"
    
    def test_get_data_for_series(self):
        """Test retrieving data for series."""
        plot = PlotStudy("Test Plot", workspace=self.workspace)
        self.workspace.add_study(plot)
        
        plot.add_series(
            study_name="Data",
            x_column="x",
            y_column="y"
        )
        
        data = plot.get_data_for_series(0)
        assert data is not None
        
        x_data, y_data, x_label, y_label = data
        assert len(x_data) == 11
        assert len(y_data) == 11
        assert x_label == "x [m]"
        assert y_label == "y [m]"
    
    def test_remove_series(self):
        """Test removing series."""
        plot = PlotStudy("Test Plot", workspace=self.workspace)
        self.workspace.add_study(plot)
        
        plot.add_series("Data", "x", "y")
        plot.add_series("Data", "y", "x")
        
        assert len(plot.series) == 2
        
        plot.remove_series(0)
        assert len(plot.series) == 1
        assert plot.series[0]["x_col"] == "y"
    
    def test_clear_series(self):
        """Test clearing all series."""
        plot = PlotStudy("Test Plot", workspace=self.workspace)
        self.workspace.add_study(plot)
        
        plot.add_series("Data", "x", "y")
        plot.add_series("Data", "y", "x")
        
        plot.clear_series()
        assert len(plot.series) == 0
    
    def test_serialization(self):
        """Test to_dict/from_dict."""
        plot = PlotStudy("Test Plot", workspace=self.workspace)
        self.workspace.add_study(plot)
        
        plot.title = "Custom Title"
        plot.xlabel = "X Axis"
        plot.ylabel = "Y Axis"
        plot.grid = False
        plot.legend = False
        plot.add_series("Data", "x", "y", label="Series 1")
        
        # Serialize
        data = plot.to_dict()
        assert data["name"] == "Test Plot"
        assert data["title"] == "Custom Title"
        assert data["xlabel"] == "X Axis"
        assert data["ylabel"] == "Y Axis"
        assert data["grid"] is False
        assert data["legend"] is False
        assert len(data["series"]) == 1
        
        # Deserialize
        restored = PlotStudy.from_dict(data, workspace=self.workspace)
        assert restored.name == "Test Plot"
        assert restored.title == "Custom Title"
        assert restored.xlabel == "X Axis"
        assert restored.ylabel == "Y Axis"
        assert restored.grid is False
        assert restored.legend is False
        assert len(restored.series) == 1
        assert restored.series[0]["label"] == "Series 1"
    
    def test_workspace_save_load(self):
        """Test workspace serialization with plot studies."""
        plot = PlotStudy("Test Plot", workspace=self.workspace)
        self.workspace.add_study(plot)
        plot.add_series("Data", "x", "y")
        
        # Serialize workspace
        workspace_data = self.workspace.to_dict()
        assert "Test Plot" in workspace_data["studies"]
        assert workspace_data["studies"]["Test Plot"]["type"] == "plot"
        
        # Deserialize workspace
        restored_workspace = Workspace.from_dict(workspace_data)
        assert "Test Plot" in restored_workspace.studies
        
        restored_plot = restored_workspace.get_study("Test Plot")
        assert isinstance(restored_plot, PlotStudy)
        assert len(restored_plot.series) == 1
    
    def test_multiple_series(self):
        """Test plot with multiple series."""
        # Add another column to data
        self.data_study.add_column("z", unit="m")
        z_data = np.sin(self.data_study.table.get_column("x").values)
        self.data_study.table.set_column("z", pd.Series(z_data))
        
        plot = PlotStudy("Multi-Series Plot", workspace=self.workspace)
        self.workspace.add_study(plot)
        
        plot.add_series("Data", "x", "y", label="Quadratic", style="line", color="blue")
        plot.add_series("Data", "x", "z", label="Sine", style="scatter", color="red")
        
        assert len(plot.series) == 2
        
        # Verify both series have data
        data1 = plot.get_data_for_series(0)
        data2 = plot.get_data_for_series(1)
        
        assert data1 is not None
        assert data2 is not None
