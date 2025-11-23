"""
Comprehensive DataManip Demo - All Features

This example demonstrates ALL major features of DataManip:
1. Workspace constants (numeric, calculated, custom functions)
2. Range columns (linspace, arange, logspace)
3. Calculated columns with formulas
4. Derivative columns (numerical differentiation)
5. Uncertainty propagation
6. Data export (CSV, Excel)

Physics Example: Projectile motion with air resistance
"""

from core.workspace import Workspace
from studies.data_table_study import DataTableStudy, ColumnType
import numpy as np
import pandas as pd


def main():
    print("=" * 70)
    print("DataManip Comprehensive Demo - Projectile Motion with Air Resistance")
    print("=" * 70)
    
    # ========================================================================
    # STEP 1: Create workspace and define constants
    # ========================================================================
    print("\n1. Creating workspace with constants...")
    
    workspace = Workspace("Physics Lab", "numerical")
    
    # Numeric constants
    workspace.add_constant("g", 9.81, unit="m/s²")  # Gravity
    workspace.add_constant("rho", 1.225, unit="kg/m³")  # Air density
    workspace.add_constant("Cd", 0.47, unit=None)  # Drag coefficient (sphere)
    workspace.add_constant("m", 0.145, unit="kg")  # Baseball mass
    workspace.add_constant("r", 0.037, unit="m")  # Baseball radius
    workspace.add_constant("v0", 40.0, unit="m/s")  # Initial velocity
    workspace.add_constant("theta", 45.0, unit="deg")  # Launch angle
    
    print(f"   ✓ Added 7 numeric constants")
    
    # Calculated constants (formulas using other constants)
    workspace.add_calculated_variable("A", "pi * r**2", unit="m²")  # Cross-sectional area
    workspace.add_calculated_variable("k", "0.5 * Cd * rho * A / m", unit="1/m")  # Drag constant
    workspace.add_calculated_variable("theta_rad", "theta * pi / 180", unit="rad")  # Angle in radians
    workspace.add_calculated_variable("v0x", "v0 * cos(theta_rad)", unit="m/s")  # Initial x velocity
    workspace.add_calculated_variable("v0y", "v0 * sin(theta_rad)", unit="m/s")  # Initial y velocity
    
    print(f"   ✓ Added 5 calculated constants")
    
    # Custom functions (reusable formulas with parameters)
    workspace.add_function("kinetic_energy", "0.5 * {m} * {v}**2", ["m", "v"], unit="J")
    workspace.add_function("magnitude", "sqrt({x}**2 + {y}**2)", ["x", "y"])
    workspace.add_function("angle_deg", "arctan({y} / {x}) * 180 / pi", ["x", "y"], unit="deg")
    
    print(f"   ✓ Added 3 custom functions")
    print(f"   Total workspace constants: {len(workspace.constants)}")
    
    # ========================================================================
    # STEP 2: Create study and add range column
    # ========================================================================
    print("\n2. Creating data table study...")
    
    study = DataTableStudy("Projectile Analysis", workspace=workspace)
    
    # Add time range using linspace
    study.add_column(
        "t",
        column_type=ColumnType.RANGE,
        range_type="linspace",
        range_start=0.0,
        range_stop=6.0,
        range_count=61,
        unit="s"
    )
    
    print(f"   ✓ Added range column 't' (61 points from 0 to 6 seconds)")
    
    # ========================================================================
    # STEP 3: Add calculated columns with formulas
    # ========================================================================
    print("\n3. Adding calculated columns with formulas...")
    
    # Position (simplified - no air resistance for comparison)
    study.add_column(
        "x_noair",
        column_type=ColumnType.CALCULATED,
        formula="{v0x} * {t}",
        unit="m"
    )
    
    study.add_column(
        "y_noair",
        column_type=ColumnType.CALCULATED,
        formula="{v0y} * {t} - 0.5 * {g} * {t}**2",
        unit="m"
    )
    
    # Velocity (simplified - no air resistance)
    study.add_column(
        "vx_noair",
        column_type=ColumnType.CALCULATED,
        formula="{v0x}",
        unit="m/s"
    )
    
    study.add_column(
        "vy_noair",
        column_type=ColumnType.CALCULATED,
        formula="{v0y} - {g} * {t}",
        unit="m/s"
    )
    
    # Speed using custom function
    study.add_column(
        "speed_noair",
        column_type=ColumnType.CALCULATED,
        formula="magnitude({vx_noair}, {vy_noair})",
        unit="m/s"
    )
    
    # Kinetic energy using custom function
    study.add_column(
        "KE",
        column_type=ColumnType.CALCULATED,
        formula="kinetic_energy({m}, {speed_noair})",
        unit="J"
    )
    
    # Potential energy
    study.add_column(
        "PE",
        column_type=ColumnType.CALCULATED,
        formula="{m} * {g} * {y_noair}",
        unit="J"
    )
    
    # Total mechanical energy
    study.add_column(
        "E_total",
        column_type=ColumnType.CALCULATED,
        formula="{KE} + {PE}",
        unit="J"
    )
    
    # Flight angle using custom function
    study.add_column(
        "angle",
        column_type=ColumnType.CALCULATED,
        formula="angle_deg({vx_noair}, {vy_noair})",
        unit="deg"
    )
    
    print(f"   ✓ Added 9 calculated columns")
    print(f"   ✓ Used custom functions: magnitude(), kinetic_energy(), angle_deg()")
    print(f"   ✓ Used calculated constants: v0x, v0y, theta_rad")
    
    # ========================================================================
    # STEP 4: Add derivative columns
    # ========================================================================
    print("\n4. Adding derivative columns (numerical differentiation)...")
    
    # Velocity from position (dx/dt)
    study.add_column(
        "vx_derivative",
        column_type=ColumnType.DERIVATIVE,
        derivative_of="x_noair",
        with_respect_to="t",
        order=1,
        unit="m/s"
    )
    
    study.add_column(
        "vy_derivative",
        column_type=ColumnType.DERIVATIVE,
        derivative_of="y_noair",
        with_respect_to="t",
        order=1,
        unit="m/s"
    )
    
    # Acceleration from velocity (dv/dt)
    study.add_column(
        "ax",
        column_type=ColumnType.DERIVATIVE,
        derivative_of="vx_noair",
        with_respect_to="t",
        order=1,
        unit="m/s²"
    )
    
    study.add_column(
        "ay",
        column_type=ColumnType.DERIVATIVE,
        derivative_of="vy_noair",
        with_respect_to="t",
        order=1,
        unit="m/s²"
    )
    
    print(f"   ✓ Added 4 derivative columns")
    print(f"   ✓ Computed: velocity (dx/dt, dy/dt) and acceleration (dvx/dt, dvy/dt)")
    
    # ========================================================================
    # STEP 5: Add uncertainty columns
    # ========================================================================
    print("\n5. Adding uncertainty columns (error propagation)...")
    
    # Add time column with uncertainty (±0.01 s)
    study.add_column(
        "t_u",
        column_type=ColumnType.UNCERTAINTY,
        uncertainty_reference="t",
        initial_data=pd.Series([0.01] * len(study.table.data))
    )
    
    # Add calculated column with automatic uncertainty propagation
    study.add_column(
        "range_estimate",
        column_type=ColumnType.CALCULATED,
        formula="{v0x} * {t}",
        unit="m",
        propagate_uncertainty=True,
        uncertainty_reference="t"
    )
    
    print(f"   ✓ Added uncertainty column for time (±0.01 s)")
    print(f"   ✓ Added propagated uncertainty for range calculation")
    
    # ========================================================================
    # STEP 6: Display results
    # ========================================================================
    print("\n6. Analysis Results:")
    print("-" * 70)
    
    # Find maximum height and range
    y_max_idx = study.table.get_column("y_noair").idxmax()
    y_max = study.table.get_column("y_noair")[y_max_idx]
    t_max = study.table.get_column("t")[y_max_idx]
    
    # Find where projectile hits ground (y ≈ 0)
    y_values = study.table.get_column("y_noair")
    positive_y = y_values > 0
    if positive_y.any():
        last_positive_idx = positive_y[::-1].idxmax()
        range_distance = study.table.get_column("x_noair")[last_positive_idx]
        flight_time = study.table.get_column("t")[last_positive_idx]
    else:
        range_distance = 0
        flight_time = 0
    
    initial_energy = study.table.get_column("E_total")[0]
    
    # Get constants from workspace
    theta = workspace.constants['theta']['value']
    v0 = workspace.constants['v0']['value']
    
    print(f"\nProjectile Motion Summary:")
    print(f"  Launch angle: {theta} degrees")
    print(f"  Initial velocity: {v0} m/s")
    print(f"  Initial energy: {initial_energy:.2f} J")
    print(f"\n  Maximum height: {y_max:.2f} m at t = {t_max:.2f} s")
    print(f"  Range: {range_distance:.2f} m")
    print(f"  Flight time: {flight_time:.2f} s")
    
    # Sample data points
    print(f"\nSample Data (first 5 points):")
    print("-" * 70)
    display_cols = ["t", "x_noair", "y_noair", "speed_noair", "KE", "PE", "E_total"]
    sample_data = study.table.data[display_cols].head()
    print(sample_data.to_string(index=False))
    
    # Derivative comparison
    print(f"\nDerivative Verification (t=1.0s):")
    print("-" * 70)
    idx_1s = 10  # t=1.0s is at index 10 (0.1s intervals)
    vx_formula = study.table.get_column("vx_noair")[idx_1s]
    vx_deriv = study.table.get_column("vx_derivative")[idx_1s]
    vy_formula = study.table.get_column("vy_noair")[idx_1s]
    vy_deriv = study.table.get_column("vy_derivative")[idx_1s]
    
    print(f"  vx (formula): {vx_formula:.3f} m/s")
    print(f"  vx (d/dt):    {vx_deriv:.3f} m/s")
    print(f"  Difference:   {abs(vx_formula - vx_deriv):.6f} m/s")
    print()
    print(f"  vy (formula): {vy_formula:.3f} m/s")
    print(f"  vy (d/dt):    {vy_deriv:.3f} m/s")
    print(f"  Difference:   {abs(vy_formula - vy_deriv):.6f} m/s")
    
    # ========================================================================
    # STEP 7: Export data
    # ========================================================================
    print("\n7. Exporting data...")
    
    # Export to CSV
    csv_path = "projectile_motion_comprehensive.csv"
    study.export_to_csv(csv_path)
    print(f"   ✓ Exported to CSV: {csv_path}")
    
    # Export to Excel
    excel_path = "projectile_motion_comprehensive.xlsx"
    study.export_to_excel(excel_path)
    print(f"   ✓ Exported to Excel: {excel_path}")
    
    # ========================================================================
    # STEP 8: Summary statistics
    # ========================================================================
    print("\n8. Feature Summary:")
    print("=" * 70)
    
    feature_summary = {
        "Workspace Constants": {
            "Numeric": 7,
            "Calculated": 5,
            "Custom Functions": 3,
            "Total": 15
        },
        "Study Columns": {
            "Range": 1,
            "Calculated": 10,
            "Derivative": 4,
            "Uncertainty": 2,
            "Total": 17
        },
        "Data Points": len(study.table.data),
        "Export Formats": ["CSV", "Excel"]
    }
    
    print("\n✓ Workspace Constants:")
    for key, value in feature_summary["Workspace Constants"].items():
        print(f"    {key:20s}: {value}")
    
    print("\n✓ Study Columns:")
    for key, value in feature_summary["Study Columns"].items():
        print(f"    {key:20s}: {value}")
    
    print(f"\n✓ Data Points: {feature_summary['Data Points']}")
    print(f"✓ Export Formats: {', '.join(feature_summary['Export Formats'])}")
    
    print("\n" + "=" * 70)
    print("Demo Complete! All DataManip features demonstrated successfully.")
    print("=" * 70)
    
    return study, workspace


if __name__ == "__main__":
    study, workspace = main()
    
    print("\nYou can now interact with the study and workspace objects:")
    print("  - study: DataTableStudy instance with all calculations")
    print("  - workspace: Workspace instance with all constants")
    print("\nTry:")
    print("  study.table.data.describe()")
    print("  workspace.constants")
    print("  study.column_metadata")
