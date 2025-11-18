"""
Main plotting widget for DataTable.

This widget provides:
- Matplotlib canvas for plotting
- Column selection UI for X and Y axes
- Integration with DataTableWidget data
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QComboBox, QLabel, QGroupBox, QMessageBox, QCheckBox
)
from PySide6.QtCore import Qt, Slot
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import numpy as np
from typing import Optional, List

from widgets import DataTableWidget, ColumnType, DataType


class AdvancedDataTablePlotWidget(QWidget):
    """Widget for plotting data from DataTableWidget.
    
    Features:
    - X and Y column selection from dropdown menus
    - Matplotlib canvas with navigation toolbar
    - Automatic plot updates
    - Unit-aware axis labels
    """
    
    def __init__(self, datatable: Optional[DataTableWidget] = None, parent=None):
        """Initialize the plot widget.
        
        Args:
            datatable: Reference to the DataTableWidget to plot from
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._datatable = datatable
        self._setup_ui()
        self._connect_signals()
        
        # Populate column selectors if datatable is provided
        if self._datatable:
            self.set_datatable(self._datatable)
    
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create column selection controls
        controls_group = QGroupBox("Plot Configuration")
        controls_layout = QHBoxLayout()
        controls_group.setLayout(controls_layout)
        
        # X-axis column selector
        x_layout = QVBoxLayout()
        x_label = QLabel("X-axis:")
        self.x_column_combo = QComboBox()
        self.x_column_combo.setMinimumWidth(150)
        x_layout.addWidget(x_label)
        x_layout.addWidget(self.x_column_combo)
        controls_layout.addLayout(x_layout)
        
        # Y-axis column selector
        y_layout = QVBoxLayout()
        y_label = QLabel("Y-axis:")
        self.y_column_combo = QComboBox()
        self.y_column_combo.setMinimumWidth(150)
        y_layout.addWidget(y_label)
        y_layout.addWidget(self.y_column_combo)
        controls_layout.addLayout(y_layout)
        
        # Uncertainty checkbox
        self.uncertainty_checkbox = QCheckBox("Show Uncertainty")
        self.uncertainty_checkbox.setToolTip("Display error bars if uncertainty columns are available")
        controls_layout.addWidget(self.uncertainty_checkbox)
        
        # Plot button
        self.plot_button = QPushButton("Plot")
        self.plot_button.setMaximumWidth(100)
        controls_layout.addWidget(self.plot_button)
        
        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.setMaximumWidth(100)
        controls_layout.addWidget(self.clear_button)
        
        controls_layout.addStretch()
        
        layout.addWidget(controls_group)
        
        # Create matplotlib figure and canvas
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        # Add navigation toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
        # Initial plot setup
        self.ax.set_xlabel("X-axis")
        self.ax.set_ylabel("Y-axis")
        self.ax.set_title("Select columns to plot")
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()
    
    def _connect_signals(self):
        """Connect widget signals."""
        self.plot_button.clicked.connect(self._on_plot_clicked)
        self.clear_button.clicked.connect(self._on_clear_clicked)
        
        # Auto-update when column selection changes
        self.x_column_combo.currentIndexChanged.connect(self._on_column_selection_changed)
        self.y_column_combo.currentIndexChanged.connect(self._on_column_selection_changed)
    
    def set_datatable(self, datatable: DataTableWidget):
        """Set or update the datatable reference.
        
        Args:
            datatable: The DataTableWidget to plot from
        """
        self._datatable = datatable
        self._populate_column_selectors()
        
        # Connect to model signals for updates
        if self._datatable:
            model = self._datatable.model()
            model.columnAdded.connect(self._on_datatable_changed)
            model.columnRemoved.connect(self._on_datatable_changed)
            model.dataChanged.connect(self._on_data_changed)
    
    def _populate_column_selectors(self):
        """Populate the X and Y column dropdown menus with available columns."""
        if not self._datatable:
            return
        
        model = self._datatable.model()
        
        # Block signals to prevent triggering updates during population
        self.x_column_combo.blockSignals(True)
        self.y_column_combo.blockSignals(True)
        
        # Store current selections
        current_x = self.x_column_combo.currentText()
        current_y = self.y_column_combo.currentText()
        
        # Clear existing items
        self.x_column_combo.clear()
        self.y_column_combo.clear()
        
        # Populate with numerical columns
        for col_name in model.get_column_names():
            try:
                metadata = model.get_column_metadata(col_name)
                
                # Only include numerical columns (not uncertainty columns typically)
                if metadata.dtype in (DataType.FLOAT, DataType.INTEGER):
                    # Create display text with name and unit
                    display_text = col_name
                    if metadata.unit:
                        display_text += f" [{metadata.unit}]"
                    
                    # Store the column name as user data
                    self.x_column_combo.addItem(display_text, col_name)
                    self.y_column_combo.addItem(display_text, col_name)
            except Exception:
                continue
        
        # Restore previous selections if possible
        x_index = self.x_column_combo.findText(current_x)
        if x_index >= 0:
            self.x_column_combo.setCurrentIndex(x_index)
        elif self.x_column_combo.count() > 0:
            self.x_column_combo.setCurrentIndex(0)
        
        y_index = self.y_column_combo.findText(current_y)
        if y_index >= 0:
            self.y_column_combo.setCurrentIndex(y_index)
        elif self.y_column_combo.count() > 1:
            self.y_column_combo.setCurrentIndex(1)  # Default to second column for Y
        
        # Re-enable signals
        self.x_column_combo.blockSignals(False)
        self.y_column_combo.blockSignals(False)
    
    def _get_column_data(self, col_name: str) -> Optional[np.ndarray]:
        """Extract numerical data from a column.
        
        Args:
            col_name: Name of the column to extract
            
        Returns:
            Numpy array of numerical values, or None if extraction fails
        """
        if not self._datatable:
            return None
        
        model = self._datatable.model()
        
        try:
            # Get column data as pandas Series
            series = model.get_column_data(col_name)
            
            # Drop NaN values and convert to numpy array
            data = series.dropna().to_numpy()
            
            return data if len(data) > 0 else None
            
        except Exception:
            return None
    
    def _find_uncertainty_column(self, data_col_name: str) -> Optional[str]:
        """Find the uncertainty column associated with a data column.
        
        Args:
            data_col_name: Name of the data column
            
        Returns:
            Name of the uncertainty column, or None if not found
        """
        if not self._datatable:
            return None
        
        model = self._datatable.model()
        
        # Look for an uncertainty column that references this data column
        for col_name in model.get_column_names():
            try:
                metadata = model.get_column_metadata(col_name)
                if (metadata.column_type == ColumnType.UNCERTAINTY and
                    metadata.uncertainty_reference == data_col_name):
                    return col_name
            except Exception:
                continue
        
        return None
    
    @Slot()
    def _on_plot_clicked(self):
        """Handle plot button click."""
        if not self._datatable:
            QMessageBox.warning(self, "No Data", "No datatable connected.")
            return
        
        model = self._datatable.model()
        
        # Get selected column names
        x_name = self.x_column_combo.currentData()
        y_name = self.y_column_combo.currentData()
        
        if x_name is None or y_name is None:
            QMessageBox.warning(self, "Invalid Selection", "Please select both X and Y columns.")
            return
        
        # Get column data
        x_data = self._get_column_data(x_name)
        y_data = self._get_column_data(y_name)
        
        if x_data is None or y_data is None:
            QMessageBox.warning(self, "No Data", "Selected columns contain no valid numerical data.")
            return
        
        # Ensure both arrays have the same length (handle derivatives which may have n-1 values)
        min_len = min(len(x_data), len(y_data))
        x_data = x_data[:min_len]
        y_data = y_data[:min_len]
        
        # Check if uncertainty plotting is requested
        show_uncertainty = self.uncertainty_checkbox.isChecked()
        
        x_unc_data = None
        y_unc_data = None
        
        if show_uncertainty:
            # Find uncertainty columns
            x_unc_name = self._find_uncertainty_column(x_name)
            y_unc_name = self._find_uncertainty_column(y_name)
            
            if x_unc_name:
                x_unc_data = self._get_column_data(x_unc_name)
                if x_unc_data is not None:
                    x_unc_data = x_unc_data[:min_len]
            
            if y_unc_name:
                y_unc_data = self._get_column_data(y_unc_name)
                if y_unc_data is not None:
                    y_unc_data = y_unc_data[:min_len]
        
        # Get column metadata for labels
        try:
            x_metadata = model.get_column_metadata(x_name)
            y_metadata = model.get_column_metadata(y_name)
        except Exception:
            QMessageBox.warning(self, "Error", "Failed to retrieve column metadata.")
            return
        
        # Create axis labels
        x_label = x_name
        if x_metadata.unit:
            x_label += f" [{x_metadata.unit}]"
        
        y_label = y_name
        if y_metadata.unit:
            y_label += f" [{y_metadata.unit}]"
        
        # Clear and plot
        self.ax.clear()
        
        # Plot with or without error bars
        if show_uncertainty and (x_unc_data is not None or y_unc_data is not None):
            # Plot with error bars
            self.ax.errorbar(x_data, y_data, xerr=x_unc_data, yerr=y_unc_data,
                           fmt='o-', linewidth=2, markersize=6, 
                           capsize=5, capthick=1.5, elinewidth=1.5,
                           label='Data with uncertainty')
            self.ax.legend()
        else:
            # Plot without error bars
            self.ax.plot(x_data, y_data, 'o-', linewidth=2, markersize=6)
        
        self.ax.set_xlabel(x_label, fontsize=12)
        self.ax.set_ylabel(y_label, fontsize=12)
        self.ax.set_title(f"{y_name} vs {x_name}", fontsize=14)
        self.ax.grid(True, alpha=0.3)
        
        # Tight layout for better spacing
        self.figure.tight_layout()
        self.canvas.draw()
    
    @Slot()
    def _on_clear_clicked(self):
        """Handle clear button click."""
        self.ax.clear()
        self.ax.set_xlabel("X-axis")
        self.ax.set_ylabel("Y-axis")
        self.ax.set_title("Select columns to plot")
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()
    
    @Slot()
    def _on_column_selection_changed(self):
        """Handle column selection change - could auto-update plot."""
        # For now, we require explicit "Plot" button click
        # Future: add auto-plot option
        pass
    
    @Slot()
    def _on_datatable_changed(self):
        """Handle datatable structure changes (columns added/removed)."""
        self._populate_column_selectors()
    
    @Slot()
    def _on_data_changed(self):
        """Handle datatable data changes."""
        # Future: add option for auto-refresh on data change
        pass
