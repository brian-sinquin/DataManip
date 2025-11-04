"""Translatable widgets for DataManip - widgets that can update their text based on language changes."""

from PySide6.QtWidgets import QLabel, QPushButton
from PySide6.QtCore import Signal

from utils.lang import get_lang_manager


class TranslatableLabel(QLabel):
    """A QLabel that can automatically update its text when language changes."""
    
    def __init__(self, translation_key: str, default_text: str = "", parent=None):
        """
        Initialize a translatable label.
        
        Args:
            translation_key: The JSON key for translation (e.g., "welcome.title")
            default_text: Default text if translation not found
            parent: Parent widget
        """
        super().__init__(parent)
        self.translation_key = translation_key
        self.default_text = default_text
        self.refresh_text()
    
    def refresh_text(self):
        """Refresh the label text from current language."""
        lang = get_lang_manager()
        self.setText(lang.get(self.translation_key, self.default_text))


class TranslatableButton(QPushButton):
    """A QPushButton that can automatically update its text when language changes."""
    
    def __init__(self, translation_key: str, default_text: str = "", parent=None):
        """
        Initialize a translatable button.
        
        Args:
            translation_key: The JSON key for translation (e.g., "common.ok")
            default_text: Default text if translation not found
            parent: Parent widget
        """
        super().__init__(parent)
        self.translation_key = translation_key
        self.default_text = default_text
        self.refresh_text()
    
    def refresh_text(self):
        """Refresh the button text from current language."""
        lang = get_lang_manager()
        self.setText(lang.get(self.translation_key, self.default_text))


class TranslatableMixin:
    """
    Mixin class to make any widget translatable.
    Add this to custom widgets that need translation support.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._translatable_elements = []
    
    def register_translatable(self, widget, translation_key: str, attribute: str = "text"):
        """
        Register a widget element for translation.
        
        Args:
            widget: The widget to translate
            translation_key: The JSON key for translation
            attribute: The attribute to set (default: "text", could be "toolTip", "statusTip", etc.)
        """
        self._translatable_elements.append({
            'widget': widget,
            'key': translation_key,
            'attribute': attribute
        })
    
    def refresh_translations(self):
        """Refresh all registered translatable elements."""
        lang = get_lang_manager()
        for element in self._translatable_elements:
            widget = element['widget']
            key = element['key']
            attr = element['attribute']
            
            translated_text = lang.get(key, "")
            
            # Set the appropriate attribute
            if hasattr(widget, f'set{attr.capitalize()}'):
                getattr(widget, f'set{attr.capitalize()}')(translated_text)
            elif attr == 'text' and hasattr(widget, 'setText'):
                widget.setText(translated_text)
            elif attr == 'title' and hasattr(widget, 'setTitle'):
                widget.setTitle(translated_text)
