"""Language selection dialog for DataManip."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QMessageBox,
)
from PySide6.QtCore import Qt

from utils.lang import get_lang_manager


class LanguageDialog(QDialog):
    """Dialog for selecting application language."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.lang = get_lang_manager()
        self.selected_language = self.lang.lang_code
        self.language_changed = False
        
        self.setWindowTitle(self.lang.get("language.dialog_title", "Language Selection"))
        self.setMinimumWidth(400)
        self.setModal(True)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title label
        title_label = QLabel(self.lang.get("language.select_language", "Select Language:"))
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Description label
        description = QLabel(
            self.lang.get(
                "language.restart_required",
                "The application will need to restart for the language change to take full effect."
            )
        )
        description.setWordWrap(True)
        description.setStyleSheet("margin-bottom: 15px;")
        layout.addWidget(description)
        
        # Language selection
        lang_layout = QHBoxLayout()
        
        lang_label = QLabel(self.lang.get("language.language", "Language:"))
        lang_layout.addWidget(lang_label)
        
        self.language_combo = QComboBox()
        
        # Language mapping
        self.language_map = {
            "en_US": "English (US)",
            "fr_FR": "Français (France)",
        }
        
        # Populate combo box with available languages
        available_langs = self.lang.get_available_languages()
        for lang_code in available_langs:
            display_name = self.language_map.get(lang_code, lang_code)
            self.language_combo.addItem(display_name, lang_code)
        
        # Set current language as selected
        current_index = self.language_combo.findData(self.lang.lang_code)
        if current_index >= 0:
            self.language_combo.setCurrentIndex(current_index)
        
        lang_layout.addWidget(self.language_combo)
        layout.addLayout(lang_layout)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton(self.lang.get("common.cancel", "Cancel"))
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.apply_button = QPushButton(self.lang.get("common.apply", "Apply"))
        self.apply_button.setDefault(True)
        self.apply_button.clicked.connect(self._apply_language)
        button_layout.addWidget(self.apply_button)
        
        layout.addLayout(button_layout)
    
    def _apply_language(self):
        """Apply the selected language."""
        selected_lang = self.language_combo.currentData()
        
        if selected_lang != self.lang.lang_code:
            # Switch language
            if self.lang.switch_language(selected_lang):
                self.selected_language = selected_lang
                self.language_changed = True
                
                # Show confirmation
                QMessageBox.information(
                    self,
                    self.lang.get("language.success_title", "Language Changed"),
                    self.lang.get(
                        "language.success_message",
                        "Language has been changed. Please restart the application for all changes to take effect."
                    ),
                )
                self.accept()
            else:
                QMessageBox.warning(
                    self,
                    self.lang.get("language.error_title", "Error"),
                    self.lang.get(
                        "language.error_message",
                        "Failed to change language. Please try again."
                    ),
                )
        else:
            self.reject()
    
    def get_selected_language(self):
        """Get the selected language code."""
        return self.selected_language
