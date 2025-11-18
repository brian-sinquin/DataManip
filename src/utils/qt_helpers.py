"""
Qt helper utilities for common UI patterns.

This module provides reusable helper functions for PyQt/PySide applications
to reduce boilerplate code.
"""

from typing import Callable, Optional
from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction


def add_action(
    menu: QMenu,
    text: str,
    callback: Callable,
    tooltip: Optional[str] = None,
    enabled: bool = True
) -> QAction:
    """Add an action to a menu with less boilerplate.
    
    Args:
        menu: Menu to add action to
        text: Action text
        callback: Function to call when triggered
        tooltip: Optional tooltip text
        enabled: Whether action is enabled
        
    Returns:
        Created QAction
        
    Example:
        >>> menu = QMenu()
        >>> add_action(menu, "Copy", lambda: print("copied"))
        >>> add_action(menu, "Paste", paste_func, "Paste from clipboard")
    """
    action = QAction(text, menu)
    action.triggered.connect(callback)
    
    if tooltip:
        action.setToolTip(tooltip)
    
    action.setEnabled(enabled)
    menu.addAction(action)
    
    return action


def add_actions(
    menu: QMenu,
    actions: list[tuple[str, Callable, Optional[str]]]
) -> list[QAction]:
    """Add multiple actions to a menu at once.
    
    Args:
        menu: Menu to add actions to
        actions: List of (text, callback, tooltip) tuples
        
    Returns:
        List of created QActions
        
    Example:
        >>> menu = QMenu()
        >>> add_actions(menu, [
        ...     ("Copy", copy_func, "Copy selection"),
        ...     ("Paste", paste_func, "Paste from clipboard"),
        ...     ("Clear", clear_func, None)
        ... ])
    """
    created_actions = []
    for item in actions:
        text, callback = item[0], item[1]
        tooltip = item[2] if len(item) > 2 else None
        action = add_action(menu, text, callback, tooltip)
        created_actions.append(action)
    
    return created_actions


def add_separator(menu: QMenu) -> None:
    """Add a separator to a menu (for consistency with add_action).
    
    Args:
        menu: Menu to add separator to
    """
    menu.addSeparator()
