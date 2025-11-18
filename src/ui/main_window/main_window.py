"""Main window UI for DataManip application."""

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTabWidget,
    QDialog,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence

import ui.notifications as mb
from ui.about_window import show_about_dialog
from ui.preference_window import show_preference_window
from utils.lang import get_lang_manager, tr
from .menu_bar import MenuBar
from .workspace import Workspace

class MainWindow(QMainWindow):
    """
    Main application window for DataManip.
    
    Language System:
    ----------------
    Language is loaded once at startup. To change language, modify preferences
    and restart the application.
    """

    def __init__(self):
        super().__init__()
        
        # Get language manager
        self.lang = get_lang_manager()
        
        self.setWindowTitle(tr("app.title"))
        self.setMinimumSize(1000, 700)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        self.workspace = Workspace(self)
        layout.addWidget(self.workspace)

        
        # Create menu bar
        self.menu_bar = MenuBar(self)
        self.menu_bar.create_menu_bar()
    # File Menu Actions
    def new_file(self):
        """Create a new file."""
        self.statusBar().showMessage(tr("status.new_file"))

    def open_file(self):
        """Open an existing file."""
        self.statusBar().showMessage(tr("status.open_file"))

    def save_file(self):
        """Save the current file."""
        self.statusBar().showMessage(tr("status.file_saved"))

    def save_as_file(self):
        """Save the file with a new name."""
        self.statusBar().showMessage(tr("status.save_as"))

    # Edit Menu Actions
    def undo(self):
        """Undo the last action."""
        self.statusBar().showMessage(tr("status.undo"))

    def redo(self):
        """Redo the last undone action."""
        self.statusBar().showMessage(tr("status.redo"))

    def cut(self):
        """Cut the selection."""
        self.statusBar().showMessage(tr("status.cut"))

    def copy(self):
        """Copy the selection."""
        self.statusBar().showMessage(tr("status.copy"))

    def paste(self):
        """Paste from clipboard."""
        self.statusBar().showMessage(tr("status.paste"))

    def show_preferences(self):
        """Open preferences window."""
        try:
            show_preference_window(self)
            self.statusBar().showMessage(tr("status.preferences"))
        except Exception as e:
            mb.show_error(
                self,
                tr("error.preferences", "Preferences Error"),
                f"Error opening preferences: {str(e)}"
            )

    def preferences(self):
        """Open preferences dialog (deprecated - use show_preferences instead)."""
        # For backward compatibility, redirect to preferences
        self.show_preferences()

    # View Menu Actions
    def zoom_in(self):
        """Zoom in."""
        self.statusBar().showMessage(tr("status.zoom_in"))

    def zoom_out(self):
        """Zoom out."""
        self.statusBar().showMessage(tr("status.zoom_out"))

    def reset_zoom(self):
        """Reset zoom to default."""
        self.statusBar().showMessage(tr("status.reset_zoom"))

    # Tools Menu Actions
    def data_analysis(self):
        """Open data analysis tools."""
        try:
            # Example: Update plot with new data
            import numpy as np
            x = np.linspace(0, 20, 200)
            y = np.sin(x) * np.exp(-x/10)
            # Note: plot_widget would need to be added back if needed
            # self.plot_widget.plot_data(x, y, xlabel='Time', ylabel='Amplitude', 
            #                            title='Data Analysis Example')
            self.statusBar().showMessage(tr("status.data_analysis"))
        except Exception as e:
            mb.show_error(
                self,
                tr("error.data_analysis", "Data Analysis Error"),
                f"Error performing data analysis: {str(e)}"
            )

    def visualization(self):
        """Open visualization tools."""
        try:
            # Example: Show multiple plots
            import numpy as np
            x = np.linspace(0, 10, 100)
            y_list = [np.sin(x), np.cos(x), np.sin(2*x)]
            # Note: plot_widget would need to be added back if needed
            # self.plot_widget.plot_data(x, y_list, xlabel='X', ylabel='Y',
            #                            title='Visualization Example',
            #                            labels=['sin(x)', 'cos(x)', 'sin(2x)'])
            self.statusBar().showMessage(tr("status.visualization"))
        except Exception as e:
            mb.show_error(
                self,
                tr("error.visualization", "Visualization Error"),
                f"Error creating visualization: {str(e)}"
            )

    # Help Menu Actions
    def documentation(self):
        """View documentation."""
        self.statusBar().showMessage(tr("status.documentation"))

