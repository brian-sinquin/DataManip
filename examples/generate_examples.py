"""
Generate all example workspace files programmatically.

This script creates the 7 example .dmw files using the DataManip API,
ensuring consistency and verifying integrity by loading each file after creation.

IMPORTANT: This is the SOURCE OF TRUTH for all examples. Do not manually edit
the .dmw files - regenerate them using this script instead.

Usage:
    cd examples
    uv run python generate_examples.py

Benefits:
    - Ensures consistent format across all examples
    - Uses proper API calls (no manual JSON editing)
    - Validates each example by loading it back
    - Catches serialization/deserialization issues immediately
    - Single source of truth for example content
    
Example Structure:
    01 - Basic Introduction: Data entry and simple plotting
    02 - Constants and Formulas: Using constants in calculated columns
    03 - Ranges and Derivatives: Range generation and numerical differentiation
    04 - Uncertainty Propagation: Automatic error propagation
    05 - Custom Functions: User-defined functions for calculations
    06 - Calculated Constants: Constants that depend on other constants
    07 - Advanced Kinematics: All features combined (2D projectile motion)

Output:
    - 7 .dmw files in examples/ directory
    - Each verified by save→load→compare cycle
    - Progress and verification status printed to console
"""

from pathlib import Path
import sys
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.workspace import Workspace
from studies.data_table_study import DataTableStudy, ColumnType
from studies.plot_study import PlotStudy


def create_01_basic_introduction():
    """Example 01: Basic data entry and plotting."""
    workspace = Workspace("01 - Basic Introduction", "numerical")
    workspace.metadata = {
        "description": "Basic data entry and simple plotting",
        "version": "0.2.0",
        "created": "2025-11-23"
    }
    
    # Create data table study
    study = DataTableStudy("Temperature Measurements", workspace=workspace)
    
    # Add time column (data)
    time_data = [0, 1, 2, 3, 4, 5, 6]
    study.add_column("t", ColumnType.DATA, unit="s", initial_data=time_data)
    
    # Add temperature column (data)
    temp_data = [20.0, 22.5, 25.0, 27.5, 30.0, 32.5, 35.0]
    study.add_column("T", ColumnType.DATA, unit="°C", initial_data=temp_data)
    
    workspace.add_study(study)
    
    # Create plot
    plot = PlotStudy("Temperature vs Time", workspace=workspace)
    plot.title = "Temperature Over Time"
    plot.xlabel = "t (s)"
    plot.ylabel = "T (°C)"
    plot.add_series(
        study_name="Temperature Measurements",
        x_column="t",
        y_column="T",
        label="Temperature",
        style="line",
        color="#e74c3c",
        marker="o",
        linestyle="-"
    )
    workspace.add_study(plot)
    
    return workspace


def create_02_constants_and_formulas():
    """Example 02: Constants and calculated columns."""
    workspace = Workspace("02 - Constants and Formulas", "numerical")
    workspace.metadata = {
        "description": "Using constants and formulas to calculate circle properties",
        "version": "0.2.0",
        "created": "2025-11-23"
    }
    
    # Add pi constant
    workspace.add_constant("pi", 3.141592653589793, None)
    
    # Create data table study
    study = DataTableStudy("Circle Properties", workspace=workspace)
    
    # Add radius column (range)
    study.add_column("r", ColumnType.RANGE, unit="m", 
                    range_type="linspace", range_start=1.0, range_stop=10.0, range_count=10)
    
    # Add calculated columns
    study.add_column("C", ColumnType.CALCULATED, formula="2 * pi * {r}", unit="m")
    study.add_column("A", ColumnType.CALCULATED, formula="pi * {r}**2", unit="m²")
    
    workspace.add_study(study)
    
    # Create plot
    plot = PlotStudy("Circumference vs Radius", workspace=workspace)
    plot.title = "Circle Circumference"
    plot.xlabel = "r (m)"
    plot.ylabel = "C (m)"
    plot.add_series(
        study_name="Circle Properties",
        x_column="r",
        y_column="C",
        label="C = 2πr",
        style="line",
        color="#3498db",
        marker="o",
        linestyle="-"
    )
    workspace.add_study(plot)
    
    return workspace


def create_03_ranges_and_derivatives():
    """Example 03: Range generation and numerical derivatives."""
    workspace = Workspace("03 - Ranges and Derivatives", "numerical")
    workspace.metadata = {
        "description": "Range generation and numerical differentiation for projectile motion",
        "version": "0.2.0",
        "created": "2025-11-23"
    }
    
    # Add constants
    workspace.add_constant("v0", 50.0, "m/s")
    workspace.add_constant("g", 9.81, "m/s²")
    
    # Create data table study
    study = DataTableStudy("Projectile Motion", workspace=workspace)
    
    # Add time range
    study.add_column("t", ColumnType.RANGE, unit="s",
                    range_type="linspace", range_start=0.0, range_stop=10.2, range_count=21)
    
    # Add height (calculated)
    study.add_column("h", ColumnType.CALCULATED, 
                    formula="v0 * {t} - 0.5 * g * {t}**2", unit="m")
    
    # Add velocity (derivative)
    study.add_column("v", ColumnType.DERIVATIVE, unit="m/s",
                    derivative_of="h", with_respect_to="t")
    
    # Add acceleration (second derivative)
    study.add_column("a", ColumnType.DERIVATIVE, unit="m/s²",
                    derivative_of="v", with_respect_to="t")
    
    workspace.add_study(study)
    
    # Create plot
    plot = PlotStudy("Height vs Time", workspace=workspace)
    plot.title = "Projectile Height"
    plot.xlabel = "t (s)"
    plot.ylabel = "h (m)"
    plot.add_series(
        study_name="Projectile Motion",
        x_column="t",
        y_column="h",
        label="Height",
        style="line",
        color="#2ecc71",
        marker="o",
        linestyle="-"
    )
    workspace.add_study(plot)
    
    return workspace


def create_04_uncertainty_propagation():
    """Example 04: Uncertainty propagation."""
    workspace = Workspace("04 - Uncertainty Propagation", "numerical")
    workspace.metadata = {
        "description": "Automatic uncertainty propagation using Ohm's law",
        "version": "0.2.0",
        "created": "2025-11-23"
    }
    
    # Create data table study
    study = DataTableStudy("Ohm's Law", workspace=workspace)
    
    # Add current column (data)
    current_data = [0.1, 0.2, 0.3, 0.4, 0.5]
    study.add_column("I", ColumnType.DATA, unit="A", initial_data=current_data)
    
    # Add resistance column (data)
    resistance_data = [100.0, 100.0, 100.0, 100.0, 100.0]
    study.add_column("R", ColumnType.DATA, unit="Ω", initial_data=resistance_data)
    
    # Add uncertainty columns (data)
    study.add_column("dI", ColumnType.DATA, unit="A", initial_data=[0.01] * 5)
    study.add_column("dR", ColumnType.DATA, unit="Ω", initial_data=[5.0] * 5)
    
    # Add calculated voltage
    study.add_column("V", ColumnType.CALCULATED, formula="{I} * {R}", unit="V")
    
    # Add propagated voltage uncertainty
    study.add_column("dV", ColumnType.UNCERTAINTY, unit="V",
                    uncertainty_reference="V", propagate_uncertainty=True)
    
    # Add calculated power
    study.add_column("P", ColumnType.CALCULATED, formula="{I} * {V}", unit="W")
    
    # Add propagated power uncertainty
    study.add_column("dP", ColumnType.UNCERTAINTY, unit="W",
                    uncertainty_reference="P", propagate_uncertainty=True)
    
    workspace.add_study(study)
    
    # Create plot with error bars
    plot = PlotStudy("Voltage vs Current", workspace=workspace)
    plot.title = "Ohm's Law with Uncertainties"
    plot.xlabel = "I (A)"
    plot.ylabel = "V (V)"
    plot.add_series(
        study_name="Ohm's Law",
        x_column="I",
        y_column="V",
        xerr_column="dI",
        yerr_column="dV",
        label="V = I×R",
        style="line",
        color="#9b59b6",
        marker="o",
        linestyle="-"
    )
    workspace.add_study(plot)
    
    return workspace


def create_05_custom_functions():
    """Example 05: Custom functions."""
    workspace = Workspace("05 - Custom Functions", "numerical")
    workspace.metadata = {
        "description": "User-defined functions for signal processing (1.5 Hz and 0.75 Hz sine waves)",
        "version": "0.2.0",
        "created": "2025-11-23"
    }
    
    # Add constants (use non-integer frequencies to avoid zero-crossing sampling)
    workspace.add_constant("f1", 1.5, "Hz")  # Changed from 5 Hz
    workspace.add_constant("f2", 0.75, "Hz")  # Changed from 2.5/3.7 Hz
    workspace.add_constant("A1", 1.0, "V")
    workspace.add_constant("A2", 1.0, "V")
    
    # Add custom functions
    workspace.add_function("sine_wave", "A * np.sin(2 * np.pi * f * t + phase)", 
                          ["t", "f", "A", "phase"], "V")
    workspace.add_function("rms", "np.sqrt((v1**2 + v2**2) / 2)", 
                          ["v1", "v2"], "V")
    
    # Create data table study
    study = DataTableStudy("Signal Analysis", workspace=workspace)
    
    # Add time range
    study.add_column("t", ColumnType.RANGE, unit="s",
                    range_type="linspace", range_start=0.0, range_stop=2.0, range_count=21)
    
    # Add signal columns
    study.add_column("s1", ColumnType.CALCULATED,
                    formula="sine_wave({t}, f1, A1, 0)", unit="V")
    study.add_column("s2", ColumnType.CALCULATED,
                    formula="sine_wave({t}, f2, A2, np.pi/4)", unit="V")
    study.add_column("sc", ColumnType.CALCULATED,
                    formula="{s1} + {s2}", unit="V")
    study.add_column("rms", ColumnType.CALCULATED,
                    formula="rms({s1}, {s2})", unit="V")
    
    workspace.add_study(study)
    
    # Create plots
    plot1 = PlotStudy("Waveforms", workspace=workspace)
    plot1.title = "Signal Waveforms"
    plot1.xlabel = "t (s)"
    plot1.ylabel = "Voltage (V)"
    plot1.add_series(study_name="Signal Analysis", x_column="t", y_column="s1",
                    label="Signal 1 (5 Hz)", style="line", color="#e74c3c", linestyle="-")
    plot1.add_series(study_name="Signal Analysis", x_column="t", y_column="s2",
                    label="Signal 2 (2.5 Hz)", style="line", color="#3498db", linestyle="-")
    plot1.add_series(study_name="Signal Analysis", x_column="t", y_column="sc",
                    label="Combined", style="line", color="#2ecc71", linestyle="--")
    workspace.add_study(plot1)
    
    plot2 = PlotStudy("RMS Analysis", workspace=workspace)
    plot2.title = "RMS Value Over Time"
    plot2.xlabel = "t (s)"
    plot2.ylabel = "RMS (V)"
    plot2.add_series(study_name="Signal Analysis", x_column="t", y_column="rms",
                    label="RMS", style="line", color="#f39c12", marker="o", linestyle="-")
    workspace.add_study(plot2)
    
    return workspace


def create_06_calculated_constants():
    """Example 06: Calculated constants with dependencies."""
    workspace = Workspace("06 - Calculated Constants", "numerical")
    workspace.metadata = {
        "description": "Calculated constants for ideal gas law (PV = nRT): V0 and n computed from other constants",
        "version": "0.2.0",
        "created": "2025-11-23"
    }
    
    # Add base constants
    workspace.add_constant("R", 8.314462618, "J/(mol·K)")
    workspace.add_constant("T0", 273.15, "K")
    workspace.add_constant("P0", 101325.0, "Pa")
    
    # Add calculated constants
    workspace.add_calculated_variable("V0", "R * T0 / P0", "m³")
    workspace.add_calculated_variable("n", "P0 * V0 / (R * T0)", "mol")
    
    # Create data table study
    study = DataTableStudy("Ideal Gas Behavior", workspace=workspace)
    
    # Add temperature range
    study.add_column("T", ColumnType.RANGE, unit="K",
                    range_type="linspace", range_start=273.15, range_stop=473.15, range_count=9)
    
    # Add calculated columns using constants
    study.add_column("P", ColumnType.CALCULATED,
                    formula="n * R * {T} / V0", unit="Pa")
    study.add_column("V", ColumnType.CALCULATED,
                    formula="n * R * {T} / P0", unit="m³")
    study.add_column("n", ColumnType.CALCULATED,
                    formula="P0 * V0 / (R * T0)", unit="mol")
    
    workspace.add_study(study)
    
    # Create plots
    plot1 = PlotStudy("Pressure vs Temperature", workspace=workspace)
    plot1.title = "Gay-Lussac's Law (P ∝ T at constant V)"
    plot1.xlabel = "T (K)"
    plot1.ylabel = "P (Pa)"
    plot1.add_series(study_name="Ideal Gas Behavior", x_column="T", y_column="P",
                    label="Constant Volume", style="line", color="#e74c3c", marker="o", linestyle="-")
    workspace.add_study(plot1)
    
    plot2 = PlotStudy("Volume vs Temperature", workspace=workspace)
    plot2.title = "Charles's Law (V ∝ T at constant P)"
    plot2.xlabel = "T (K)"
    plot2.ylabel = "V (m³)"
    plot2.add_series(study_name="Ideal Gas Behavior", x_column="T", y_column="V",
                    label="Constant Pressure", style="line", color="#3498db", marker="s", linestyle="-")
    workspace.add_study(plot2)
    
    return workspace


def create_07_advanced_kinematics():
    """Example 07: Advanced example with all features."""
    workspace = Workspace("07 - Advanced Kinematics", "numerical")
    workspace.metadata = {
        "description": "2D projectile motion with uncertainties, derivatives, and statistics",
        "version": "0.2.0",
        "created": "2025-11-23"
    }
    
    # Add constants
    workspace.add_constant("v0", 100.0, "m/s")
    workspace.add_constant("angle", 30.0, "°")
    workspace.add_constant("g", 9.81, "m/s²")
    
    # Create data table study
    study = DataTableStudy("Projectile Motion 2D", workspace=workspace)
    
    # Add time range
    study.add_column("t", ColumnType.RANGE, unit="s",
                    range_type="linspace", range_start=0.0, range_stop=10.0, range_count=21)
    
    # Add position columns
    study.add_column("x", ColumnType.CALCULATED,
                    formula="v0 * np.cos(np.radians(angle)) * {t}", unit="m")
    study.add_column("y", ColumnType.CALCULATED,
                    formula="v0 * np.sin(np.radians(angle)) * {t} - 0.5 * g * {t}**2", unit="m")
    
    # Add uncertainties for positions
    study.add_column("dx", ColumnType.DATA, unit="m", initial_data=[1.0] * 21)
    study.add_column("dy", ColumnType.DATA, unit="m", initial_data=[1.0] * 21)
    
    # Add velocity components (derivatives)
    study.add_column("vx", ColumnType.DERIVATIVE, unit="m/s",
                    derivative_of="x", with_respect_to="t")
    study.add_column("vy", ColumnType.DERIVATIVE, unit="m/s",
                    derivative_of="y", with_respect_to="t")
    
    # Add speed (calculated from velocity components)
    study.add_column("speed", ColumnType.CALCULATED,
                    formula="np.sqrt({vx}**2 + {vy}**2)", unit="m/s")
    
    # Add speed uncertainty (propagated)
    study.add_column("dspeed", ColumnType.UNCERTAINTY, unit="m/s",
                    uncertainty_reference="speed", propagate_uncertainty=True)
    
    workspace.add_study(study)
    
    # Create plots
    plot1 = PlotStudy("Trajectory", workspace=workspace)
    plot1.title = "2D Projectile Trajectory"
    plot1.xlabel = "x (m)"
    plot1.ylabel = "y (m)"
    plot1.add_series(study_name="Projectile Motion 2D", x_column="x", y_column="y",
                    xerr_column="dx", yerr_column="dy",
                    label="Trajectory", style="line", color="#e74c3c", marker="o", linestyle="-")
    workspace.add_study(plot1)
    
    plot2 = PlotStudy("Height vs Time", workspace=workspace)
    plot2.title = "Vertical Motion"
    plot2.xlabel = "t (s)"
    plot2.ylabel = "y (m)"
    plot2.add_series(study_name="Projectile Motion 2D", x_column="t", y_column="y",
                    yerr_column="dy",
                    label="Height", style="line", color="#2ecc71", marker="o", linestyle="-")
    workspace.add_study(plot2)
    
    plot3 = PlotStudy("Speed vs Time", workspace=workspace)
    plot3.title = "Speed Over Time"
    plot3.xlabel = "t (s)"
    plot3.ylabel = "speed (m/s)"
    plot3.add_series(study_name="Projectile Motion 2D", x_column="t", y_column="speed",
                    yerr_column="dspeed",
                    label="Speed", style="line", color="#3498db", marker="o", linestyle="-")
    workspace.add_study(plot3)
    
    return workspace


def verify_workspace(workspace: Workspace, filepath: Path):
    """Verify workspace by saving and reloading it.
    
    Args:
        workspace: Workspace to verify
        filepath: Path to save file
        
    Returns:
        True if verification passed, False otherwise
    """
    try:
        # Save workspace
        workspace_data = workspace.to_dict()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(workspace_data, f, indent=2)
        print(f"  ✓ Saved to {filepath.name}")
        
        # Load workspace back
        with open(filepath, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        loaded = Workspace.from_dict(loaded_data)
        print(f"  ✓ Loaded from {filepath.name}")
        
        # Verify basic properties
        assert loaded.name == workspace.name, "Name mismatch"
        assert loaded.workspace_type == workspace.workspace_type, "Type mismatch"
        assert len(loaded.studies) == len(workspace.studies), "Study count mismatch"
        assert len(loaded.constants) == len(workspace.constants), "Constants count mismatch"
        
        print(f"  ✓ Integrity verified: {len(loaded.studies)} studies, {len(loaded.constants)} constants")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Generate all example files."""
    examples_dir = Path(__file__).parent
    
    print("Generating DataManip Example Workspaces")
    print("=" * 60)
    
    examples = [
        ("01_basic_introduction.dmw", create_01_basic_introduction),
        ("02_constants_and_formulas.dmw", create_02_constants_and_formulas),
        ("03_ranges_and_derivatives.dmw", create_03_ranges_and_derivatives),
        ("04_uncertainty_propagation.dmw", create_04_uncertainty_propagation),
        ("05_custom_functions.dmw", create_05_custom_functions),
        ("06_calculated_constants.dmw", create_06_calculated_constants),
        ("07_advanced_kinematics.dmw", create_07_advanced_kinematics),
    ]
    
    success_count = 0
    
    for filename, creator_func in examples:
        print(f"\n{filename}")
        print("-" * 60)
        
        try:
            # Create workspace
            workspace = creator_func()
            print(f"  ✓ Created workspace: {workspace.name}")
            
            # Verify by saving and reloading
            filepath = examples_dir / filename
            if verify_workspace(workspace, filepath):
                success_count += 1
            
        except Exception as e:
            print(f"  ✗ Failed to create: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"Generated {success_count}/{len(examples)} examples successfully")
    
    if success_count == len(examples):
        print("✓ All examples created and verified!")
        return 0
    else:
        print("✗ Some examples failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
