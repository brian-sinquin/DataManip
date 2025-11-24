"""Preferences dialog for application settings."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QComboBox, QSpinBox, QCheckBox, QPushButton,
    QGroupBox, QFormLayout, QListWidget, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPalette
import json
from pathlib import Path
from typing import Dict, Any

from constants import DISPLAY_PRECISION


class PreferencesDialog(QDialog):
    """Dialog for application preferences.
    
    Signals:
        settings_changed: Emitted when settings are applied
    """
    
    settings_changed = Signal(dict)
    
    def __init__(self, parent=None):
        """Initialize preferences dialog.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.setWindowTitle("Preferences")
        self.resize(600, 500)
        
        # Load current settings
        self.settings = self._load_settings()
        
        # Setup UI
        self._setup_ui()
        
        # Load values into UI
        self._load_values()
    
    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout(self)
        
        # Tab widget for different preference categories
        self.tabs = QTabWidget()
        
        # Add tabs
        self.tabs.addTab(self._create_general_tab(), "General")
        self.tabs.addTab(self._create_display_tab(), "Display")
        self.tabs.addTab(self._create_performance_tab(), "Performance")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._reset_to_defaults)
        button_layout.addWidget(reset_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self._apply_settings)
        button_layout.addWidget(apply_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self._accept_settings)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
    
    def _create_general_tab(self) -> QWidget:
        """Create general settings tab.
        
        Returns:
            QWidget with general settings
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Language group
        language_group = QGroupBox("Language")
        language_layout = QFormLayout()
        
        self.language_combo = QComboBox()
        
        # Try to get language manager, initialize if needed
        try:
            from utils.lang import get_lang_manager, get_current_language
            lang_manager = get_lang_manager()
            available_langs = lang_manager.get_available_languages()
            current_lang = get_current_language()
            
            for lang_code in available_langs:
                lang_name = lang_manager.get_language_name(lang_code)
                self.language_combo.addItem(lang_name, lang_code)
                if lang_code == current_lang:
                    self.language_combo.setCurrentText(lang_name)
        except Exception:
            # Language system not initialized (e.g., in tests)
            self.language_combo.addItem("English (US)", "en_US")
            self.language_combo.setCurrentIndex(0)
        
        language_layout.addRow("Language:", self.language_combo)
        language_info = QLabel("Changes will be applied immediately to menus and dialogs.")
        language_info.setWordWrap(True)
        language_info.setStyleSheet("color: #666; font-size: 10px;")
        language_layout.addRow("", language_info)
        
        language_group.setLayout(language_layout)
        layout.addWidget(language_group)
        
        layout.addStretch()
        return widget
    
    def _create_display_tab(self) -> QWidget:
        """Create display settings tab.
        
        Returns:
            QWidget with display settings
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Number formatting group
        format_group = QGroupBox("Number Formatting")
        format_layout = QFormLayout()
        
        self.precision_spin = QSpinBox()
        self.precision_spin.setRange(1, 15)
        self.precision_spin.setSuffix(" digits")
        self.precision_spin.setToolTip(
            "Number of significant digits to display in cells.\n"
            "Full precision is preserved internally and used for calculations."
        )
        format_layout.addRow("Display Precision:", self.precision_spin)
        
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        layout.addStretch()
        return widget
    
    def _create_performance_tab(self) -> QWidget:
        """Create performance settings tab.
        
        Returns:
            QWidget with performance settings
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Memory group
        memory_group = QGroupBox("History")
        memory_layout = QFormLayout()
        
        self.max_undo_steps = QSpinBox()
        self.max_undo_steps.setRange(10, 100)
        self.max_undo_steps.setSuffix(" steps")
        self.max_undo_steps.setToolTip(
            "Maximum number of undo/redo operations to keep in memory.\n"
            "Changes apply to new studies only."
        )
        memory_layout.addRow("Undo History:", self.max_undo_steps)
        
        memory_group.setLayout(memory_layout)
        layout.addWidget(memory_group)
        
        layout.addStretch()
        return widget
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file.
        
        Returns:
            Dictionary of settings
        """
        settings_file = Path.home() / ".datamanip" / "preferences.json"
        
        # Default settings
        defaults = {
            # General
            "language": "en_US",
            
            # Display
            "display_precision": DISPLAY_PRECISION,
            
            # Performance
            "max_undo_steps": 50,
        }
        
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    loaded = json.load(f)
                    defaults.update(loaded)
            except Exception:
                pass  # Use defaults if loading fails
        
        return defaults
    
    def _save_settings(self):
        """Save settings to file."""
        settings_file = Path.home() / ".datamanip" / "preferences.json"
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Save Error",
                f"Failed to save preferences: {e}"
            )
    
    def _load_values(self):
        """Load current settings into UI controls."""
        # General - Language
        lang_code = self.settings.get("language", "en_US")
        index = self.language_combo.findData(lang_code)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
        
        # Display
        self.precision_spin.setValue(self.settings["display_precision"])
        
        # Performance
        self.max_undo_steps.setValue(self.settings["max_undo_steps"])
    
    def _collect_values(self):
        """Collect values from UI controls into settings."""
        # General
        self.settings["language"] = self.language_combo.currentData()
        
        # Display
        self.settings["display_precision"] = self.precision_spin.value()
        
        # Performance
        self.settings["max_undo_steps"] = self.max_undo_steps.value()
    
    def _apply_settings(self):
        """Apply settings without closing dialog."""
        self._collect_values()
        
        # Apply language change immediately (if language system available)
        try:
            from utils.lang import get_current_language, set_language
            new_lang = self.settings.get("language", "en_US")
            if new_lang != get_current_language():
                set_language(new_lang)
        except Exception:
            pass  # Language system not available
        
        self._save_settings()
        self.settings_changed.emit(self.settings)
        
        # Only show message box if we have a parent (not during tests)
        if self.parent() is not None:
            QMessageBox.information(
                self,
                "Settings Applied",
                "Preferences have been applied."
            )
    
    def _accept_settings(self):
        """Apply settings and close dialog."""
        self._collect_values()
        
        # Apply language change immediately (if language system available)
        try:
            from utils.lang import get_current_language, set_language
            new_lang = self.settings.get("language", "en_US")
            if new_lang != get_current_language():
                set_language(new_lang)
        except Exception:
            pass  # Language system not available
        
        self._save_settings()
        self.settings_changed.emit(self.settings)
        self.accept()
    
    def _reset_to_defaults(self):
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset to Defaults",
            "Reset all preferences to default values?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.settings = self._load_settings()
            # Clear saved file
            settings_file = Path.home() / ".datamanip" / "preferences.json"
            if settings_file.exists():
                settings_file.unlink()
            
            self._load_values()
    
    @staticmethod
    def get_settings() -> Dict[str, Any]:
        """Get current settings without showing dialog.
        
        Returns:
            Dictionary of current settings
        """
        dialog = PreferencesDialog()
        return dialog.settings
