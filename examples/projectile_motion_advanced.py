"""
Advanced example: Projectile Motion Analysis

Demonstrates:
- Creating a complete physics experiment in DataManip
- Multiple calculated columns with dependencies
- Using global variables for constants
- Complex formulas with trigonometry
"""

from studies.data_table_study import DataTableStudy, ColumnType
import numpy as np


def main():
    """Projectile motion analysis."""
    
    print("=" * 70)
    print("PROJECTILE MOTION ANALYSIS")
    print("=" * 70)
    print()
    
    # Create study
    study = DataTableStudy("Projectile Motion")
    
    # Define constants
    study.add_variable("g", 9.81, "m/s^2")
    study.add_variable("v0", 20.0, "m/s")
    study.add_variable("angle_deg", 45.0, "°")
    
    print("Constants:")
    print(f"  g = {study.get_variable('g')}")
    print(f"  v0 = {study.get_variable('v0')}")
    print(f"  angle = {study.get_variable('angle_deg')}")
    print()
    
    # Add time column (data)
    study.add_column("t", ColumnType.DATA, unit="s")
    
    # Add calculated columns
    
    # Convert angle to radians
    study.add_column(
        "angle",
        ColumnType.CALCULATED,
        formula="{angle_deg} * pi / 180",
        unit="rad"
    )
    
    # Initial velocity components
    study.add_column(
        "v0x",
        ColumnType.CALCULATED,
        formula="{v0} * cos({angle})",
        unit="m/s"
    )
    
    study.add_column(
        "v0y",
        ColumnType.CALCULATED,
        formula="{v0} * sin({angle})",
        unit="m/s"
    )
    
    # Position
    study.add_column(
        "x",
        ColumnType.CALCULATED,
        formula="{v0x} * {t}",
        unit="m"
    )
    
    study.add_column(
        "y",
        ColumnType.CALCULATED,
        formula="{v0y} * {t} - 0.5 * {g} * {t}**2",
        unit="m"
    )
    
    # Velocity components
    study.add_column(
        "vx",
        ColumnType.CALCULATED,
        formula="{v0x}",
        unit="m/s"
    )
    
    study.add_column(
        "vy",
        ColumnType.CALCULATED,
        formula="{v0y} - {g} * {t}",
        unit="m/s"
    )
    
    # Total velocity
    study.add_column(
        "v",
        ColumnType.CALCULATED,
        formula="np.sqrt({vx}**2 + {vy}**2)",
        unit="m/s"
    )
    
    # Kinetic energy (assuming 1 kg mass)
    study.add_column(
        "KE",
        ColumnType.CALCULATED,
        formula="0.5 * {v}**2",
        unit="J"
    )
    
    # Potential energy (assuming 1 kg mass)
    study.add_column(
        "PE",
        ColumnType.CALCULATED,
        formula="{g} * {y}",
        unit="J"
    )
    
    # Total energy
    study.add_column(
        "E_total",
        ColumnType.CALCULATED,
        formula="{KE} + {PE}",
        unit="J"
    )
    
    print("Columns created:")
    for col_name in study.table.columns:
        col_type = study.get_column_type(col_name)
        col_unit = study.get_column_unit(col_name)
        col_formula = study.get_column_formula(col_name)
        
        unit_str = f" [{col_unit}]" if col_unit else ""
        
        if col_type == ColumnType.CALCULATED:
            print(f"  {col_name}{unit_str} = {col_formula}")
        else:
            print(f"  {col_name}{unit_str} (data)")
    print()
    
    # Add time data points
    study.add_rows(21)
    
    # Set time values (0 to 4 seconds in 0.2s steps)
    time_col = study.table.data["t"]
    for i in range(21):
        study.table.data.at[i, "t"] = i * 0.2
    
    # Trigger recalculation of all formulas
    study.recalculate_all()
    
    print("\nDebug: First few rows of data:")
    print(study.table.data.head())
    print()
    
    print("Data (showing every 4th row):")
    print("-" * 70)
    
    # Display header
    header = " ".join([f"{col:>8}" for col in ["t", "x", "y", "v", "KE", "PE", "E_tot"]])
    print(header)
    print("-" * 70)
    
    # Display data
    for i in range(0, 21, 4):
        row = study.table.data.iloc[i]
        t = row["t"]
        x = row["x"]
        y = row["y"]
        v = row["v"]
        ke = row["KE"]
        pe = row["PE"]
        e_tot = row["E_total"]
        
        print(f"{t:8.2f}{x:8.2f}{y:8.2f}{v:8.2f}{ke:8.2f}{pe:8.2f}{e_tot:8.2f}")
    
    print("-" * 70)
    print()
    
    # Analyze results
    max_height_idx = study.table.data["y"].idxmax()
    max_height = study.table.data.iloc[max_height_idx]["y"]
    time_at_max = study.table.data.iloc[max_height_idx]["t"]
    
    # Find where projectile hits ground (y < 0)
    ground_idx = None
    for i in range(len(study.table.data)):
        if study.table.data.iloc[i]["y"] < 0 and i > 0:
            ground_idx = i
            break
    
    if ground_idx:
        range_x = study.table.data.iloc[ground_idx - 1]["x"]
        time_flight = study.table.data.iloc[ground_idx - 1]["t"]
    else:
        range_x = study.table.data.iloc[-1]["x"]
        time_flight = study.table.data.iloc[-1]["t"]
    
    print("Analysis:")
    print(f"  Maximum height: {max_height:.2f} m at t={time_at_max:.2f} s")
    print(f"  Range: {range_x:.2f} m")
    print(f"  Time of flight: {time_flight:.2f} s")
    print()
    
    # Energy conservation check
    initial_energy = study.table.data.iloc[0]["E_total"]
    final_energies = study.table.data["E_total"].values
    energy_variation = np.std(final_energies[final_energies > 0])
    
    print(f"  Initial total energy: {initial_energy:.2f} J")
    print(f"  Energy variation (std dev): {energy_variation:.4f} J")
    print(f"  Energy conserved: {energy_variation < 0.01}")
    print()
    
    print("=" * 70)
    print("Analysis complete!")
    print()
    print("This demonstrates DataManip's ability to:")
    print("  ✓ Handle complex multi-step calculations")
    print("  ✓ Use global variables and constants")
    print("  ✓ Automatic dependency resolution")
    print("  ✓ Physics formulas with trigonometry")
    print("  ✓ Energy conservation analysis")
    print("=" * 70)


if __name__ == "__main__":
    main()
