"""
Main application window.

Single workspace containing multiple study tabs.
"""

from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QMessageBox, QInputDialog, QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
import json
from pathlib import Path
import numpy as np

from core.workspace import Workspace
from core.study import Study
from studies.data_table_study import DataTableStudy, ColumnType
from studies.plot_study import PlotStudy
from studies.statistics_study import StatisticsStudy
from .widgets import DataTableWidget, ConstantsWidget, StatisticsWidget
from .widgets.plot_widget import PlotWidget
from .widgets.column_dialogs import CSVImportDialog


class MainWindow(QMainWindow):
    """Main application window.
    
    Single workspace with multiple study tabs.
    """
    
    def __init__(self):
        """Initialize main window."""
        super().__init__()
        
        self.setWindowTitle("DataManip v0.2.0 - Data Analysis for Experimental Sciences")
        self.resize(1200, 800)
        
        # Single workspace
        self.workspace = Workspace("Workspace", "numerical")
        
        # Setup UI
        self._setup_ui()
        self._setup_menu()
        
        # Create default study
        self._create_default_study()
        
        # Welcome message
        self.statusBar().showMessage("Welcome to DataManip! Press Ctrl+T for new table, Ctrl+P for new plot, F1 for help")
    
    def _setup_ui(self):
        """Setup UI components."""
        # Study tabs as central widget
        self.study_tabs = QTabWidget()
        self.study_tabs.setTabsClosable(True)
        self.study_tabs.tabCloseRequested.connect(self._close_study)
        
        self.setCentralWidget(self.study_tabs)
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def _setup_menu(self):
        """Setup menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # New submenu
        new_menu = file_menu.addMenu("&New")
        
        new_table_action = QAction("Data &Table", self)
        new_table_action.setShortcut("Ctrl+T")
        new_table_action.triggered.connect(self._new_data_table)
        new_menu.addAction(new_table_action)
        
        new_plot_action = QAction("&Plot", self)
        new_plot_action.setShortcut("Ctrl+P")
        new_plot_action.triggered.connect(self._new_plot)
        new_menu.addAction(new_plot_action)
        
        new_statistics_action = QAction("&Statistics", self)
        new_statistics_action.setShortcut("Ctrl+S")
        new_statistics_action.triggered.connect(self._new_statistics)
        new_menu.addAction(new_statistics_action)
        
        new_menu.addSeparator()
        
        new_vars_action = QAction("&Constants Tab", self)
        new_vars_action.setShortcut("Ctrl+K")
        new_vars_action.triggered.connect(self._new_variables_tab)
        new_menu.addAction(new_vars_action)
        
        file_menu.addSeparator()
        
        # Export/Import submenu
        export_menu = file_menu.addMenu("&Export")
        
        export_csv_action = QAction("Export to &CSV...", self)
        export_csv_action.setShortcut("Ctrl+E")
        export_csv_action.triggered.connect(self._export_to_csv)
        export_menu.addAction(export_csv_action)
        
        export_excel_action = QAction("Export to &Excel...", self)
        export_excel_action.triggered.connect(self._export_to_excel)
        export_menu.addAction(export_excel_action)
        
        import_menu = file_menu.addMenu("&Import")
        
        import_csv_action = QAction("Import from &CSV...", self)
        import_csv_action.setShortcut("Ctrl+I")
        import_csv_action.triggered.connect(self._import_from_csv)
        import_menu.addAction(import_csv_action)
        
        import_excel_action = QAction("Import from &Excel...", self)
        import_excel_action.triggered.connect(self._import_from_excel)
        import_menu.addAction(import_excel_action)
        
        file_menu.addSeparator()
        
        # Save/Load
        save_action = QAction("&Save Workspace...", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_workspace)
        file_menu.addAction(save_action)
        
        load_action = QAction("&Open Workspace...", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self._load_workspace)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        rename_study_action = QAction("&Rename Study", self)
        rename_study_action.setShortcut("F2")
        rename_study_action.triggered.connect(self._rename_current_study)
        edit_menu.addAction(rename_study_action)
        
        edit_menu.addSeparator()
        
        close_study_action = QAction("&Close Study", self)
        close_study_action.setShortcut("Ctrl+W")
        close_study_action.triggered.connect(self._close_current_study)
        edit_menu.addAction(close_study_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        next_tab_action = QAction("Next Tab", self)
        next_tab_action.setShortcut("Ctrl+Tab")
        next_tab_action.triggered.connect(self._next_tab)
        view_menu.addAction(next_tab_action)
        
        prev_tab_action = QAction("Previous Tab", self)
        prev_tab_action.setShortcut("Ctrl+Shift+Tab")
        prev_tab_action.triggered.connect(self._prev_tab)
        view_menu.addAction(prev_tab_action)
        
        # Examples menu
        examples_menu = menubar.addMenu("E&xamples")
        
        projectile_action = QAction("Projectile Motion", self)
        projectile_action.setToolTip("Baseball trajectory with uncertainty")
        projectile_action.triggered.connect(lambda: self._load_example("projectile_motion"))
        examples_menu.addAction(projectile_action)
        
        freefall_action = QAction("Free Fall Motion", self)
        freefall_action.setToolTip("Simple free fall with drag")
        freefall_action.triggered.connect(lambda: self._load_example("freefall"))
        examples_menu.addAction(freefall_action)
        
        oscillator_action = QAction("Harmonic Oscillator", self)
        oscillator_action.setToolTip("Damped spring oscillation")
        oscillator_action.triggered.connect(lambda: self._load_example("oscillator"))
        examples_menu.addAction(oscillator_action)
        
        derivatives_action = QAction("Derivatives Demo", self)
        derivatives_action.setToolTip("Position → velocity → acceleration")
        derivatives_action.triggered.connect(lambda: self._load_example("derivatives"))
        examples_menu.addAction(derivatives_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        shortcuts_action = QAction("Keyboard &Shortcuts", self)
        shortcuts_action.setShortcut("F1")
        shortcuts_action.triggered.connect(self._show_shortcuts)
        help_menu.addAction(shortcuts_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("&About DataManip", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_default_study(self):
        """Create default DataTable study with comprehensive examples."""
        # Initialize workspace constants
        self.workspace.add_constant("g", 9.81, "m/s^2")
        self.workspace.add_constant("pi", 3.14159265359, None)
        
        study = DataTableStudy("Physics Demo", workspace=self.workspace)
        
        # Example: Free fall motion demonstrating all column types
        # 1. RANGE column - generate time points
        study.add_column(
            "time",
            ColumnType.RANGE,
            unit="s",
            range_type="linspace",
            range_start=0.0,
            range_stop=3.0,
            range_count=13
        )
        
        # 2. DATA columns with uncertainties
        study.add_column("h0", ColumnType.DATA, 
                        initial_data=np.full(13, 50.0), 
                        unit="m")
        study.add_column("h0_u", ColumnType.DATA, 
                        initial_data=np.full(13, 0.5), 
                        unit="m")
        
        # 3. CALCULATED column - position with uncertainty propagation
        study.add_column(
            "height",
            ColumnType.CALCULATED,
            formula="{h0} - 0.5 * 9.81 * {time}**2",
            unit="m",
            propagate_uncertainty=True  # Auto-creates height_u column
        )
        
        # 4. DERIVATIVE column - velocity (derivative of height)
        study.add_column(
            "velocity",
            ColumnType.DERIVATIVE,
            derivative_of="height",
            with_respect_to="time",
            unit="m/s"
        )
        
        # 5. CALCULATED column - kinetic energy
        study.add_column(
            "mass",
            ColumnType.DATA,
            initial_data=np.full(13, 2.0),
            unit="kg"
        )
        
        study.add_column(
            "KE",
            ColumnType.CALCULATED,
            formula="0.5 * {mass} * {velocity}**2",
            unit="J"
        )
        
        # 6. CALCULATED column - potential energy
        study.add_column(
            "PE",
            ColumnType.CALCULATED,
            formula="{mass} * 9.81 * {height}",
            unit="J"
        )
        
        # 7. CALCULATED column - total energy
        study.add_column(
            "total_energy",
            ColumnType.CALCULATED,
            formula="{KE} + {PE}",
            unit="J"
        )
        
        self._add_study(study)
        
        # Add Variables tab
        self._new_variables_tab()
    
    def _add_study(self, study: Study):
        """Add study tab.
        
        Args:
            study: Study to add
        """
        # Ensure study has workspace reference (for studies that support it)
        if hasattr(study, 'workspace'):
            if not getattr(study, 'workspace'):
                setattr(study, 'workspace', self.workspace)
        
        self.workspace.add_study(study)
        
        # Create widget for study
        if isinstance(study, DataTableStudy):
            widget = DataTableWidget(study)
            self.study_tabs.addTab(widget, study.name)
        elif isinstance(study, PlotStudy):
            widget = PlotWidget(study, self.workspace)
            self.study_tabs.addTab(widget, study.name)
        elif isinstance(study, StatisticsStudy):
            widget = StatisticsWidget(study, self)
            self.study_tabs.addTab(widget, study.name)
    
    def _new_data_table(self):
        """Create new Data Table study."""
        # Ask for study name
        name, ok = QInputDialog.getText(
            self,
            "New Data Table",
            "Table name:",
            text=f"Table {len(self.workspace.studies) + 1}"
        )
        
        if ok and name:
            # Create new DataTable study
            study = DataTableStudy(name, workspace=self.workspace)
            
            study.add_column("x")
            study.add_column("y")
            study.add_rows(10)
            
            self._add_study(study)
            
            # Switch to new study
            self.study_tabs.setCurrentIndex(self.study_tabs.count() - 1)
    
    def _new_plot(self):
        """Create new Plot study."""
        # Ask for study name
        name, ok = QInputDialog.getText(
            self,
            "New Plot",
            "Plot name:",
            text=f"Plot {len(self.workspace.studies) + 1}"
        )
        
        if ok and name:
            # Create new Plot study
            study = PlotStudy(name, workspace=self.workspace)
            
            self._add_study(study)
            
            # Switch to new study
            self.study_tabs.setCurrentIndex(self.study_tabs.count() - 1)
    
    def _new_statistics(self):
        """Create new Statistics study."""
        # Get list of data table studies
        data_tables = [s.name for s in self.workspace.studies.values() if isinstance(s, DataTableStudy)]
        
        if not data_tables:
            QMessageBox.warning(
                self,
                "No Data Tables",
                "Create a Data Table first to analyze."
            )
            return
        
        # Ask for study name
        name, ok = QInputDialog.getText(
            self,
            "New Statistics",
            "Statistics name:",
            text=f"Statistics {len(self.workspace.studies) + 1}"
        )
        
        if ok and name:
            # Ask which data table to analyze
            from PySide6.QtWidgets import QInputDialog as QID
            source_table, ok = QID.getItem(
                self,
                "Select Data Source",
                "Analyze data from:",
                data_tables,
                0,
                False
            )
            
            if ok and source_table:
                # Create new Statistics study
                study = StatisticsStudy(name, source_study=source_table, workspace=self.workspace)
                
                self._add_study(study)
                
                # Switch to new study
                self.study_tabs.setCurrentIndex(self.study_tabs.count() - 1)
    
    def _new_variables_tab(self):
        """Create new Variables tab."""
        vars_widget = ConstantsWidget(self.workspace, self)
        
        # Connect signal to update all studies
        vars_widget.constants_changed.connect(self._on_variables_changed)
        
        self.study_tabs.addTab(vars_widget, "Constants & Functions")
        
        # Make Variables tab non-closable by moving close button
        # (We'll handle this by checking tab name in close handler)
    
    def _on_variables_changed(self):
        """Handle variables changed signal."""
        # Recalculate all studies
        for study in self.workspace.studies.values():
            if isinstance(study, DataTableStudy):
                study.recalculate_all()
        
        self.statusBar().showMessage("Constants updated, studies recalculated")
    
    def _close_study(self, index: int):
        """Close study tab.
        
        Args:
            index: Tab index
        """
        # Get study name from tab
        study_name = self.study_tabs.tabText(index)
        
        # Don't allow closing Constants tab
        if study_name == "Constants & Functions":
            return
        
        # Confirm close
        reply = QMessageBox.question(
            self,
            "Close Study",
            f"Close study '{study_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove from workspace
            self.workspace.remove_study(study_name)
            
            # Remove tab
            self.study_tabs.removeTab(index)
    
    def _export_to_csv(self):
        """Export current data table to CSV."""
        # Get current study
        current_widget = self.study_tabs.currentWidget()
        
        if not isinstance(current_widget, DataTableWidget):
            QMessageBox.warning(
                self,
                "Export Error",
                "Please select a Data Table to export."
            )
            return
        
        study = current_widget.study
        
        # Get filename
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export to CSV",
            f"{study.name}.csv",
            "CSV Files (*.csv)"
        )
        
        if filename:
            try:
                # Ask about metadata
                reply = QMessageBox.question(
                    self,
                    "Include Metadata",
                    "Include column metadata (types, units, formulas) as comments?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                include_metadata = reply == QMessageBox.StandardButton.Yes
                
                study.export_to_csv(filename, include_metadata=include_metadata)
                self.statusBar().showMessage(f"Exported to {filename}")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Error",
                    f"Failed to export: {str(e)}"
                )
    
    def _export_to_excel(self):
        """Export current data table to Excel."""
        current_widget = self.study_tabs.currentWidget()
        
        if not isinstance(current_widget, DataTableWidget):
            QMessageBox.warning(
                self,
                "Export Error",
                "Please select a Data Table to export."
            )
            return
        
        study = current_widget.study
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export to Excel",
            f"{study.name}.xlsx",
            "Excel Files (*.xlsx)"
        )
        
        if filename:
            try:
                study.export_to_excel(filename, sheet_name=study.name)
                self.statusBar().showMessage(f"Exported to {filename}")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Error",
                    f"Failed to export: {str(e)}"
                )
    
    def _import_from_csv(self):
        """Import data table from CSV."""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Import from CSV",
            "",
            "CSV Files (*.csv)"
        )
        
        if filename:
            try:
                # Open CSV import dialog with preview
                dialog = CSVImportDialog(filename, self)
                
                if dialog.exec():
                    settings = dialog.get_import_settings()
                    
                    # Ask for study name
                    import os
                    default_name = os.path.splitext(os.path.basename(filename))[0]
                    name, ok = QInputDialog.getText(
                        self,
                        "Import CSV",
                        "Study name:",
                        text=default_name
                    )
                    
                    if ok and name:
                        study = DataTableStudy(name, workspace=self.workspace)
                        study.import_from_csv(filename, **settings)
                        
                        self._add_study(study)
                        self.study_tabs.setCurrentIndex(self.study_tabs.count() - 1)
                        self.statusBar().showMessage(f"Imported from {filename}")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Import Error",
                    f"Failed to import: {str(e)}"
                )
    
    def _import_from_excel(self):
        """Import data table from Excel."""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Import from Excel",
            "",
            "Excel Files (*.xlsx *.xls)"
        )
        
        if filename:
            try:
                # Ask for study name
                import os
                default_name = os.path.splitext(os.path.basename(filename))[0]
                name, ok = QInputDialog.getText(
                    self,
                    "Import Excel",
                    "Study name:",
                    text=default_name
                )
                
                if ok and name:
                    study = DataTableStudy(name, workspace=self.workspace)
                    study.import_from_excel(filename)
                    
                    self._add_study(study)
                    self.study_tabs.setCurrentIndex(self.study_tabs.count() - 1)
                    self.statusBar().showMessage(f"Imported from {filename}")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Import Error",
                    f"Failed to import: {str(e)}"
                )
    
    def _rename_current_study(self):
        """Rename current study."""
        current_index = self.study_tabs.currentIndex()
        if current_index < 0:
            return
        
        old_name = self.study_tabs.tabText(current_index)
        
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Study",
            "New study name:",
            text=old_name
        )
        
        if ok and new_name and new_name != old_name:
            # Update workspace
            if old_name in self.workspace.studies:
                study = self.workspace.studies.pop(old_name)
                study.name = new_name
                self.workspace.studies[new_name] = study
            
            # Update tab
            self.study_tabs.setTabText(current_index, new_name)
    
    def _close_current_study(self):
        """Close current study tab."""
        current_index = self.study_tabs.currentIndex()
        if current_index >= 0:
            self._close_study(current_index)
    
    def _next_tab(self):
        """Switch to next tab."""
        if self.study_tabs.count() > 0:
            current = self.study_tabs.currentIndex()
            next_index = (current + 1) % self.study_tabs.count()
            self.study_tabs.setCurrentIndex(next_index)
    
    def _prev_tab(self):
        """Switch to previous tab."""
        if self.study_tabs.count() > 0:
            current = self.study_tabs.currentIndex()
            prev_index = (current - 1) % self.study_tabs.count()
            self.study_tabs.setCurrentIndex(prev_index)
    
    def _load_example(self, example_name: str):
        """Load example dataset into a new data table.
        
        Args:
            example_name: Name of example to load
        """
        # Close welcome tab if present
        for i in range(self.study_tabs.count()):
            if self.study_tabs.tabText(i) == "Physics Demo":
                self._close_study(i)
                break
        
        # Create study based on example type
        if example_name == "projectile_motion":
            self._load_projectile_motion_example()
        elif example_name == "freefall":
            self._load_freefall_example()
        elif example_name == "oscillator":
            self._load_oscillator_example()
        elif example_name == "derivatives":
            self._load_derivatives_example()
    
    def _load_projectile_motion_example(self):
        """Load projectile motion example - Baseball trajectory."""
        study = DataTableStudy("Projectile Motion", workspace=self.workspace)
        
        # Physical constants
        self.workspace.add_constant("g", 9.80665, "m/s^2")
        self.workspace.add_constant("v0", 45.0, "m/s")
        self.workspace.add_constant("theta", 35.0, "deg")
        
        import math
        theta_rad = 35.0 * math.pi / 180.0
        v0y = 45.0 * math.sin(theta_rad)
        t_max = 2 * v0y / 9.80665
        
        # Time column
        study.add_column("t", ColumnType.RANGE,
                        range_type="linspace",
                        range_start=0,
                        range_stop=t_max,
                        range_count=30,
                        unit="s")
        
        # Position calculations
        study.add_column("x", ColumnType.CALCULATED,
                        formula="{v0} * cos({theta} * pi / 180) * {t}",
                        unit="m")
        
        study.add_column("y", ColumnType.CALCULATED,
                        formula="{v0} * sin({theta} * pi / 180) * {t} - 0.5 * {g} * {t}**2",
                        unit="m")
        
        # Velocity components (derivatives)
        study.add_column("vx", ColumnType.DERIVATIVE,
                        derivative_of="x",
                        with_respect_to="t",
                        unit="m/s")
        
        study.add_column("vy", ColumnType.DERIVATIVE,
                        derivative_of="y",
                        with_respect_to="t",
                        unit="m/s")
        
        self._add_study(study)
        self.study_tabs.setCurrentIndex(self.study_tabs.count() - 1)
        self.statusBar().showMessage("Loaded: Projectile Motion example")
    
    def _load_freefall_example(self):
        """Load free fall example."""
        study = DataTableStudy("Free Fall", workspace=self.workspace)
        
        self.workspace.add_constant("g", 9.81, "m/s^2")
        self.workspace.add_constant("h0", 100.0, "m")
        
        # Time column
        study.add_column("t", ColumnType.RANGE,
                        range_type="linspace",
                        range_start=0,
                        range_stop=4.5,
                        range_count=20,
                        unit="s")
        
        # Height
        study.add_column("h", ColumnType.CALCULATED,
                        formula="{h0} - 0.5 * {g} * {t}**2",
                        unit="m")
        
        # Velocity
        study.add_column("v", ColumnType.DERIVATIVE,
                        derivative_of="h",
                        with_respect_to="t",
                        unit="m/s")
        
        # Acceleration
        study.add_column("a", ColumnType.DERIVATIVE,
                        derivative_of="v",
                        with_respect_to="t",
                        unit="m/s^2")
        
        self._add_study(study)
        self.study_tabs.setCurrentIndex(self.study_tabs.count() - 1)
        self.statusBar().showMessage("Loaded: Free Fall example")
    
    def _load_oscillator_example(self):
        """Load damped harmonic oscillator example."""
        study = DataTableStudy("Damped Oscillator", workspace=self.workspace)
        
        self.workspace.add_constant("k", 10.0, "N/m")
        self.workspace.add_constant("m", 0.5, "kg")
        self.workspace.add_constant("b", 0.5, "kg/s")
        self.workspace.add_constant("omega", 4.47, "rad/s")
        self.workspace.add_constant("gamma", 0.5, "1/s")
        
        # Time column
        study.add_column("t", ColumnType.RANGE,
                        range_type="linspace",
                        range_start=0,
                        range_stop=10,
                        range_count=100,
                        unit="s")
        
        # Position (damped sinusoid)
        study.add_column("x", ColumnType.CALCULATED,
                        formula="exp(-{gamma} * {t}) * cos({omega} * {t})",
                        unit="m")
        
        # Velocity
        study.add_column("v", ColumnType.DERIVATIVE,
                        derivative_of="x",
                        with_respect_to="t",
                        unit="m/s")
        
        # Acceleration
        study.add_column("a", ColumnType.DERIVATIVE,
                        derivative_of="v",
                        with_respect_to="t",
                        unit="m/s^2")
        
        self._add_study(study)
        self.study_tabs.setCurrentIndex(self.study_tabs.count() - 1)
        self.statusBar().showMessage("Loaded: Damped Oscillator example")
    
    def _load_derivatives_example(self):
        """Load derivatives demonstration example."""
        study = DataTableStudy("Derivatives Demo", workspace=self.workspace)
        
        # Time column
        study.add_column("t", ColumnType.RANGE,
                        range_type="linspace",
                        range_start=0,
                        range_stop=10,
                        range_count=50,
                        unit="s")
        
        # Position (cubic polynomial)
        study.add_column("position", ColumnType.CALCULATED,
                        formula="{t}**3 - 5*{t}**2 + 6*{t}",
                        unit="m")
        
        # 1st derivative: velocity
        study.add_column("velocity", ColumnType.DERIVATIVE,
                        derivative_of="position",
                        with_respect_to="t",
                        unit="m/s")
        
        # 2nd derivative: acceleration
        study.add_column("acceleration", ColumnType.DERIVATIVE,
                        derivative_of="velocity",
                        with_respect_to="t",
                        unit="m/s^2")
        
        # 3rd derivative: jerk
        study.add_column("jerk", ColumnType.DERIVATIVE,
                        derivative_of="acceleration",
                        with_respect_to="t",
                        unit="m/s^3")
        
        self._add_study(study)
        self.study_tabs.setCurrentIndex(self.study_tabs.count() - 1)
        self.statusBar().showMessage("Loaded: Derivatives Demo example")
    
    def _save_workspace(self):
        """Save workspace to JSON file."""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Workspace",
            "",
            "DataManip Workspace (*.dmw);;JSON Files (*.json);;All Files (*)"
        )
        
        if not filename:
            return
        
        try:
            workspace_data = self.workspace.to_dict()
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(workspace_data, f, indent=2)
            
            self.statusBar().showMessage(f"Workspace saved to {Path(filename).name}", 3000)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save workspace:\n{str(e)}"
            )
    
    def _load_workspace(self):
        """Load workspace from JSON file."""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open Workspace",
            "",
            "DataManip Workspace (*.dmw);;JSON Files (*.json);;All Files (*)"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                workspace_data = json.load(f)
            
            # Clear current workspace
            self.study_tabs.clear()
            
            # Load workspace
            self.workspace = Workspace.from_dict(workspace_data)
            
            # Recreate study tabs
            for study_name, study in self.workspace.studies.items():
                if isinstance(study, DataTableStudy):
                    widget = DataTableWidget(study)
                    self.study_tabs.addTab(widget, study.name)
                elif isinstance(study, PlotStudy):
                    widget = PlotWidget(study, self.workspace)
                    self.study_tabs.addTab(widget, study.name)
            
            # Add variables tab
            self._new_variables_tab()
            
            self.statusBar().showMessage(f"Workspace loaded from {Path(filename).name}", 3000)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load workspace:\n{str(e)}"
            )
    
    def _show_shortcuts(self):
        """Show keyboard shortcuts help."""
        shortcuts_text = """
        <h3>Keyboard Shortcuts</h3>
        <table>
        <tr><td><b>Ctrl+T</b></td><td>New Data Table</td></tr>
        <tr><td><b>Ctrl+P</b></td><td>New Plot</td></tr>
        <tr><td><b>Ctrl+K</b></td><td>New Constants Tab</td></tr>
        <tr><td><b>Ctrl+S</b></td><td>Save Workspace</td></tr>
        <tr><td><b>Ctrl+O</b></td><td>Open Workspace</td></tr>
        <tr><td><b>Ctrl+W</b></td><td>Close Study</td></tr>
        <tr><td><b>Ctrl+Q</b></td><td>Exit Application</td></tr>
        <tr><td><b>F2</b></td><td>Rename Study</td></tr>
        <tr><td><b>Ctrl+Tab</b></td><td>Next Tab</td></tr>
        <tr><td><b>Ctrl+Shift+Tab</b></td><td>Previous Tab</td></tr>
        <tr><td><b>F1</b></td><td>Show This Help</td></tr>
        </table>
        <h4>DataTable View</h4>
        <table>
        <tr><td><b>Ctrl+R</b></td><td>Add Row</td></tr>
        <tr><td><b>Ctrl+D</b></td><td>Delete Row(s)</td></tr>
        <tr><td><b>Ctrl+Shift+D</b></td><td>Add Data Column</td></tr>
        <tr><td><b>Ctrl+Shift+C</b></td><td>Add Calculated Column</td></tr>
        <tr><td><b>Ctrl+F</b></td><td>Search/Filter</td></tr>
        <tr><td><b>Double-click header</b></td><td>Rename Column</td></tr>
        </table>
        <h4>Plot View</h4>
        <table>
        <tr><td><b>Ctrl+A</b></td><td>Add Series</td></tr>
        <tr><td><b>Ctrl+R</b></td><td>Remove Series</td></tr>
        <tr><td><b>F5</b></td><td>Refresh Plot</td></tr>
        </table>
        <h4>Constants & Functions View</h4>
        <table>
        <tr><td><b>Ctrl+N</b></td><td>Add New</td></tr>
        <tr><td><b>Ctrl+E</b></td><td>Edit Selected</td></tr>
        <tr><td><b>Delete</b></td><td>Remove Selected</td></tr>
        <tr><td><b>Ctrl+F</b></td><td>Search/Filter</td></tr>
        <tr><td><b>F5</b></td><td>Refresh</td></tr>
        </table>
        """
        QMessageBox.information(self, "Keyboard Shortcuts", shortcuts_text)
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About DataManip",
            "<h3>DataManip v0.2.0</h3>"
            "<p>Data manipulation and analysis application for experimental sciences.</p>"
            "<p>Features:</p>"
            "<ul>"
            "<li>4 column types: DATA, CALCULATED, DERIVATIVE, RANGE</li>"
            "<li>Formula engine with dependency tracking</li>"
            "<li>Constants & functions support</li>"
            "<li>Unit tracking and visualization</li>"
            "</ul>"
            "<p>Built with PySide6, pandas, and NumPy.</p>"
            "<p><i>88/88 unit tests passing!</i></p>"
        )
