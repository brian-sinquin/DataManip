"""Configuration management system for DataManip."""

import json
import copy
from pathlib import Path
from typing import Dict, Any, Optional, Union
import threading

from .paths import CONFIG_FILE


class ConfigManager:
    """
    Manages application configuration loaded from config.json.
    
    This class provides a centralized way to manage application settings
    with support for nested configuration values using dot notation.
    """

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to the config file. If None, uses default location.
        """
        self._lock = threading.Lock()
        
        if config_file is None:
            # Use centralized path definition
            self.config_file = CONFIG_FILE
        else:
            self.config_file = config_file
            
        self._config: Dict[str, Any] = {}
        self._defaults: Dict[str, Any] = {
            "lang": "en_US",
        }
        
        self.load_config()

    def load_config(self) -> bool:
        """
        Load configuration from the config file.
        
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            try:
                if self.config_file.exists():
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        self._config = json.load(f)
                else:
                    # Create config file with defaults if it doesn't exist
                    self._config = self._defaults.copy()
                    self.save_config()
                    
                # Ensure all default values exist
                self._merge_defaults()
                return True
                
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config file: {e}")
                # Fall back to defaults
                self._config = self._defaults.copy()
                return False

    def save_config(self) -> bool:
        """
        Save the current configuration to the config file.
        
        Returns:
            True if successful, False otherwise
        """
        # Take a snapshot of the config under the lock
        with self._lock:
            config_to_save = copy.deepcopy(self._config)
        
        # Save to disk outside the lock
        try:
            # Ensure the parent directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=4)
            return True
            
        except IOError as e:
            print(f"Error saving config file: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation (e.g., 'window.width')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        # Use a shorter critical section - copy the config data first
        with self._lock:
            config_copy = copy.deepcopy(self._config)
        
        # Parse the key outside the lock
        keys = key.split('.')
        value = config_copy
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value

    def set(self, key: str, value: Any) -> bool:
        """
        Set a configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation
            value: Value to set
            
        Returns:
            True if successful, False otherwise
        """
        # Update the config in memory first
        with self._lock:
            keys = key.split('.')
            config = self._config
            
            # Navigate to the parent of the target key
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                elif not isinstance(config[k], dict):
                    # Can't navigate further, key path is invalid
                    return False
                config = config[k]
            
            # Set the value
            config[keys[-1]] = value
        
        # Save to disk outside the lock to avoid blocking other operations
        return self.save_config()

    def has(self, key: str) -> bool:
        """
        Check if a configuration key exists.
        
        Args:
            key: Configuration key in dot notation
            
        Returns:
            True if key exists, False otherwise
        """
        with self._lock:
            keys = key.split('.')
            value = self._config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return False
            
            return True

    def delete(self, key: str) -> bool:
        """
        Delete a configuration key.
        
        Args:
            key: Configuration key in dot notation
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            keys = key.split('.')
            config = self._config
            
            # Navigate to the parent of the target key
            for k in keys[:-1]:
                if isinstance(config, dict) and k in config:
                    config = config[k]
                else:
                    return False  # Key doesn't exist
            
            # Delete the key if it exists
            if isinstance(config, dict) and keys[-1] in config:
                del config[keys[-1]]
                return self.save_config()
            
            return False

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get an entire configuration section.
        
        Args:
            section: Section name
            
        Returns:
            Dictionary containing the section data
        """
        value = self.get(section, {})
        return value if isinstance(value, dict) else {}

    def reset_to_defaults(self) -> bool:
        """
        Reset configuration to default values.
        
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            self._config = self._defaults.copy()
            return self.save_config()

    def _merge_defaults(self):
        """Merge default values into the configuration, preserving existing values."""
        def merge_dicts(target: dict, source: dict):
            for key, value in source.items():
                if key not in target:
                    target[key] = value
                elif isinstance(value, dict) and isinstance(target[key], dict):
                    merge_dicts(target[key], value)
        
        merge_dicts(self._config, self._defaults)

    def get_language(self) -> str:
        """
        Get the configured language.
        
        Returns:
            Language code (e.g., 'en_US')
        """
        return self.get("lang", "en_US")

    def set_language(self, lang_code: str) -> bool:
        """
        Set the application language.
        
        Args:
            lang_code: Language code to set
            
        Returns:
            True if successful, False otherwise
        """
        return self.set("lang", lang_code)
# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def init_config(config_file: Optional[Path] = None) -> ConfigManager:
    """
    Initialize the global configuration manager.
    
    Args:
        config_file: Path to config file. If None, uses default location.
        
    Returns:
        The initialized configuration manager
    """
    global _config_manager
    _config_manager = ConfigManager(config_file)
    return _config_manager


def get_config() -> ConfigManager:
    """
    Get the global configuration manager instance.
    
    Returns:
        The configuration manager instance
        
    Raises:
        RuntimeError: If configuration manager not initialized
    """
    if _config_manager is None:
        raise RuntimeError("Configuration manager not initialized. Call init_config() first.")
    return _config_manager


def get_config_value(key: str, default: Any = None) -> Any:
    """
    Get a configuration value (convenience function).
    
    Args:
        key: Configuration key in dot notation
        default: Default value if key not found
        
    Returns:
        Configuration value or default
    """
    try:
        return get_config().get(key, default)
    except RuntimeError:
        return default


def set_config_value(key: str, value: Any) -> bool:
    """
    Set a configuration value (convenience function).
    
    Args:
        key: Configuration key in dot notation
        value: Value to set
        
    Returns:
        True if successful, False otherwise
    """
    try:
        return get_config().set(key, value)
    except RuntimeError:
        return False
