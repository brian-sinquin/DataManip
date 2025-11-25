"""
Generate all example workspace files programmatically.

This script creates 10 example .dmw files using the DataManip API,
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
    
Example Structure (Tutorial - One Feature Each):
    01 - Simple Pendulum: Basic data entry and plotting
    02 - Resistor Network: Calculated columns with formulas
    03 - Free Fall: Range generation (linspace)
    04 - Inclined Plane: Numerical derivatives
    05 - Density Measurement: Uncertainty propagation
    06 - Damped Oscillation: Custom functions
    
Example Structure (Complete Experiments - All Features):
    07 - Calorimetry: Heat capacity measurement with full analysis
    08 - Photoelectric Effect: Determining Planck's constant
    09 - Spring-Mass System: Damped SHM with energy analysis

Output:
    - 10 .dmw files in examples/ directory
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


def create_01_simple_pendulum():
    """Example 01: Simple pendulum - Basic data entry and plotting."""
    workspace = Workspace("01 - Simple Pendulum", "numerical")
    workspace.metadata = {
        "description": "Tutorial: Basic data entry - measuring period vs length for simple pendulum",
        "version": "0.2.0",
        "created": "2025-11-24"
    }
    
    # Create data table study
    study = DataTableStudy("Pendulum Measurements", workspace=workspace)
    
    # Measured data: length (0.2m to 1.2m) and period
    length_data = [0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00, 1.10, 1.20]
    period_data = [0.90, 1.10, 1.27, 1.42, 1.55, 1.68, 1.80, 1.91, 2.01, 2.11, 2.20]
    
    study.add_column("L", ColumnType.DATA, unit="m", initial_data=length_data)
    study.add_column("T", ColumnType.DATA, unit="s", initial_data=period_data)
    
    # Calculate T² for linearity check (T² ∝ L)
    study.add_column("T_squared", ColumnType.CALCULATED, formula="{T}**2", unit="s²")
    
    workspace.add_study(study)
    
    # Create plots
    plot1 = PlotStudy("Period vs Length", workspace=workspace)
    plot1.title = "Simple Pendulum: Period vs Length"
    plot1.xlabel = "L (m)"
    plot1.ylabel = "T (s)"
    plot1.add_series(
        study_name="Pendulum Measurements",
        x_column="L",
        y_column="T",
        label="Measured Period",
        style="line",
        color="#3498db",
        marker="o",
        linestyle="-"
    )
    workspace.add_study(plot1)
    
    plot2 = PlotStudy("T² vs L (Linearity)", workspace=workspace)
    plot2.title = "Linearity Check: T² ∝ L"
    plot2.xlabel = "L (m)"
    plot2.ylabel = "T² (s²)"
    plot2.add_series(
        study_name="Pendulum Measurements",
        x_column="L",
        y_column="T_squared",
        label="T² vs L",
        style="line",
        color="#e74c3c",
        marker="s",
        linestyle="-"
    )
    workspace.add_study(plot2)
    
    return workspace


def create_02_resistor_network():
    """Example 02: Resistor network - Calculated columns."""
    workspace = Workspace("02 - Resistor Network", "numerical")
    workspace.metadata = {
        "description": "Tutorial: Calculated columns - series and parallel resistor combinations",
        "version": "0.2.0",
        "created": "2025-11-24"
    }
    
    # Create data table study
    study = DataTableStudy("Resistor Combinations", workspace=workspace)
    
    # Measured resistances - R2 fixed at 100Ω, varying R1
    r1_data = [100, 150, 220, 330, 470, 680, 820, 1000, 1200, 1500]
    r2_data = [100] * 10
    
    study.add_column("R1", ColumnType.DATA, unit="Ω", initial_data=r1_data)
    study.add_column("R2", ColumnType.DATA, unit="Ω", initial_data=r2_data)
    
    # Calculated: series and parallel combinations
    study.add_column("Rseries", ColumnType.CALCULATED, 
                    formula="{R1} + {R2}", unit="Ω")
    study.add_column("Rparallel", ColumnType.CALCULATED,
                    formula="({R1} * {R2}) / ({R1} + {R2})", unit="Ω")
    
    workspace.add_study(study)
    
    # Create plots
    plot1 = PlotStudy("Series Resistance", workspace=workspace)
    plot1.title = "Series Combination: R_total = R1 + R2"
    plot1.xlabel = "R1 (Ω)"
    plot1.ylabel = "R_series (Ω)"
    plot1.add_series(
        study_name="Resistor Combinations",
        x_column="R1",
        y_column="Rseries",
        label="Series",
        style="line",
        color="#e74c3c",
        marker="s",
        linestyle="-"
    )
    workspace.add_study(plot1)
    
    plot2 = PlotStudy("Parallel Resistance", workspace=workspace)
    plot2.title = "Parallel Combination: 1/R_total = 1/R1 + 1/R2"
    plot2.xlabel = "R1 (Ω)"
    plot2.ylabel = "R_parallel (Ω)"
    plot2.add_series(
        study_name="Resistor Combinations",
        x_column="R1",
        y_column="Rparallel",
        label="Parallel",
        style="line",
        color="#3498db",
        marker="o",
        linestyle="-"
    )
    workspace.add_study(plot2)
    
    return workspace


def create_03_free_fall():
    """Example 03: Free fall - Range generation."""
    workspace = Workspace("03 - Free Fall", "numerical")
    workspace.metadata = {
        "description": "Tutorial: Range generation - free fall experiment with calculated positions",
        "version": "0.2.0",
        "created": "2025-11-24"
    }
    
    # Add constants
    workspace.add_constant("g", 9.81, "m/s²")
    workspace.add_constant("h0", 10.0, "m")
    
    # Create data table study
    study = DataTableStudy("Free Fall Motion", workspace=workspace)
    
    # Time range from 0 to 1.4s (just before hitting ground from 10m height)
    study.add_column("t", ColumnType.RANGE, unit="s",
                    range_type="linspace", range_start=0.0, range_stop=1.4, range_count=20)
    
    # Height calculated from kinematic equation: h = h₀ - ½gt²
    study.add_column("h", ColumnType.CALCULATED,
                    formula="h0 - 0.5 * g * {t}**2", unit="m")
    
    # Velocity magnitude (downward positive): v = gt
    study.add_column("v", ColumnType.CALCULATED,
                    formula="g * {t}", unit="m/s")
    
    workspace.add_study(study)
    
    # Create plots
    plot1 = PlotStudy("Height vs Time", workspace=workspace)
    plot1.title = "Free Fall: Height Decrease"
    plot1.xlabel = "t (s)"
    plot1.ylabel = "h (m)"
    plot1.add_series(
        study_name="Free Fall Drop",
        x_column="t",
        y_column="h",
        label="Height",
        style="line",
        color="#e74c3c",
        marker="o",
        linestyle="-"
    )
    workspace.add_study(plot1)
    
    plot2 = PlotStudy("Velocity vs Time", workspace=workspace)
    plot2.title = "Free Fall: Velocity Increase"
    plot2.xlabel = "t (s)"
    plot2.ylabel = "v (m/s)"
    plot2.add_series(
        study_name="Free Fall Drop",
        x_column="t",
        y_column="v",
        label="Velocity",
        style="line",
        color="#3498db",
        marker="s",
        linestyle="-"
    )
    workspace.add_study(plot2)
    
    return workspace


def create_04_inclined_plane():
    """Example 04: Inclined plane - Derivatives."""
    workspace = Workspace("04 - Inclined Plane", "numerical")
    workspace.metadata = {
        "description": "Tutorial: Derivatives - cart acceleration on inclined plane",
        "version": "0.2.0",
        "created": "2025-11-24"
    }
    
    # Create data table study
    study = DataTableStudy("Cart Motion", workspace=workspace)
    
    # Measured position data (cart rolling down 2° incline)
    time_data = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
    position_data = [0.000, 0.009, 0.034, 0.077, 0.137, 0.214, 0.308, 0.419, 0.548]
    
    study.add_column("t", ColumnType.DATA, unit="s", initial_data=time_data)
    study.add_column("x", ColumnType.DATA, unit="m", initial_data=position_data)
    
    # Velocity (first derivative)
    study.add_column("v", ColumnType.DERIVATIVE, unit="m/s",
                    derivative_of="x", with_respect_to="t")
    
    # Acceleration (second derivative)
    study.add_column("a", ColumnType.DERIVATIVE, unit="m/s²",
                    derivative_of="v", with_respect_to="t")
    
    workspace.add_study(study)
    
    # Create plots
    plot1 = PlotStudy("Position", workspace=workspace)
    plot1.title = "Cart Position vs Time"
    plot1.xlabel = "t (s)"
    plot1.ylabel = "x (m)"
    plot1.add_series(
        study_name="Cart Motion",
        x_column="t",
        y_column="x",
        label="Position",
        style="line",
        color="#2ecc71",
        marker="o",
        linestyle="-"
    )
    workspace.add_study(plot1)
    
    plot2 = PlotStudy("Velocity", workspace=workspace)
    plot2.title = "Cart Velocity (1st Derivative)"
    plot2.xlabel = "t (s)"
    plot2.ylabel = "v (m/s)"
    plot2.add_series(
        study_name="Cart Motion",
        x_column="t",
        y_column="v",
        label="Velocity",
        style="line",
        color="#3498db",
        marker="s",
        linestyle="-"
    )
    workspace.add_study(plot2)
    
    plot3 = PlotStudy("Acceleration", workspace=workspace)
    plot3.title = "Cart Acceleration (2nd Derivative)"
    plot3.xlabel = "t (s)"
    plot3.ylabel = "a (m/s²)"
    plot3.add_series(
        study_name="Cart Motion",
        x_column="t",
        y_column="a",
        label="Acceleration",
        style="scatter",
        color="#e74c3c",
        marker="^",
        linestyle=""
    )
    workspace.add_study(plot3)
    
    return workspace


def create_05_density_measurement():
    """Example 05: Density measurement - Uncertainty propagation."""
    workspace = Workspace("05 - Density Measurement", "numerical")
    workspace.metadata = {
        "description": "Tutorial: Uncertainty propagation - measuring metal cylinder density",
        "version": "0.2.0",
        "created": "2025-11-24"
    }
    
    # Create data table study
    study = DataTableStudy("Metal Cylinders", workspace=workspace)
    
    # Measured quantities for 7 different cylinders
    mass_data = [15.8, 23.5, 31.2, 42.1, 50.3, 65.7, 78.4]
    diameter_data = [10.1, 10.0, 10.2, 9.9, 10.1, 10.0, 9.8]
    height_data = [20.0, 30.1, 39.8, 50.2, 60.0, 79.9, 100.1]
    
    # Uncertainties
    mass_unc = [0.1, 0.1, 0.1, 0.2, 0.2, 0.2, 0.3]
    diameter_unc = [0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05]
    height_unc = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
    
    study.add_column("m", ColumnType.DATA, unit="g", initial_data=mass_data)
    study.add_column("d", ColumnType.DATA, unit="mm", initial_data=diameter_data)
    study.add_column("h", ColumnType.DATA, unit="mm", initial_data=height_data)
    
    study.add_column("dm", ColumnType.DATA, unit="g", initial_data=mass_unc)
    study.add_column("dd", ColumnType.DATA, unit="mm", initial_data=diameter_unc)
    study.add_column("dh", ColumnType.DATA, unit="mm", initial_data=height_unc)
    
    # Calculate volume (cylinder: V = πr²h)
    study.add_column("V", ColumnType.CALCULATED,
                    formula="np.pi * ({d}/2)**2 * {h}", unit="mm³")
    
    # Propagate volume uncertainty
    study.add_column("dV", ColumnType.UNCERTAINTY, unit="mm³",
                    uncertainty_reference="V", propagate_uncertainty=True)
    
    # Calculate density (convert to g/cm³: 1 mm³ = 0.001 cm³)
    study.add_column("ρ", ColumnType.CALCULATED,
                    formula="{m} / ({V} * 0.001)", unit="g/cm³")
    
    # Propagate density uncertainty
    study.add_column("δρ", ColumnType.UNCERTAINTY, unit="g/cm³",
                    uncertainty_reference="ρ", propagate_uncertainty=True)
    
    workspace.add_study(study)
    
    # Create plots
    plot1 = PlotStudy("Mass vs Volume", workspace=workspace)
    plot1.title = "Mass-Volume Relationship"
    plot1.xlabel = "V (mm³)"
    plot1.ylabel = "m (g)"
    plot1.add_series(
        study_name="Metal Cylinders",
        x_column="V",
        y_column="m",
        xerr_column="dV",
        yerr_column="dm",
        label="Measurements",
        style="line",
        color="#9b59b6",
        marker="o",
        linestyle="-"
    )
    workspace.add_study(plot1)
    
    plot2 = PlotStudy("Density Results", workspace=workspace)
    plot2.title = "Calculated Density with Uncertainties"
    plot2.xlabel = "Sample Number"
    plot2.ylabel = "ρ (g/cm³)"
    plot2.add_series(
        study_name="Metal Cylinders",
        x_column="h",  # Using height as proxy for sample order
        y_column="ρ",
        yerr_column="δρ",
        label="Density",
        style="scatter",
        color="#e74c3c",
        marker="s",
        linestyle=""
    )
    workspace.add_study(plot2)
    
    return workspace


def create_06_damped_oscillation():
    """Example 06: Damped oscillation - Custom functions."""
    workspace = Workspace("06 - Damped Oscillation", "numerical")
    workspace.metadata = {
        "description": "Tutorial: Custom functions - analyzing damped harmonic motion",
        "version": "0.2.0",
        "created": "2025-11-24"
    }
    
    # Add constants
    workspace.add_constant("A0", 10.0, "cm")
    workspace.add_constant("ω", 2.0, "rad/s")
    workspace.add_constant("γ", 0.15, "1/s")
    
    # Add custom function for damped oscillation
    workspace.add_function("damped_osc", 
                          "A0 * np.exp(-γ * t) * np.cos(ω * t)",
                          ["t", "A0", "ω", "γ"], "cm")
    workspace.add_function("envelope", 
                          "A0 * np.exp(-γ * t)",
                          ["t", "A0", "γ"], "cm")
    
    # Create data table study
    study = DataTableStudy("Damped Motion", workspace=workspace)
    
    # Time range
    study.add_column("t", ColumnType.RANGE, unit="s",
                    range_type="linspace", range_start=0.0, range_stop=20.0, range_count=101)
    
    # Position using custom function
    study.add_column("x", ColumnType.CALCULATED,
                    formula="damped_osc({t}, A0, ω, γ)", unit="cm")
    
    # Upper and lower envelopes
    study.add_column("env_plus", ColumnType.CALCULATED,
                    formula="envelope({t}, A0, γ)", unit="cm")
    study.add_column("env_minus", ColumnType.CALCULATED,
                    formula="-envelope({t}, A0, γ)", unit="cm")
    
    # Energy (proportional to amplitude squared)
    study.add_column("E", ColumnType.CALCULATED,
                    formula="({x})**2", unit="cm²")
    
    workspace.add_study(study)
    
    # Create plots
    plot1 = PlotStudy("Damped Oscillation", workspace=workspace)
    plot1.title = "Damped Harmonic Motion"
    plot1.xlabel = "t (s)"
    plot1.ylabel = "x (cm)"
    plot1.add_series(
        study_name="Damped Motion",
        x_column="t",
        y_column="x",
        label="Position",
        style="line",
        color="#3498db",
        linestyle="-"
    )
    plot1.add_series(
        study_name="Damped Motion",
        x_column="t",
        y_column="env_plus",
        label="Envelope",
        style="line",
        color="#e74c3c",
        linestyle="--"
    )
    plot1.add_series(
        study_name="Damped Motion",
        x_column="t",
        y_column="env_minus",
        label="",
        style="line",
        color="#e74c3c",
        linestyle="--"
    )
    workspace.add_study(plot1)
    
    plot2 = PlotStudy("Energy Decay", workspace=workspace)
    plot2.title = "Energy vs Time (Exponential Decay)"
    plot2.xlabel = "t (s)"
    plot2.ylabel = "E (cm²)"
    plot2.add_series(
        study_name="Damped Motion",
        x_column="t",
        y_column="E",
        label="Energy",
        style="line",
        color="#2ecc71",
        linestyle="-"
    )
    workspace.add_study(plot2)
    
    return workspace


def create_07_calorimetry():
    """Example 07: Calorimetry - Complete experiment with all features."""
    workspace = Workspace("07 - Calorimetry", "numerical")
    workspace.metadata = {
        "description": "Complete: Heat capacity measurement with uncertainties and thermal analysis",
        "version": "0.2.0",
        "created": "2025-11-24"
    }
    
    # Constants
    workspace.add_constant("m_water", 200.0, "g")
    workspace.add_constant("c_water", 4.184, "J/(g·K)")
    workspace.add_constant("T_initial", 20.0, "°C")
    
    # Calculated constant: water heat capacity
    workspace.add_calculated_variable("C_water", "m_water * c_water", "J/K")
    
    # Custom function for heat transfer
    workspace.add_function("heat_transfer", "m * c * (Tf - Ti)", ["m", "c", "Tf", "Ti"], "J")
    
    # Create data table study
    study = DataTableStudy("Heating Experiment", workspace=workspace)
    
    # Time range for heating
    study.add_column("t", ColumnType.RANGE, unit="s",
                    range_type="linspace", range_start=0.0, range_stop=300.0, range_count=31)
    
    # Measured temperature (with realistic heating curve)
    study.add_column("T", ColumnType.CALCULATED,
                    formula="T_initial + 0.15 * {t} + 0.0001 * {t}**2", unit="°C")
    
    # Temperature uncertainty (thermometer precision)
    study.add_column("dT", ColumnType.DATA, unit="°C", initial_data=[0.1] * 31)
    
    # Heat transfer rate (derivative of temperature → power)
    study.add_column("dTdt", ColumnType.DERIVATIVE, unit="°C/s",
                    derivative_of="T", with_respect_to="t")
    
    # Power input (P = C_water * dT/dt)
    study.add_column("P", ColumnType.CALCULATED,
                    formula="C_water * {dTdt}", unit="W")
    
    # Cumulative energy (integrate power over time)
    study.add_column("Q", ColumnType.CALCULATED,
                    formula="C_water * ({T} - T_initial)", unit="J")
    
    # Propagate uncertainty to energy
    study.add_column("dQ", ColumnType.UNCERTAINTY, unit="J",
                    uncertainty_reference="Q", propagate_uncertainty=True)
    
    workspace.add_study(study)
    
    # Create plots
    plot1 = PlotStudy("Temperature vs Time", workspace=workspace)
    plot1.title = "Calorimetry: Heating Curve"
    plot1.xlabel = "t (s)"
    plot1.ylabel = "T (°C)"
    plot1.add_series(
        study_name="Heating Experiment",
        x_column="t",
        y_column="T",
        yerr_column="dT",
        label="Temperature",
        style="line",
        color="#e74c3c",
        marker="o",
        linestyle="-"
    )
    workspace.add_study(plot1)
    
    plot2 = PlotStudy("Power Input", workspace=workspace)
    plot2.title = "Heating Power (from dT/dt)"
    plot2.xlabel = "t (s)"
    plot2.ylabel = "P (W)"
    plot2.add_series(
        study_name="Heating Experiment",
        x_column="t",
        y_column="P",
        label="Power",
        style="line",
        color="#3498db",
        marker="s",
        linestyle="-"
    )
    workspace.add_study(plot2)
    
    plot3 = PlotStudy("Energy vs Temperature", workspace=workspace)
    plot3.title = "Cumulative Heat Transfer"
    plot3.xlabel = "T (°C)"
    plot3.ylabel = "Q (J)"
    plot3.add_series(
        study_name="Heating Experiment",
        x_column="T",
        y_column="Q",
        yerr_column="dQ",
        label="Heat",
        style="line",
        color="#2ecc71",
        marker="^",
        linestyle="-"
    )
    workspace.add_study(plot3)
    
    return workspace


def create_07_calorimetry():
    """Example 07: Calorimetry - Complete experiment with all features."""
    workspace = Workspace("07 - Calorimetry", "numerical")
    workspace.metadata = {
        "description": "Complete: Heat capacity measurement with uncertainties and thermal analysis",
        "version": "0.2.0",
        "created": "2025-11-24"
    }
    
    # Constants
    workspace.add_constant("m_water", 200.0, "g")
    workspace.add_constant("c_water", 4.184, "J/(g·K)")
    workspace.add_constant("T_initial", 20.0, "°C")
    
    # Calculated constant: water heat capacity
    workspace.add_calculated_variable("C_water", "m_water * c_water", "J/K")
    
    # Custom function for heat transfer
    workspace.add_function("heat_transfer", "m * c * (Tf - Ti)", ["m", "c", "Tf", "Ti"], "J")
    
    # Create data table study
    study = DataTableStudy("Heating Experiment", workspace=workspace)
    
    # Time range for heating
    study.add_column("t", ColumnType.RANGE, unit="s",
                    range_type="linspace", range_start=0.0, range_stop=300.0, range_count=31)
    
    # Measured temperature (with realistic heating curve)
    study.add_column("T", ColumnType.CALCULATED,
                    formula="T_initial + 0.15 * {t} + 0.0001 * {t}**2", unit="°C")
    
    # Temperature uncertainty (thermometer precision)
    study.add_column("dT", ColumnType.DATA, unit="°C", initial_data=[0.1] * 31)
    
    # Heat transfer rate (derivative of temperature → power)
    study.add_column("dTdt", ColumnType.DERIVATIVE, unit="°C/s",
                    derivative_of="T", with_respect_to="t")
    
    # Power input (P = C_water * dT/dt)
    study.add_column("P", ColumnType.CALCULATED,
                    formula="C_water * {dTdt}", unit="W")
    
    # Cumulative energy (integrate power over time)
    study.add_column("Q", ColumnType.CALCULATED,
                    formula="C_water * ({T} - T_initial)", unit="J")
    
    # Propagate uncertainty to energy
    study.add_column("dQ", ColumnType.UNCERTAINTY, unit="J",
                    uncertainty_reference="Q", propagate_uncertainty=True)
    
    workspace.add_study(study)
    
    # Create plots
    plot1 = PlotStudy("Temperature vs Time", workspace=workspace)
    plot1.title = "Calorimetry: Heating Curve"
    plot1.xlabel = "t (s)"
    plot1.ylabel = "T (°C)"
    plot1.add_series(
        study_name="Heating Experiment",
        x_column="t",
        y_column="T",
        yerr_column="dT",
        label="Temperature",
        style="line",
        color="#e74c3c",
        marker="o",
        linestyle="-"
    )
    workspace.add_study(plot1)
    
    plot2 = PlotStudy("Power Input", workspace=workspace)
    plot2.title = "Heating Power (from dT/dt)"
    plot2.xlabel = "t (s)"
    plot2.ylabel = "P (W)"
    plot2.add_series(
        study_name="Heating Experiment",
        x_column="t",
        y_column="P",
        label="Power",
        style="line",
        color="#3498db",
        marker="s",
        linestyle="-"
    )
    workspace.add_study(plot2)
    
    plot3 = PlotStudy("Energy vs Temperature", workspace=workspace)
    plot3.title = "Cumulative Heat Transfer"
    plot3.xlabel = "T (°C)"
    plot3.ylabel = "Q (J)"
    plot3.add_series(
        study_name="Heating Experiment",
        x_column="T",
        y_column="Q",
        yerr_column="dQ",
        label="Heat",
        style="line",
        color="#2ecc71",
        marker="^",
        linestyle="-"
    )
    workspace.add_study(plot3)
    
    return workspace


def create_08_photoelectric_effect():
    """Example 08: Photoelectric Effect - Planck's constant determination."""
    workspace = Workspace("08 - Photoelectric Effect", "numerical")
    workspace.metadata = {
        "description": "Complete: Determining Planck's constant from photoelectric effect",
        "version": "0.2.0",
        "created": "2025-11-24"
    }
    
    # Constants
    workspace.add_constant("c", 2.998e8, "m/s")
    workspace.add_constant("e", 1.602e-19, "C")
    workspace.add_constant("φ", 2.28, "eV")  # Work function of sodium
    
    # Calculated constant: speed of light in nm/s
    workspace.add_calculated_variable("c_nm", "c * 1e9", "nm/s")
    
    # Custom function: theoretical stopping potential
    # From Einstein: K_max = h*f - φ, and K_max = e*V_stop
    # So V_stop = (h*f - φ)/e = (h/e)*f - φ/e
    workspace.add_function("V_theory", "(h_eV * f_THz - φ) / 1.0", 
                          ["f_THz", "h_eV", "φ"], "V")
    
    # Create data table study
    study = DataTableStudy("Photoelectric Measurements", workspace=workspace)
    
    # Measured wavelengths (UV to violet) - λ in column headers shown as Greek
    wavelength_data = [365, 405, 436, 492, 546, 577]
    study.add_column("lambda_nm", ColumnType.DATA, unit="nm", initial_data=wavelength_data)
    
    # Wavelength uncertainty (spectrometer resolution)
    study.add_column("d_lambda", ColumnType.DATA, unit="nm", initial_data=[2.0] * 6)
    
    # Measured stopping potentials
    v_stop_data = [1.10, 0.78, 0.56, 0.24, -0.10, -0.31]
    study.add_column("V_stop", ColumnType.DATA, unit="V", initial_data=v_stop_data)
    
    # Stopping potential uncertainty (voltmeter precision)
    study.add_column("d_Vstop", ColumnType.DATA, unit="V", initial_data=[0.02] * 6)
    
    # Frequency (c/λ) - convert from Hz to THz
    study.add_column("f_THz", ColumnType.CALCULATED,
                    formula="(c_nm / {lambda_nm}) / 1e12", unit="THz")
    
    # Propagate frequency uncertainty
    study.add_column("d_f", ColumnType.UNCERTAINTY, unit="THz",
                    uncertainty_reference="f_THz", propagate_uncertainty=True)
    
    # Kinetic energy (K = e * V_stop)
    study.add_column("K_J", ColumnType.CALCULATED,
                    formula="e * {V_stop}", unit="J")
    
    # Convert to eV for easier interpretation
    study.add_column("K_eV", ColumnType.CALCULATED,
                    formula="{V_stop}", unit="eV")
    
    # Propagate kinetic energy uncertainty
    study.add_column("d_K", ColumnType.UNCERTAINTY, unit="eV",
                    uncertainty_reference="K_eV", propagate_uncertainty=True)
    
    workspace.add_study(study)
    
    # Create plots
    plot1 = PlotStudy("Stopping Potential vs Frequency", workspace=workspace)
    plot1.title = "Photoelectric Effect: V_stop vs f (Slope = h/e)"
    plot1.xlabel = "f (THz)"
    plot1.ylabel = "V_stop (V)"
    plot1.add_series(
        study_name="Photoelectric Measurements",
        x_column="f_THz",
        y_column="V_stop",
        xerr_column="d_f",
        yerr_column="d_Vstop",
        label="Measurements",
        style="scatter",
        color="#9b59b6",
        marker="o",
        linestyle=""
    )
    workspace.add_study(plot1)
    
    plot2 = PlotStudy("Energy vs Wavelength", workspace=workspace)
    plot2.title = "Kinetic Energy vs Wavelength"
    plot2.xlabel = "λ (nm)"
    plot2.ylabel = "K (eV)"
    plot2.add_series(
        study_name="Photoelectric Measurements",
        x_column="lambda_nm",
        y_column="K_eV",
        xerr_column="d_lambda",
        yerr_column="d_K",
        label="Kinetic Energy",
        style="scatter",
        color="#e74c3c",
        marker="s",
        linestyle=""
    )
    workspace.add_study(plot2)
    
    return workspace


def create_09_spring_mass_shm():
    """Example 09: Spring-Mass System - Complete SHM analysis with damping."""
    workspace = Workspace("09 - Spring-Mass System", "numerical")
    workspace.metadata = {
        "description": "Complete: Simple harmonic motion with damping and energy analysis",
        "version": "0.2.0",
        "created": "2025-11-24"
    }
    
    # Constants
    workspace.add_constant("m", 0.250, "kg")
    workspace.add_constant("k", 25.0, "N/m")
    workspace.add_constant("b", 0.30, "kg/s")  # Damping coefficient
    workspace.add_constant("x0", 0.15, "m")
    
    # Calculated constants
    workspace.add_calculated_variable("ω0", "np.sqrt(k / m)", "rad/s")
    workspace.add_calculated_variable("γ", "b / (2 * m)", "1/s")
    workspace.add_calculated_variable("ω", "np.sqrt(ω0**2 - γ**2)", "rad/s")
    workspace.add_calculated_variable("T", "2 * np.pi / ω", "s")
    
    # Custom functions
    workspace.add_function("position", 
                          "x0 * np.exp(-γ * t) * np.cos(ω * t)",
                          ["t", "x0", "γ", "ω"], "m")
    workspace.add_function("velocity_analytic",
                          "-x0 * np.exp(-γ * t) * (γ * np.cos(ω * t) + ω * np.sin(ω * t))",
                          ["t", "x0", "γ", "ω"], "m/s")
    workspace.add_function("kinetic_energy",
                          "0.5 * m * v**2",
                          ["v", "m"], "J")
    workspace.add_function("potential_energy",
                          "0.5 * k * x**2",
                          ["x", "k"], "J")
    
    # Create data table study
    study = DataTableStudy("Damped Oscillation", workspace=workspace)
    
    # Time range (3 periods)
    study.add_column("t", ColumnType.RANGE, unit="s",
                    range_type="linspace", range_start=0.0, range_stop=3.8, range_count=77)
    
    # Position using custom function
    study.add_column("x", ColumnType.CALCULATED,
                    formula="position({t}, x0, γ, ω)", unit="m")
    
    # Position uncertainty (measurement error)
    study.add_column("dx", ColumnType.DATA, unit="m", initial_data=[0.002] * 77)
    
    # Velocity from derivative
    study.add_column("v", ColumnType.DERIVATIVE, unit="m/s",
                    derivative_of="x", with_respect_to="t")
    
    # Propagate velocity uncertainty
    study.add_column("dv", ColumnType.UNCERTAINTY, unit="m/s",
                    uncertainty_reference="v", propagate_uncertainty=True)
    
    # Acceleration from second derivative
    study.add_column("a", ColumnType.DERIVATIVE, unit="m/s²",
                    derivative_of="v", with_respect_to="t")
    
    # Energies
    study.add_column("KE", ColumnType.CALCULATED,
                    formula="kinetic_energy({v}, m)", unit="J")
    study.add_column("PE", ColumnType.CALCULATED,
                    formula="potential_energy({x}, k)", unit="J")
    study.add_column("E_total", ColumnType.CALCULATED,
                    formula="{KE} + {PE}", unit="J")
    
    # Propagate total energy uncertainty
    study.add_column("dE", ColumnType.UNCERTAINTY, unit="J",
                    uncertainty_reference="E_total", propagate_uncertainty=True)
    
    workspace.add_study(study)
    
    # Create plots
    plot1 = PlotStudy("Position vs Time", workspace=workspace)
    plot1.title = "Damped SHM: Position"
    plot1.xlabel = "t (s)"
    plot1.ylabel = "x (m)"
    plot1.add_series(
        study_name="Damped Oscillation",
        x_column="t",
        y_column="x",
        yerr_column="dx",
        label="Position",
        style="line",
        color="#3498db",
        marker="o",
        linestyle="-"
    )
    workspace.add_study(plot1)
    
    plot2 = PlotStudy("Phase Space", workspace=workspace)
    plot2.title = "Phase Space Diagram (Damping Spiral)"
    plot2.xlabel = "x (m)"
    plot2.ylabel = "v (m/s)"
    plot2.add_series(
        study_name="Damped Oscillation",
        x_column="x",
        y_column="v",
        label="Phase Trajectory",
        style="line",
        color="#2ecc71",
        linestyle="-"
    )
    workspace.add_study(plot2)
    
    plot3 = PlotStudy("Energy vs Time", workspace=workspace)
    plot3.title = "Energy Components (Dissipation)"
    plot3.xlabel = "t (s)"
    plot3.ylabel = "E (J)"
    plot3.add_series(
        study_name="Damped Oscillation",
        x_column="t",
        y_column="KE",
        label="Kinetic",
        style="line",
        color="#e74c3c",
        linestyle="--"
    )
    plot3.add_series(
        study_name="Damped Oscillation",
        x_column="t",
        y_column="PE",
        label="Potential",
        style="line",
        color="#3498db",
        linestyle="--"
    )
    plot3.add_series(
        study_name="Damped Oscillation",
        x_column="t",
        y_column="E_total",
        yerr_column="dE",
        label="Total",
        style="line",
        color="#2ecc71",
        marker="o",
        linestyle="-"
    )
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
        ("01_simple_pendulum.dmw", create_01_simple_pendulum),
        ("02_resistor_network.dmw", create_02_resistor_network),
        ("03_free_fall.dmw", create_03_free_fall),
        ("04_inclined_plane.dmw", create_04_inclined_plane),
        ("05_density_measurement.dmw", create_05_density_measurement),
        ("06_damped_oscillation.dmw", create_06_damped_oscillation),
        ("07_calorimetry.dmw", create_07_calorimetry),
        ("08_photoelectric_effect.dmw", create_08_photoelectric_effect),
        ("09_spring_mass_shm.dmw", create_09_spring_mass_shm),
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
