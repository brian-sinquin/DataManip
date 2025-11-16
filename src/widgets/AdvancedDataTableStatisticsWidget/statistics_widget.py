"""
AdvancedDataTableStatisticsWidget - Statistical analysis widget for data table columns.

This widget provides:
- Descriptive statistics (mean, median, std dev, min, max, quartiles)
- Histogram visualization
- Box plot visualization
- Column selection interface
"""

from typing import Optional, List
import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel,
    QGroupBox, QGridLayout, QPushButton, QTextEdit, QSplitter
)
from PySide6.QtCore import Qt, Slot

# Matplotlib imports
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class AdvancedDataTableStatisticsWidget(QWidget):
    """Widget for statistical analysis of datatable columns.
    
    Features:
    - Column selector dropdown
    - Descriptive statistics display
    - Histogram visualization
    - Box plot visualization
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the statistics widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._datatable = None  # Reference to the AdvancedDataTableWidget
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        main_layout = QVBoxLayout(self)
        
        # Column selection section
        selection_layout = QHBoxLayout()
        selection_layout.addWidget(QLabel("Analyze Column:"))
        
        self.column_combo = QComboBox()
        self.column_combo.setMinimumWidth(200)
        self.column_combo.currentIndexChanged.connect(self._on_column_changed)
        selection_layout.addWidget(self.column_combo)
        
        selection_layout.addStretch()
        
        self.analyze_button = QPushButton("Analyze")
        self.analyze_button.clicked.connect(self._on_analyze_clicked)
        selection_layout.addWidget(self.analyze_button)
        
        main_layout.addLayout(selection_layout)
        
        # Create splitter for statistics and plots
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: Statistics display
        stats_group = QGroupBox("Descriptive Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_display = QTextEdit()
        self.stats_display.setReadOnly(True)
        self.stats_display.setMaximumWidth(350)
        stats_layout.addWidget(self.stats_display)
        
        splitter.addWidget(stats_group)
        
        # Right side: Visualizations
        viz_widget = QWidget()
        viz_layout = QVBoxLayout(viz_widget)
        viz_layout.setContentsMargins(0, 0, 0, 0)
        
        # Matplotlib figure for plots
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        viz_layout.addWidget(self.toolbar)
        viz_layout.addWidget(self.canvas)
        
        splitter.addWidget(viz_widget)
        
        # Set initial splitter sizes (30% stats, 70% plots)
        splitter.setSizes([300, 700])
        
        main_layout.addWidget(splitter)
        
        # Initial message
        self._show_initial_message()
    
    def set_datatable(self, datatable):
        """Set the datatable to analyze.
        
        Args:
            datatable: Instance of AdvancedDataTableWidget
        """
        self._datatable = datatable
        self._populate_column_selector()
        
        # Connect to datatable signals for updates
        if self._datatable:
            self._datatable.columnAdded.connect(self._on_datatable_changed)
            self._datatable.columnRemoved.connect(self._on_datatable_changed)
            self._datatable.itemChanged.connect(self._on_data_changed)
    
    def _populate_column_selector(self):
        """Populate the column dropdown with numerical columns."""
        if not self._datatable:
            return
        
        # Block signals during population
        self.column_combo.blockSignals(True)
        
        # Store current selection
        current_text = self.column_combo.currentText()
        
        # Clear existing items
        self.column_combo.clear()
        
        # Populate with numerical columns
        column_count = self._datatable.columnCount()
        for col_idx in range(column_count):
            metadata = self._datatable._columns[col_idx]
            
            # Only include numerical columns (exclude uncertainty columns typically)
            if metadata.data_type.value == "numerical":
                # Create display text with diminutive and unit
                display_text = metadata.diminutive
                if metadata.unit:
                    display_text += f" [{metadata.unit}]"
                
                # Add type indicator
                type_symbol = self._datatable._get_column_type_symbol(metadata.column_type)
                display_text = f"{type_symbol}{display_text}"
                
                # Store the column index as user data
                self.column_combo.addItem(display_text, col_idx)
        
        # Restore previous selection if possible
        index = self.column_combo.findText(current_text)
        if index >= 0:
            self.column_combo.setCurrentIndex(index)
        elif self.column_combo.count() > 0:
            self.column_combo.setCurrentIndex(0)
        
        # Re-enable signals
        self.column_combo.blockSignals(False)
    
    def _get_column_data(self, col_idx: int) -> Optional[np.ndarray]:
        """Extract numerical data from a column.
        
        Skips empty cells and error values.
        
        Args:
            col_idx: Index of the column to extract
            
        Returns:
            Numpy array of numerical values, or None if no valid data
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
                # Skip empty cells and error values
                if not text or text.startswith("ERROR"):
                    continue
                try:
                    value = float(text)
                    # Skip inf and nan
                    if not (np.isinf(value) or np.isnan(value)):
                        data.append(value)
                except (ValueError, TypeError):
                    continue
        
        return np.array(data) if data else None
    
    def _calculate_statistics(self, data: np.ndarray) -> dict:
        """Calculate descriptive statistics for the data.
        
        Args:
            data: Numpy array of numerical values
            
        Returns:
            Dictionary of statistical measures
        """
        if data is None or len(data) == 0:
            return {}
        
        stats = {
            'count': len(data),
            'mean': np.mean(data),
            'median': np.median(data),
            'std': np.std(data, ddof=1) if len(data) > 1 else 0.0,
            'variance': np.var(data, ddof=1) if len(data) > 1 else 0.0,
            'min': np.min(data),
            'max': np.max(data),
            'range': np.max(data) - np.min(data),
            'q25': np.percentile(data, 25),
            'q50': np.percentile(data, 50),
            'q75': np.percentile(data, 75),
            'iqr': np.percentile(data, 75) - np.percentile(data, 25),
            'skewness': self._calculate_skewness(data),
            'kurtosis': self._calculate_kurtosis(data),
        }
        
        return stats
    
    def _calculate_skewness(self, data: np.ndarray) -> float:
        """Calculate skewness (measure of asymmetry).
        
        Args:
            data: Numpy array of values
            
        Returns:
            Skewness value
        """
        if len(data) < 3:
            return 0.0
        
        n = len(data)
        mean = np.mean(data)
        std = np.std(data, ddof=1)
        
        if std == 0:
            return 0.0
        
        m3 = np.sum((data - mean)**3) / n
        skew = m3 / (std**3)
        
        # Apply bias correction
        skew = skew * np.sqrt(n * (n - 1)) / (n - 2)
        
        return skew
    
    def _calculate_kurtosis(self, data: np.ndarray) -> float:
        """Calculate kurtosis (measure of tailedness).
        
        Excess kurtosis: subtract 3 so that normal distribution has kurtosis of 0.
        
        Args:
            data: Numpy array of values
            
        Returns:
            Excess kurtosis value
        """
        if len(data) < 4:
            return 0.0
        
        n = len(data)
        mean = np.mean(data)
        std = np.std(data, ddof=1)
        
        if std == 0:
            return 0.0
        
        m4 = np.sum((data - mean)**4) / n
        kurt = m4 / (std**4)
        
        # Excess kurtosis (subtract 3 for normal distribution = 0)
        excess_kurt = kurt - 3.0
        
        # Apply bias correction
        excess_kurt = ((n - 1) * ((n + 1) * excess_kurt + 6)) / ((n - 2) * (n - 3))
        
        return excess_kurt
    
    def _format_statistics_text(self, stats: dict, column_name: str, unit: str = "") -> str:
        """Format statistics as readable text.
        
        Args:
            stats: Dictionary of statistical measures
            column_name: Name of the analyzed column
            unit: Unit of measurement
            
        Returns:
            Formatted string for display
        """
        if not stats:
            return "No valid data to analyze."
        
        unit_str = f" {unit}" if unit else ""
        
        text = f"<h3>Statistics for: {column_name}</h3>\n"
        text += "<hr>\n"
        text += f"<b>Sample Size</b><br>\n"
        text += f"Count: {stats['count']}<br>\n"
        text += "<br>\n"
        
        text += f"<b>Central Tendency</b><br>\n"
        text += f"Mean: {stats['mean']:.6g}{unit_str}<br>\n"
        text += f"Median: {stats['median']:.6g}{unit_str}<br>\n"
        text += "<br>\n"
        
        text += f"<b>Dispersion</b><br>\n"
        text += f"Std Dev: {stats['std']:.6g}{unit_str}<br>\n"
        text += f"Variance: {stats['variance']:.6g}{unit_str}²<br>\n"
        text += f"Range: {stats['range']:.6g}{unit_str}<br>\n"
        text += f"IQR: {stats['iqr']:.6g}{unit_str}<br>\n"
        text += "<br>\n"
        
        text += f"<b>Extremes</b><br>\n"
        text += f"Min: {stats['min']:.6g}{unit_str}<br>\n"
        text += f"Max: {stats['max']:.6g}{unit_str}<br>\n"
        text += "<br>\n"
        
        text += f"<b>Quartiles</b><br>\n"
        text += f"Q1 (25%): {stats['q25']:.6g}{unit_str}<br>\n"
        text += f"Q2 (50%): {stats['q50']:.6g}{unit_str}<br>\n"
        text += f"Q3 (75%): {stats['q75']:.6g}{unit_str}<br>\n"
        text += "<br>\n"
        
        text += f"<b>Shape</b><br>\n"
        text += f"Skewness: {stats['skewness']:.4f}<br>\n"
        text += f"Kurtosis: {stats['kurtosis']:.4f}<br>\n"
        
        # Interpretation hints
        text += "<br><hr>\n"
        text += "<small><i>Interpretation:</i><br>\n"
        text += "Skewness: 0 = symmetric, >0 = right-skewed, <0 = left-skewed<br>\n"
        text += "Kurtosis: 0 = normal, >0 = heavy tails, <0 = light tails</small>\n"
        
        return text
    
    def _create_visualizations(self, data: np.ndarray, column_name: str, unit: str = ""):
        """Create histogram and box plot visualizations.
        
        Args:
            data: Numpy array of values
            column_name: Name of the column
            unit: Unit of measurement
        """
        if data is None or len(data) == 0:
            return
        
        # Clear previous plots
        self.figure.clear()
        
        # Create 2 subplots: histogram and box plot
        ax1 = self.figure.add_subplot(2, 1, 1)
        ax2 = self.figure.add_subplot(2, 1, 2)
        
        # Histogram
        n_bins = min(50, max(10, int(np.sqrt(len(data)))))  # Sturges' rule adjusted
        ax1.hist(data, bins=n_bins, color='steelblue', alpha=0.7, edgecolor='black')
        ax1.set_xlabel(f"{column_name} [{unit}]" if unit else column_name)
        ax1.set_ylabel("Frequency")
        ax1.set_title(f"Histogram of {column_name}")
        ax1.grid(True, alpha=0.3)
        
        # Add mean and median lines
        mean_val = np.mean(data)
        median_val = np.median(data)
        ax1.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.4g}')
        ax1.axvline(median_val, color='green', linestyle='--', linewidth=2, label=f'Median: {median_val:.4g}')
        ax1.legend()
        
        # Box plot (horizontal)
        bp = ax2.boxplot(data, vert=False, patch_artist=True, widths=0.5)
        
        # Customize box plot colors
        for patch in bp['boxes']:
            patch.set_facecolor('lightblue')
            patch.set_alpha(0.7)
        
        for whisker in bp['whiskers']:
            whisker.set(color='black', linewidth=1.5)
        
        for cap in bp['caps']:
            cap.set(color='black', linewidth=1.5)
        
        for median in bp['medians']:
            median.set(color='red', linewidth=2)
        
        ax2.set_xlabel(f"{column_name} [{unit}]" if unit else column_name)
        ax2.set_title(f"Box Plot of {column_name}")
        ax2.set_yticks([])
        ax2.grid(True, alpha=0.3, axis='x')
        
        # Tight layout
        self.figure.tight_layout()
        self.canvas.draw()
    
    def _show_initial_message(self):
        """Show initial message when no analysis has been performed."""
        self.stats_display.setHtml(
            "<h3>Statistical Analysis</h3>"
            "<p>Select a column and click <b>Analyze</b> to view statistics.</p>"
        )
        
        self.figure.clear()
        ax = self.figure.add_subplot(1, 1, 1)
        ax.text(0.5, 0.5, 'Select a column to analyze', 
                ha='center', va='center', fontsize=14, color='gray')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        self.canvas.draw()
    
    @Slot()
    def _on_analyze_clicked(self):
        """Handle analyze button click."""
        if not self._datatable:
            return
        
        # Get selected column
        col_idx = self.column_combo.currentData()
        if col_idx is None:
            self._show_initial_message()
            return
        
        # Get column metadata
        metadata = self._datatable._columns[col_idx]
        column_name = metadata.diminutive
        unit = metadata.unit or ""
        
        # Extract data
        data = self._get_column_data(col_idx)
        
        if data is None or len(data) == 0:
            self.stats_display.setHtml(
                f"<h3>Statistics for: {column_name}</h3>"
                "<p><b>Error:</b> No valid numerical data found in this column.</p>"
            )
            self.figure.clear()
            ax = self.figure.add_subplot(1, 1, 1)
            ax.text(0.5, 0.5, 'No valid data', 
                    ha='center', va='center', fontsize=14, color='red')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            self.canvas.draw()
            return
        
        # Calculate statistics
        stats = self._calculate_statistics(data)
        
        # Display statistics
        stats_text = self._format_statistics_text(stats, column_name, unit)
        self.stats_display.setHtml(stats_text)
        
        # Create visualizations
        self._create_visualizations(data, column_name, unit)
    
    @Slot()
    def _on_column_changed(self):
        """Handle column selection change."""
        # Could auto-analyze on selection change
        # For now, require explicit "Analyze" button click
        pass
    
    @Slot()
    def _on_datatable_changed(self):
        """Handle datatable structure changes."""
        self._populate_column_selector()
    
    @Slot()
    def _on_data_changed(self):
        """Handle datatable data changes."""
        # Could auto-update if a column is currently being analyzed
        # For now, require explicit re-analysis
        pass
