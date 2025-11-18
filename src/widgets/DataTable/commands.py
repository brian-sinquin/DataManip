"""
Command pattern for undo/redo functionality.

This module implements the Command pattern for undoable/redoable operations
on the DataTableModel. Each operation (edit cell, paste, clear, etc.) is
encapsulated in a Command object that knows how to execute and undo itself.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, TYPE_CHECKING
import pandas as pd
import numpy as np

if TYPE_CHECKING:
    from .model import DataTableModel


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


class SetCellValueCommand(Command):
    """Command to set a single cell value."""
    
    def __init__(self, model: 'DataTableModel', row: int, col: int, new_value: Any):
        """Initialize command.
        
        Args:
            model: DataTableModel instance
            row: Row index
            col: Column index
            new_value: Value to set
        """
        self.model = model
        self.row = row
        self.col = col
        self.new_value = new_value
        self.old_value: Optional[Any] = None
    
    def execute(self) -> None:
        """Set the cell value and store the old value."""
        # Get old value
        col_name = self.model._column_order[self.col]
        self.old_value = self.model._columns[col_name].iloc[self.row]
        
        # Set new value (bypass command system to avoid infinite recursion)
        self.model._columns[col_name].iloc[self.row] = self.new_value
        
        # Emit dataChanged signal
        idx = self.model.index(self.row, self.col)
        self.model.dataChanged.emit(idx, idx)
        
        # Trigger recalculation if needed
        if self.model._config.auto_recalculate:
            recalc_cols = self.model._get_recalculation_order(col_name)
            if recalc_cols:
                self.model.calculationStarted.emit()
                for col in recalc_cols:
                    self.model._recalculate_column(col)
                self.model.calculationFinished.emit()
    
    def undo(self) -> None:
        """Restore the old cell value."""
        col_name = self.model._column_order[self.col]
        self.model._columns[col_name].iloc[self.row] = self.old_value
        
        # Emit dataChanged signal
        idx = self.model.index(self.row, self.col)
        self.model.dataChanged.emit(idx, idx)
        
        # Trigger recalculation if needed
        if self.model._config.auto_recalculate:
            recalc_cols = self.model._get_recalculation_order(col_name)
            if recalc_cols:
                self.model.calculationStarted.emit()
                for col in recalc_cols:
                    self.model._recalculate_column(col)
                self.model.calculationFinished.emit()
        # Emit dataChanged signal
        idx = self.model.index(self.row, self.col)
        self.model.dataChanged.emit(idx, idx)
    
    def get_description(self) -> str:
        return f"Edit Cell ({self.row}, {self.col})"


class PasteCommand(Command):
    """Command to paste multiple cells from TSV data."""
    
    def __init__(
        self,
        model: 'DataTableModel',
        tsv_data: str,
        start_row: int,
        start_col: int,
        skip_readonly: bool = True
    ):
        """Initialize command.
        
        Args:
            model: DataTableModel instance
            tsv_data: Tab-separated values to paste
            start_row: Starting row index
            start_col: Starting column index
            skip_readonly: If True, skip read-only columns
        """
        self.model = model
        self.tsv_data = tsv_data
        self.start_row = start_row
        self.start_col = start_col
        self.skip_readonly = skip_readonly
        self.old_values: dict[tuple[int, int], Any] = {}
    
    def execute(self) -> None:
        """Paste the data and store old values."""
        if not self.tsv_data:
            return
        
        lines = self.tsv_data.strip().split("\n")
        
        for i, line in enumerate(lines):
            values = line.split("\t")
            row = self.start_row + i
            
            if row >= self.model._row_count:
                continue
            
            for j, value in enumerate(values):
                col = self.start_col + j
                
                if col >= len(self.model._column_order):
                    continue
                
                col_name = self.model._column_order[col]
                metadata = self.model._metadata[col_name]
                
                # Skip read-only columns if requested
                if self.skip_readonly and not metadata.editable:
                    continue
                
                # Skip empty values
                if not value.strip():
                    continue
                
                # Store old value
                self.old_values[(row, col)] = self.model._columns[col_name].iloc[row]
                
                # Set new value (using model's type conversion)
                try:
                    if metadata.dtype.value == "float64":
                        new_val = float(value)
                    elif metadata.dtype.value == "int64":
                        new_val = int(float(value))
                    elif metadata.dtype.value == "bool":
                        new_val = value.lower() in ("true", "1", "yes")
                    else:
                        new_val = value
                    
                    self.model._columns[col_name].iloc[row] = new_val
                except (ValueError, TypeError):
                    continue
        
        # Emit signals for changed cells
        if self.old_values:
            min_row = min(row for row, col in self.old_values.keys())
            max_row = max(row for row, col in self.old_values.keys())
            min_col = min(col for row, col in self.old_values.keys())
            max_col = max(col for row, col in self.old_values.keys())
            
            top_left = self.model.index(min_row, min_col)
            bottom_right = self.model.index(max_row, max_col)
            self.model.dataChanged.emit(top_left, bottom_right)
            
            # Trigger recalculation for affected columns
            if self.model._config.auto_recalculate:
                affected_cols = set()
                for row, col in self.old_values.keys():
                    col_name = self.model._column_order[col]
                    affected_cols.add(col_name)
                
                # Get all columns that need recalculation
                all_recalc_cols = set()
                for col_name in affected_cols:
                    recalc_cols = self.model._get_recalculation_order(col_name)
                    all_recalc_cols.update(recalc_cols)
                
                if all_recalc_cols:
                    self.model.calculationStarted.emit()
                    for col in all_recalc_cols:
                        self.model._recalculate_column(col)
                    self.model.calculationFinished.emit()
    
    def undo(self) -> None:
        """Restore all old cell values."""
        for (row, col), old_value in self.old_values.items():
            col_name = self.model._column_order[col]
            self.model._columns[col_name].iloc[row] = old_value
        
        # Emit signals
        if self.old_values:
            min_row = min(row for row, col in self.old_values.keys())
            max_row = max(row for row, col in self.old_values.keys())
            min_col = min(col for row, col in self.old_values.keys())
            max_col = max(col for row, col in self.old_values.keys())
            
            top_left = self.model.index(min_row, min_col)
            bottom_right = self.model.index(max_row, max_col)
            self.model.dataChanged.emit(top_left, bottom_right)
            
            # Trigger recalculation for affected columns
            if self.model._config.auto_recalculate:
                affected_cols = set()
                for row, col in self.old_values.keys():
                    col_name = self.model._column_order[col]
                    affected_cols.add(col_name)
                
                # Get all columns that need recalculation
                all_recalc_cols = set()
                for col_name in affected_cols:
                    recalc_cols = self.model._get_recalculation_order(col_name)
                    all_recalc_cols.update(recalc_cols)
                
                if all_recalc_cols:
                    self.model.calculationStarted.emit()
                    for col in all_recalc_cols:
                        self.model._recalculate_column(col)
                    self.model.calculationFinished.emit()
    
    def get_description(self) -> str:
        return f"Paste {len(self.old_values)} cells"


class ClearSelectionCommand(Command):
    """Command to clear selected cells."""
    
    def __init__(self, model: 'DataTableModel', selection: list[tuple[int, int]]):
        """Initialize command.
        
        Args:
            model: DataTableModel instance
            selection: List of (row, col) tuples to clear
        """
        self.model = model
        self.selection = selection
        self.old_values: dict[tuple[int, int], Any] = {}
    
    def execute(self) -> None:
        """Clear cells and store old values."""
        for row, col in self.selection:
            if col >= len(self.model._column_order):
                continue
            
            col_name = self.model._column_order[col]
            metadata = self.model._metadata[col_name]
            
            # Skip read-only columns
            if not metadata.editable:
                continue
            
            # Store old value
            self.old_values[(row, col)] = self.model._columns[col_name].iloc[row]
            
            # Set appropriate empty value
            if metadata.dtype.value in ("float64", "int64"):
                self.model._columns[col_name].iloc[row] = np.nan
            else:
                self.model._columns[col_name].iloc[row] = ""
        
        # Emit signals
        if self.old_values:
            min_row = min(row for row, col in self.old_values.keys())
            max_row = max(row for row, col in self.old_values.keys())
            min_col = min(col for row, col in self.old_values.keys())
            max_col = max(col for row, col in self.old_values.keys())
            
            top_left = self.model.index(min_row, min_col)
            bottom_right = self.model.index(max_row, max_col)
            self.model.dataChanged.emit(top_left, bottom_right)
            
            # Trigger recalculation for affected columns
            if self.model._config.auto_recalculate:
                affected_cols = set()
                for row, col in self.old_values.keys():
                    col_name = self.model._column_order[col]
                    affected_cols.add(col_name)
                
                # Get all columns that need recalculation
                all_recalc_cols = set()
                for col_name in affected_cols:
                    recalc_cols = self.model._get_recalculation_order(col_name)
                    all_recalc_cols.update(recalc_cols)
                
                if all_recalc_cols:
                    self.model.calculationStarted.emit()
                    for col in all_recalc_cols:
                        self.model._recalculate_column(col)
                    self.model.calculationFinished.emit()
    
    def undo(self) -> None:
        """Restore all cleared cells."""
        for (row, col), old_value in self.old_values.items():
            col_name = self.model._column_order[col]
            self.model._columns[col_name].iloc[row] = old_value
        
        # Emit signals
        if self.old_values:
            min_row = min(row for row, col in self.old_values.keys())
            max_row = max(row for row, col in self.old_values.keys())
            min_col = min(col for row, col in self.old_values.keys())
            max_col = max(col for row, col in self.old_values.keys())
            
            top_left = self.model.index(min_row, min_col)
            bottom_right = self.model.index(max_row, max_col)
            self.model.dataChanged.emit(top_left, bottom_right)
            
            # Trigger recalculation for affected columns
            if self.model._config.auto_recalculate:
                affected_cols = set()
                for row, col in self.old_values.keys():
                    col_name = self.model._column_order[col]
                    affected_cols.add(col_name)
                
                # Get all columns that need recalculation
                all_recalc_cols = set()
                for col_name in affected_cols:
                    recalc_cols = self.model._get_recalculation_order(col_name)
                    all_recalc_cols.update(recalc_cols)
                
                if all_recalc_cols:
                    self.model.calculationStarted.emit()
                    for col in all_recalc_cols:
                        self.model._recalculate_column(col)
                    self.model.calculationFinished.emit()
    
    def get_description(self) -> str:
        return f"Clear {len(self.old_values)} cells"


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
        """Check if undo is available.
        
        Returns:
            True if there are commands to undo
        """
        return len(self._undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is available.
        
        Returns:
            True if there are commands to redo
        """
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
        """Get description of next undo command.
        
        Returns:
            Description string or None if undo stack is empty
        """
        if self._undo_stack:
            return self._undo_stack[-1].get_description()
        return None
    
    def get_redo_description(self) -> Optional[str]:
        """Get description of next redo command.
        
        Returns:
            Description string or None if redo stack is empty
        """
        if self._redo_stack:
            return self._redo_stack[-1].get_description()
        return None
