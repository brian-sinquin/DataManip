"""
Basic usage example for DataManip.

This example demonstrates:
- Creating a DataTableStudy
- Adding data columns
- Adding calculated columns  
- Working with formulas
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from studies.data_table_study import DataTableStudy, ColumnType


def main():
    print("=" * 70)
    print("BASIC USAGE EXAMPLE")
    print("=" * 70)
    
    # Create study
    study = DataTableStudy("Basic Example")
    
    # Add time column (data)
    study.add_column("time", ColumnType.DATA, unit="s")
    
    # Add position column (data)
    study.add_column("position", ColumnType.DATA, unit="m")
    
    # Add calculated velocity column
    study.add_column(
        "velocity",
        ColumnType.CALCULATED,
        formula="{position} / {time}",
        unit="m/s"
    )
    
    print("\nColumns created:")
    print(f"  - time [{study.get_column_unit('time')}]")
    print(f"  - position [{study.get_column_unit('position')}]")
    print(f"  - velocity [{study.get_column_unit('velocity')}] = {study.get_column_formula('velocity')}")
    
    # Add data
    study.add_rows(6)
    time_data = [0, 1, 2, 3, 4, 5]
    position_data = [0, 5, 20, 45, 80, 125]
    
    study.table.data["time"] = time_data
    study.table.data["position"] = position_data
    
    # Recalculate formulas
    study.on_data_changed("position")
    
    print("\nData table:")
    print(study.table.data)
    
    print("\n" + "=" * 70)
    print("Example complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()

