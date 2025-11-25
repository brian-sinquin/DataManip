"""
Main application window.

Single workspace containing multiple study tabs.
"""

from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QMessageBox, QInputDialog, QFileDialog, QTabBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
import json
from pathlib import Path
import numpy as np

from .preferences_dialog import PreferencesDialog
from .notification_manager import NotificationManager, ProgressNotification
from utils.lang import tr
from constants import (
    MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT,
    APP_NAME, APP_VERSION, APP_DESCRIPTION
)
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
        
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION} - {APP_DESCRIPTION}")
        self.resize(MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT)
        
        # Single workspace
        self.workspace = Workspace("Workspace", "numerical")
        
        # Notification manager
        self.notifications = None  # Initialized after UI setup
        
        # Load preferences
        self.preferences = PreferencesDialog.get_settings()
        
        # Setup UI
        self._setup_ui()
        self._setup_menu()
        
        # Initialize notification manager after UI is ready
        self.notifications = NotificationManager(self)
        
        # Apply initial preferences (display precision)
        from .widgets.shared import set_display_precision
        set_display_precision(self.preferences.get("display_precision", 3))
        
        # Welcome message
        self.statusBar().showMessage("Welcome to DataManip! Press Ctrl+T for new table, Ctrl+P for new plot, F1 for help")
        self.notifications.show_info("Welcome to DataManip! Create a new table or open an example to get started")

    
    def _setup_ui(self):
        """Setup UI components."""
        # Study tabs as central widget
        self.study_tabs = QTabWidget()
        self.study_tabs.setTabsClosable(True)
        self.study_tabs.tabCloseRequested.connect(self._close_study)
        self.study_tabs.currentChanged.connect(self._on_tab_changed)
        
        self.setCentralWidget(self.study_tabs)
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def _setup_menu(self):
        """Setup menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu(tr("menu.file", "&File"))
        
        # New submenu
        new_menu = file_menu.addMenu(tr("file.new", "&New"))
        
        new_table_action = QAction(tr("file.new_table", "Data &Table"), self)
        new_table_action.setShortcut("Ctrl+T")
        new_table_action.setToolTip(tr("file.new_table_tip", "Create a new data table"))
        new_table_action.triggered.connect(self._new_data_table)
        new_menu.addAction(new_table_action)
        
        new_plot_action = QAction(tr("file.new_plot", "&Plot"), self)
        new_plot_action.setShortcut("Ctrl+P")
        new_plot_action.setToolTip(tr("file.new_plot_tip", "Create a new plot"))
        new_plot_action.triggered.connect(self._new_plot)
        new_menu.addAction(new_plot_action)
        
        new_statistics_action = QAction(tr("file.new_statistics", "&Statistics"), self)
        new_statistics_action.setShortcut("Ctrl+S")
        new_statistics_action.setToolTip(tr("file.new_statistics_tip", "Create a new statistics study"))
        new_statistics_action.triggered.connect(self._new_statistics)
        new_menu.addAction(new_statistics_action)
        
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
        
        self.undo_action = QAction("&Undo", self)
        self.undo_action.setShortcut("Ctrl+Z")
        self.undo_action.triggered.connect(self._undo)
        self.undo_action.setEnabled(False)
        edit_menu.addAction(self.undo_action)
        
        self.redo_action = QAction("&Redo", self)
        self.redo_action.setShortcut("Ctrl+Y")
        self.redo_action.triggered.connect(self._redo)
        self.redo_action.setEnabled(False)
        edit_menu.addAction(self.redo_action)
        
        edit_menu.addSeparator()
        
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
        
        constants_action = QAction("Constants && &Functions", self)
        constants_action.setShortcut("Ctrl+K")
        constants_action.setToolTip("Open Constants & Functions panel")
        constants_action.triggered.connect(self._open_constants_tab)
        view_menu.addAction(constants_action)
        
        view_menu.addSeparator()
        
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
        
        # Tutorial examples (one feature each)
        tutorial_menu = examples_menu.addMenu("📚 Tutorial (One Feature)")
        
        example_01 = QAction("01 - Simple Pendulum", self)
        example_01.setToolTip("Tutorial: Basic data entry and plotting")
        example_01.triggered.connect(lambda: self._load_example_workspace("01_simple_pendulum.dmw"))
        tutorial_menu.addAction(example_01)
        
        example_02 = QAction("02 - Resistor Network", self)
        example_02.setToolTip("Tutorial: Calculated columns with formulas")
        example_02.triggered.connect(lambda: self._load_example_workspace("02_resistor_network.dmw"))
        tutorial_menu.addAction(example_02)
        
        example_03 = QAction("03 - Free Fall", self)
        example_03.setToolTip("Tutorial: Range generation (linspace)")
        example_03.triggered.connect(lambda: self._load_example_workspace("03_free_fall.dmw"))
        tutorial_menu.addAction(example_03)
        
        example_04 = QAction("04 - Inclined Plane", self)
        example_04.setToolTip("Tutorial: Numerical derivatives (1st and 2nd order)")
        example_04.triggered.connect(lambda: self._load_example_workspace("04_inclined_plane.dmw"))
        tutorial_menu.addAction(example_04)
        
        example_05 = QAction("05 - Density Measurement", self)
        example_05.setToolTip("Tutorial: Uncertainty propagation")
        example_05.triggered.connect(lambda: self._load_example_workspace("05_density_measurement.dmw"))
        tutorial_menu.addAction(example_05)
        
        example_06 = QAction("06 - Damped Oscillation", self)
        example_06.setToolTip("Tutorial: Custom functions")
        example_06.triggered.connect(lambda: self._load_example_workspace("06_damped_oscillation.dmw"))
        tutorial_menu.addAction(example_06)
        
        # Complete experimental examples (all features)
        complete_menu = examples_menu.addMenu("🔬 Complete Experiments")
        
        example_07 = QAction("07 - Calorimetry", self)
        example_07.setToolTip("Complete: Heat capacity with derivatives and uncertainties")
        example_07.triggered.connect(lambda: self._load_example_workspace("07_calorimetry.dmw"))
        complete_menu.addAction(example_07)
        
        example_08 = QAction("08 - Photoelectric Effect", self)
        example_08.setToolTip("Complete: Planck's constant determination")
        example_08.triggered.connect(lambda: self._load_example_workspace("08_photoelectric_effect.dmw"))
        complete_menu.addAction(example_08)
        
        example_09 = QAction("09 - Spring-Mass System", self)
        example_09.setToolTip("Complete: SHM with damping and phase space")
        example_09.triggered.connect(lambda: self._load_example_workspace("09_spring_mass_shm.dmw"))
        complete_menu.addAction(example_09)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        preferences_action = QAction("&Preferences...", self)
        preferences_action.setShortcut("Ctrl+,")
        preferences_action.triggered.connect(self._show_preferences)
        tools_menu.addAction(preferences_action)
        
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
        # Initialize workspace constants - physics and calculated values
        self.workspace.add_constant("g", 9.81, "m/s^2")
        self.workspace.add_constant("pi", 3.14159265359, None)
        self.workspace.add_constant("air_density", 1.225, "kg/m^3")
        self.workspace.add_constant("mass", 0.145, "kg")  # Baseball mass
        self.workspace.add_constant("Cd", 0.47, None)  # Sphere drag coefficient
        
        # Calculated constant - cross-sectional area
        self.workspace.add_calculated_variable(
            "area",
            "pi * (0.037)**2",  # Baseball radius ~3.7 cm (no braces for workspace formulas)
            "m^2"
        )
        
        max_undo_steps = self.preferences.get("max_undo_steps", 50)
        study = DataTableStudy("Baseball Trajectory Analysis", workspace=self.workspace, max_undo_steps=max_undo_steps)
        
        # Comprehensive example: Baseball trajectory with all features
        
        # 1. RANGE column - time sequence
        study.add_column(
            "time",
            ColumnType.RANGE,
            unit="s",
            range_type="linspace",
            range_start=0.0,
            range_stop=4.0,
            range_count=41
        )
        
        # 2. DATA columns - initial conditions with manual uncertainties
        study.add_column("v0", ColumnType.DATA, 
                        initial_data=np.full(41, 45.0), 
                        unit="m/s")
        study.add_column("v0_u", ColumnType.UNCERTAINTY, 
                        initial_data=np.full(41, 1.0), 
                        unit="m/s",
                        uncertainty_reference="v0")
        
        study.add_column("angle", ColumnType.DATA, 
                        initial_data=np.full(41, 30.0), 
                        unit="deg")
        study.add_column("angle_u", ColumnType.UNCERTAINTY, 
                        initial_data=np.full(41, 2.0), 
                        unit="deg",
                        uncertainty_reference="angle")
        
        # 3. CALCULATED columns - velocity components using constants
        study.add_column(
            "vx",
            ColumnType.CALCULATED,
            formula="{v0} * np.cos({angle} * {pi} / 180)",
            unit="m/s",
            propagate_uncertainty=True
        )
        
        study.add_column(
            "vy",
            ColumnType.CALCULATED,
            formula="{v0} * np.sin({angle} * {pi} / 180) - {g} * {time}",
            unit="m/s",
            propagate_uncertainty=True
        )
        
        # 4. CALCULATED columns - position trajectories
        study.add_column(
            "x",
            ColumnType.CALCULATED,
            formula="{vx} * {time}",
            unit="m",
            propagate_uncertainty=True
        )
        
        study.add_column(
            "y",
            ColumnType.CALCULATED,
            formula="{v0} * np.sin({angle} * {pi} / 180) * {time} - 0.5 * {g} * {time}**2",
            unit="m",
            propagate_uncertainty=True
        )
        
        # 5. CALCULATED column - instantaneous speed
        study.add_column(
            "speed",
            ColumnType.CALCULATED,
            formula="np.sqrt({vx}**2 + {vy}**2)",
            unit="m/s"
        )
        
        # 6. CALCULATED column - kinetic energy using constant
        study.add_column(
            "KE",
            ColumnType.CALCULATED,
            formula="0.5 * {mass} * {speed}**2",
            unit="J"
        )
        
        # 7. CALCULATED column - potential energy
        study.add_column(
            "PE",
            ColumnType.CALCULATED,
            formula="{mass} * {g} * np.maximum({y}, 0)",  # max to avoid negative height
            unit="J"
        )
        
        # 8. CALCULATED column - total mechanical energy
        study.add_column(
            "E_total",
            ColumnType.CALCULATED,
            formula="{KE} + {PE}",
            unit="J"
        )
        
        # 9. DERIVATIVE columns - acceleration
        study.add_column(
            "ax",
            ColumnType.DERIVATIVE,
            derivative_of="vx",
            with_respect_to="time",
            unit="m/s^2"
        )
        
        study.add_column(
            "ay",
            ColumnType.DERIVATIVE,
            derivative_of="vy",
            with_respect_to="time",
            unit="m/s^2"
        )
        
        # 10. CALCULATED column - trajectory angle
        study.add_column(
            "trajectory_angle",
            ColumnType.CALCULATED,
            formula="np.arctan2({vy}, {vx}) * 180 / {pi}",
            unit="deg"
        )
        
        # 11. CALCULATED column - distance from origin
        study.add_column(
            "distance",
            ColumnType.CALCULATED,
            formula="np.sqrt({x}**2 + {y}**2)",
            unit="m"
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
            # Connect dataChanged signal to refresh dependent widgets
            widget.dataChanged.connect(self._on_data_table_changed)
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
            max_undo_steps = self.preferences.get("max_undo_steps", 50)
            study = DataTableStudy(name, workspace=self.workspace, max_undo_steps=max_undo_steps)
            
            study.add_column("x")
            study.add_column("y")
            study.add_rows(10)
            
            self._add_study(study)
            
            # Switch to new study
            self.study_tabs.setCurrentIndex(self.study_tabs.count() - 1)
            self.notifications.show_success(f"Data table '{name}' created")
    
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
            self.notifications.show_success(f"Plot '{name}' created")
    
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
        """Create new Variables tab (only if one doesn't already exist)."""
        # Check if Constants & Functions tab already exists
        for i in range(self.study_tabs.count()):
            if "Constants" in self.study_tabs.tabText(i) and "Functions" in self.study_tabs.tabText(i):
                # Tab already exists, don't create another one
                return
        
        # Tab doesn't exist, create it
        vars_widget = ConstantsWidget(self.workspace, self)
        
        # Connect signal to update all studies
        vars_widget.constants_changed.connect(self._on_variables_changed)
        
        # Add tab and make it non-closable
        tab_index = self.study_tabs.addTab(vars_widget, "Constants & Functions")
        self.study_tabs.tabBar().setTabButton(tab_index, QTabBar.ButtonPosition.RightSide, None)
        self.study_tabs.tabBar().setTabButton(tab_index, QTabBar.ButtonPosition.LeftSide, None)
    
    def _open_constants_tab(self):
        """Open or switch to Constants & Functions tab."""
        # Check if Constants & Functions tab already exists
        for i in range(self.study_tabs.count()):
            if "Constants" in self.study_tabs.tabText(i) and "Functions" in self.study_tabs.tabText(i):
                # Tab exists, switch to it
                self.study_tabs.setCurrentIndex(i)
                return
        
        # Tab doesn't exist, create it
        self._new_variables_tab()
        # Switch to the newly created tab
        self.study_tabs.setCurrentIndex(self.study_tabs.count() - 1)
    
    def _on_variables_changed(self):
        """Handle variables changed signal."""
        # Recalculate all studies that use formulas
        for study in self.workspace.studies.values():
            if isinstance(study, DataTableStudy):
                study.recalculate_all()
        
        # Refresh the Constants tab itself to show updated calculated values
        # Find Constants tab by searching all tabs
        for i in range(self.study_tabs.count()):
            constants_tab = self.study_tabs.widget(i)
            if isinstance(constants_tab, ConstantsWidget):
                constants_tab._load_constants()
                break
        
        self.statusBar().showMessage("Constants updated, studies recalculated")
    
    def _on_data_table_changed(self, study_name: str):
        """Handle data table change to refresh dependent widgets.
        
        Args:
            study_name: Name of the data table that changed
        """
        # Refresh all plot widgets that depend on this data table
        for i in range(self.study_tabs.count()):
            widget = self.study_tabs.widget(i)
            
            # Refresh PlotWidget if it references this data table
            if isinstance(widget, PlotWidget):
                if hasattr(widget.study, 'series'):
                    for series in widget.study.series:
                        if series.get('study_name') == study_name:
                            widget.refresh()
                            break
            
            # Refresh StatisticsWidget if it references this data table
            elif isinstance(widget, StatisticsWidget):
                if hasattr(widget.study, 'source_study_name'):
                    if widget.study.source_study_name == study_name:
                        widget.refresh()
    
    def _close_study(self, index: int):
        """Close study tab.
        
        Args:
            index: Tab index
        """
        # Get study name from tab
        study_name = self.study_tabs.tabText(index)
        
        # Prevent closing Constants & Functions tab
        if "Constants" in study_name and "Functions" in study_name:
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
                        max_undo_steps = self.preferences.get("max_undo_steps", 50)
                        study = DataTableStudy(name, workspace=self.workspace, max_undo_steps=max_undo_steps)
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
                    max_undo_steps = self.preferences.get("max_undo_steps", 50)
                    study = DataTableStudy(name, workspace=self.workspace, max_undo_steps=max_undo_steps)
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
            self.notifications.show_success(f"Study renamed to '{new_name}'")
    
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
    
    def _load_example_workspace(self, filename: str):
        """Load example workspace from examples directory.
        
        Args:
            filename: Name of the example workspace file (e.g., "01_basic_introduction.dmw")
        """
        # Get path to examples directory using importlib.resources
        try:
            from importlib.resources import files
            examples_dir = Path(str(files('core').joinpath('examples')))
            # Check if it actually exists (dev mode vs installed)
            if not examples_dir.exists():
                # Fallback for development mode
                examples_dir = Path(__file__).parent.parent.parent / "examples"
        except Exception:
            # Fallback for development mode
            examples_dir = Path(__file__).parent.parent.parent / "examples"
        
        filepath = examples_dir / filename
        
        if not filepath.exists():
            QMessageBox.warning(
                self,
                "Example Not Found",
                f"Example file not found: {filename}\n\nPath: {filepath}"
            )
            return
        
        try:
            # Ask if user wants to save current workspace (only if there are any tabs)
            if self.study_tabs.count() > 0:
                reply = QMessageBox.question(
                    self,
                    "Load Example",
                    "Loading an example will replace the current workspace.\n\nDo you want to continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.No:
                    return
            
            # Load the workspace
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Clear current workspace
            while self.study_tabs.count() > 0:
                self.study_tabs.removeTab(0)
            
            # Load new workspace
            self.workspace = Workspace.from_dict(data)
            self.setWindowTitle(f"{APP_NAME} v{APP_VERSION} - {self.workspace.name}")
            
            # Create tabs for each study
            for study in self.workspace.studies.values():
                self._add_study(study)
            
            # Always add constants tab
            self._new_variables_tab()
            
            self.statusBar().showMessage(f"Loaded example: {self.workspace.name}")
            self.notifications.show_success(f"Loaded: {self.workspace.name}")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load example:\n{str(e)}"
            )
    
    def _save_workspace(self):
        """Save workspace to JSON file with atomic write."""
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
            
            # Atomic write: write to temp file, then rename
            filepath = Path(filename)
            temp_path = filepath.with_suffix(filepath.suffix + '.tmp')
            
            # Create backup if file exists
            if filepath.exists():
                backup_path = filepath.with_suffix(filepath.suffix + '.bak')
                if backup_path.exists():
                    backup_path.unlink()
                filepath.rename(backup_path)
            
            try:
                # Write to temp file
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(workspace_data, f, indent=2)
                
                # Atomic rename
                temp_path.rename(filepath)
                
                # Remove backup on success
                backup_path = filepath.with_suffix(filepath.suffix + '.bak')
                if backup_path.exists():
                    backup_path.unlink()
                
                self.statusBar().showMessage(f"Workspace saved to {filepath.name}", 3000)
                self.notifications.show_success(f"Workspace saved to {filepath.name}")
            except Exception as e:
                # Restore from backup on failure
                if temp_path.exists():
                    temp_path.unlink()
                backup_path = filepath.with_suffix(filepath.suffix + '.bak')
                if backup_path.exists():
                    backup_path.rename(filepath)
                raise
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save workspace:\n{str(e)}"
            )
            self.notifications.show_error("Failed to save workspace")
    
    def _load_workspace(self, filename: str = None):
        """Load workspace from JSON file.
        
        Args:
            filename: Optional path to workspace file. If None, shows file dialog.
        """
        if not filename:
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
                    # Connect dataChanged signal
                    widget.dataChanged.connect(self._on_data_table_changed)
                elif isinstance(study, PlotStudy):
                    widget = PlotWidget(study, self.workspace)
                    self.study_tabs.addTab(widget, study.name)
            
            # Add variables tab
            self._new_variables_tab()
            
            self.statusBar().showMessage(f"Workspace loaded from {Path(filename).name}", 3000)
            self.notifications.show_success(f"Workspace loaded from {Path(filename).name}")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load workspace:\n{str(e)}"
            )
            self.notifications.show_error("Failed to load workspace")
    
    def _show_shortcuts(self):
        """Show keyboard shortcuts help."""
        shortcuts_text = """
        <h2>Keyboard Shortcuts</h2>
        <h3>File Menu</h3>
        <table>
        <tr><td><b>Ctrl+T</b></td><td>New Data Table</td></tr>
        <tr><td><b>Ctrl+P</b></td><td>New Plot</td></tr>
        <tr><td><b>Ctrl+S (Stats menu)</b></td><td>New Statistics</td></tr>
        <tr><td><b>Ctrl+I</b></td><td>Import from CSV</td></tr>
        <tr><td><b>Ctrl+E</b></td><td>Export to CSV</td></tr>
        <tr><td><b>Ctrl+S (File menu)</b></td><td>Save Workspace</td></tr>
        <tr><td><b>Ctrl+O</b></td><td>Open Workspace</td></tr>
        <tr><td><b>Ctrl+Q</b></td><td>Exit Application</td></tr>
        </table>
        
        <h3>Edit Menu</h3>
        <table>
        <tr><td><b>Ctrl+Z</b></td><td>Undo</td></tr>
        <tr><td><b>Ctrl+Y</b></td><td>Redo</td></tr>
        <tr><td><b>F2</b></td><td>Rename Study</td></tr>
        <tr><td><b>Ctrl+W</b></td><td>Close Study</td></tr>
        </table>
        
        <h3>View Menu</h3>
        <table>
        <tr><td><b>Ctrl+K</b></td><td>Constants & Functions</td></tr>
        <tr><td><b>Ctrl+Tab</b></td><td>Next Tab</td></tr>
        <tr><td><b>Ctrl+Shift+Tab</b></td><td>Previous Tab</td></tr>
        </table>
        
        <h3>Tools Menu</h3>
        <table>
        <tr><td><b>Ctrl+,</b></td><td>Preferences</td></tr>
        </table>
        
        <h3>Help Menu</h3>
        <table>
        <tr><td><b>F1</b></td><td>Show This Help</td></tr>
        </table>
        
        <h3>DataTable View</h3>
        <table>
        <tr><td><b>Ctrl+R</b></td><td>Add Row</td></tr>
        <tr><td><b>Ctrl+D</b></td><td>Delete Row(s)</td></tr>
        <tr><td><b>Ctrl+Shift+D</b></td><td>Add Data Column</td></tr>
        <tr><td><b>Ctrl+Shift+C</b></td><td>Add Calculated Column</td></tr>
        <tr><td><b>Ctrl+Shift+F</b></td><td>Fill Column/Cells</td></tr>
        <tr><td><b>Ctrl+F</b></td><td>Search/Filter</td></tr>
        <tr><td><b>Double-click header</b></td><td>Rename Column</td></tr>
        </table>
        
        <h3>Plot View</h3>
        <table>
        <tr><td><b>Ctrl+A</b></td><td>Add Series</td></tr>
        <tr><td><b>Ctrl+R</b></td><td>Remove Series</td></tr>
        <tr><td><b>F5</b></td><td>Refresh Plot</td></tr>
        </table>
        
        <h3>Constants & Functions View</h3>
        <table>
        <tr><td><b>Ctrl+N</b></td><td>Add New</td></tr>
        <tr><td><b>Ctrl+E</b></td><td>Edit Selected</td></tr>
        <tr><td><b>Delete</b></td><td>Remove Selected</td></tr>
        <tr><td><b>Ctrl+F</b></td><td>Search/Filter</td></tr>
        <tr><td><b>F5</b></td><td>Refresh</td></tr>
        </table>
        """
        QMessageBox.information(self, "Keyboard Shortcuts", shortcuts_text)
    
    def _show_preferences(self):
        """Show preferences dialog."""
        dialog = PreferencesDialog(self)
        dialog.settings_changed.connect(self._apply_preferences)
        dialog.exec()
    
    def _apply_preferences(self, settings: dict):
        """Apply preferences changes.
        
        Args:
            settings: Dictionary of settings from preferences dialog
        """
        # Update stored preferences
        self.preferences = settings
        
        # Update display precision
        if "display_precision" in settings:
            from .widgets.shared import set_display_precision, emit_full_model_update
            set_display_precision(settings["display_precision"])
            
            # Refresh all table widgets to update display
            for i in range(self.study_tabs.count()):
                widget = self.study_tabs.widget(i)
                if hasattr(widget, 'model'):
                    # Force full model update to refresh displayed values
                    emit_full_model_update(widget.model)
        
        # Note: max_undo_steps only applies to new studies
        
        self.statusBar().showMessage("Preferences updated", 3000)
    
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
            "<p><i>160/160 unit tests passing!</i></p>"
        )
    
    def _on_tab_changed(self, index: int):
        """Handle tab change to update undo/redo state.
        
        Args:
            index: New tab index
        """
        if index < 0:
            self.undo_action.setEnabled(False)
            self.redo_action.setEnabled(False)
            return
        
        widget = self.study_tabs.widget(index)
        
        # Check if widget has a study with undo manager
        if hasattr(widget, 'study') and hasattr(widget.study, 'undo_manager'):
            undo_mgr = widget.study.undo_manager
            
            # Update undo/redo buttons
            self.undo_action.setEnabled(undo_mgr.can_undo())
            self.redo_action.setEnabled(undo_mgr.can_redo())
            
            # Update tooltips with descriptions
            if undo_mgr.can_undo():
                self.undo_action.setToolTip(f"Undo: {undo_mgr.get_undo_description()}")
            else:
                self.undo_action.setToolTip("Undo")
            
            if undo_mgr.can_redo():
                self.redo_action.setToolTip(f"Redo: {undo_mgr.get_redo_description()}")
            else:
                self.redo_action.setToolTip("Redo")
        else:
            self.undo_action.setEnabled(False)
            self.redo_action.setEnabled(False)
    
    def _undo(self):
        """Undo last action in current study."""
        widget = self.study_tabs.currentWidget()
        
        if hasattr(widget, 'study') and hasattr(widget.study, 'undo_manager'):
            undo_mgr = widget.study.undo_manager
            
            if undo_mgr.can_undo():
                description = undo_mgr.get_undo_description()
                try:
                    undo_mgr.undo()
                    self.notifications.show_info(f"Undone: {description}")
                    
                    # Update model display (no full recalculation needed)
                    if hasattr(widget, 'model'):
                        widget.model.layoutChanged.emit()
                    
                    # Update undo/redo state
                    self._on_tab_changed(self.study_tabs.currentIndex())
                except Exception as e:
                    self.notifications.show_error(f"Undo failed: {e}")
    
    def _redo(self):
        """Redo last undone action in current study."""
        widget = self.study_tabs.currentWidget()
        
        if hasattr(widget, 'study') and hasattr(widget.study, 'undo_manager'):
            undo_mgr = widget.study.undo_manager
            
            if undo_mgr.can_redo():
                description = undo_mgr.get_redo_description()
                try:
                    undo_mgr.redo()
                    self.notifications.show_info(f"Redone: {description}")
                    
                    # Update model display (no full recalculation needed)
                    if hasattr(widget, 'model'):
                        widget.model.layoutChanged.emit()
                    
                    # Update undo/redo state
                    self._on_tab_changed(self.study_tabs.currentIndex())
                except Exception as e:
                    self.notifications.show_error(f"Redo failed: {e}")
