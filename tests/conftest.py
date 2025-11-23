"""Pytest configuration and shared fixtures."""

import pytest
from unittest.mock import Mock, MagicMock


@pytest.fixture(autouse=True)
def mock_language_manager(request, monkeypatch):
    """Mock language manager to prevent file I/O in tests.
    
    Skip mocking for tests in the utils.test_lang module.
    """
    # Don't mock if we're testing the language module itself
    if 'test_lang' in request.node.nodeid:
        return None
    
    mock_manager = Mock()
    mock_manager.get_available_languages.return_value = ['en_US', 'fr_FR']
    mock_manager.get_language_name.side_effect = lambda code: {
        'en_US': 'English (US)',
        'fr_FR': 'Français (France)'
    }.get(code, code)
    mock_manager.get.return_value = ""
    mock_manager.lang_code = "en_US"
    
    # Mock the module-level functions
    mock_get_lang_manager = MagicMock(return_value=mock_manager)
    mock_tr = MagicMock(side_effect=lambda key, default=None: default or key)
    mock_set_language = MagicMock()
    mock_get_current_language = MagicMock(return_value="en_US")
    mock_init_language = MagicMock()
    
    # Patch the module
    monkeypatch.setattr("utils.lang.get_lang_manager", mock_get_lang_manager)
    monkeypatch.setattr("utils.lang.tr", mock_tr)
    monkeypatch.setattr("utils.lang.set_language", mock_set_language)
    monkeypatch.setattr("utils.lang.get_current_language", mock_get_current_language)
    monkeypatch.setattr("utils.lang.init_language", mock_init_language)
    
    return mock_manager
