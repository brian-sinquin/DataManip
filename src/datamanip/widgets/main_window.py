"""Main window widget for DataManip application."""

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence


class MainWindow(QMainWindow):
    """Main application window for DataManip."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DataManip - Data Manipulation Tool")
        self.setMinimumSize(1000, 700)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Add welcome label
        welcome_label = QLabel("Welcome to DataManip")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        layout.addWidget(welcome_label)

        # Add description label
        description_label = QLabel(
            "An open-source data manipulation software for experimental sciences"
        )
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(description_label)

        # Add stretch to center content
        layout.addStretch()

        # Create menu bar
        self._create_menu_bar()

    def _create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("&File")

        # New action
        new_action = QAction("&New", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.setStatusTip("Create a new file")
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        # Open action
        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.setStatusTip("Open an existing file")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        # Save action
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.setStatusTip("Save the current file")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        # Save As action
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.setStatusTip("Save the file with a new name")
        save_as_action.triggered.connect(self.save_as_file)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit Menu
        edit_menu = menubar.addMenu("&Edit")

        # Undo action
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.setStatusTip("Undo the last action")
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)

        # Redo action
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.setStatusTip("Redo the last undone action")
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        # Cut action
        cut_action = QAction("Cu&t", self)
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        cut_action.setStatusTip("Cut the selection")
        cut_action.triggered.connect(self.cut)
        edit_menu.addAction(cut_action)

        # Copy action
        copy_action = QAction("&Copy", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.setStatusTip("Copy the selection")
        copy_action.triggered.connect(self.copy)
        edit_menu.addAction(copy_action)

        # Paste action
        paste_action = QAction("&Paste", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.setStatusTip("Paste from clipboard")
        paste_action.triggered.connect(self.paste)
        edit_menu.addAction(paste_action)

        edit_menu.addSeparator()

        # Preferences action
        preferences_action = QAction("&Preferences...", self)
        preferences_action.setShortcut(QKeySequence.StandardKey.Preferences)
        preferences_action.setStatusTip("Configure application settings")
        preferences_action.triggered.connect(self.preferences)
        edit_menu.addAction(preferences_action)

        # View Menu
        view_menu = menubar.addMenu("&View")

        # Zoom In action
        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in_action.setStatusTip("Zoom in")
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)

        # Zoom Out action
        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out_action.setStatusTip("Zoom out")
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)

        # Reset Zoom action
        reset_zoom_action = QAction("&Reset Zoom", self)
        reset_zoom_action.setShortcut("Ctrl+0")
        reset_zoom_action.setStatusTip("Reset zoom to default")
        reset_zoom_action.triggered.connect(self.reset_zoom)
        view_menu.addAction(reset_zoom_action)

        # Tools Menu
        tools_menu = menubar.addMenu("&Tools")

        # Data Analysis action
        data_analysis_action = QAction("&Data Analysis", self)
        data_analysis_action.setStatusTip("Open data analysis tools")
        data_analysis_action.triggered.connect(self.data_analysis)
        tools_menu.addAction(data_analysis_action)

        # Visualization action
        visualization_action = QAction("&Visualization", self)
        visualization_action.setStatusTip("Open visualization tools")
        visualization_action.triggered.connect(self.visualization)
        tools_menu.addAction(visualization_action)

        # Help Menu
        help_menu = menubar.addMenu("&Help")

        # Documentation action
        documentation_action = QAction("&Documentation", self)
        documentation_action.setShortcut(QKeySequence.StandardKey.HelpContents)
        documentation_action.setStatusTip("View documentation")
        documentation_action.triggered.connect(self.documentation)
        help_menu.addAction(documentation_action)

        help_menu.addSeparator()

        # About action
        about_action = QAction("&About DataManip", self)
        about_action.setStatusTip("About this application")
        about_action.triggered.connect(self.about)
        help_menu.addAction(about_action)

        # Create status bar
        self.statusBar().showMessage("Ready")

    # File Menu Actions
    def new_file(self):
        """Create a new file."""
        self.statusBar().showMessage("New file created", 2000)

    def open_file(self):
        """Open an existing file."""
        self.statusBar().showMessage("Open file dialog", 2000)

    def save_file(self):
        """Save the current file."""
        self.statusBar().showMessage("File saved", 2000)

    def save_as_file(self):
        """Save the file with a new name."""
        self.statusBar().showMessage("Save as dialog", 2000)

    # Edit Menu Actions
    def undo(self):
        """Undo the last action."""
        self.statusBar().showMessage("Undo", 2000)

    def redo(self):
        """Redo the last undone action."""
        self.statusBar().showMessage("Redo", 2000)

    def cut(self):
        """Cut the selection."""
        self.statusBar().showMessage("Cut", 2000)

    def copy(self):
        """Copy the selection."""
        self.statusBar().showMessage("Copy", 2000)

    def paste(self):
        """Paste from clipboard."""
        self.statusBar().showMessage("Paste", 2000)

    def preferences(self):
        """Open preferences dialog."""
        self.statusBar().showMessage("Preferences", 2000)

    # View Menu Actions
    def zoom_in(self):
        """Zoom in."""
        self.statusBar().showMessage("Zoom In", 2000)

    def zoom_out(self):
        """Zoom out."""
        self.statusBar().showMessage("Zoom Out", 2000)

    def reset_zoom(self):
        """Reset zoom to default."""
        self.statusBar().showMessage("Reset Zoom", 2000)

    # Tools Menu Actions
    def data_analysis(self):
        """Open data analysis tools."""
        self.statusBar().showMessage("Data Analysis", 2000)

    def visualization(self):
        """Open visualization tools."""
        self.statusBar().showMessage("Visualization", 2000)

    # Help Menu Actions
    def documentation(self):
        """View documentation."""
        self.statusBar().showMessage("Documentation", 2000)

    def about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About DataManip",
            "<h3>DataManip v0.1.0</h3>"
            "<p>An open-source data manipulation software for experimental sciences</p>"
            "<p>Built with PySide6 and Python</p>",
        )
