"""
Basic usage example for DataManip.

This example demonstrates:
- Creating a simple data table
- Adding data columns
- Adding calculated columns
- Saving and loading data
"""

from widgets import DataTableWidget, DataTableModel
from constants import DataType

def main():
    # Create model
    model = DataTableModel()
    
    # Add a time column
    model.add_data_column(
        name="time",
        unit="s",
        description="Time in seconds",
        data=[0, 1, 2, 3, 4, 5]
    )
    
    # Add a position column
    model.add_data_column(
        name="position",
        unit="m",
        description="Position in meters",
        data=[0, 5, 20, 45, 80, 125]
    )
    
    # Add a calculated velocity column
    model.add_calculated_column(
        name="velocity",
        formula="{position} / {time}",
        unit="m/s",
        description="Average velocity"
    )
    
    # Print data
    print("Time (s)\tPosition (m)\tVelocity (m/s)")
    for i in range(model.rowCount()):
        time = model.get_cell_value(i, "time")
        pos = model.get_cell_value(i, "position")
        vel = model.get_cell_value(i, "velocity")
        print(f"{time}\t\t{pos}\t\t{vel:.2f if vel else 'N/A'}")
    
    # Save to file
    model.save_to_file("example_data.json")
    print("\nData saved to example_data.json")

if __name__ == "__main__":
    main()
