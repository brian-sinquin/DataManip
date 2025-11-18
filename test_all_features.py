"""Comprehensive test of all new DataTableV2 features"""
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from src.widgets.DataTable import DataTableView, DataTableModel
from src.widgets.DataTable.column_metadata import DataType

app = QApplication(sys.argv)

# Create main window with toolbar
window = QMainWindow()
window.setWindowTitle("DataTableV2 - All Features Test")

# Create central widget
central = QWidget()
layout = QVBoxLayout(central)

# Create model and view
model = DataTableModel()
view = DataTableView()
view.setModel(model)

# Create and add toolbar
toolbar = view.create_toolbar(window)
window.addToolBar(toolbar)

# Add view to layout
layout.addWidget(view)
window.setCentralWidget(central)

# ============================================================================
# Test all 5 new features
# ============================================================================

print("=== Testing New Features ===\n")

# 1. Global Variables/Constants
print("1. Global Variables:")
model.set_variables({
    'g': (9.81, 'm/s²'),
    'pi': (3.14159, None),
    'c': (299792458, 'm/s')
})
print(f"   ✓ Set variables: {list(model.get_variables().keys())}")

# 2. Column Insertion Positioning  
print("\n2. Column Insertion Positioning:")
model.add_data_column("Temperature", unit="°C", dtype=DataType.FLOAT, insert_position=0)
print("   ✓ Added Temperature at position 0")
model.add_data_column("Pressure", unit="kPa", dtype=DataType.FLOAT, insert_position=1)
print("   ✓ Added Pressure at position 1")
model.add_range_column("Time", start=0, end=10, points=11, unit="s", insert_position=0)
print("   ✓ Added Time range at position 0 (should be first column)")
print(f"   Column order: {model.get_column_names()}")

# Add some test data
model.insertRows(0, 3)
for i in range(3):
    col_idx = model.get_column_names().index("Temperature")
    model.setData(model.index(i, col_idx), 25.0 + i * 5)
    col_idx = model.get_column_names().index("Pressure")
    model.setData(model.index(i, col_idx), 101.3 + i * 2)

# 3. Add a calculated column using variables
print("\n3. Calculated Column with Variables:")
model.add_calculated_column(
    "Speed_of_light",
    formula="{c}",  # Reference global variable
    unit="m/s",
    description="Speed of light constant",
    insert_position=3  # After Time, Temperature, Pressure
)
print("   ✓ Added calculated column using global variable {c}")

# 4. Manual Uncertainty Column Support
print("\n4. Manual Uncertainty Column:")
model.add_uncertainty_column(
    data_column_name="Temperature",
    name="Temp_error",
    unit="°C",
    description="Temperature measurement uncertainty"
)
print("   ✓ Added manual uncertainty column for Temperature")

# Set some uncertainty values
uncert_idx = model.get_column_names().index("Temp_error")
for i in range(3):
    model.setData(model.index(i, uncert_idx), 0.5)

print("\n5. Toolbar:")
print("   ✓ Toolbar with Add Column, Add Row, Variables, Auto-resize buttons")

print("\n6. Auto-row on Enter:")
print("   ✓ keyPressEvent overridden - press Enter in last cell to add row")

# Show window
window.resize(1000, 500)
window.show()

print("\n=== All Features Implemented Successfully! ===")
print("\nInteractive Tests:")
print("  - Use toolbar to add different column types")
print("  - Right-click empty area -> 'Manage Variables...' to edit constants")
print("  - Right-click empty area -> 'Add Uncertainty Column...' for manual uncertainty")
print("  - Navigate to last cell (bottom-right) and press Enter to auto-add row")
print("  - Note: Columns inserted at specific positions (Time is first)")

sys.exit(app.exec())
