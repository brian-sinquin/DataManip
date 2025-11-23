"""Undo/Redo system for DataManip operations."""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class ActionType(Enum):
    """Types of undoable actions."""
    ADD_COLUMN = "add_column"
    REMOVE_COLUMN = "remove_column"
    RENAME_COLUMN = "rename_column"
    ADD_ROWS = "add_rows"
    REMOVE_ROWS = "remove_rows"
    MODIFY_DATA = "modify_data"
    ADD_CONSTANT = "add_constant"
    REMOVE_CONSTANT = "remove_constant"
    MODIFY_CONSTANT = "modify_constant"
    ADD_FUNCTION = "add_function"
    REMOVE_FUNCTION = "remove_function"
    MODIFY_FUNCTION = "modify_function"


@dataclass
class UndoAction:
    """Represents a single undoable action.
    
    Attributes:
        action_type: Type of action performed
        undo_func: Function to undo the action
        redo_func: Function to redo the action
        description: Human-readable description
        state_before: Optional state before action
        state_after: Optional state after action
    """
    action_type: ActionType
    undo_func: Callable
    redo_func: Callable
    description: str
    state_before: Optional[Dict[str, Any]] = None
    state_after: Optional[Dict[str, Any]] = None


class UndoManager:
    """Manager for undo/redo operations.
    
    Maintains undo and redo stacks with configurable history limit.
    """
    
    def __init__(self, max_history: int = 50):
        """Initialize undo manager.
        
        Args:
            max_history: Maximum number of actions to keep in history
        """
        self.max_history = max_history
        self.undo_stack: List[UndoAction] = []
        self.redo_stack: List[UndoAction] = []
        self._enabled = True
    
    def push(self, action: UndoAction):
        """Push action onto undo stack.
        
        Args:
            action: Action to add to undo history
        """
        if not self._enabled:
            return
        
        # Add to undo stack
        self.undo_stack.append(action)
        
        # Clear redo stack (new action invalidates redo history)
        self.redo_stack.clear()
        
        # Limit stack size
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
    
    def undo(self) -> bool:
        """Undo last action.
        
        Returns:
            True if action was undone, False if nothing to undo
        """
        if not self.can_undo():
            return False
        
        action = self.undo_stack.pop()
        
        # Execute undo
        try:
            action.undo_func()
            self.redo_stack.append(action)
            return True
        except Exception as e:
            # If undo fails, restore to undo stack
            self.undo_stack.append(action)
            raise RuntimeError(f"Undo failed: {e}") from e
    
    def redo(self) -> bool:
        """Redo last undone action.
        
        Returns:
            True if action was redone, False if nothing to redo
        """
        if not self.can_redo():
            return False
        
        action = self.redo_stack.pop()
        
        # Execute redo
        try:
            action.redo_func()
            self.undo_stack.append(action)
            return True
        except Exception as e:
            # If redo fails, restore to redo stack
            self.redo_stack.append(action)
            raise RuntimeError(f"Redo failed: {e}") from e
    
    def can_undo(self) -> bool:
        """Check if undo is available.
        
        Returns:
            True if there are actions to undo
        """
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is available.
        
        Returns:
            True if there are actions to redo
        """
        return len(self.redo_stack) > 0
    
    def get_undo_description(self) -> Optional[str]:
        """Get description of next undo action.
        
        Returns:
            Description string or None if no undo available
        """
        if self.can_undo():
            return self.undo_stack[-1].description
        return None
    
    def get_redo_description(self) -> Optional[str]:
        """Get description of next redo action.
        
        Returns:
            Description string or None if no redo available
        """
        if self.can_redo():
            return self.redo_stack[-1].description
        return None
    
    def clear(self):
        """Clear all undo/redo history."""
        self.undo_stack.clear()
        self.redo_stack.clear()
    
    def set_enabled(self, enabled: bool):
        """Enable or disable undo tracking.
        
        Args:
            enabled: Whether to track actions
        """
        self._enabled = enabled
    
    def is_enabled(self) -> bool:
        """Check if undo tracking is enabled.
        
        Returns:
            True if enabled
        """
        return self._enabled
    
    def get_undo_count(self) -> int:
        """Get number of undoable actions.
        
        Returns:
            Number of actions in undo stack
        """
        return len(self.undo_stack)
    
    def get_redo_count(self) -> int:
        """Get number of redoable actions.
        
        Returns:
            Number of actions in redo stack
        """
        return len(self.redo_stack)
    
    def get_history(self, limit: int = 10) -> List[str]:
        """Get recent action history.
        
        Args:
            limit: Maximum number of actions to return
        
        Returns:
            List of action descriptions (most recent first)
        """
        return [action.description for action in reversed(self.undo_stack[-limit:])]


class UndoContext:
    """Context manager for disabling undo tracking temporarily.
    
    Example:
        with UndoContext(undo_manager, enabled=False):
            # Operations here won't be tracked
            study.add_column("temp")
    """
    
    def __init__(self, undo_manager: UndoManager, enabled: bool = False):
        """Initialize undo context.
        
        Args:
            undo_manager: Manager to modify
            enabled: Whether undo should be enabled in context
        """
        self.undo_manager = undo_manager
        self.enabled = enabled
        self.previous_state = None
    
    def __enter__(self):
        """Enter context."""
        self.previous_state = self.undo_manager.is_enabled()
        self.undo_manager.set_enabled(self.enabled)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        self.undo_manager.set_enabled(self.previous_state)
        return False
