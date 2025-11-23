"""
Projectile motion example.

Demonstrates:
- Range columns for evenly-spaced time values
- Calculated columns for position using physics formulas
- Derivative columns for velocity and acceleration
- Variable usage for constants
"""

import sys
from pathlib import Path
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from studies.data_table_study import DataTableStudy, ColumnType


def main():
    """Create projectile motion analysis."""
    print("=" * 70)
    print("PROJECTILE MOTION EXAMPLE")
    print("=" * 70)
    
    # Create study
    study = DataTableStudy("Projectile Motion")
    
    # Initial conditions
    v0 = 20.0  # m/s
    angle = 45  # degrees
    g = 9.81  # m/s²
    
    # Set variables
    study.add_variable("v0", v0, "m/s")
    study.add_variable("angle_deg", angle, "deg")
    study.add_variable("g", g, "m/s^2")
    study.add_variable("angle_rad", np.deg2rad(angle), "rad")
    study.add_variable("cos_angle", np.cos(np.deg2rad(angle)))
    study.add_variable("sin_angle", np.sin(np.deg2rad(angle)))
    
    print("\nInitial conditions:")
    print(f"  v0 = {v0} m/s")
    print(f"  angle = {angle}°")
    print(f"  g = {g} m/s²")
    
    # Time range from 0 to 3 seconds
    print("\n" + "-" * 70)
    print("Creating time range (0 to 3s, 31 points)")
    study.add_column(
        "t",
        ColumnType.RANGE,
        range_type="linspace",
        range_start=0.0,
        range_stop=3.0,
        range_count=31,
        unit="s"
    )
    print("✓ Time column created")
    
    # Horizontal position: x = v0 * cos(θ) * t
    print("\n" + "-" * 70)
    print("Calculating horizontal position: x = v0·cos(θ)·t")
    study.add_column(
        "x",
        ColumnType.CALCULATED,
        formula="{v0} * {cos_angle} * {t}",
        unit="m"
    )
    print("✓ x column created")
    
    # Vertical position: y = v0 * sin(θ) * t - 0.5 * g * t²
    print("\n" + "-" * 70)
    print("Calculating vertical position: y = v0·sin(θ)·t - 0.5·g·t²")
    study.add_column(
        "y",
        ColumnType.CALCULATED,
        formula="{v0} * {sin_angle} * {t} - 0.5 * {g} * {t}**2",
        unit="m"
    )
    print("✓ y column created")
    
    # Horizontal velocity (derivative)
    print("\n" + "-" * 70)
    print("Calculating horizontal velocity: vx = dx/dt")
    study.add_column(
        "vx",
        ColumnType.DERIVATIVE,
        derivative_of="x",
        with_respect_to="t",
        order=1,
        unit="m/s"
    )
    print("✓ vx column created")
    
    # Vertical velocity (derivative)
    print("\n" + "-" * 70)
    print("Calculating vertical velocity: vy = dy/dt")
    study.add_column(
        "vy",
        ColumnType.DERIVATIVE,
        derivative_of="y",
        with_respect_to="t",
        order=1,
        unit="m/s"
    )
    print("✓ vy column created")
    
    print("\n" + "=" * 70)
    print("Data sample (first 10 rows):")
    print("=" * 70)
    print(study.table.data.head(10))
    
    print("\n" + "=" * 70)
    print("Example complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
