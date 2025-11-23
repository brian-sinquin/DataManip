"""
Widget for displaying PlotStudy visualizations.

Integrates matplotlib canvas with PySide6 for interactive plotting.
"""

from __future__ import annotations
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QDialog,
    QComboBox, QLabel, QFormLayout, QLineEdit, QDialogButtonBox,
    QListWidget, QListWidgetItem, QCheckBox
)
from PySide6.QtCore import Qt

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from matplotlib.figure import Figure

from studies.plot_study import PlotStudy


class PlotWidget(QWidget):
    """Widget displaying matplotlib plot for PlotStudy.
    
    Features:
    - Matplotlib canvas with toolbar
    - Add/remove series dialog
    - Auto-refresh on data changes
    """
    
    def __init__(self, study: PlotStudy, workspace):
        """Initialize PlotWidget.
        
        Args:
            study: PlotStudy to visualize
            workspace: Workspace reference for data access
        """
        super().__init__()
        self.study = study
        self.workspace = workspace
        
        self._init_ui()
        self._refresh_plot()
    
    def _init_ui(self):
        """Setup UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Matplotlib canvas
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvasQTAgg(self.figure)
        
        # Matplotlib toolbar
        self.mpl_toolbar = NavigationToolbar2QT(self.canvas, self)
        
        # Custom toolbar for series management
        from PySide6.QtWidgets import QToolBar
        from PySide6.QtGui import QAction
        
        self.toolbar = QToolBar()
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)  # type: ignore
        
        add_action = QAction("Add Series", self)
        add_action.setShortcut("Ctrl+A")
        add_action.setToolTip("Add new data series to plot (Ctrl+A)")
        add_action.triggered.connect(self._add_series_dialog)
        self.toolbar.addAction(add_action)
        
        remove_action = QAction("Remove Series", self)
        remove_action.setShortcut("Ctrl+R")
        remove_action.setToolTip("Remove series from plot (Ctrl+R)")
        remove_action.triggered.connect(self._remove_series_dialog)
        self.toolbar.addAction(remove_action)
        
        self.toolbar.addSeparator()
        
        refresh_action = QAction("Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.setToolTip("Refresh plot (F5)")
        refresh_action.triggered.connect(self._refresh_plot)
        self.toolbar.addAction(refresh_action)
        
        clear_action = QAction("Clear All", self)
        clear_action.setToolTip("Remove all series from plot")
        clear_action.triggered.connect(self._clear_all_series)
        self.toolbar.addAction(clear_action)
        
        # Layout
        layout.addWidget(self.toolbar)
        layout.addWidget(self.mpl_toolbar)
        layout.addWidget(self.canvas)
    
    def _refresh_plot(self):
        """Redraw plot with current data."""
        self.study.update_plot(self.figure)
        self.canvas.draw()
    
    def _add_series_dialog(self):
        """Show dialog to add new series."""
        dialog = AddSeriesDialog(self.workspace, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            values = dialog.get_values()
            self.study.add_series(**values)
            self._refresh_plot()
    
    def _clear_all_series(self):
        """Clear all series from plot."""
        if not self.study.series:
            return
        
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Clear All Series",
            f"Remove all {len(self.study.series)} series from plot?",
            QMessageBox.Yes | QMessageBox.No  # type: ignore
        )
        
        if reply == QMessageBox.Yes:  # type: ignore
            self.study.clear_series()
            self._refresh_plot()
    
    def _remove_series_dialog(self):
        """Show dialog to remove existing series."""
        if not self.study.series:
            return
        
        dialog = RemoveSeriesDialog(self.study, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            index = dialog.get_selected_index()
            if index is not None:
                self.study.remove_series(index)
                self._refresh_plot()


class AddSeriesDialog(QDialog):
    """Dialog for adding plot series."""
    
    def __init__(self, workspace, parent=None):
        """Initialize dialog.
        
        Args:
            workspace: Workspace reference
            parent: Parent widget
        """
        super().__init__(parent)
        self.workspace = workspace
        
        self.setWindowTitle("Add Series")
        self.setModal(True)
        
        self._init_ui()
    
    def _init_ui(self):
        """Setup UI."""
        layout = QFormLayout(self)
        
        # Study selector
        self.study_combo = QComboBox()
        from studies.data_table_study import DataTableStudy
        for study in self.workspace.studies.values():
            if isinstance(study, DataTableStudy):
                self.study_combo.addItem(study.name)
        self.study_combo.currentTextChanged.connect(self._on_study_changed)
        
        # Column selectors
        self.x_combo = QComboBox()
        self.y_combo = QComboBox()
        
        # Label
        self.label_edit = QLineEdit()
        
        # Style
        self.style_combo = QComboBox()
        self.style_combo.addItems(["line", "scatter", "both"])
        
        # Color
        self.color_edit = QLineEdit()
        self.color_edit.setPlaceholderText("e.g., blue, #FF0000 (optional)")
        
        # Marker
        self.marker_combo = QComboBox()
        self.marker_combo.addItems(["o", "s", "^", "v", "D", "*", "+", "x"])
        
        # Linestyle
        self.linestyle_combo = QComboBox()
        self.linestyle_combo.addItems(["-", "--", "-.", ":"])
        
        # Layout
        layout.addRow("Study:", self.study_combo)
        layout.addRow("X Column:", self.x_combo)
        layout.addRow("Y Column:", self.y_combo)
        layout.addRow("Label:", self.label_edit)
        layout.addRow("Style:", self.style_combo)
        layout.addRow("Color:", self.color_edit)
        layout.addRow("Marker:", self.marker_combo)
        layout.addRow("Line Style:", self.linestyle_combo)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        # Initialize columns
        if self.study_combo.count() > 0:
            self._on_study_changed(self.study_combo.currentText())
    
    def _on_study_changed(self, study_name: str):
        """Update column lists when study selection changes."""
        self.x_combo.clear()
        self.y_combo.clear()
        
        study = self.workspace.get_study(study_name)
        if study:
            from studies.data_table_study import DataTableStudy
            if isinstance(study, DataTableStudy):
                columns = study.table.columns
                self.x_combo.addItems(columns)
                self.y_combo.addItems(columns)
    
    def get_values(self) -> dict:
        """Get dialog values.
        
        Returns:
            Dictionary with series configuration
        """
        color = self.color_edit.text().strip() or None
        return {
            "study_name": self.study_combo.currentText(),
            "x_column": self.x_combo.currentText(),
            "y_column": self.y_combo.currentText(),
            "label": self.label_edit.text() or None,
            "style": self.style_combo.currentText(),
            "color": color,
            "marker": self.marker_combo.currentText(),
            "linestyle": self.linestyle_combo.currentText()
        }


class RemoveSeriesDialog(QDialog):
    """Dialog for removing plot series."""
    
    def __init__(self, study: PlotStudy, parent=None):
        """Initialize dialog.
        
        Args:
            study: PlotStudy with series
            parent: Parent widget
        """
        super().__init__(parent)
        self.study = study
        
        self.setWindowTitle("Remove Series")
        self.setModal(True)
        
        self._init_ui()
    
    def _init_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        
        # Series list
        self.list_widget = QListWidget()
        for series in self.study.series:
            label = series.get("label", "Unnamed")
            self.list_widget.addItem(label)
        
        # Select first item by default
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
        
        layout.addWidget(QLabel("Select series to remove:"))
        layout.addWidget(self.list_widget)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_selected_index(self) -> Optional[int]:
        """Get selected series index."""
        item = self.list_widget.currentItem()
        if item:
            return self.list_widget.row(item)
        return None
