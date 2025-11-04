"""Language and translation utilities for DataManip."""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class LanguageManager:
    """Manages application translations and language switching."""

    def __init__(self, lang_code: str = "en_US"):
        """
        Initialize the language manager.
        
        Args:
            lang_code: Language code (e.g., 'en_US', 'fr_FR')
        """
        self.lang_code = lang_code
        self.translations: Dict[str, Any] = {}
        # Go up from src/utils to project root, then to assets/lang
        self.lang_dir = Path(__file__).parent.parent.parent / "assets" / "lang"
        self.load_language(lang_code)

    def load_language(self, lang_code: str) -> bool:
        """
        Load translations for the specified language.
        
        Args:
            lang_code: Language code to load
            
        Returns:
            True if successful, False otherwise
        """
        lang_file = self.lang_dir / f"{lang_code}.json"
        
        if not lang_file.exists():
            print(f"Language file not found: {lang_file}")
            # Try to load English as fallback
            lang_file = self.lang_dir / "en_US.json"
            if not lang_file.exists():
                print("Fallback language (en_US) not found!")
                return False
        
        try:
            with open(lang_file, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
            self.lang_code = lang_code
            return True
        except Exception as e:
            print(f"Error loading language file: {e}")
            return False

    def get(self, key: str, default: str = "") -> str:
        """
        Get a translation by key using dot notation.
        
        Args:
            key: Translation key in dot notation (e.g., 'menu.file')
            default: Default value if key not found
            
        Returns:
            Translated string or default value
        """
        keys = key.split('.')
        value = self.translations
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default or key
        
        return str(value) if value is not None else default

    def get_available_languages(self) -> list:
        """
        Get list of available language codes.
        
        Returns:
            List of language codes
        """
        if not self.lang_dir.exists():
            return []
        
        languages = []
        for file in self.lang_dir.glob("*.json"):
            languages.append(file.stem)
        return sorted(languages)

    def switch_language(self, lang_code: str) -> bool:
        """
        Switch to a different language.
        
        Args:
            lang_code: Language code to switch to
            
        Returns:
            True if successful, False otherwise
        """
        return self.load_language(lang_code)


# Global language manager instance
_lang_manager: Optional[LanguageManager] = None


def init_language(lang_code: str = "en_US") -> LanguageManager:
    """
    Initialize the global language manager.
    
    Args:
        lang_code: Language code to use
        
    Returns:
        The initialized language manager
    """
    global _lang_manager
    _lang_manager = LanguageManager(lang_code)
    return _lang_manager


def get_lang_manager() -> LanguageManager:
    """
    Get the global language manager instance.
    
    Returns:
        The language manager instance
        
    Raises:
        RuntimeError: If language manager not initialized
    """
    if _lang_manager is None:
        raise RuntimeError("Language manager not initialized. Call init_language() first.")
    return _lang_manager


def tr(key: str, default: str = "") -> str:
    """
    Translate a key to the current language.
    
    This is a convenience function for quick translations.
    
    Args:
        key: Translation key in dot notation
        default: Default value if key not found
        
    Returns:
        Translated string
    """
    try:
        return get_lang_manager().get(key, default)
    except RuntimeError:
        return default or key
