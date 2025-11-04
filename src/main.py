from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
import sys
from pathlib import Path

from utils.lang import init_language
from ui import MainWindow


def main():
    """Main entry point for the DataManip application."""
    # Initialize language system (default: English)
    # Change to 'fr_FR' for French
    lang = init_language("en_US")
    
    # Create the application instance
    app = QApplication(sys.argv)

    # Create and show the main window
    window = MainWindow()
    
    # Set window icon using absolute path (go up from src to project root)
    icon_path = Path(__file__).parent.parent / "assets" / "icons" / "ICON.png"
    if icon_path.exists():
        window.setWindowIcon(QIcon(str(icon_path)))
    
    window.show()

    # Start the event loop
    app.exec()
if __name__ == "__main__":
    main()
