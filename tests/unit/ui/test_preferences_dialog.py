"""Unit tests for preferences dialog."""

import pytest
from pathlib import Path
import json
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from ui.preferences_dialog import PreferencesDialog
from constants import DISPLAY_PRECISION


@pytest.fixture
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def preferences_file(tmp_path):
    """Create temporary preferences file."""
    prefs_dir = tmp_path / ".datamanip"
    prefs_dir.mkdir()
    yield prefs_dir / "preferences.json"


class TestPreferencesDialog:
    """Tests for PreferencesDialog."""
    
    def test_initialization(self, qapp):
        """Test dialog initialization."""
        dialog = PreferencesDialog()
        
        assert dialog.windowTitle() == "Preferences"
        assert dialog.tabs.count() == 4
        assert dialog.tabs.tabText(0) == "General"
        assert dialog.tabs.tabText(1) == "Display"
        assert dialog.tabs.tabText(2) == "Performance"
        assert dialog.tabs.tabText(3) == "Recent Files"
    
    def test_default_settings(self, qapp, tmp_path, monkeypatch):
        """Test default settings values."""
        # Mock home directory to isolate from saved preferences
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        dialog = PreferencesDialog()
        settings = dialog.settings
        
        # General defaults
        assert settings["autosave_enabled"] is False
        assert settings["autosave_interval"] == 5
        assert settings["restore_session"] is True
        assert settings["show_welcome"] is True
        assert settings["confirm_delete_column"] is True
        assert settings["confirm_delete_row"] is True
        assert settings["confirm_close_study"] is True
        
        # Display defaults
        assert settings["theme"] == "System Default"
        assert settings["display_precision"] == DISPLAY_PRECISION
        assert settings["scientific_threshold"] == 6
        assert settings["show_grid"] is True
        assert settings["alternate_colors"] is True
        assert settings["compact_rows"] is True
        
        # Performance defaults
        assert settings["parallel_calc"] is True
        assert settings["max_workers"] == 4
        assert settings["cache_formulas"] is True
        assert settings["max_undo_steps"] == 50
        
        # Recent files defaults
        assert settings["recent_files"] == []
        assert settings["max_recent_files"] == 10
    
    def test_load_values(self, qapp, tmp_path, monkeypatch):
        """Test loading values into UI controls."""
        # Mock home directory to isolate from saved preferences
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        dialog = PreferencesDialog()
        
        # Check general tab
        assert dialog.autosave_enabled.isChecked() is False
        assert dialog.autosave_interval.value() == 5
        assert dialog.restore_session.isChecked() is True
        assert dialog.show_welcome.isChecked() is True
        
        # Check display tab
        assert dialog.theme_combo.currentText() == "System Default"
        assert dialog.precision_spin.value() == DISPLAY_PRECISION
        assert dialog.scientific_threshold.value() == 6
        
        # Check performance tab
        assert dialog.parallel_calc.isChecked() is True
        assert dialog.max_workers.value() == 4
        assert dialog.cache_formulas.isChecked() is True
        assert dialog.max_undo_steps.value() == 50
    
    def test_collect_values(self, qapp):
        """Test collecting values from UI controls."""
        dialog = PreferencesDialog()
        
        # Modify some values
        dialog.autosave_enabled.setChecked(True)
        dialog.autosave_interval.setValue(10)
        dialog.precision_spin.setValue(5)
        dialog.theme_combo.setCurrentText("Dark")
        dialog.max_workers.setValue(8)
        
        # Collect values
        dialog._collect_values()
        
        # Verify settings updated
        assert dialog.settings["autosave_enabled"] is True
        assert dialog.settings["autosave_interval"] == 10
        assert dialog.settings["display_precision"] == 5
        assert dialog.settings["theme"] == "Dark"
        assert dialog.settings["max_workers"] == 8
    
    def test_theme_options(self, qapp):
        """Test theme selection options."""
        dialog = PreferencesDialog()
        
        # Check available themes
        themes = [dialog.theme_combo.itemText(i) 
                 for i in range(dialog.theme_combo.count())]
        
        assert "System Default" in themes
        assert "Light" in themes
        assert "Dark" in themes
    
    def test_precision_range(self, qapp):
        """Test precision spin box range."""
        dialog = PreferencesDialog()
        
        assert dialog.precision_spin.minimum() == 1
        assert dialog.precision_spin.maximum() == 15
    
    def test_autosave_interval_range(self, qapp):
        """Test autosave interval range."""
        dialog = PreferencesDialog()
        
        assert dialog.autosave_interval.minimum() == 1
        assert dialog.autosave_interval.maximum() == 60
    
    def test_max_workers_range(self, qapp):
        """Test max workers range."""
        dialog = PreferencesDialog()
        
        assert dialog.max_workers.minimum() == 1
        assert dialog.max_workers.maximum() == 16
    
    def test_max_undo_steps_range(self, qapp):
        """Test max undo steps range."""
        dialog = PreferencesDialog()
        
        assert dialog.max_undo_steps.minimum() == 10
        assert dialog.max_undo_steps.maximum() == 100
    
    def test_recent_files_range(self, qapp):
        """Test recent files maximum range."""
        dialog = PreferencesDialog()
        
        assert dialog.max_recent_spin.minimum() == 5
        assert dialog.max_recent_spin.maximum() == 50
    
    def test_confirmations_group(self, qapp):
        """Test confirmation checkboxes."""
        dialog = PreferencesDialog()
        
        assert dialog.confirm_delete_column.isChecked() is True
        assert dialog.confirm_delete_row.isChecked() is True
        assert dialog.confirm_close_study.isChecked() is True
        
        # Toggle confirmations
        dialog.confirm_delete_column.setChecked(False)
        dialog.confirm_delete_row.setChecked(False)
        dialog.confirm_close_study.setChecked(False)
        
        dialog._collect_values()
        
        assert dialog.settings["confirm_delete_column"] is False
        assert dialog.settings["confirm_delete_row"] is False
        assert dialog.settings["confirm_close_study"] is False
    
    def test_table_display_options(self, qapp):
        """Test table display checkboxes."""
        dialog = PreferencesDialog()
        
        assert dialog.show_grid.isChecked() is True
        assert dialog.alternate_colors.isChecked() is True
        assert dialog.compact_rows.isChecked() is True
        
        # Toggle options
        dialog.show_grid.setChecked(False)
        dialog.alternate_colors.setChecked(False)
        dialog.compact_rows.setChecked(False)
        
        dialog._collect_values()
        
        assert dialog.settings["show_grid"] is False
        assert dialog.settings["alternate_colors"] is False
        assert dialog.settings["compact_rows"] is False
    
    def test_performance_options(self, qapp):
        """Test performance checkboxes."""
        dialog = PreferencesDialog()
        
        assert dialog.parallel_calc.isChecked() is True
        assert dialog.cache_formulas.isChecked() is True
        
        # Toggle options
        dialog.parallel_calc.setChecked(False)
        dialog.cache_formulas.setChecked(False)
        
        dialog._collect_values()
        
        assert dialog.settings["parallel_calc"] is False
        assert dialog.settings["cache_formulas"] is False
    
    def test_get_settings_static_method(self, qapp):
        """Test static get_settings method."""
        settings = PreferencesDialog.get_settings()
        
        assert isinstance(settings, dict)
        assert "autosave_enabled" in settings
        assert "theme" in settings
        assert "display_precision" in settings
        assert "parallel_calc" in settings
    
    def test_settings_signal(self, qapp):
        """Test settings_changed signal emission."""
        dialog = PreferencesDialog()
        
        signal_received = []
        dialog.settings_changed.connect(lambda s: signal_received.append(s))
        
        # Trigger settings change
        dialog._apply_settings()
        
        assert len(signal_received) == 1
        assert isinstance(signal_received[0], dict)
    
    def test_recent_files_list(self, qapp):
        """Test recent files list display."""
        dialog = PreferencesDialog()
        
        # Add some recent files
        dialog.settings["recent_files"] = ["/path/to/file1.dmw", "/path/to/file2.dmw"]
        dialog._load_values()
        
        assert dialog.recent_files_list.count() == 2
        assert dialog.recent_files_list.item(0).text() == "/path/to/file1.dmw"
        assert dialog.recent_files_list.item(1).text() == "/path/to/file2.dmw"


class TestPreferencesPersistence:
    """Tests for preferences persistence."""
    
    def test_save_load_settings(self, qapp, tmp_path, monkeypatch):
        """Test saving and loading settings from file."""
        # Mock home directory
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        # Create dialog and modify settings
        dialog1 = PreferencesDialog()
        dialog1.autosave_enabled.setChecked(True)
        dialog1.autosave_interval.setValue(15)
        dialog1.precision_spin.setValue(7)
        dialog1.theme_combo.setCurrentText("Dark")
        
        dialog1._collect_values()
        dialog1._save_settings()
        
        # Create new dialog and verify it loads saved settings
        dialog2 = PreferencesDialog()
        
        assert dialog2.settings["autosave_enabled"] is True
        assert dialog2.settings["autosave_interval"] == 15
        assert dialog2.settings["display_precision"] == 7
        assert dialog2.settings["theme"] == "Dark"
    
    def test_settings_file_location(self, qapp, tmp_path, monkeypatch):
        """Test settings file is created in correct location."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        dialog = PreferencesDialog()
        dialog._save_settings()
        
        settings_file = tmp_path / ".datamanip" / "preferences.json"
        assert settings_file.exists()
    
    def test_invalid_settings_file(self, qapp, tmp_path, monkeypatch):
        """Test handling of invalid settings file."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        # Create invalid JSON file
        settings_file = tmp_path / ".datamanip" / "preferences.json"
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        settings_file.write_text("invalid json content")
        
        # Should fall back to defaults without crashing
        dialog = PreferencesDialog()
        
        assert dialog.settings["autosave_enabled"] is False
        assert dialog.settings["display_precision"] == DISPLAY_PRECISION


class TestPreferencesDialogButtons:
    """Tests for dialog buttons."""
    
    def test_cancel_button(self, qapp):
        """Test cancel button rejects dialog."""
        dialog = PreferencesDialog()
        
        # Modify setting
        dialog.precision_spin.setValue(10)
        
        # Click cancel (simulated by calling reject)
        dialog.reject()
        
        # Settings should not be saved
        dialog2 = PreferencesDialog()
        assert dialog2.settings["display_precision"] == DISPLAY_PRECISION
    
    def test_apply_button_emits_signal(self, qapp):
        """Test apply button emits signal without closing."""
        dialog = PreferencesDialog()
        
        signal_received = []
        dialog.settings_changed.connect(lambda s: signal_received.append(s))
        
        dialog._apply_settings()
        
        assert len(signal_received) == 1
