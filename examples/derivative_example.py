"""
Example: Using derivative columns to analyze motion.

This example demonstrates:
- Computing velocity from position data (first derivative)
- Computing acceleration from velocity (second derivative)
- Analyzing oscillatory motion (position → velocity → acceleration)
"""

import sys
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from studies.data_table_study import DataTableStudy, ColumnType


def main():
    print("=" * 70)
    print("DERIVATIVE COLUMN EXAMPLE: Simple Harmonic Motion")
    print("=" * 70)
    
    # Create study
    study = DataTableStudy("harmonic_motion")
    
    # Generate time data
    t = np.linspace(0, 4*np.pi, 201)  # 0 to 2 full periods
    
    # Position: x(t) = A * sin(ωt)
    A = 2.0  # amplitude (m)
    omega = 1.0  # angular frequency (rad/s)
    x = A * np.sin(omega * t)
    
    # Add time and position columns
    study.add_column("t", ColumnType.DATA, initial_data=t, unit="s")
    study.add_column("x", ColumnType.DATA, initial_data=x, unit="m")
    
    # Add velocity as derivative of position
    # Analytical: v(t) = A*ω*cos(ωt)
    study.add_column(
        "v",
        ColumnType.DERIVATIVE,
        derivative_of="x",
        with_respect_to="t",
        unit="m/s"
    )
    
    # Add acceleration as derivative of velocity
    # Analytical: a(t) = -A*ω²*sin(ωt) = -ω²*x(t)
    study.add_column(
        "a",
        ColumnType.DERIVATIVE,
        derivative_of="v",
        with_respect_to="t",
        unit="m/s^2"
    )
    
    # Display sample values
    print("\nSimple Harmonic Motion: x(t) = 2.0 * sin(t)")
    print("\nSample data (every 20th point):")
    print("-" * 70)
    print(f"{'t [s]':>8} {'x [m]':>10} {'v [m/s]':>12} {'a [m/s^2]':>14}")
    print("-" * 70)
    
    for i in range(0, len(study.table.data), 20):
        t_val = study.table.data.at[i, "t"]
        x_val = study.table.data.at[i, "x"]
        v_val = study.table.data.at[i, "v"]
        a_val = study.table.data.at[i, "a"]
        print(f"{t_val:8.2f} {x_val:10.4f} {v_val:12.4f} {a_val:14.4f}")
    
    # Verify relationships
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)
    
    # Check that acceleration ≈ -ω² * position
    x_vals = study.table.data["x"].values
    a_vals = study.table.data["a"].values
    expected_a = -omega**2 * x_vals
    
    # Skip edge points for numerical derivative
    error = np.abs(a_vals[10:-10] - expected_a[10:-10])
    max_error = np.max(error)
    mean_error = np.mean(error)
    
    print(f"\nRelationship: a(t) = -ω² * x(t) where ω = {omega} rad/s")
    print(f"  Max error: {max_error:.6f} m/s²")
    print(f"  Mean error: {mean_error:.6f} m/s²")
    
    if max_error < 0.01:
        print("  ✓ Relationship verified!")
    else:
        print("  ⚠ Higher error than expected (numerical derivative limitations)")
    
    # Energy analysis
    print("\nEnergy Analysis:")
    m = 1.0  # mass (kg)
    KE = 0.5 * m * study.table.data["v"]**2
    PE = 0.5 * m * omega**2 * study.table.data["x"]**2
    E_total = KE + PE
    
    E_mean = E_total.mean()
    E_std = E_total.std()
    E_theoretical = 0.5 * m * (A * omega)**2
    
    print(f"  Theoretical total energy: {E_theoretical:.4f} J")
    print(f"  Computed total energy: {E_mean:.4f} ± {E_std:.6f} J")
    print(f"  Energy conservation: {E_std/E_mean*100:.4f}% variation")
    
    print("\n" + "=" * 70)
    print("Example complete!")
    print("\nThis demonstrates how derivative columns automatically compute")
    print("derivatives using numerical differentiation, perfect for analyzing")
    print("experimental data where you only have position measurements.")
    print("=" * 70)


if __name__ == "__main__":
    main()
