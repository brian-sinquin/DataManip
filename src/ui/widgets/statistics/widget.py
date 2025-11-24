"""
StatisticsWidget - UI widget for StatisticsStudy.

Provides statistical analysis visualization with column selection,
descriptive statistics display, and interactive plots.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel,
    QGroupBox, QPushButton, QTextEdit, QSplitter
)
from PySide6.QtCore import Qt, Slot

# Matplotlib imports
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import numpy as np

from constants import (
    COLUMN_COMBO_MIN_WIDTH, STATS_SPLITTER_LEFT, STATS_SPLITTER_RIGHT,
    HISTOGRAM_MIN_BINS, HISTOGRAM_MAX_BINS
)
from studies.statistics_study import StatisticsStudy


class StatisticsWidget(QWidget):
    """Widget for displaying and interacting with StatisticsStudy.
    
    Features:
    - Column selector dropdown (from linked DataTableStudy)
    - Descriptive statistics display
    - Histogram visualization
    - Box plot visualization
    - Real-time analysis updates
    """
    
    def __init__(self, study: StatisticsStudy, parent: Optional[QWidget] = None):
        """Initialize the statistics widget.
        
        Args:
            study: StatisticsStudy instance to display
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.study = study
        
        self._setup_ui()
        self._populate_column_selector()
        self._show_initial_message()
    
    def _setup_ui(self):
        """Set up the user interface."""
        main_layout = QVBoxLayout(self)
        
        # Column selection section
        selection_layout = QHBoxLayout()
        selection_layout.addWidget(QLabel("Analyze Column:"))
        
        self.column_combo = QComboBox()
        self.column_combo.setMinimumWidth(COLUMN_COMBO_MIN_WIDTH)
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
    
    def _populate_column_selector(self):
        """Populate the column dropdown with available columns."""
        # Block signals during population
        self.column_combo.blockSignals(True)
        
        # Clear existing items
        self.column_combo.clear()
        
        # Get available columns from study
        columns = self.study.get_available_columns()
        
        for col_name in columns:
            self.column_combo.addItem(col_name, col_name)
        
        # Re-enable signals
        self.column_combo.blockSignals(False)
        
        # Enable/disable analyze button
        self.analyze_button.setEnabled(len(columns) > 0)
    
    def _format_statistics_html(self, stats: dict, column_name: str) -> str:
        """Format statistics as HTML for display.
        
        Args:
            stats: Dictionary of statistical measures
            column_name: Name of the analyzed column
            
        Returns:
            Formatted HTML string
        """
        if not stats:
            return "No valid data to analyze."
        
        html = f"<h3>Statistics for: {column_name}</h3>\n"
        html += "<hr>\n"
        html += f"<b>Sample Size</b><br>\n"
        html += f"Count: {stats['count']}<br>\n"
        html += "<br>\n"
        
        html += f"<b>Central Tendency</b><br>\n"
        html += f"Mean: {stats['mean']:.6g}<br>\n"
        html += f"Median: {stats['median']:.6g}<br>\n"
        html += "<br>\n"
        
        html += f"<b>Dispersion</b><br>\n"
        html += f"Std Dev: {stats['std']:.6g}<br>\n"
        html += f"Variance: {stats['variance']:.6g}<br>\n"
        html += f"Range: {stats['range']:.6g}<br>\n"
        html += f"IQR: {stats['iqr']:.6g}<br>\n"
        html += "<br>\n"
        
        html += f"<b>Extremes</b><br>\n"
        html += f"Min: {stats['min']:.6g}<br>\n"
        html += f"Max: {stats['max']:.6g}<br>\n"
        html += "<br>\n"
        
        html += f"<b>Quartiles</b><br>\n"
        html += f"Q1 (25%): {stats['q25']:.6g}<br>\n"
        html += f"Q2 (50%): {stats['q50']:.6g}<br>\n"
        html += f"Q3 (75%): {stats['q75']:.6g}<br>\n"
        html += "<br>\n"
        
        html += f"<b>Shape</b><br>\n"
        html += f"Skewness: {stats['skewness']:.4f}<br>\n"
        html += f"Kurtosis: {stats['kurtosis']:.4f}<br>\n"
        
        # Interpretation hints
        html += "<br><hr>\n"
        html += "<small><i>Interpretation:</i><br>\n"
        html += "Skewness: 0 = symmetric, >0 = right-skewed, <0 = left-skewed<br>\n"
        html += "Kurtosis: 0 = normal, >0 = heavy tails, <0 = light tails</small>\n"
        
        return html
    
    def _create_visualizations(self, column_name: str):
        """Create histogram and box plot visualizations.
        
        Args:
            column_name: Name of the column to visualize
        """
        import numpy as np
        
        data = self.study.get_source_data(column_name)
        
        if data is None or len(data) == 0:
            self._show_no_data_plot()
            return
        
        # Clear previous plots
        self.figure.clear()
        
        # Create 2 subplots: histogram and box plot
        ax1 = self.figure.add_subplot(2, 1, 1)
        ax2 = self.figure.add_subplot(2, 1, 2)
        
        # Histogram
        n_bins = min(50, max(10, int(np.sqrt(len(data)))))  # Sturges' rule adjusted
        ax1.hist(data, bins=n_bins, color='steelblue', alpha=0.7, edgecolor='black')
        ax1.set_xlabel(column_name)
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
        
        ax2.set_xlabel(column_name)
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
    
    def _show_no_data_plot(self):
        """Show message when no valid data is available."""
        self.figure.clear()
        ax = self.figure.add_subplot(1, 1, 1)
        ax.text(0.5, 0.5, 'No valid data', 
                ha='center', va='center', fontsize=14, color='red')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        self.canvas.draw()
    
    @Slot()
    def _on_analyze_clicked(self):
        """Handle analyze button click."""
        # Get selected column name
        col_name = self.column_combo.currentData()
        if col_name is None:
            self._show_initial_message()
            return
        
        # Analyze column
        stats = self.study.analyze_column(col_name)
        
        if not stats:
            self.stats_display.setHtml(
                f"<h3>Statistics for: {col_name}</h3>"
                "<p><b>Error:</b> No valid numerical data found in this column.</p>"
            )
            self._show_no_data_plot()
            return
        
        # Display statistics
        stats_html = self._format_statistics_html(stats, col_name)
        self.stats_display.setHtml(stats_html)
        
        # Create visualizations
        self._create_visualizations(col_name)
    
    @Slot()
    def _on_column_changed(self):
        """Handle column selection change."""
        # Could auto-analyze on selection change
        # For now, require explicit "Analyze" button click
        pass
    
    def refresh(self):
        """Refresh the widget (update column list and redraw)."""
        self._populate_column_selector()
        # If a column is currently selected and analyzed, re-analyze it
        col_name = self.column_combo.currentData()
        if col_name is not None:
            self._on_analyze_clicked()
