"""Simple About Dialog for DataManip application."""

from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
)
from PySide6.QtCore import Qt

from utils.lang import get_lang_manager, tr


class AboutDialog(QMainWindow):
    """Simple about dialog with basic information."""

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.lang = get_lang_manager()
        self._setup_ui()

    def _setup_ui(self):
        """Setup the basic user interface."""
        self.setWindowTitle(tr('about.title', 'About DataManip'))
        self.setFixedSize(400, 300)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # App title
        title_label = QLabel(tr('app.name', 'DataManip'))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Version
        version_label = QLabel("Version 0.1.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)
        
        # Description
        description_label = QLabel(tr('about.description', 'A data manipulation application'))
        description_label.setWordWrap(True)
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description_label)
        
        # Copyright
        copyright_label = QLabel(tr('about.copyright', 'Copyright © 2025 Brian Sinquin'))
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(copyright_label)
        
        # License
        license_label = QLabel(tr('about.license_text', 'MIT License'))
        license_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(license_label)
        
        # Spacer
        layout.addStretch()
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton(tr('common.close', 'Close'))
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)


def show_about_dialog(parent=None):
    """Show the about dialog."""
    dialog = AboutDialog(parent)
    dialog.show()
    return dialog
