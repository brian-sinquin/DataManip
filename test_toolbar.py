"""Test toolbar feature"""
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from src.widgets.DataTable import DataTableView, DataTableModel

app = QApplication(sys.argv)

# Create main window
window = QMainWindow()
window.setWindowTitle("DataTableV2 - Toolbar Test")

# Create central widget with layout
central = QWidget()
layout = QVBoxLayout(central)

# Create model and view
model = DataTableModel()
view = DataTableView()
view.setModel(model)

# Create toolbar and add to window
toolbar = view.create_toolbar(window)
window.addToolBar(toolbar)

# Add view to layout
layout.addWidget(view)
window.setCentralWidget(central)

# Add some test data
model.add_data_column("Temperature", unit="°C")
model.add_data_column("Pressure", unit="kPa")
model.insertRows(0, 3)

# Show window
window.resize(800, 600)
window.show()

print("✓ Created DataTableV2 with toolbar")
print("Toolbar buttons:")
print("  - Add Column (dropdown with all column types)")
print("  - Add Row")
print("  - Variables...")
print("  - Auto-resize")

sys.exit(app.exec())
