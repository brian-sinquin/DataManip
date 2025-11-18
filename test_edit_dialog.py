"""
Test script for DataTableV2 edit dialogs and context menus.

This script verifies:
1. Double-click on headers opens edit dialogs
2. Context menus work for headers, cells, and rows
3. Edit dialogs properly load and save column properties
"""

import sys
from PySide6.QtWidgets import QApplication
from src.widgets.DataTable import DataTableWidget

def main():
    app = QApplication(sys.argv)
    
    # Create widget with sample data
    widget = DataTableWidget()
    
    # Add sample columns
    print("Creating sample data...")
    widget.add_data_column("temperature", unit="°C", description="Temperature measurement", precision=2)
    widget.add_data_column("pressure", unit="kPa", description="Pressure measurement", precision=1)
    widget.add_range_column("time", start=0, end=10, points=11, unit="s", description="Time values")
    widget.add_calculated_column(
        "ratio",
        formula="{temperature} / {pressure}",
        description="Temperature to pressure ratio",
        propagate_uncertainty=False,
        precision=3
    )
    
    # Add some sample data
    model = widget.model()
    for i in range(5):
        model.setData(model.index(i, 0), 20 + i * 5)  # temperature
        model.setData(model.index(i, 1), 100 + i * 10)  # pressure
    
    print("\n" + "="*60)
    print("DataTableV2 Edit Dialog Test")
    print("="*60)
    print("\nTest the following features:")
    print("1. Double-click on 'temperature' header to edit")
    print("2. Right-click on 'temperature' header for context menu")
    print("3. Right-click on a cell to copy/paste")
    print("4. Right-click on row header to insert/delete rows")
    print("5. Select multiple cells and copy/paste")
    print("\nExpected behaviors:")
    print("  • Edit dialog shows current properties")
    print("  • Changes are saved when clicking OK")
    print("  • Can rename columns")
    print("  • Can modify units and descriptions")
    print("  • Calculated columns can have formula edited")
    print("="*60 + "\n")
    
    widget.resize(800, 600)
    widget.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
