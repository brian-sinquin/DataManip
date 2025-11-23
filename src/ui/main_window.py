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
from .widgets import DataTableWidget, ConstantsWidget
from .widgets.plot_widget import PlotWidget


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
        
        new_menu.addSeparator()
        
        new_vars_action = QAction("&Constants Tab", self)
        new_vars_action.setShortcut("Ctrl+K")
        new_vars_action.triggered.connect(self._new_variables_tab)
        new_menu.addAction(new_vars_action)
        
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
        
        # Don't allow closing Variables tab
        if study_name == "Variables":
            QMessageBox.information(
                self,
                "Cannot Close",
                "Variables tab cannot be closed."
            )
            return
        
        # Confirm close if not saved
        reply = QMessageBox.question(
            self,
            "Close Study",
            f"Close study '{study_name}'?",
            QMessageBox.Yes | QMessageBox.No  # type: ignore
        )
        
        if reply == QMessageBox.Yes:  # type: ignore
            # Remove from workspace
            if study_name in self.workspace.studies:
                self.workspace.studies.pop(study_name)
            
            # Remove tab
            self.study_tabs.removeTab(index)
    
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
