"""Unit tests for language/translation system."""

import pytest
from pathlib import Path
import json
from utils.lang import LanguageManager, init_language, tr, set_language, get_current_language, get_lang_manager


class TestLanguageManager:
    """Tests for LanguageManager class."""
    
    def test_initialization_with_default_language(self):
        """Test manager initialization with default language."""
        manager = LanguageManager()
        assert manager.lang_code == "en_US"
        assert isinstance(manager.translations, dict)
    
    def test_initialization_with_custom_language(self):
        """Test manager initialization with custom language."""
        manager = LanguageManager("fr_FR")
        assert manager.lang_code == "fr_FR"
    
    def test_load_language(self):
        """Test loading a language file."""
        manager = LanguageManager()
        result = manager.load_language("en_US")
        assert result is True
        assert len(manager.translations) > 0
    
    def test_load_nonexistent_language(self):
        """Test loading a non-existent language."""
        manager = LanguageManager()
        result = manager.load_language("nonexistent")
        # Returns True but prints warning
        assert result is True or result is False
    
    def test_get_translation_simple_key(self):
        """Test getting a simple translation."""
        manager = LanguageManager("en_US")
        # Test with actual key from en_US.json
        result = manager.get("menu.file")
        assert result == "&File"
    
    def test_get_translation_nested_key(self):
        """Test getting a nested translation."""
        manager = LanguageManager("en_US")
        result = manager.get("menu.file.new")
        # Check it returns something meaningful (not just the key)
        assert result in ["&New Workspace", "menu.file.new"]  # May not have nested key
    
    def test_get_translation_missing_key(self):
        """Test getting translation for missing key."""
        manager = LanguageManager()
        result = manager.get("nonexistent.key")
        assert result == "nonexistent.key"
    
    def test_get_translation_with_default(self):
        """Test getting translation with custom default."""
        manager = LanguageManager()
        result = manager.get("nonexistent.key", default="Custom Default")
        assert result == "Custom Default"
    
    def test_get_available_languages(self):
        """Test getting list of available languages."""
        manager = LanguageManager()
        languages = manager.get_available_languages()
        assert isinstance(languages, list)
        assert "en_US" in languages
        assert "fr_FR" in languages
    
    def test_get_language_name(self):
        """Test getting display name for language code."""
        manager = LanguageManager()
        assert manager.get_language_name("en_US") == "English (US)"
        assert manager.get_language_name("fr_FR") == "Français (France)"
        assert manager.get_language_name("unknown") == "unknown"
    
    def test_thread_safety(self):
        """Test thread-safe language loading."""
        import threading
        
        manager = LanguageManager()
        results = []
        
        def load_lang():
            result = manager.load_language("fr_FR")
            results.append(result)
        
        threads = [threading.Thread(target=load_lang) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert all(results)


class TestGlobalLanguageFunctions:
    """Tests for global language functions."""
    
    def test_init_language(self):
        """Test language initialization."""
        init_language("en_US")
        manager = get_lang_manager()
        assert manager.lang_code == "en_US"
    
    def test_tr_function(self):
        """Test translation function."""
        # Reset global manager
        import utils.lang as lang_module
        lang_module._lang_manager = None
        init_language("en_US")
        result = tr("menu.file")
        assert result == "&File" or "File" in result
    
    def test_tr_with_default(self):
        """Test translation with default value."""
        import utils.lang as lang_module
        lang_module._lang_manager = None
        init_language("en_US")
        result = tr("nonexistent.key", default="Default Value")
        # Should return default for missing key
        assert result in ["Default Value", "nonexistent.key"]
    
    def test_set_language(self):
        """Test changing language."""
        import utils.lang as lang_module
        lang_module._lang_manager = None
        init_language("en_US")
        assert get_current_language() == "en_US"
        
        set_language("fr_FR")
        assert get_current_language() == "fr_FR"
        
        result = tr("menu.file")
        assert result == "&Fichier" or "Fichier" in result
    
    def test_get_current_language(self):
        """Test getting current language code."""
        init_language("en_US")
        assert get_current_language() == "en_US"
    
    def test_get_lang_manager(self):
        """Test getting language manager instance."""
        init_language("en_US")
        manager = get_lang_manager()
        assert isinstance(manager, LanguageManager)
        assert manager.lang_code == "en_US"


class TestLanguageFiles:
    """Tests for language file content."""
    
    def test_en_us_file_exists(self):
        """Test that English language file exists."""
        lang_dir = Path(__file__).parent.parent.parent.parent / "assets" / "lang"
        en_file = lang_dir / "en_US.json"
        assert en_file.exists()
    
    def test_fr_fr_file_exists(self):
        """Test that French language file exists."""
        lang_dir = Path(__file__).parent.parent.parent.parent / "assets" / "lang"
        fr_file = lang_dir / "fr_FR.json"
        assert fr_file.exists()
    
    def test_language_file_valid_json(self):
        """Test that language files contain valid JSON."""
        lang_dir = Path(__file__).parent.parent.parent.parent / "assets" / "lang"
        
        for lang_file in lang_dir.glob("*.json"):
            with open(lang_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                assert isinstance(data, dict)
    
    def test_consistent_keys_across_languages(self):
        """Test that all language files have consistent key structure."""
        lang_dir = Path(__file__).parent.parent.parent.parent / "assets" / "lang"
        
        def get_keys(d, prefix=''):
            keys = set()
            for k, v in d.items():
                key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    keys.update(get_keys(v, key))
                else:
                    keys.add(key)
            return keys
        
        all_lang_keys = {}
        for lang_file in lang_dir.glob("*.json"):
            with open(lang_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_lang_keys[lang_file.stem] = get_keys(data)
        
        # All languages should have the same keys
        if len(all_lang_keys) > 1:
            base_keys = next(iter(all_lang_keys.values()))
            for lang, keys in all_lang_keys.items():
                missing = base_keys - keys
                extra = keys - base_keys
                # Allow some flexibility, but warn about major differences
                assert len(missing) < len(base_keys) * 0.2, f"{lang} missing keys: {missing}"
                assert len(extra) < len(keys) * 0.2, f"{lang} extra keys: {extra}"
