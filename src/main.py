"""
DataManip main entry point.
"""

import sys
import json
from pathlib import Path
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from utils.lang import init_language


def main():
    """Main entry point."""
    # Load language from preferences
    settings_file = Path.home() / ".datamanip" / "preferences.json"
    language = "en_US"  # Default
    
    if settings_file.exists():
        try:
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                language = settings.get("language", "en_US")
        except Exception:
            pass  # Use default if loading fails
    
    # Initialize language system
    init_language(language)
    
    app = QApplication(sys.argv)
    app.setApplicationName("DataManip")
    app.setApplicationVersion("0.2.0")
    
    window = MainWindow()
    
    # Load workspace from CLI argument if provided
    if len(sys.argv) > 1:
        workspace_file = Path(sys.argv[1])
        if workspace_file.exists() and workspace_file.suffix == ".dmw":
            window._load_workspace(str(workspace_file))
    
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
