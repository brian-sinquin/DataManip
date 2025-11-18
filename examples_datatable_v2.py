"""
Quick Start Examples for DataTableV2.

Simple examples showing common use cases.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.widgets.DataTableV2 import DataTableWidget


# ============================================================================
# Example 1: Basic Data Table
# ============================================================================
def example_basic():
    """Create a simple data table with editable columns."""
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Create widget
    table = DataTableWidget()
    
    # Add data columns
    table.add_data_column("name", dtype="string", data=["Alice", "Bob", "Charlie"])
    table.add_data_column("age", dtype="int", data=[25, 30, 35])
    table.add_data_column("score", data=[85.5, 92.3, 78.9])
    
    table.setWindowTitle("Example 1: Basic Data Table")
    table.show()
    
    return app.exec()


# ============================================================================
# Example 2: Calculated Columns
# ============================================================================
def example_calculated():
    """Create table with formulas that auto-recalculate."""
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    table = DataTableWidget()
    
    # Input data
    table.add_data_column("length", unit="m", data=[1, 2, 3, 4, 5])
    table.add_data_column("width", unit="m", data=[2, 3, 4, 5, 6])
    
    # Calculated columns
    table.add_calculated_column("area", formula="{length} * {width}", unit="m²")
    table.add_calculated_column("perimeter", formula="2 * ({length} + {width})", unit="m")
    
    table.setWindowTitle("Example 2: Calculated Columns (Try editing length/width!)")
    table.show()
    
    return app.exec()


# ============================================================================
# Example 3: Range Columns
# ============================================================================
def example_range():
    """Create auto-generated range columns."""
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    table = DataTableWidget()
    
    # Evenly-spaced time (linspace)
    table.add_range_column("time", start=0, end=10, points=11, unit="s")
    
    # Logarithmic frequency sweep (logspace)
    table.add_range_column("freq", start=1, end=1000, points=4, mode="logspace", unit="Hz")
    
    # Fixed step (arange)
    table.add_range_column("index", start=0, end=10, step=1, mode="arange")
    
    # Use range in formula
    table.add_calculated_column("position", formula="{time} * 5", unit="m")
    
    table.setWindowTitle("Example 3: Range Columns")
    table.show()
    
    return app.exec()


# ============================================================================
# Example 4: Derivative Columns
# ============================================================================
def example_derivatives():
    """Calculate numerical derivatives."""
    from PySide6.QtWidgets import QApplication
    import numpy as np
    
    app = QApplication(sys.argv)
    
    table = DataTableWidget()
    
    # Time range
    table.add_range_column("t", start=0, end=5, points=51, unit="s")
    
    # Position: x = 5*t²
    table.add_calculated_column("x", formula="5 * {t} ** 2", unit="m")
    
    # Velocity: v = dx/dt (should be ~10*t)
    table.add_derivative_column("v", "x", "t")
    
    # Acceleration: a = dv/dt (should be ~10)
    table.add_derivative_column("a", "v", "t")
    
    table.setWindowTitle("Example 4: Derivatives (x=5t², v=dx/dt, a=dv/dt)")
    table.show()
    
    return app.exec()


# ============================================================================
# Example 5: Complete MVC (Model + View Separation)
# ============================================================================
def example_mvc():
    """Use Model/View architecture for more control."""
    from PySide6.QtWidgets import QApplication
    from src.widgets.DataTableV2 import DataTableModel, DataTableView
    
    app = QApplication(sys.argv)
    
    # Create model separately
    model = DataTableModel()
    model.add_data_column("x", data=[1, 2, 3, 4, 5])
    model.add_calculated_column("y", "{x} ** 2")
    model.add_calculated_column("z", "{x} + {y}")
    
    # Create view and connect to model
    view = DataTableView()
    view.setModel(model)
    
    view.setWindowTitle("Example 5: MVC Pattern (Separate Model/View)")
    view.show()
    
    # You can now access model independently
    print(f"Columns: {model.get_column_names()}")
    print(f"DataFrame:\n{model.to_dataframe()}")
    
    return app.exec()


# ============================================================================
# Run Examples
# ============================================================================
if __name__ == "__main__":
    import sys
    
    examples = {
        "1": ("Basic Data Table", example_basic),
        "2": ("Calculated Columns", example_calculated),
        "3": ("Range Columns", example_range),
        "4": ("Derivative Columns", example_derivatives),
        "5": ("MVC Pattern", example_mvc),
    }
    
    print("="*60)
    print("DataTableV2 Quick Start Examples")
    print("="*60)
    for key, (name, _) in examples.items():
        print(f"{key}. {name}")
    print("="*60)
    
    choice = input("\nSelect example (1-5) or 'all' to run first: ").strip()
    
    if choice == "all":
        choice = "1"
    
    if choice in examples:
        name, func = examples[choice]
        print(f"\nRunning: {name}\n")
        sys.exit(func())
    else:
        print("Invalid choice. Running example 1...")
        sys.exit(example_basic())
