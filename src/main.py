"""
DataManip main entry point.
"""

import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from utils.lang import init_language


def main():
    """Main entry point."""
    # Initialize language system (will auto-load from config later)
    init_language("en_US")
    
    app = QApplication(sys.argv)
    app.setApplicationName("DataManip")
    app.setApplicationVersion("0.2.0")
    
    window = MainWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
