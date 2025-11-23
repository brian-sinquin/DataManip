"""Convert example files to standard workspace format."""
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.workspace import Workspace
from studies.data_table_study import DataTableStudy, ColumnType
from studies.plot_study import PlotStudy
import numpy as np


def create_example_01():
    """Example 01: Basic Introduction - Temperature measurements."""
    workspace = Workspace("01 - Basic Introduction", "numerical")
    
    # Data table
    study = DataTableStudy("Temperature Measurements", workspace=workspace)
    study.add_column("Time (s)", ColumnType.DATA, unit="s")
    study.add_column("Temperature (°C)", ColumnType.DATA, unit="°C")
    
    times = [0, 10, 20, 30, 40, 50, 60]
    temps = [20.5, 23.2, 26.8, 30.1, 33.5, 36.9, 40.2]
    for i, (t, temp) in enumerate(zip(times, temps)):
        study.table.data.loc[i, "Time (s)"] = t
        study.table.data.loc[i, "Temperature (°C)"] = temp
    
    workspace.add_study(study)
    
    # Plot
    plot = PlotStudy("Temperature vs Time", workspace=workspace)
    plot.title = "Temperature Evolution"
    plot.xlabel = "Time (s)"
    plot.ylabel = "Temperature (°C)"
    plot.grid = True
    plot.legend = True
    plot.add_series("Temperature Measurements", "Time (s)", "Temperature (°C)", 
                    "Heating Curve", "o-", "#e74c3c")
    workspace.add_study(plot)
    
    workspace.metadata = {
        "description": "Basic introduction to DataManip: simple data entry and plotting",
        "version": "0.2.0",
        "created": "2025-11-23"
    }
    return workspace


def create_example_02():
    """Example 02: Constants and Formulas - Circle geometry."""
    workspace = Workspace("02 - Constants and Formulas", "numerical")
    workspace.add_constant("pi", 3.14159265359, "")
    
    study = DataTableStudy("Circle Properties", workspace=workspace)
    study.add_column("Radius (m)", ColumnType.DATA, unit="m")
    study.add_column("Circumference (m)", ColumnType.CALCULATED, 
                    formula="2 * {pi} * {Radius (m)}", unit="m")
    study.add_column("Area (m²)", ColumnType.CALCULATED,
                    formula="{pi} * {Radius (m)}**2", unit="m²")
    
    radii = list(range(1, 11))
    for i, r in enumerate(radii):
        study.table.data.loc[i, "Radius (m)"] = r
    study.recalculate_all()
    
    workspace.add_study(study)
    
    # Plot
    plot = PlotStudy("Circle Properties", workspace=workspace)
    plot.title = "Circle Measurements"
    plot.xlabel = "Radius (m)"
    plot.ylabel = "Value"
    plot.grid = True
    plot.legend = True
    plot.add_series("Circle Properties", "Radius (m)", "Circumference (m)",
                    "Circumference", "o-", "#3498db")
    plot.add_series("Circle Properties", "Radius (m)", "Area (m²)",
                    "Area", "s-", "#e74c3c")
    workspace.add_study(plot)
    
    workspace.metadata = {
        "description": "Using constants and formula columns to calculate circle properties",
        "version": "0.2.0",
        "created": "2025-11-23"
    }
    return workspace


def create_example_03():
    """Example 03: Ranges and Derivatives - Projectile motion."""
    workspace = Workspace("03 - Ranges and Derivatives", "numerical")
    workspace.add_constant("v0", 50.0, "m/s")
    workspace.add_constant("g", 9.81, "m/s²")
    
    study = DataTableStudy("Projectile Motion", workspace=workspace)
    study.add_column("Time (s)", ColumnType.RANGE, unit="s",
                    range_type="linspace", range_start=0, range_stop=10.2, range_count=21)
    study.add_column("Height (m)", ColumnType.CALCULATED,
                    formula="{v0} * {Time (s)} - 0.5 * {g} * {Time (s)}**2", unit="m")
    study.add_column("Velocity (m/s)", ColumnType.DERIVATIVE,
                    derivative_of="Height (m)", with_respect_to="Time (s)", unit="m/s")
    study.add_column("Acceleration (m/s²)", ColumnType.DERIVATIVE,
                    derivative_of="Velocity (m/s)", with_respect_to="Time (s)", unit="m/s²")
    study.recalculate_all()
    
    workspace.add_study(study)
    
    # Plots
    plot1 = PlotStudy("Height vs Time", workspace=workspace)
    plot1.title = "Projectile Trajectory"
    plot1.xlabel = "Time (s)"
    plot1.ylabel = "Height (m)"
    plot1.grid = True
    plot1.legend = True
    plot1.add_series("Projectile Motion", "Time (s)", "Height (m)",
                     "Height", "o-", "#e74c3c")
    workspace.add_study(plot1)
    
    plot2 = PlotStudy("Derivatives", workspace=workspace)
    plot2.title = "Velocity and Acceleration"
    plot2.xlabel = "Time (s)"
    plot2.ylabel = "Value"
    plot2.grid = True
    plot2.legend = True
    plot2.add_series("Projectile Motion", "Time (s)", "Velocity (m/s)",
                     "Velocity", "o-", "#3498db")
    plot2.add_series("Projectile Motion", "Time (s)", "Acceleration (m/s²)",
                     "Acceleration", "s-", "#e74c3c")
    workspace.add_study(plot2)
    
    workspace.metadata = {
        "description": "Range generation and numerical derivatives for projectile motion",
        "version": "0.2.0",
        "created": "2025-11-23"
    }
    return workspace


def create_example_04():
    """Example 04: Uncertainty Propagation - Ohm's law."""
    workspace = Workspace("04 - Uncertainty Propagation", "numerical")
    
    study = DataTableStudy("Ohm's Law", workspace=workspace)
    study.add_column("Current (A)", ColumnType.DATA, unit="A")
    study.add_column("δI (A)", ColumnType.DATA, unit="A")
    study.add_column("Resistance (Ω)", ColumnType.DATA, unit="Ω")
    study.add_column("δR (Ω)", ColumnType.DATA, unit="Ω")
    study.add_column("Voltage (V)", ColumnType.CALCULATED,
                    formula="{Current (A)} * {Resistance (Ω)}", unit="V")
    study.add_column("δV (V)", ColumnType.UNCERTAINTY,
                    uncertainty_reference="Voltage (V)", unit="V")
    study.add_column("Power (W)", ColumnType.CALCULATED,
                    formula="{Current (A)} * {Voltage (V)}", unit="W")
    study.add_column("δP (W)", ColumnType.UNCERTAINTY,
                    uncertainty_reference="Power (W)", unit="W")
    
    currents = [0.5, 1.0, 1.5, 2.0, 2.5]
    d_currents = [0.05, 0.05, 0.05, 0.05, 0.05]
    resistances = [10, 10, 10, 10, 10]
    d_resistances = [0.5, 0.5, 0.5, 0.5, 0.5]
    
    for i, (curr, d_curr, res, d_res) in enumerate(zip(currents, d_currents, resistances, d_resistances)):
        study.table.data.loc[i, "Current (A)"] = curr
        study.table.data.loc[i, "δI (A)"] = d_curr
        study.table.data.loc[i, "Resistance (Ω)"] = res
        study.table.data.loc[i, "δR (Ω)"] = d_res
    study.recalculate_all()
    
    workspace.add_study(study)
    
    # Plots
    plot1 = PlotStudy("Voltage vs Current", workspace=workspace)
    plot1.title = "Ohm's Law with Error Bars"
    plot1.xlabel = "Current (A)"
    plot1.ylabel = "Voltage (V)"
    plot1.grid = True
    plot1.legend = True
    plot1.add_series("Ohm's Law", "Current (A)", "Voltage (V)",
                     "V = I×R", "o-", "#3498db", "δI (A)", "δV (V)")
    workspace.add_study(plot1)
    
    plot2 = PlotStudy("Power vs Current", workspace=workspace)
    plot2.title = "Power with Error Propagation"
    plot2.xlabel = "Current (A)"
    plot2.ylabel = "Power (W)"
    plot2.grid = True
    plot2.legend = True
    plot2.add_series("Ohm's Law", "Current (A)", "Power (W)",
                     "P = I×V", "s-", "#e74c3c", "δI (A)", "δP (W)")
    workspace.add_study(plot2)
    
    workspace.metadata = {
        "description": "Uncertainty propagation through calculations with error bars",
        "version": "0.2.0",
        "created": "2025-11-23"
    }
    return workspace


# Generate all examples
if __name__ == "__main__":
    examples = [
        ("01_basic_introduction.dmw", create_example_01),
        ("02_constants_and_formulas.dmw", create_example_02),
        ("03_ranges_and_derivatives.dmw", create_example_03),
        ("04_uncertainty_propagation.dmw", create_example_04),
    ]
    
    for filename, create_func in examples:
        try:
            workspace = create_func()
            output_path = Path("examples") / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(workspace.to_dict(), f, indent=2)
            print(f"✓ Saved: {filename}")
        except Exception as e:
            print(f"✗ Failed {filename}: {e}")
    
    print("\nNote: Examples 05-07 require custom functions/calculated constants.")
    print("Please create these manually through the UI and save them.")
