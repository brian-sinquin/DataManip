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
        self.tabs.addTab(self._create_recent_files_tab(), "Recent Files")
        
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
        
        # Auto-save group
        autosave_group = QGroupBox("Auto-Save")
        autosave_layout = QFormLayout()
        
        self.autosave_enabled = QCheckBox("Enable auto-save")
        autosave_layout.addRow("", self.autosave_enabled)
        
        self.autosave_interval = QSpinBox()
        self.autosave_interval.setRange(1, 60)
        self.autosave_interval.setSuffix(" minutes")
        autosave_layout.addRow("Interval:", self.autosave_interval)
        
        autosave_group.setLayout(autosave_layout)
        layout.addWidget(autosave_group)
        
        # Startup group
        startup_group = QGroupBox("Startup")
        startup_layout = QFormLayout()
        
        self.restore_session = QCheckBox("Restore last session on startup")
        startup_layout.addRow("", self.restore_session)
        
        self.show_welcome = QCheckBox("Show welcome dialog")
        startup_layout.addRow("", self.show_welcome)
        
        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)
        
        # Confirmations group
        confirm_group = QGroupBox("Confirmations")
        confirm_layout = QVBoxLayout()
        
        self.confirm_delete_column = QCheckBox("Confirm before deleting columns")
        confirm_layout.addWidget(self.confirm_delete_column)
        
        self.confirm_delete_row = QCheckBox("Confirm before deleting rows")
        confirm_layout.addWidget(self.confirm_delete_row)
        
        self.confirm_close_study = QCheckBox("Confirm before closing studies")
        confirm_layout.addWidget(self.confirm_close_study)
        
        confirm_group.setLayout(confirm_layout)
        layout.addWidget(confirm_group)
        
        layout.addStretch()
        return widget
    
    def _create_display_tab(self) -> QWidget:
        """Create display settings tab.
        
        Returns:
            QWidget with display settings
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Theme group
        theme_group = QGroupBox("Theme")
        theme_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["System Default", "Light", "Dark"])
        theme_layout.addRow("Theme:", self.theme_combo)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Number formatting group
        format_group = QGroupBox("Number Formatting")
        format_layout = QFormLayout()
        
        self.precision_spin = QSpinBox()
        self.precision_spin.setRange(1, 15)
        self.precision_spin.setSuffix(" digits")
        self.precision_spin.setToolTip("Number of significant digits to display in cells")
        format_layout.addRow("Display Precision:", self.precision_spin)
        
        self.scientific_threshold = QSpinBox()
        self.scientific_threshold.setRange(2, 10)
        self.scientific_threshold.setToolTip("Use scientific notation for numbers with more than this many digits")
        format_layout.addRow("Scientific Notation:", self.scientific_threshold)
        
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        # Table display group
        table_group = QGroupBox("Table Display")
        table_layout = QVBoxLayout()
        
        self.show_grid = QCheckBox("Show grid lines")
        table_layout.addWidget(self.show_grid)
        
        self.alternate_colors = QCheckBox("Alternate row colors")
        table_layout.addWidget(self.alternate_colors)
        
        self.compact_rows = QCheckBox("Compact row height")
        table_layout.addWidget(self.compact_rows)
        
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)
        
        layout.addStretch()
        return widget
    
    def _create_performance_tab(self) -> QWidget:
        """Create performance settings tab.
        
        Returns:
            QWidget with performance settings
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Calculation group
        calc_group = QGroupBox("Calculations")
        calc_layout = QFormLayout()
        
        self.parallel_calc = QCheckBox("Enable parallel calculations")
        calc_layout.addRow("", self.parallel_calc)
        
        self.max_workers = QSpinBox()
        self.max_workers.setRange(1, 16)
        self.max_workers.setToolTip("Number of parallel workers for calculations")
        calc_layout.addRow("Max Workers:", self.max_workers)
        
        self.cache_formulas = QCheckBox("Cache compiled formulas")
        calc_layout.addRow("", self.cache_formulas)
        
        calc_group.setLayout(calc_layout)
        layout.addWidget(calc_group)
        
        # Memory group
        memory_group = QGroupBox("Memory")
        memory_layout = QFormLayout()
        
        self.max_undo_steps = QSpinBox()
        self.max_undo_steps.setRange(10, 100)
        self.max_undo_steps.setSuffix(" steps")
        memory_layout.addRow("Undo History:", self.max_undo_steps)
        
        memory_group.setLayout(memory_layout)
        layout.addWidget(memory_group)
        
        layout.addStretch()
        return widget
    
    def _create_recent_files_tab(self) -> QWidget:
        """Create recent files tab.
        
        Returns:
            QWidget with recent files list
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel("Recent Files:"))
        
        self.recent_files_list = QListWidget()
        layout.addWidget(self.recent_files_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._clear_recent_files)
        btn_layout.addWidget(clear_btn)
        
        btn_layout.addStretch()
        
        self.max_recent_spin = QSpinBox()
        self.max_recent_spin.setRange(5, 50)
        self.max_recent_spin.setSuffix(" files")
        btn_layout.addWidget(QLabel("Maximum:"))
        btn_layout.addWidget(self.max_recent_spin)
        
        layout.addLayout(btn_layout)
        
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
            "autosave_enabled": False,
            "autosave_interval": 5,
            "restore_session": True,
            "show_welcome": True,
            "confirm_delete_column": True,
            "confirm_delete_row": True,
            "confirm_close_study": True,
            
            # Display
            "theme": "System Default",
            "display_precision": DISPLAY_PRECISION,
            "scientific_threshold": 6,
            "show_grid": True,
            "alternate_colors": True,
            "compact_rows": True,
            
            # Performance
            "parallel_calc": True,
            "max_workers": 4,
            "cache_formulas": True,
            "max_undo_steps": 50,
            
            # Recent files
            "recent_files": [],
            "max_recent_files": 10,
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
        # General
        self.autosave_enabled.setChecked(self.settings["autosave_enabled"])
        self.autosave_interval.setValue(self.settings["autosave_interval"])
        self.restore_session.setChecked(self.settings["restore_session"])
        self.show_welcome.setChecked(self.settings["show_welcome"])
        self.confirm_delete_column.setChecked(self.settings["confirm_delete_column"])
        self.confirm_delete_row.setChecked(self.settings["confirm_delete_row"])
        self.confirm_close_study.setChecked(self.settings["confirm_close_study"])
        
        # Display
        self.theme_combo.setCurrentText(self.settings["theme"])
        self.precision_spin.setValue(self.settings["display_precision"])
        self.scientific_threshold.setValue(self.settings["scientific_threshold"])
        self.show_grid.setChecked(self.settings["show_grid"])
        self.alternate_colors.setChecked(self.settings["alternate_colors"])
        self.compact_rows.setChecked(self.settings["compact_rows"])
        
        # Performance
        self.parallel_calc.setChecked(self.settings["parallel_calc"])
        self.max_workers.setValue(self.settings["max_workers"])
        self.cache_formulas.setChecked(self.settings["cache_formulas"])
        self.max_undo_steps.setValue(self.settings["max_undo_steps"])
        
        # Recent files
        self.recent_files_list.clear()
        for file_path in self.settings["recent_files"]:
            self.recent_files_list.addItem(file_path)
        self.max_recent_spin.setValue(self.settings["max_recent_files"])
    
    def _collect_values(self):
        """Collect values from UI controls into settings."""
        # General
        self.settings["language"] = self.language_combo.currentData()
        self.settings["autosave_enabled"] = self.autosave_enabled.isChecked()
        self.settings["autosave_interval"] = self.autosave_interval.value()
        self.settings["restore_session"] = self.restore_session.isChecked()
        self.settings["show_welcome"] = self.show_welcome.isChecked()
        self.settings["confirm_delete_column"] = self.confirm_delete_column.isChecked()
        self.settings["confirm_delete_row"] = self.confirm_delete_row.isChecked()
        self.settings["confirm_close_study"] = self.confirm_close_study.isChecked()
        
        # Display
        self.settings["theme"] = self.theme_combo.currentText()
        self.settings["display_precision"] = self.precision_spin.value()
        self.settings["scientific_threshold"] = self.scientific_threshold.value()
        self.settings["show_grid"] = self.show_grid.isChecked()
        self.settings["alternate_colors"] = self.alternate_colors.isChecked()
        self.settings["compact_rows"] = self.compact_rows.isChecked()
        
        # Performance
        self.settings["parallel_calc"] = self.parallel_calc.isChecked()
        self.settings["max_workers"] = self.max_workers.value()
        self.settings["cache_formulas"] = self.cache_formulas.isChecked()
        self.settings["max_undo_steps"] = self.max_undo_steps.value()
        
        # Recent files
        self.settings["max_recent_files"] = self.max_recent_spin.value()
    
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
                "Preferences have been applied.\nLanguage changes take effect immediately."
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
    
    def _clear_recent_files(self):
        """Clear recent files list."""
        reply = QMessageBox.question(
            self,
            "Clear Recent Files",
            "Clear all recent files?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.recent_files_list.clear()
            self.settings["recent_files"] = []
    
    @staticmethod
    def get_settings() -> Dict[str, Any]:
        """Get current settings without showing dialog.
        
        Returns:
            Dictionary of current settings
        """
        dialog = PreferencesDialog()
        return dialog.settings
