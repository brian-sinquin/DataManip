"""Test auto-row on Enter feature"""
import sys
from PySide6.QtWidgets import QApplication
from src.widgets.DataTable import DataTableView, DataTableModel
from src.widgets.DataTable.column_metadata import DataType

app = QApplication(sys.argv)

# Create model and view
model = DataTableModel()
view = DataTableView()
view.setModel(model)

# Add columns
model.add_data_column("Name", dtype=DataType.STRING)
model.add_data_column("Value", dtype=DataType.FLOAT)

# Add initial rows
model.insertRows(0, 2)

# Show view
view.show()
view.resize(600, 400)

print("✓ Created data table with 2 columns and 2 rows")
print("Test auto-row creation:")
print("  1. Click on the last cell (row 1, column 1)")
print("  2. Press Enter")
print("  3. A new row should be created and cursor should move to first cell of new row")

sys.exit(app.exec())
