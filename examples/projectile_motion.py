"""
Projectile motion example.

Demonstrates:
- Range columns for evenly-spaced time values
- Calculated columns for position using physics formulas
- Derivative columns for velocity and acceleration
- Uncertainty propagation
"""

from widgets import DataTableModel
import numpy as np

def create_projectile_motion_table():
    """Create a projectile motion data table."""
    model = DataTableModel()
    
    # Initial conditions
    v0 = 20.0  # m/s
    angle = 45  # degrees
    g = 9.81  # m/s²
    
    # Set variables
    model.set_variables({
        'v0': v0,
        'angle': angle,
        'g': g,
        'angle_rad': np.deg2rad(angle)
    })
    
    # Time range from 0 to 3 seconds
    model.add_range_column(
        name="t",
        start=0.0,
        end=3.0,
        points=31,
        unit="s",
        description="Time"
    )
    
    # Horizontal position
    model.add_calculated_column(
        name="x",
        formula="v0 * cos(angle_rad) * {t}",
        unit="m",
        description="Horizontal position",
        propagate_uncertainty=True
    )
    
    # Vertical position
    model.add_calculated_column(
        name="y",
        formula="v0 * sin(angle_rad) * {t} - 0.5 * g * {t}**2",
        unit="m",
        description="Vertical position",
        propagate_uncertainty=True
    )
    
    # Horizontal velocity (derivative)
    model.add_derivative_column(
        name="vx",
        numerator="x",
        denominator="t",
        description="Horizontal velocity"
    )
    
    # Vertical velocity (derivative)
    model.add_derivative_column(
        name="vy",
        numerator="y",
        denominator="t",
        description="Vertical velocity"
    )
    
    # Total velocity
    model.add_calculated_column(
        name="v",
        formula="sqrt({vx}**2 + {vy}**2)",
        unit="m/s",
        description="Total velocity"
    )
    
    # Kinetic energy
    mass = 0.145  # kg (baseball)
    model.set_variables({'m': mass})
    model.add_calculated_column(
        name="KE",
        formula="0.5 * m * {v}**2",
        unit="J",
        description="Kinetic energy"
    )
    
    # Potential energy
    model.add_calculated_column(
        name="PE",
        formula="m * g * {y}",
        unit="J",
        description="Potential energy"
    )
    
    # Total energy
    model.add_calculated_column(
        name="E_total",
        formula="{KE} + {PE}",
        unit="J",
        description="Total mechanical energy"
    )
    
    return model

if __name__ == "__main__":
    model = create_projectile_motion_table()
    
    # Print first 10 rows
    print("Projectile Motion Analysis")
    print("="*80)
    print(f"{'t(s)':<8}{'x(m)':<10}{'y(m)':<10}{'vx(m/s)':<12}{'vy(m/s)':<12}{'E(J)':<10}")
    print("-"*80)
    
    for i in range(min(10, model.rowCount())):
        t = model.get_cell_value(i, "t")
        x = model.get_cell_value(i, "x")
        y = model.get_cell_value(i, "y")
        vx = model.get_cell_value(i, "vx")
        vy = model.get_cell_value(i, "vy")
        e = model.get_cell_value(i, "E_total")
        
        print(f"{t:<8.2f}{x:<10.2f}{y:<10.2f}{vx:<12.2f}{vy:<12.2f}{e:<10.2f}")
    
    # Save model
    model.save_to_file("projectile_motion.json")
    print("\nData saved to projectile_motion.json")
