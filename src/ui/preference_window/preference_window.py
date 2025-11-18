"""Preference window for DataManip application."""

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QFormLayout,
    QGroupBox,
    QMessageBox,
    QSpacerItem,
    QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QTimer
from PySide6.QtGui import QFont

from utils.lang import get_lang_manager, tr
from utils.config import get_config


class GeneralPreferencesTab(QWidget):
    """General preferences tab with language settings only."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.lang = get_lang_manager()
        self.config = get_config()
        self.language_changed = False
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the UI for general preferences."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Language Settings Group
        self.language_group = QGroupBox(tr('preferences.language_settings', 'Language Settings'))
        language_layout = QFormLayout()
        self.language_group.setLayout(language_layout)
        
        # Language selection
        self.language_combo = QComboBox()
        self.language_combo.currentTextChanged.connect(self._on_language_changed)
        
        # Language mapping
        self.language_map = {
            "en_US": "English (US)",
            "fr_FR": "Français (France)",
        }
        
        # Populate combo box with available languages
        available_langs = self.lang.get_available_languages()
        for lang_code in available_langs:
            display_name = self.language_map.get(lang_code, lang_code)
            if display_name:
                self.language_combo.addItem(display_name)
                self.language_combo.setItemData(self.language_combo.count() - 1, lang_code)
        
        # Set current language as selected
        current_index = self.language_combo.findData(self.lang.lang_code)
        if current_index >= 0:
            self.language_combo.setCurrentIndex(current_index)
        
        self.language_label = QLabel(tr('language.language', 'Language:'))
        language_layout.addRow(self.language_label, self.language_combo)
        
        # Language info
        self.language_info = QLabel(tr('preferences.restart_info', 
            'Changes will be applied after restarting the application.'))
        self.language_info.setWordWrap(True)
        self.language_info.setStyleSheet("color: #666; font-style: italic;")
        language_layout.addRow(self.language_info)
        
        layout.addWidget(self.language_group)
        
        # Add stretch to push content to top
        layout.addStretch()
    
    def _on_language_changed(self):
        """Handle language selection change."""
        selected_lang = self.language_combo.currentData()
        if selected_lang and selected_lang != self.lang.lang_code:
            self.language_changed = True
    
    def apply_changes(self):
        """Apply the changes made in this tab."""
        if self.language_changed:
            selected_lang = self.language_combo.currentData()
            if selected_lang:
                try:
                    # Save config change in a try-except to prevent freezing
                    success = self.config.set_language(selected_lang)
                    if success:
                        self.language_changed = False
                        return True
                    else:
                        print("Warning: Failed to save language to config")
                        return False
                except Exception as e:
                    print(f"Error saving language config: {e}")
                    return False
        return False


class PreferenceWindow(QMainWindow):
    """
    Preference window for configuring language settings.
    
    This window provides a simple interface for language selection.
    Changes require application restart to take effect.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.lang = get_lang_manager()
        self.config = get_config()
        
        self._setup_ui()
        
        # Add status bar
        self.statusBar().showMessage(tr("status.ready", "Ready"))
    
    def _setup_ui(self):
        """Setup the preference window UI."""
        self.setWindowTitle(tr('preferences.title', 'Language Preferences'))
        self.setMinimumSize(500, 400)
        self.setMaximumSize(600, 500)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Title
        self.title_label = QLabel(tr('preferences.title', 'Language Preferences'))
        title_font = QFont()
        title_font.setPointSize(16)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Language preferences content (no tabs)
        self.language_tab = GeneralPreferencesTab()
        layout.addWidget(self.language_tab)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        button_layout.addStretch()
        
        # Cancel button
        self.cancel_button = QPushButton(tr('common.cancel', 'Cancel'))
        self.cancel_button.clicked.connect(self.close)
        button_layout.addWidget(self.cancel_button)
        
        # Apply button
        self.apply_button = QPushButton(tr('common.apply', 'Apply'))
        self.apply_button.clicked.connect(self._apply_changes)
        button_layout.addWidget(self.apply_button)
        
        # OK button
        self.ok_button = QPushButton(tr('common.ok', 'OK'))
        self.ok_button.setDefault(True)
        self.ok_button.clicked.connect(self._ok_clicked)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
    
    def _apply_changes(self):
        """Apply changes from language tab."""
        try:
            print("Applying language changes...")  # Debug output
            
            # Apply changes from language tab only
            language_changed = self.language_tab.apply_changes()
            
            if language_changed:
                print("Language was changed, scheduling restart dialog...")  # Debug output
                
                # Update status immediately
                self.statusBar().showMessage(
                    tr("preferences.success_message", "Language preference saved"), 
                    3000
                )
                
                # Schedule the dialog to show after a short delay to avoid blocking
                QTimer.singleShot(100, self._show_restart_dialog)
                
                return True
            else:
                print("No language changes to apply")  # Debug output
            
        except Exception as e:
            print(f"Error in _apply_changes: {e}")  # Debug output
            # Show error dialog immediately
            self._show_error_dialog(str(e))
            return False
        
        return False
    
    def _show_restart_dialog(self):
        """Show the restart dialog safely."""
        try:
            QMessageBox.information(
                self,
                tr("preferences.restart_title", "Language Changed"),
                tr("preferences.restart_message", 
                    "Language preference has been saved.\n\n"
                    "Please restart the application to apply the new language.")
            )
        except Exception as e:
            print(f"Error showing restart dialog: {e}")
    
    def _show_error_dialog(self, error_msg: str):
        """Show error dialog safely."""
        try:
            QMessageBox.warning(
                self,
                tr("preferences.error_title", "Error"),
                tr("preferences.error_message", f"Failed to save preferences: {error_msg}")
            )
        except Exception as e:
            print(f"Error showing error dialog: {e}")
    
    def _ok_clicked(self):
        """Handle OK button click."""
        if self._apply_changes():
            self.close()


def show_preference_window(parent=None):
    """
    Convenience function to show the preference window.
    
    Args:
        parent: Parent widget for the window
    
    Returns:
        PreferenceWindow: The preference window instance
    """
    window = PreferenceWindow(parent)
    window.show()
    return window