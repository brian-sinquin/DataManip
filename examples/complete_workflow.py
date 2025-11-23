"""
Example: Complete data analysis workflow.

This example demonstrates the full power of DataManip by combining:
- Range columns (auto-generated sequences)
- Calculated columns (formulas)
- Derivative columns (numerical differentiation)

Analysis: Damped harmonic oscillator
"""

import sys
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from studies.data_table_study import DataTableStudy, ColumnType


def main():
    print("=" * 70)
    print("COMPLETE WORKFLOW: Damped Harmonic Oscillator Analysis")
    print("=" * 70)
    
    # Create study
    study = DataTableStudy("damped_oscillator")
    
    # Add constants
    study.add_variable("A", 2.0)  # amplitude (m)
    study.add_variable("omega", 2.0)  # angular frequency (rad/s)
    study.add_variable("gamma", 0.2)  # damping coefficient (1/s)
    
    print("\nSystem parameters:")
    print(f"  Amplitude A = {study.variables['A'][0]} m")
    print(f"  Angular frequency ω = {study.variables['omega'][0]} rad/s")
    print(f"  Damping coefficient γ = {study.variables['gamma'][0]} 1/s")
    
    # Step 1: Generate time range
    print("\n" + "-" * 70)
    print("Step 1: Generate time range (0 to 10s, 201 points)")
    print("-" * 70)
    
    study.add_column(
        "t",
        ColumnType.RANGE,
        range_type="linspace",
        range_start=0,
        range_stop=10,
        range_count=201,
        unit="s"
    )
    print("✓ Created range column 't'")
    
    # Step 2: Calculate position
    # x(t) = A * exp(-γt) * cos(ωt)
    print("\n" + "-" * 70)
    print("Step 2: Calculate position x(t) = A exp(-γt) cos(ωt)")
    print("-" * 70)
    
    study.add_column(
        "x",
        ColumnType.CALCULATED,
        formula="{A} * np.exp(-{gamma} * {t}) * np.cos({omega} * {t})",
        unit="m"
    )
    print("✓ Created calculated column 'x'")
    
    # Step 3: Calculate velocity (derivative)
    print("\n" + "-" * 70)
    print("Step 3: Calculate velocity v = dx/dt")
    print("-" * 70)
    
    study.add_column(
        "v",
        ColumnType.DERIVATIVE,
        derivative_of="x",
        with_respect_to="t",
        unit="m/s"
    )
    print("✓ Created derivative column 'v'")
    
    # Step 4: Calculate acceleration (second derivative)
    print("\n" + "-" * 70)
    print("Step 4: Calculate acceleration a = dv/dt")
    print("-" * 70)
    
    study.add_column(
        "a",
        ColumnType.DERIVATIVE,
        derivative_of="v",
        with_respect_to="t",
        unit="m/s^2"
    )
    print("✓ Created derivative column 'a'")
    
    # Step 5: Calculate energy
    print("\n" + "-" * 70)
    print("Step 5: Calculate kinetic and potential energy")
    print("-" * 70)
    
    m = 1.0  # mass (kg)
    study.add_variable("m", m)
    study.add_variable("k", m * study.variables["omega"][0]**2)  # spring constant
    
    study.add_column(
        "KE",
        ColumnType.CALCULATED,
        formula="0.5 * {m} * {v}**2",
        unit="J"
    )
    
    study.add_column(
        "PE",
        ColumnType.CALCULATED,
        formula="0.5 * {k} * {x}**2",
        unit="J"
    )
    
    study.add_column(
        "E_total",
        ColumnType.CALCULATED,
        formula="{KE} + {PE}",
        unit="J"
    )
    print("✓ Created energy columns (KE, PE, E_total)")
    
    # Display results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    print("\nSample data (every 20th point):")
    print("-" * 70)
    print(f"{'t [s]':>8} {'x [m]':>10} {'v [m/s]':>12} {'a [m/s^2]':>14} {'E [J]':>10}")
    print("-" * 70)
    
    for i in range(0, len(study.table.data), 20):
        t_val = study.table.data.at[i, "t"]
        x_val = study.table.data.at[i, "x"]
        v_val = study.table.data.at[i, "v"]
        a_val = study.table.data.at[i, "a"]
        E_val = study.table.data.at[i, "E_total"]
        print(f"{t_val:8.2f} {x_val:10.4f} {v_val:12.4f} {a_val:14.4f} {E_val:10.4f}")
    
    # Analysis
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    
    # Find amplitude decay
    t_vals = study.table.data["t"].values
    x_vals = study.table.data["x"].values
    envelope = study.variables["A"][0] * np.exp(-study.variables["gamma"][0] * t_vals)
    
    print(f"\nAmplitude decay:")
    print(f"  Initial amplitude: {envelope[0]:.4f} m")
    print(f"  Final amplitude: {envelope[-1]:.4f} m")
    print(f"  Decay to {envelope[-1]/envelope[0]*100:.1f}% of initial")
    
    # Energy loss
    E_initial = study.table.data.at[0, "E_total"]
    E_final = study.table.data.at[len(study.table.data)-1, "E_total"]
    
    print(f"\nEnergy dissipation:")
    print(f"  Initial energy: {E_initial:.4f} J")
    print(f"  Final energy: {E_final:.4f} J")
    print(f"  Energy lost: {(E_initial - E_final):.4f} J ({(E_initial - E_final)/E_initial*100:.1f}%)")
    
    # Column summary
    print("\n" + "=" * 70)
    print("COLUMN SUMMARY")
    print("=" * 70)
    
    print(f"\nTotal columns: {len(study.table.columns)}")
    for col_name in study.table.columns:
        col_type = study.get_column_type(col_name)
        col_unit = study.get_column_unit(col_name)
        unit_str = f" [{col_unit}]" if col_unit else ""
        print(f"  {col_name}{unit_str} ({col_type})")
    
    print("\n" + "=" * 70)
    print("Analysis complete!")
    print("\nThis workflow demonstrates:")
    print("  ✓ Range columns for automatic sequence generation")
    print("  ✓ Calculated columns with formulas and variables")
    print("  ✓ Derivative columns for numerical differentiation")
    print("  ✓ Complex multi-step analysis in a few lines of code")
    print("=" * 70)


if __name__ == "__main__":
    main()
