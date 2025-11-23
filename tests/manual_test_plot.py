"""
Test script for PlotStudy functionality.
"""

from pathlib import Path
import sys

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.workspace import Workspace
from studies.data_table_study import DataTableStudy, ColumnType
from studies.plot_study import PlotStudy
import numpy as np


def test_plot_study():
    """Test PlotStudy basic functionality."""
    # Create workspace
    workspace = Workspace("Test", "numerical")
    
    # Create data table with physics demo
    data_study = DataTableStudy("Physics Demo", workspace=workspace)
    workspace.add_study(data_study)
    
    # Add time column (0 to 3 in steps of 0.25 = 13 points)
    data_study.add_column(
        "time",
        column_type=ColumnType.RANGE,
        range_type="arange",
        range_start=0.0,
        range_stop=3.25,  # Stop is exclusive, so use 3.25 to include 3.0
        range_step=0.25,
        unit="s"
    )
    
    # Get number of rows
    n_rows = len(data_study.table.get_column("time"))
    print(f"Number of rows: {n_rows}")
    
    # Add height column (calculated)
    data_study.add_column("height", unit="m")
    
    # Add velocity column as simple data column
    data_study.add_column("velocity", unit="m/s")
    
    # Populate with physics formulas
    time_values = data_study.table.get_column("time").values
    height_values = 50 - 0.5 * 9.81 * time_values**2
    velocity_values = -9.81 * time_values
    
    data_study.table.set_column("height", height_values)
    data_study.table.set_column("velocity", velocity_values)
    
    # Add mass column
    data_study.add_column("mass", unit="kg")
    data_study.table.set_column("mass", np.full(n_rows, 2.0))
    
    data_study.add_column(
        "KE",
        formula="0.5 * {mass} * {velocity}^2",
        unit="J"
    )
    
    # Create plot study
    plot_study = PlotStudy("Height vs Time", workspace=workspace)
    workspace.add_study(plot_study)
    
    # Add series
    plot_study.add_series(
        study_name="Physics Demo",
        x_column="time",
        y_column="height",
        label="Height",
        style="both",
        color="blue"
    )
    
    # Test data retrieval
    print("Testing PlotStudy...")
    print(f"Plot title: {plot_study.title}")
    print(f"Number of series: {len(plot_study.series)}")
    
    data = plot_study.get_data_for_series(0)
    if data:
        x_data, y_data, x_label, y_label = data
        print(f"X label: {x_label}")
        print(f"Y label: {y_label}")
        print(f"Data points: {len(x_data)}")
        print(f"X range: [{x_data.min():.2f}, {x_data.max():.2f}]")
        print(f"Y range: [{y_data.min():.2f}, {y_data.max():.2f}]")
    else:
        print("ERROR: Failed to get data")
        return False
    
    # Test serialization
    print("\nTesting serialization...")
    plot_dict = plot_study.to_dict()
    print(f"Serialized keys: {list(plot_dict.keys())}")
    
    restored_plot = PlotStudy.from_dict(plot_dict, workspace=workspace)
    print(f"Restored title: {restored_plot.title}")
    print(f"Restored series: {len(restored_plot.series)}")
    
    # Test workspace save/load
    print("\nTesting workspace save/load...")
    workspace_dict = workspace.to_dict()
    print(f"Workspace studies: {list(workspace_dict['studies'].keys())}")
    
    restored_workspace = Workspace.from_dict(workspace_dict)
    print(f"Restored studies: {list(restored_workspace.studies.keys())}")
    
    restored_plot_study = restored_workspace.get_study("Height vs Time")
    if restored_plot_study:
        print(f"Restored plot type: {type(restored_plot_study).__name__}")
        print(f"Restored plot series: {len(restored_plot_study.series)}")
    else:
        print("ERROR: Failed to restore plot study")
        return False
    
    print("\n✓ All tests passed!")
    return True


if __name__ == "__main__":
    success = test_plot_study()
    sys.exit(0 if success else 1)
