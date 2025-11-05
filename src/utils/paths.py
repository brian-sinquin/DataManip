"""Project path definitions for DataManip.

This module provides centralized path definitions that can be imported
by any module in the project to ensure consistent access to project
directories and files.
"""

from pathlib import Path

# Project root directory (go up from src/utils to project root)
ROOT_DIR = Path(__file__).parent.parent.parent

# Common asset directories
ASSETS_DIR = ROOT_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
LANG_DIR = ASSETS_DIR / "lang" 
STYLES_DIR = ASSETS_DIR / "styles"

# Configuration file
CONFIG_FILE = ROOT_DIR / "config.json"

# Source directory
SRC_DIR = ROOT_DIR / "src"