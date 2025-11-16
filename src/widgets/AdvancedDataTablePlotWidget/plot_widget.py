"""
Main plotting widget for AdvancedDataTableWidget.

This widget provides:
- Matplotlib canvas for plotting
- Column selection UI for X and Y axes
- Integration with AdvancedDataTableWidget data
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

from widgets.AdvancedDataTableWidget.advanced_datatable import AdvancedDataTableWidget
from widgets.AdvancedDataTableWidget.models import AdvancedColumnType


class AdvancedDataTablePlotWidget(QWidget):
    """Widget for plotting data from AdvancedDataTableWidget.
    
    Features:
    - X and Y column selection from dropdown menus
    - Matplotlib canvas with navigation toolbar
    - Automatic plot updates
    - Unit-aware axis labels
    """
    
    def __init__(self, datatable: Optional[AdvancedDataTableWidget] = None, parent=None):
        """Initialize the plot widget.
        
        Args:
            datatable: Reference to the AdvancedDataTableWidget to plot from
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
    
    def set_datatable(self, datatable: AdvancedDataTableWidget):
        """Set or update the datatable reference.
        
        Args:
            datatable: The AdvancedDataTableWidget to plot from
        """
        self._datatable = datatable
        self._populate_column_selectors()
        
        # Connect to datatable signals for updates
        if self._datatable:
            self._datatable.columnAdded.connect(self._on_datatable_changed)
            self._datatable.columnRemoved.connect(self._on_datatable_changed)
            self._datatable.itemChanged.connect(self._on_data_changed)
    
    def _populate_column_selectors(self):
        """Populate the X and Y column dropdown menus with available columns."""
        if not self._datatable:
            return
        
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
        column_count = self._datatable.columnCount()
        for col_idx in range(column_count):
            metadata = self._datatable._columns[col_idx]
            
            # Only include numerical columns (not uncertainty columns typically)
            if metadata.data_type.value == "numerical":
                # Create display text with diminutive and unit
                display_text = metadata.diminutive
                if metadata.unit:
                    display_text += f" [{metadata.unit}]"
                
                # Store the column index as user data
                self.x_column_combo.addItem(display_text, col_idx)
                self.y_column_combo.addItem(display_text, col_idx)
        
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
    
    def _get_column_data(self, col_idx: int) -> Optional[np.ndarray]:
        """Extract numerical data from a column.
        
        Skips empty cells, error values, and invalid data.
        This ensures derivative columns (which have n-1 values) plot correctly.
        
        Args:
            col_idx: Index of the column to extract
            
        Returns:
            Numpy array of numerical values, or None if extraction fails
        """
        if not self._datatable:
            return None
        
        row_count = self._datatable.rowCount()
        if row_count == 0:
            return None
        
        data = []
        for row in range(row_count):
            item = self._datatable.item(row, col_idx)
            if item:
                text = item.text().strip()
                # Skip empty cells, error values
                if not text or text.startswith("ERROR"):
                    continue
                try:
                    value = float(text)
                    data.append(value)
                except (ValueError, TypeError):
                    continue
        
        return np.array(data) if data else None
    
    def _find_uncertainty_column(self, data_col_idx: int) -> Optional[int]:
        """Find the uncertainty column associated with a data column.
        
        Args:
            data_col_idx: Index of the data column
            
        Returns:
            Index of the uncertainty column, or None if not found
        """
        if not self._datatable:
            return None
        
        # Look for an uncertainty column that references this data column
        for col_idx, metadata in enumerate(self._datatable._columns):
            if (metadata.column_type == AdvancedColumnType.UNCERTAINTY and
                metadata.uncertainty_reference == data_col_idx):
                return col_idx
        
        return None
    
    @Slot()
    def _on_plot_clicked(self):
        """Handle plot button click."""
        if not self._datatable:
            QMessageBox.warning(self, "No Data", "No datatable connected.")
            return
        
        # Get selected column indices
        x_idx = self.x_column_combo.currentData()
        y_idx = self.y_column_combo.currentData()
        
        if x_idx is None or y_idx is None:
            QMessageBox.warning(self, "Invalid Selection", "Please select both X and Y columns.")
            return
        
        # Check if uncertainty plotting is requested
        show_uncertainty = self.uncertainty_checkbox.isChecked()
        
        # Find uncertainty columns if requested
        x_unc_idx = None
        y_unc_idx = None
        if show_uncertainty:
            x_unc_idx = self._find_uncertainty_column(x_idx)
            y_unc_idx = self._find_uncertainty_column(y_idx)
        
        # Extract data row-by-row to maintain pairing
        # This handles derivative columns (with n-1 values) correctly
        x_data = []
        y_data = []
        x_unc_data = []
        y_unc_data = []
        
        row_count = self._datatable.rowCount()
        for row in range(row_count):
            x_item = self._datatable.item(row, x_idx)
            y_item = self._datatable.item(row, y_idx)
            
            # Both cells must exist and have valid values
            if x_item and y_item:
                x_text = x_item.text().strip()
                y_text = y_item.text().strip()
                
                # Skip empty or error cells
                if not x_text or not y_text or x_text.startswith("ERROR") or y_text.startswith("ERROR"):
                    continue
                
                try:
                    x_val = float(x_text)
                    y_val = float(y_text)
                    
                    # Extract uncertainty values if available
                    x_unc = 0.0
                    y_unc = 0.0
                    
                    if show_uncertainty:
                        if x_unc_idx is not None:
                            x_unc_item = self._datatable.item(row, x_unc_idx)
                            if x_unc_item:
                                x_unc_text = x_unc_item.text().strip()
                                if x_unc_text and not x_unc_text.startswith("ERROR"):
                                    try:
                                        x_unc = float(x_unc_text)
                                    except (ValueError, TypeError):
                                        x_unc = 0.0
                        
                        if y_unc_idx is not None:
                            y_unc_item = self._datatable.item(row, y_unc_idx)
                            if y_unc_item:
                                y_unc_text = y_unc_item.text().strip()
                                if y_unc_text and not y_unc_text.startswith("ERROR"):
                                    try:
                                        y_unc = float(y_unc_text)
                                    except (ValueError, TypeError):
                                        y_unc = 0.0
                    
                    x_data.append(x_val)
                    y_data.append(y_val)
                    x_unc_data.append(x_unc)
                    y_unc_data.append(y_unc)
                    
                except (ValueError, TypeError):
                    continue
        
        if not x_data or not y_data:
            QMessageBox.warning(self, "No Data", "Selected columns contain no valid numerical data pairs.")
            return
        
        # Convert to numpy arrays
        x_data = np.array(x_data)
        y_data = np.array(y_data)
        x_unc_data = np.array(x_unc_data) if show_uncertainty else None
        y_unc_data = np.array(y_unc_data) if show_uncertainty else None
        
        # Get column metadata for labels
        x_metadata = self._datatable._columns[x_idx]
        y_metadata = self._datatable._columns[y_idx]
        
        # Create axis labels
        x_label = x_metadata.diminutive
        if x_metadata.unit:
            x_label += f" [{x_metadata.unit}]"
        
        y_label = y_metadata.diminutive
        if y_metadata.unit:
            y_label += f" [{y_metadata.unit}]"
        
        # Clear and plot
        self.ax.clear()
        
        # Plot with or without error bars
        if show_uncertainty and (x_unc_idx is not None or y_unc_idx is not None):
            # Prepare error bar arrays (None if no uncertainty column found)
            xerr = x_unc_data if x_unc_idx is not None else None
            yerr = y_unc_data if y_unc_idx is not None else None
            
            # Plot with error bars
            self.ax.errorbar(x_data, y_data, xerr=xerr, yerr=yerr,
                           fmt='o-', linewidth=2, markersize=6, 
                           capsize=5, capthick=1.5, elinewidth=1.5,
                           label='Data with uncertainty')
            self.ax.legend()
        else:
            # Plot without error bars
            self.ax.plot(x_data, y_data, 'o-', linewidth=2, markersize=6)
        
        self.ax.set_xlabel(x_label, fontsize=12)
        self.ax.set_ylabel(y_label, fontsize=12)
        self.ax.set_title(f"{y_metadata.diminutive} vs {x_metadata.diminutive}", fontsize=14)
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
