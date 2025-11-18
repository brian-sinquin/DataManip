"""Test global variables feature in DataTableV2."""

import sys
from PySide6.QtWidgets import QApplication
from src.widgets.DataTable import DataTableWidget

def test_variables():
    """Test global variables functionality."""
    app = QApplication(sys.argv)
    
    # Create widget
    widget = DataTableWidget()
    widget.resize(800, 600)
    widget.setWindowTitle("Global Variables Test")
    
    # Add some global variables programmatically
    widget.model().set_variables({
        'g': (9.81, 'm/s²'),
        'pi': (3.14159265, ''),
        'c': (299792458, 'm/s')
    })
    
    # Add a simple data column
    widget.add_data_column("time", data=[0, 1, 2, 3, 4], unit="s")
    
    # Add calculated column using global variable
    widget.add_calculated_column(
        name="distance",
        formula="{g} * {time}**2 / 2",
        unit="m",
        description="Free fall distance: d = g*t²/2"
    )
    
    # Add another calculated column using pi
    widget.add_calculated_column(
        name="circle_area",
        formula="{pi} * {time}**2",
        unit="m²",
        description="Area = π*r² where r=time"
    )
    
    print("✓ Created columns with global variables")
    print(f"  - Variables: {list(widget.model().get_variables().keys())}")
    print(f"  - Columns: {widget.model().get_column_names()}")
    print(f"\nTest: Right-click on empty area and select 'Manage Variables...'")
    print(f"Test: Try adding new variables or modifying existing ones")
    print(f"Test: Formulas should recalculate automatically")
    
    widget.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    test_variables()
