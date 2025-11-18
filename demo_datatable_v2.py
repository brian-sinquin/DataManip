"""
DataTableV2 Demo - Comprehensive example showing all features.

Run this script to see DataTableV2 in action with:
- Data columns
- Calculated columns (formulas)
- Range columns (linspace, logspace, arange)
- Derivative columns (dy/dx)
- Different data types
- Real-time recalculation
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt

from src.widgets.DataTableV2 import DataTableWidget


class DataTableV2Demo(QMainWindow):
    """Demo window showing DataTableV2 capabilities."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("DataTableV2 Demo - All Features")
        self.resize(1200, 800)
        
        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Add title
        title = QLabel("<h2>DataTableV2 Demo - Physics Kinematics Example</h2>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Create table widget
        self.table = DataTableWidget()
        layout.addWidget(self.table)
        
        # Add instructions
        instructions = QLabel(
            "<b>Features demonstrated:</b><br>"
            "• RANGE columns (auto-generated evenly-spaced data)<br>"
            "• CALCULATED columns (formulas with automatic recalculation)<br>"
            "• DERIVATIVE columns (numerical derivatives dy/dx)<br>"
            "• Unit propagation (m/s from m and s)<br>"
            "• Try editing 'v0' or 'a' values to see real-time updates!<br>"
            "• Note: Range, Calculated, and Derivative columns are read-only"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Populate table with physics example
        self.create_physics_example()
    
    def create_physics_example(self):
        """Create a physics kinematics example.
        
        Shows position, velocity, acceleration calculations:
        - x = x0 + v0*t + 0.5*a*t²
        - v = dx/dt
        - a_measured = dv/dt (should match input acceleration)
        """
        # Time range (0 to 5 seconds, 51 points)
        self.table.add_range_column(
            "t",
            start=0.0,
            end=5.0,
            points=51,
            unit="s",
            description="Time"
        )
        
        # Initial conditions (editable data columns)
        self.table.add_data_column(
            "x0",
            unit="m",
            data=[0.0] * 51,
            description="Initial position"
        )
        
        self.table.add_data_column(
            "v0",
            unit="m/s",
            data=[10.0] * 51,  # 10 m/s initial velocity
            description="Initial velocity"
        )
        
        self.table.add_data_column(
            "a",
            unit="m/s²",
            data=[-9.8] * 51,  # -9.8 m/s² (gravity)
            description="Acceleration"
        )
        
        # Position: x = x0 + v0*t + 0.5*a*t²
        self.table.add_calculated_column(
            "x",
            formula="{x0} + {v0} * {t} + 0.5 * {a} * {t} ** 2",
            unit="m",
            description="Position (calculated from kinematics)"
        )
        
        # Velocity from derivative: v = dx/dt
        self.table.add_derivative_column(
            "v",
            numerator="x",
            denominator="t",
            description="Velocity (derivative of position)"
        )
        
        # Acceleration from derivative: a_measured = dv/dt
        self.table.add_derivative_column(
            "a_measured",
            numerator="v",
            denominator="t",
            description="Measured acceleration (should match 'a')"
        )
        
        # Kinetic energy: KE = 0.5 * m * v²  (assume m=1kg)
        self.table.add_calculated_column(
            "KE",
            formula="0.5 * 1.0 * {v} ** 2",
            unit="J",
            description="Kinetic energy (assumes m=1kg)"
        )
        
        # Potential energy: PE = m * g * h  (h = x - x0, m=1kg, g=9.8)
        self.table.add_calculated_column(
            "PE",
            formula="1.0 * 9.8 * ({x} - {x0})",
            unit="J",
            description="Potential energy (assumes m=1kg)"
        )
        
        # Total energy: E = KE + PE
        self.table.add_calculated_column(
            "E_total",
            formula="{KE} + {PE}",
            unit="J",
            description="Total mechanical energy"
        )


def main():
    """Run the demo application."""
    app = QApplication(sys.argv)
    
    # Create and show demo window
    demo = DataTableV2Demo()
    demo.show()
    
    print("="*60)
    print("DataTableV2 Demo Running!")
    print("="*60)
    print("\nFeatures:")
    print("  • 51 rows of data (time: 0-5 seconds)")
    print("  • 10 columns (1 range, 3 data, 4 calculated, 2 derivative)")
    print("  • Physics kinematics example")
    print("\nTry this:")
    print("  1. Edit 'v0' (initial velocity) - watch x, v, KE update")
    print("  2. Edit 'a' (acceleration) - watch all calculations update")
    print("  3. Compare 'a' vs 'a_measured' (should be close)")
    print("\nNote:")
    print("  • RANGE, CALCULATED, DERIVATIVE columns are read-only")
    print("  • Only DATA columns (x0, v0, a) are editable")
    print("="*60)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
