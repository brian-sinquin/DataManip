from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon
import sys
from pathlib import Path

from utils.config import init_config
from utils.lang import init_language
from utils.paths import ICONS_DIR
from ui import MainWindow

def main():
    """Main entry point for the DataManip application."""
    try:
        # Initialize configuration system
        config = init_config()
        
        # Initialize language system using configured language
        default_lang = config.get_language()
        lang = init_language(default_lang)
        
        # Create the application instance
        app = QApplication(sys.argv)
        app.setApplicationName("DataManip")
        app.setApplicationVersion("0.1.0")
        app.setOrganizationName("DataManip")
        
        # Create and show the main window
        window = MainWindow()
        
        # Set window icon using absolute path (go up from src to project root)
        icon_path = ICONS_DIR / "ICON.png"
        if icon_path.exists():
            window.setWindowIcon(QIcon(str(icon_path)))
        
        
        window.show()
        
        # Start the event loop
        exit_code = app.exec()

        try:
            config.save_config()
        except Exception as e:
            print(f"Error saving configuration on exit: {e}")

    except Exception as e:
        # Only show error dialog for critical startup failures
        try:
            if 'app' not in locals():
                app = QApplication(sys.argv)
            
            QMessageBox.critical(
                None,
                "Application Error",
                f"DataManip failed to start:\n\n{str(e)}"
            )
        except:
            print(f"Critical error: {e}")
        
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
