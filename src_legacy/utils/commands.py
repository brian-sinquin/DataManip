"""
Command pattern for undo/redo functionality.

This module implements a reusable Command pattern that can be used across
different widgets and components. Each operation is encapsulated in a Command
object that knows how to execute and undo itself.

Example:
    >>> class MyCommand(Command):
    ...     def execute(self):
    ...         # Do something
    ...         pass
    ...     def undo(self):
    ...         # Undo it
    ...         pass
    >>> 
    >>> manager = CommandManager()
    >>> manager.execute(MyCommand())
    >>> manager.undo()  # Undoes the command
    >>> manager.redo()  # Redoes it
"""

from abc import ABC, abstractmethod
from typing import Optional


class Command(ABC):
    """Base class for undoable commands.
    
    Each command encapsulates a single operation that can be executed,
    undone, and redone. Commands are managed by CommandManager.
    """
    
    @abstractmethod
    def execute(self) -> None:
        """Execute the command.
        
        This method performs the actual operation and stores any information
        needed to undo it later.
        """
        pass
    
    @abstractmethod
    def undo(self) -> None:
        """Undo the command.
        
        This method reverses the operation, restoring the state before execute()
        was called.
        """
        pass
    
    def redo(self) -> None:
        """Redo the command.
        
        By default, just calls execute() again. Override if redo needs
        different behavior than initial execution.
        """
        self.execute()
    
    def get_description(self) -> str:
        """Get human-readable description of this command.
        
        Returns:
            String describing what this command does (e.g., "Edit Cell")
        """
        return self.__class__.__name__


class CommandManager:
    """Manages command history for undo/redo operations.
    
    Maintains two stacks:
    - undo_stack: Commands that can be undone
    - redo_stack: Commands that can be redone
    
    When a new command is executed, it's added to undo_stack and redo_stack
    is cleared. When undo is called, the command is moved from undo_stack to
    redo_stack. When redo is called, it's moved back.
    """
    
    def __init__(self, max_history: int = 100):
        """Initialize command manager.
        
        Args:
            max_history: Maximum number of commands to keep in history
        """
        self.max_history = max_history
        self._undo_stack: list[Command] = []
        self._redo_stack: list[Command] = []
    
    def execute(self, command: Command) -> None:
        """Execute a command and add it to undo history.
        
        Args:
            command: Command to execute
        """
        command.execute()
        self._undo_stack.append(command)
        self._redo_stack.clear()  # Clear redo stack on new action
        
        # Limit history size
        if len(self._undo_stack) > self.max_history:
            self._undo_stack.pop(0)
    
    def undo(self) -> bool:
        """Undo the last command.
        
        Returns:
            True if undo was performed, False if undo stack is empty
        """
        if not self._undo_stack:
            return False
        
        command = self._undo_stack.pop()
        command.undo()
        self._redo_stack.append(command)
        return True
    
    def redo(self) -> bool:
        """Redo the last undone command.
        
        Returns:
            True if redo was performed, False if redo stack is empty
        """
        if not self._redo_stack:
            return False
        
        command = self._redo_stack.pop()
        command.redo()
        self._undo_stack.append(command)
        return True
    
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self._undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self._redo_stack) > 0
    
    def clear(self) -> None:
        """Clear all command history."""
        self._undo_stack.clear()
        self._redo_stack.clear()
    
    def get_undo_count(self) -> int:
        """Get number of commands in undo stack."""
        return len(self._undo_stack)
    
    def get_redo_count(self) -> int:
        """Get number of commands in redo stack."""
        return len(self._redo_stack)
    
    def get_undo_description(self) -> Optional[str]:
        """Get description of next undo command."""
        if self._undo_stack:
            return self._undo_stack[-1].get_description()
        return None
    
    def get_redo_description(self) -> Optional[str]:
        """Get description of next redo command."""
        if self._redo_stack:
            return self._redo_stack[-1].get_description()
        return None
