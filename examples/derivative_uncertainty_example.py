"""
Example: Derivative Uncertainty Propagation

Demonstrates automatic uncertainty propagation for numerical derivatives.
Shows how uncertainties in position measurements propagate to velocity 
and acceleration calculations.
"""

import numpy as np
from studies.data_table_study import DataTableStudy, ColumnType


def main():
    print("=" * 60)
    print("Derivative Uncertainty Propagation Example")
    print("=" * 60)
    print()
    
    # Create study
    study = DataTableStudy("Kinematics with Uncertainties")
    
    # Simulate position measurements with uncertainty
    # Motion: x(t) = 0.5 * a * t²  (constant acceleration)
    t = np.linspace(0, 5, 26)  # 0 to 5 seconds, 26 points (Δt = 0.2s)
    a = 2.0  # m/s² (acceleration)
    x = 0.5 * a * t**2  # Position in meters
    
    # Add measurement uncertainty to position (±0.05 m)
    dx = np.full_like(t, 0.05)
    
    print("Setup:")
    print(f"  Time range: {t[0]:.1f} to {t[-1]:.1f} seconds")
    print(f"  Time step: Δt = {t[1] - t[0]:.2f} s")
    print(f"  True acceleration: {a:.1f} m/s²")
    print(f"  Position uncertainty: ±{dx[0]:.3f} m")
    print()
    
    # Add columns
    study.add_column("t", ColumnType.DATA, unit="s", initial_data=t)
    study.add_column("x", ColumnType.DATA, unit="m", initial_data=x)
    study.add_column("dx", ColumnType.UNCERTAINTY, 
                    uncertainty_reference="x", initial_data=dx)
    
    # Calculate velocity (first derivative: v = dx/dt)
    study.add_column("v", ColumnType.DERIVATIVE,
                    derivative_of="x", with_respect_to="t", 
                    order=1, unit="m/s")
    study.add_column("dv", ColumnType.UNCERTAINTY,
                    uncertainty_reference="v")
    
    # Calculate acceleration (second derivative: a = d²x/dt²)
    study.add_column("a", ColumnType.DERIVATIVE,
                    derivative_of="x", with_respect_to="t",
                    order=2, unit="m/s²")
    study.add_column("da", ColumnType.UNCERTAINTY,
                    uncertainty_reference="a")
    
    # Recalculate uncertainties
    study._recalculate_uncertainty("v")
    study._recalculate_uncertainty("a")
    
    # Get results
    v_calc = study.table.get_column("v").values
    dv_calc = study.table.get_column("dv").values
    a_calc = study.table.get_column("a").values
    da_calc = study.table.get_column("da").values
    
    # Show results at selected time points
    print("Results at selected times:")
    print("-" * 60)
    print(f"{'Time (s)':<10} {'Velocity (m/s)':<20} {'Acceleration (m/s²)':<25}")
    print(f"{'':10} {'v ± δv':<20} {'a ± δa':<25}")
    print("-" * 60)
    
    # Show every 5th point
    for i in range(0, len(t), 5):
        v_str = f"{v_calc[i]:.3f} ± {dv_calc[i]:.3f}"
        a_str = f"{a_calc[i]:.3f} ± {da_calc[i]:.3f}"
        print(f"{t[i]:<10.1f} {v_str:<20} {a_str:<25}")
    
    print()
    print("Analysis:")
    print("-" * 60)
    
    # Theoretical uncertainty for first derivative: δv ≈ δx / Δt
    dt = t[1] - t[0]
    theoretical_dv = dx[0] / dt
    print(f"Position uncertainty: δx = {dx[0]:.3f} m")
    print(f"Time step: Δt = {dt:.2f} s")
    print(f"Velocity uncertainty (theoretical): δv ≈ δx/Δt = {theoretical_dv:.3f} m/s")
    print(f"Velocity uncertainty (calculated): δv = {np.mean(dv_calc):.3f} m/s")
    print()
    
    # Theoretical uncertainty for second derivative: δa ≈ δx / (Δt)²
    theoretical_da = dx[0] / (dt**2)
    print(f"Acceleration uncertainty (theoretical): δa ≈ δx/(Δt)² = {theoretical_da:.2f} m/s²")
    print(f"Acceleration uncertainty (calculated): δa = {np.mean(da_calc):.2f} m/s²")
    print()
    
    # Compare with true value
    print(f"True acceleration: {a:.1f} m/s²")
    print(f"Calculated acceleration: {np.mean(a_calc):.2f} ± {np.mean(da_calc):.2f} m/s²")
    
    # Check if true value is within uncertainty
    a_mean = np.mean(a_calc)
    da_mean = np.mean(da_calc)
    within_1sigma = abs(a_mean - a) <= da_mean
    
    print(f"True value within 1σ: {'✓ Yes' if within_1sigma else '✗ No'}")
    print()
    
    print("Key Insights:")
    print("-" * 60)
    print("1. First derivative uncertainty: δv = δx / Δt")
    print("   → Smaller time steps increase velocity uncertainty")
    print()
    print("2. Second derivative uncertainty: δa = δx / (Δt)²")
    print("   → Uncertainty grows quadratically with differentiation")
    print()
    print("3. Numerical differentiation amplifies measurement noise")
    print("   → Use larger time steps or filtering for better results")
    print()
    
    # Save workspace
    import json
    from pathlib import Path
    from core.workspace import Workspace
    
    ws = Workspace(name="Derivative Uncertainty Demo", workspace_type="general")
    ws.add_study(study)
    
    filepath = Path(__file__).parent / "derivative_uncertainty_demo.dmw"
    workspace_data = ws.to_dict()
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(workspace_data, f, indent=2)
    
    print(f"✓ Workspace saved to '{filepath.name}'")


if __name__ == "__main__":
    main()
