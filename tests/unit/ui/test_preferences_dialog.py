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
        assert dialog.tabs.count() == 3
        assert dialog.tabs.tabText(0) == "General"
        assert dialog.tabs.tabText(1) == "Display"
        assert dialog.tabs.tabText(2) == "Performance"
    
    def test_default_settings(self, qapp, tmp_path, monkeypatch):
        """Test default settings values."""
        # Mock home directory to isolate from saved preferences
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        dialog = PreferencesDialog()
        settings = dialog.settings
        
        # General defaults
        assert settings["language"] == "en_US"
        
        # Display defaults
        assert settings["display_precision"] == DISPLAY_PRECISION
        
        # Performance defaults
        assert settings["max_undo_steps"] == 50
    
    def test_load_values(self, qapp, tmp_path, monkeypatch):
        """Test loading values into UI controls."""
        # Mock home directory to isolate from saved preferences
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        dialog = PreferencesDialog()
        
        # Check display tab
        assert dialog.precision_spin.value() == DISPLAY_PRECISION
        
        # Check performance tab
        assert dialog.max_undo_steps.value() == 50
    
    def test_collect_values(self, qapp):
        """Test collecting values from UI controls."""
        dialog = PreferencesDialog()
        
        # Modify some values
        dialog.precision_spin.setValue(5)
        dialog.max_undo_steps.setValue(75)
        
        # Collect values
        dialog._collect_values()
        
        # Verify settings updated
        assert dialog.settings["display_precision"] == 5
        assert dialog.settings["max_undo_steps"] == 75
    
    def test_precision_range(self, qapp):
        """Test precision spin box range."""
        dialog = PreferencesDialog()
        
        assert dialog.precision_spin.minimum() == 1
        assert dialog.precision_spin.maximum() == 15
    
    def test_max_undo_steps_range(self, qapp):
        """Test max undo steps range."""
        dialog = PreferencesDialog()
        
        assert dialog.max_undo_steps.minimum() == 10
        assert dialog.max_undo_steps.maximum() == 100
    
    def test_get_settings_static_method(self, qapp):
        """Test static get_settings method."""
        settings = PreferencesDialog.get_settings()
        
        assert isinstance(settings, dict)
        assert "language" in settings
        assert "display_precision" in settings
        assert "max_undo_steps" in settings
    
    def test_settings_signal(self, qapp):
        """Test settings_changed signal emission."""
        dialog = PreferencesDialog()
        
        signal_received = []
        dialog.settings_changed.connect(lambda s: signal_received.append(s))
        
        # Trigger settings change
        dialog._apply_settings()
        
        assert len(signal_received) == 1
        assert isinstance(signal_received[0], dict)
    

class TestPreferencesPersistence:
    """Tests for preferences persistence."""
    
    def test_save_load_settings(self, qapp, tmp_path, monkeypatch):
        """Test saving and loading settings from file."""
        # Mock home directory
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        # Create dialog and modify settings
        dialog1 = PreferencesDialog()
        dialog1.precision_spin.setValue(7)
        dialog1.max_undo_steps.setValue(75)
        
        dialog1._collect_values()
        dialog1._save_settings()
        
        # Create new dialog and verify it loads saved settings
        dialog2 = PreferencesDialog()
        
        assert dialog2.settings["display_precision"] == 7
        assert dialog2.settings["max_undo_steps"] == 75
    
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
        
        assert dialog.settings["language"] == "en_US"
        assert dialog.settings["display_precision"] == DISPLAY_PRECISION


class TestPreferencesDialogButtons:
    """Tests for dialog buttons."""
    
    def test_cancel_button(self, qapp, tmp_path, monkeypatch):
        """Test cancel button rejects dialog."""
        # Mock home directory to isolate from saved preferences
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
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
