from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt

from utils.lang import get_lang_manager, tr
from widgets.AdvancedDataTableWidget.advanced_datatable import AdvancedDataTableWidget, AdvancedColumnType, AdvancedColumnDataType
from widgets.AdvancedDataTableWidget.toolbar import DataTableToolbar

class Workspace(QWidget):
    """Workspace area for data manipulation tasks.
    
    Default Example: Projectile Motion Analysis
    -------------------------------------------
    The workspace loads with a comprehensive physics example demonstrating:
    
    1. RANGE Column (t): Evenly-spaced time values from 0 to 3 seconds
    2. CALCULATED Columns: Position (x, y), distance, velocity, energy
    3. DERIVATIVE Columns: Velocity components (vx, vy) and acceleration (ay)
    
    Key Physics Concepts Demonstrated:
    - Horizontal motion: constant velocity (vx ≈ 14.142 m/s)
    - Vertical motion: affected by gravity (ay ≈ -9.81 m/s²)
    - Energy conservation: Total energy (E) should remain constant ≈ 200 J
    
    Interactive Features to Explore:
    - Right-click column headers: Edit, delete, or convert columns to DATA
    - Right-click cells: Copy values, paste data, clear selections
    - Right-click empty area: Add new columns of any type
    - Keyboard navigation: Press Enter on last cell to auto-create new rows
    - Formula editing: Double-click headers to modify formulas
    - Derivative columns can be used in formulas (e.g., {vx}, {vy}, {ay})
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.lang = get_lang_manager()
        self._setup_ui()
        self._connect_signals()
        self._setup_initial_data()
    
    def _setup_ui(self):
        """Setup the UI for the workspace."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create the advanced data table
        self.table = AdvancedDataTableWidget()
        
        # Create the toolbar for the table
        self.toolbar = DataTableToolbar(self.table)
        layout.addWidget(self.toolbar)
        
        layout.addWidget(self.table)
    
    def _connect_signals(self):
        """Connect table signals."""
        # Connect table signals
        self.table.columnAdded.connect(self.on_column_added)
        self.table.columnRemoved.connect(self.on_column_removed)
        self.table.formulaChanged.connect(self.on_formula_changed)
    
    def _setup_initial_data(self):
        """Set up initial physics example - Projectile Motion Analysis.
        
        This example demonstrates:
        - Range columns for time values
        - Calculated columns using formulas
        - Derivative columns for velocity and acceleration
        - Unit handling and propagation
        """
        try:
            # Clear any existing data
            self.table.clear()
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            
            # Physics parameters for projectile motion
            # Initial velocity: 20 m/s at 45 degrees
            # v0 = 20 m/s, angle = 45°, g = 9.81 m/s²
            
            # 1. Create time range (0 to 3 seconds, 31 points = 0.1s intervals)
            self.table.addRangeColumn(
                header_label="Time",
                start=0.0,
                end=3.0,
                points=31,
                diminutive="t",
                unit="s",
                description="Time elapsed since launch"
            )
            
            # 2. Add horizontal position x = v0 * cos(45°) * t
            # v0 * cos(45°) ≈ 20 * 0.7071 ≈ 14.142 m/s
            self.table.addCalculatedColumn(
                header_label="Position X",
                formula="14.142 * {t}",
                diminutive="x",
                unit="m",
                description="Horizontal position (constant velocity)",
                propagate_uncertainty=False
            )
            
            # 3. Add vertical position y = v0 * sin(45°) * t - 0.5 * g * t²
            # y = 14.142*t - 4.905*t²
            self.table.addCalculatedColumn(
                header_label="Position Y",
                formula="14.142 * {t} - 4.905 * {t}**2",
                diminutive="y",
                unit="m",
                description="Vertical position (with gravity)",
                propagate_uncertainty=False
            )
            
            # 4. Add total distance from origin
            self.table.addCalculatedColumn(
                header_label="Distance",
                formula="sqrt({x}**2 + {y}**2)",
                diminutive="r",
                unit="m",
                description="Distance from launch point",
                propagate_uncertainty=False
            )
            
            # 5. Add horizontal velocity (derivative of x with respect to t)
            # Should be constant ≈ 14.142 m/s
            x_col_idx = 1  # x is the second column (index 1)
            t_col_idx = 0  # t is the first column (index 0)
            self.table.addDerivativeColumn(
                header_label="Velocity X",
                numerator_index=x_col_idx,
                denominator_index=t_col_idx,
                diminutive="vx",
                unit="m/s",
                description="Horizontal velocity component (dx/dt)"
            )
            
            # 6. Add vertical velocity (derivative of y with respect to t)
            # vy = 14.142 - 9.81*t
            y_col_idx = 2  # y is the third column (index 2)
            self.table.addDerivativeColumn(
                header_label="Velocity Y",
                numerator_index=y_col_idx,
                denominator_index=t_col_idx,
                diminutive="vy",
                unit="m/s",
                description="Vertical velocity component (dy/dt)"
            )
            
            # 7. Add total velocity magnitude
            self.table.addCalculatedColumn(
                header_label="Velocity",
                formula="sqrt({vx}**2 + {vy}**2)",
                diminutive="v",
                unit="m/s",
                description="Total velocity magnitude",
                propagate_uncertainty=False
            )
            
            # 8. Add vertical acceleration (derivative of vy with respect to t)
            # Should be approximately -9.81 m/s²
            vy_col_idx = 5  # vy is at index 5
            self.table.addDerivativeColumn(
                header_label="Acceleration Y",
                numerator_index=vy_col_idx,
                denominator_index=t_col_idx,
                diminutive="ay",
                unit="m/s²",
                description="Vertical acceleration (gravity)"
            )
            
            # 9. Add kinetic energy KE = 0.5 * m * v²
            # Assuming mass m = 1 kg for simplicity
            self.table.addCalculatedColumn(
                header_label="Kinetic Energy",
                formula="0.5 * 1.0 * {v}**2",
                diminutive="KE",
                unit="J",
                description="Kinetic energy (mass = 1 kg)",
                propagate_uncertainty=False
            )
            
            # 10. Add potential energy PE = m * g * y
            # PE = 1.0 * 9.81 * y
            self.table.addCalculatedColumn(
                header_label="Potential Energy",
                formula="9.81 * {y}",
                diminutive="PE",
                unit="J",
                description="Gravitational potential energy",
                propagate_uncertainty=False
            )
            
            # 11. Add total mechanical energy (should be conserved ≈ 200 J)
            self.table.addCalculatedColumn(
                header_label="Total Energy",
                formula="{KE} + {PE}",
                diminutive="E",
                unit="J",
                description="Total mechanical energy (should be constant)",
                propagate_uncertainty=False
            )
            
            # Force recalculation of all columns
            self.table._recalculate_all_calculated_columns()
            
            # Resize columns to fit content
            self.table.resizeColumnsToContents()
            
            self._show_status_message(
                "Loaded physics example: Projectile Motion (v0=20 m/s, θ=45°)"
            )
            
            print("\n" + "="*70)
            print("PHYSICS EXAMPLE: PROJECTILE MOTION ANALYSIS")
            print("="*70)
            print("Initial conditions:")
            print("  • Initial velocity: v0 = 20 m/s")
            print("  • Launch angle: θ = 45°")
            print("  • Gravity: g = 9.81 m/s²")
            print("  • Mass: m = 1 kg")
            print("\nColumns created:")
            print("  [RANGE]  t - Time (0 to 3 s)")
            print("  [CALC]   x - Horizontal position")
            print("  [CALC]   y - Vertical position")
            print("  [CALC]   r - Distance from origin")
            print("  [DERIV]  vx - Horizontal velocity (dx/dt)")
            print("  [DERIV]  vy - Vertical velocity (dy/dt)")
            print("  [CALC]   v - Total velocity magnitude")
            print("  [DERIV]  ay - Vertical acceleration (should ≈ -9.81 m/s²)")
            print("  [CALC]   KE - Kinetic energy")
            print("  [CALC]   PE - Potential energy")
            print("  [CALC]   E - Total energy (should be conserved)")
            print("\nTry:")
            print("  • Right-click headers to edit or convert columns")
            print("  • Right-click cells to copy/paste data")
            print("  • Press Enter on last cell to add new rows")
            print("  • Observe energy conservation in column E!")
            print("="*70 + "\n")
            
        except Exception as e:
            QMessageBox.critical(self, tr("Error"), tr("Failed to setup physics example: ") + str(e))
            import traceback
            traceback.print_exc()
            return
    
    def _show_status_message(self, message):
        """Show a status message if the parent has a statusBar."""
        try:
            parent = self.parent()
            if parent and hasattr(parent, 'statusBar'):
                parent.statusBar().showMessage(message)  # type: ignore
        except:
            pass  # Silently ignore if status bar is not available
    
    def on_column_added(self, col_index, header, col_type, data_type):
        """Handle column added signal."""
        print(f"Column added: {header} (index {col_index}, type {col_type.value}, data_type {data_type.value})")
    
    def on_column_removed(self, col_index):
        """Handle column removed signal."""
        print(f"Column removed: index {col_index}")
    
    def on_formula_changed(self, col_index, formula):
        """Handle formula changed signal."""
        header_item = self.table.horizontalHeaderItem(col_index)
        col_name = header_item.text() if header_item else f"Column {col_index}"
        print(f"Formula changed for {col_name}: {formula}")