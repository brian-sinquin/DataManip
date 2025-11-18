"""Test manual uncertainty column feature"""
import sys
from PySide6.QtWidgets import QApplication
from src.widgets.DataTable import DataTableView, DataTableModel

app = QApplication(sys.argv)

# Create model and view
model = DataTableModel()
view = DataTableView()
view.setModel(model)

# Add a data column
model.add_data_column("Temperature", unit="°C", description="Sample temperature")
model.add_data_column("Pressure", unit="kPa", description="Sample pressure")

# Add some data
for row in range(2):
    model.insertRows(row, 1)

# Set data using Qt model indices
temp_idx = model.get_column_names().index("Temperature")
pressure_idx = model.get_column_names().index("Pressure")

model.setData(model.index(0, temp_idx), 25.0)
model.setData(model.index(1, temp_idx), 30.0)
model.setData(model.index(0, pressure_idx), 101.3)
model.setData(model.index(1, pressure_idx), 105.2)

# Show the dialog via right-click menu
view.show()
view.resize(800, 400)

print("✓ Created data table with Temperature and Pressure columns")
print("Right-click on empty area and select 'Add Uncertainty Column...'")
print("This should show a dialog to add a manual uncertainty column")

sys.exit(app.exec())
