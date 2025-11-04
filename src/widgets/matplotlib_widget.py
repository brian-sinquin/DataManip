"""Interactive matplotlib widget for PySide6."""

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtWidgets import QWidget, QVBoxLayout


class MatplotlibWidget(QWidget):
    """
    A widget that embeds matplotlib with interactive navigation toolbar.
    
    Features:
    - Interactive plot with zoom, pan, save
    - Navigation toolbar
    - Easy to update with new data
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create the matplotlib figure and canvas
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvasQTAgg(self.figure)
        
        # Create the navigation toolbar
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        
        # Setup layout
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        
        # Create initial axes
        self.axes = self.figure.add_subplot(111)
        
        # Plot some sample data
        self.plot_sample_data()
    
    def plot_sample_data(self):
        """Plot sample data as a demonstration."""
        # Generate sample data
        x = np.linspace(0, 10, 100)
        y1 = np.sin(x)
        y2 = np.cos(x)
        
        # Clear previous plot
        self.axes.clear()
        
        # Plot data
        self.axes.plot(x, y1, label='sin(x)', linewidth=2)
        self.axes.plot(x, y2, label='cos(x)', linewidth=2)
        
        # Customize plot
        self.axes.set_xlabel('X axis')
        self.axes.set_ylabel('Y axis')
        self.axes.set_title('Interactive Plot - Try the toolbar!')
        self.axes.legend()
        self.axes.grid(True, alpha=0.3)
        
        # Refresh canvas
        self.canvas.draw()
    
    def plot_data(self, x, y, xlabel='X', ylabel='Y', title='Plot', **kwargs):
        """
        Plot custom data.
        
        Args:
            x: X-axis data
            y: Y-axis data (can be list of arrays for multiple lines)
            xlabel: Label for X axis
            ylabel: Label for Y axis
            title: Plot title
            **kwargs: Additional matplotlib plot arguments
        """
        self.axes.clear()
        
        # Handle multiple y datasets
        if isinstance(y, list):
            for i, y_data in enumerate(y):
                label = kwargs.pop('labels', [f'Line {i+1}'] * len(y))[i]
                self.axes.plot(x, y_data, label=label, **kwargs)
            self.axes.legend()
        else:
            self.axes.plot(x, y, **kwargs)
        
        self.axes.set_xlabel(xlabel)
        self.axes.set_ylabel(ylabel)
        self.axes.set_title(title)
        self.axes.grid(True, alpha=0.3)
        
        self.canvas.draw()
    
    def clear_plot(self):
        """Clear the current plot."""
        self.axes.clear()
        self.canvas.draw()
    
    def save_plot(self, filename):
        """
        Save the current plot to a file.
        
        Args:
            filename: Path to save the plot
        """
        self.figure.savefig(filename, dpi=300, bbox_inches='tight')
