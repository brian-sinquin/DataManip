from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidgetItem, QMessageBox, QTabWidget, QLabel
)
from PySide6.QtCore import Qt

from utils.lang import get_lang_manager, tr
from utils.example_data import load_projectile_motion
from widgets.AdvancedDataTableWidget.advanced_datatable import AdvancedDataTableWidget, AdvancedColumnType, AdvancedColumnDataType
from widgets.AdvancedDataTablePlotWidget import AdvancedDataTablePlotWidget
from widgets.AdvancedDataTableStatisticsWidget import AdvancedDataTableStatisticsWidget

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
        """Setup the UI for the workspace with tabs."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create Data Table tab
        self.data_tab = QWidget()
        data_tab_layout = QVBoxLayout()
        self.data_tab.setLayout(data_tab_layout)
        
        # Create the advanced data table (without toolbar)
        self.table = AdvancedDataTableWidget()
        data_tab_layout.addWidget(self.table)
        
        # Create Plotting tab with the plot widget
        self.plot_tab = QWidget()
        plot_tab_layout = QVBoxLayout()
        self.plot_tab.setLayout(plot_tab_layout)
        
        # Create the plot widget (will be connected after table setup)
        self.plot_widget = AdvancedDataTablePlotWidget()
        plot_tab_layout.addWidget(self.plot_widget)
        
        # Create Statistics tab
        self.stats_tab = QWidget()
        stats_tab_layout = QVBoxLayout()
        self.stats_tab.setLayout(stats_tab_layout)
        
        # Create the statistics widget (will be connected after table setup)
        self.stats_widget = AdvancedDataTableStatisticsWidget()
        stats_tab_layout.addWidget(self.stats_widget)
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.data_tab, "Data Table")
        self.tab_widget.addTab(self.plot_tab, "Plotting")
        self.tab_widget.addTab(self.stats_tab, "Statistics")
    
    def _connect_signals(self):
        """Connect table signals."""
        # Connect table signals
        self.table.columnAdded.connect(self.on_column_added)
        self.table.columnRemoved.connect(self.on_column_removed)
        self.table.formulaChanged.connect(self.on_formula_changed)
        
        # Connect plot widget to datatable
        self.plot_widget.set_datatable(self.table)
        
        # Connect statistics widget to datatable
        self.stats_widget.set_datatable(self.table)
    
    def _setup_initial_data(self):
        """Set up initial physics example - Baseball Trajectory."""
        try:
            # Load the projectile motion example from example_data module
            load_projectile_motion(self.table)
            
            self._show_status_message(
                "Loaded example: Baseball Trajectory (v0=45 m/s, θ=35°)"
            )
            
            print("\n" + "="*70)
            print("PHYSICS EXAMPLE: BASEBALL TRAJECTORY")
            print("="*70)
            print("Realistic scenario:")
            print("  • Baseball hit at 45 m/s (162 km/h)")
            print("  • Launch angle: θ = 35°")
            print("  • Mass: 0.145 kg (official MLB baseball)")
            print("  • Standard gravity: g = 9.80665 m/s²")
            print("\nPhysical constants defined (use Variables dialog to view):")
            print("  • g = 9.80665 m/s²")
            print("  • v0 = 45.0 m/s")
            print("  • theta = 35.0 deg")
            print("  • mass = 0.145 kg")
            print("\nColumns created:")
            print("  [RANGE]  t - Time (0 to 5.3 s)")
            print("  [CALC]   x - Horizontal position")
            print("  [CALC]   y - Vertical position")
            print("  [CALC]   r - Distance from origin")
            print("  [DERIV]  vx - Horizontal velocity")
            print("  [DERIV]  vy - Vertical velocity")
            print("  [CALC]   v - Total speed")
            print("  [DERIV]  ay - Vertical acceleration")
            print("  [CALC]   KE - Kinetic energy")
            print("  [CALC]   PE - Potential energy")
            print("  [CALC]   E - Total energy (conserved)")
            print("\nTry:")
            print("  • Plot x vs y to see the parabolic trajectory!")
            print("  • Load other examples from the Examples menu")
            print("  • Right-click table header → 'Manage Variables' to see constants")
            print("  • All examples use realistic values and physical constants")
            print("="*70 + "\n")
            
        except Exception as e:
            QMessageBox.critical(self, tr("Error"), tr("Failed to setup physics example: ") + str(e))
            import traceback
            traceback.print_exc()
            return
    
    def load_example(self, example_name: str):
        """Load a specific example by name.
        
        Args:
            example_name: Name of the example to load
        """
        try:
            from utils.example_data import load_example
            
            if load_example(self.table, example_name):
                self._show_status_message(f"Loaded example: {example_name}")
                print(f"\n{'='*70}")
                print(f"EXAMPLE LOADED: {example_name.upper()}")
                print(f"{'='*70}\n")
            else:
                QMessageBox.warning(self, "Unknown Example", f"Example '{example_name}' not found.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error Loading Example", 
                               f"Failed to load example '{example_name}':\n{str(e)}")
            import traceback
            traceback.print_exc()
    
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