"""Quick test of interpolation column functionality."""

import sys
from PySide6.QtWidgets import QApplication
from src.widgets.DataTable import DataTableWidget
import numpy as np

def test_interpolation():
    """Test interpolation column creation and editing."""
    app = QApplication(sys.argv)
    
    # Create widget
    widget = DataTableWidget()
    widget.resize(800, 600)
    widget.setWindowTitle("Interpolation Test")
    
    # Add X data column with sparse points
    widget.add_data_column("x_sparse", data=[0, 2, 4, 6, 8, 10], unit="s")
    
    # Add Y data column (quadratic function)
    x_vals = np.array([0, 2, 4, 6, 8, 10])
    y_vals = x_vals ** 2
    widget.add_data_column("y_sparse", data=y_vals, unit="m")
    
    # Add dense X column for evaluation
    widget.add_range_column("x_dense", start=0, end=10, points=21, unit="s")
    
    # Add interpolation column using linear method
    widget.add_interpolation_column(
        name="y_interp_linear",
        x_column="x_sparse",
        y_column="y_sparse",
        eval_column="x_dense",
        method="linear",
        description="Linear interpolation of sparse Y data"
    )
    
    # Add interpolation column using cubic method
    widget.add_interpolation_column(
        name="y_interp_cubic",
        x_column="x_sparse",
        y_column="y_sparse",
        eval_column="x_dense",
        method="cubic",
        description="Cubic spline interpolation of sparse Y data"
    )
    
    # Add calculated column using interpolated data
    widget.add_calculated_column(
        name="error",
        formula="{y_interp_cubic} - {x_dense}**2",
        unit="m",
        description="Error between cubic interpolation and true function"
    )
    
    print("✓ Created interpolation columns successfully")
    print(f"  - Columns: {widget.model().get_column_names()}")
    print(f"  - Rows: {widget.model().rowCount()}")
    
    # Show widget
    widget.show()
    
    # Test editing interpolation column via dialog
    print("\nTest: Right-click on 'y_interp_linear' header to edit")
    print("Test: Change method to 'quadratic' or 'nearest'")
    print("Test: Context menu should show 'Add Interpolation Column...'")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_interpolation()
