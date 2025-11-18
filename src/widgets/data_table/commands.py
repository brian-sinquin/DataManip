"""
DataTable-specific Command implementations.

This module implements concrete Command classes for DataTable operations
like editing cells, pasting data, and clearing selections.
"""

from typing import Any, Optional, TYPE_CHECKING, Set
import numpy as np

from utils.commands import Command

if TYPE_CHECKING:
    from .model import DataTableModel


def _emit_changes_and_recalc(
    model: 'DataTableModel',
    affected_cells: dict[tuple[int, int], Any]
) -> None:
    """Helper to emit dataChanged signals and trigger recalculation.
    
    Args:
        model: DataTableModel instance
        affected_cells: Dictionary of (row, col) -> value that were changed
    """
    if not affected_cells:
        return
    
    # Emit dataChanged signal for changed region
    min_row = min(row for row, col in affected_cells.keys())
    max_row = max(row for row, col in affected_cells.keys())
    min_col = min(col for row, col in affected_cells.keys())
    max_col = max(col for row, col in affected_cells.keys())
    
    top_left = model.index(min_row, min_col)
    bottom_right = model.index(max_row, max_col)
    model.dataChanged.emit(top_left, bottom_right)
    
    # Trigger recalculation for affected columns
    if model._config.auto_recalculate:
        affected_cols: Set[str] = set()
        for row, col in affected_cells.keys():
            col_name = model._column_order[col]
            affected_cols.add(col_name)
        
        # Get all columns that need recalculation
        all_recalc_cols: Set[str] = set()
        for col_name in affected_cols:
            recalc_cols = model._get_recalculation_order(col_name)
            all_recalc_cols.update(recalc_cols)
        
        if all_recalc_cols:
            model.calculationStarted.emit()
            for col in all_recalc_cols:
                model._recalculate_column(col)
            model.calculationFinished.emit()


class SetCellValueCommand(Command):
    """Command to set a single cell value."""
    
    def __init__(self, model: 'DataTableModel', row: int, col: int, new_value: Any):
        self.model = model
        self.row = row
        self.col = col
        self.new_value = new_value
        self.old_value: Optional[Any] = None
    
    def execute(self) -> None:
        """Set the cell value and store the old value."""
        col_name = self.model._column_order[self.col]
        self.old_value = self.model._columns[col_name].iloc[self.row]
        self.model._columns[col_name].iloc[self.row] = self.new_value
        _emit_changes_and_recalc(self.model, {(self.row, self.col): self.new_value})
    
    def undo(self) -> None:
        """Restore the old cell value."""
        col_name = self.model._column_order[self.col]
        self.model._columns[col_name].iloc[self.row] = self.old_value
        _emit_changes_and_recalc(self.model, {(self.row, self.col): self.old_value})
    
    def get_description(self) -> str:
        return f"Edit Cell ({self.row}, {self.col})"


class PasteCommand(Command):
    """Command to paste multiple cells from TSV data."""
    
    def __init__(self, model: 'DataTableModel', tsv_data: str, start_row: int, 
                 start_col: int, skip_readonly: bool = True):
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
        
        _emit_changes_and_recalc(self.model, self.old_values)
    
    def undo(self) -> None:
        """Restore all old cell values."""
        for (row, col), old_value in self.old_values.items():
            col_name = self.model._column_order[col]
            self.model._columns[col_name].iloc[row] = old_value
        
        _emit_changes_and_recalc(self.model, self.old_values)
    
    def get_description(self) -> str:
        return f"Paste {len(self.old_values)} cells"


class ClearSelectionCommand(Command):
    """Command to clear selected cells."""
    
    def __init__(self, model: 'DataTableModel', selection: list[tuple[int, int]]):
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
        
        _emit_changes_and_recalc(self.model, self.old_values)
    
    def undo(self) -> None:
        """Restore all cleared cells."""
        for (row, col), old_value in self.old_values.items():
            col_name = self.model._column_order[col]
            self.model._columns[col_name].iloc[row] = old_value
        
        _emit_changes_and_recalc(self.model, self.old_values)
    
    def get_description(self) -> str:
        return f"Clear {len(self.old_values)} cells"