"""Example: Uncertainty propagation for experimental measurements.

Demonstrates automatic uncertainty calculation using symbolic differentiation.
"""

import numpy as np
from core.workspace import Workspace
from studies.data_table_study import DataTableStudy, ColumnType


def main():
    # Create workspace and study
    workspace = Workspace("Uncertainty Demo", "numerical")
    study = DataTableStudy("measurements", workspace=workspace)
    
    # Scenario: Measuring kinetic energy KE = 0.5 * m * v^2
    # with uncertainties in mass and velocity
    
    # Add measured data with uncertainties
    study.add_column("mass", ColumnType.DATA, 
                    initial_data=np.array([2.0, 3.0, 5.0]), 
                    unit="kg")
    study.add_column("mass_u", ColumnType.DATA, 
                    initial_data=np.array([0.1, 0.1, 0.2]), 
                    unit="kg")
    
    study.add_column("velocity", ColumnType.DATA, 
                    initial_data=np.array([10.0, 15.0, 20.0]), 
                    unit="m/s")
    study.add_column("velocity_u", ColumnType.DATA, 
                    initial_data=np.array([0.5, 0.5, 1.0]), 
                    unit="m/s")
    
    # Calculate kinetic energy with automatic uncertainty propagation
    study.add_column(
        "KE", 
        ColumnType.CALCULATED,
        formula="0.5 * {mass} * {velocity}**2",
        unit="J",
        propagate_uncertainty=True
    )
    
    # Display results
    print("Kinetic Energy Calculation with Uncertainty Propagation")
    print("=" * 60)
    print(f"{'Mass (kg)':<15} {'Velocity (m/s)':<15} {'KE (J)':<15} {'δKE (J)':<15}")
    print("-" * 60)
    
    mass = study.table.get_column("mass").values
    mass_u = study.table.get_column("mass_u").values
    velocity = study.table.get_column("velocity").values
    velocity_u = study.table.get_column("velocity_u").values
    ke = study.table.get_column("KE").values
    ke_u = study.table.get_column("KE_u").values
    
    for i in range(len(mass)):
        print(f"{mass[i]:>5.1f} ± {mass_u[i]:>4.1f}    "
              f"{velocity[i]:>5.1f} ± {velocity_u[i]:>4.1f}    "
              f"{ke[i]:>7.1f}        {ke_u[i]:>7.2f}")
    
    print("\n" + "=" * 60)
    print("Formula used: KE = 0.5 * m * v²")
    print("Uncertainty: δKE = √((0.5*v²*δm)² + (m*v*δv)²)")
    print("\nUncertainty propagation is automatic!")
    print("The KE_u column was created automatically using symbolic differentiation.")


if __name__ == "__main__":
    main()
