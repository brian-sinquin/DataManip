"""Qt model for DataTableStudy."""

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QFont
from typing import Any

from studies.data_table_study import DataTableStudy, ColumnType
from ..shared import format_cell_value, emit_full_model_update
from constants import COLUMN_SYMBOLS


class DataTableModel(QAbstractTableModel):
    """Qt model for DataTableStudy."""
    
    def __init__(self, study: DataTableStudy):
        """Initialize model.
        
        Args:
            study: DataTableStudy to display
        """
        super().__init__()
        self.study = study
    
    def rowCount(self, parent=QModelIndex()) -> int:
        """Get row count."""
        if parent.isValid():
            return 0
        return len(self.study.table.data)
    
    def columnCount(self, parent=QModelIndex()) -> int:
        """Get column count."""
        if parent.isValid():
            return 0
        return len(self.study.table.columns)
    
    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> Any:  # type: ignore
        """Get cell data.
        
        Args:
            index: Cell index
            role: Data role
            
        Returns:
            Cell value or None
        """
        if not index.isValid():
            return None
        
        value = self.study.table.data.iloc[index.row(), index.column()]
        
        if role == Qt.DisplayRole:  # type: ignore
            # Format for display with limited precision
            return format_cell_value(value)
        
        if role == Qt.EditRole:  # type: ignore
            # Return full precision value for editing
            if value is None or (isinstance(value, float) and value != value):  # NaN
                return ""
            return str(value)
        
        return None
    
    def setData(self, index: QModelIndex, value: Any, role=Qt.EditRole) -> bool:  # type: ignore
        """Set cell data.
        
        Args:
            index: Cell index
            value: New value
            role: Data role
            
        Returns:
            True if successful
        """
        if not index.isValid() or role != Qt.EditRole:  # type: ignore
            return False
        
        col_name = self.study.table.columns[index.column()]
        
        # Check if column is editable
        col_type = self.study.get_column_type(col_name)
        if col_type == ColumnType.DATA:
            pass  # Always editable
        elif col_type == ColumnType.UNCERTAINTY:
            # Only manual uncertainty columns are editable
            col_meta = self.study.column_metadata.get(col_name, {})
            ref_col = col_meta.get("uncertainty_reference")
            if ref_col and ref_col in self.study.column_metadata:
                if self.study.column_metadata[ref_col].get("propagate_uncertainty", False):
                    return False  # Auto-propagated uncertainty - not editable
        else:
            return False  # Can't edit calculated/derivative/range columns
        
        # Convert and set value
        try:
            if value == "":
                value = None
            else:
                value = float(value)
            
            # Track undo for data edits
            row = index.row()
            col = index.column()
            old_value = self.study.table.data.iloc[row, col]
            
            # Only track if value actually changed
            if old_value != value:
                from core.undo_manager import UndoAction, ActionType
                
                def undo_edit():
                    self.study.table.data.iloc[row, col] = old_value
                    self.study.on_data_changed(col_name)
                    emit_full_model_update(self)
                
                def redo_edit():
                    self.study.table.data.iloc[row, col] = value
                    self.study.on_data_changed(col_name)
                    emit_full_model_update(self)
                
                action = UndoAction(
                    action_type=ActionType.MODIFY_DATA,
                    undo_func=undo_edit,
                    redo_func=redo_edit,
                    description=f"Edit cell [{row+1}, {col_name}]"
                )
                self.study.undo_manager.push(action)
            
            self.study.table.data.iloc[row, col] = value
            
            # Trigger recalculation
            self.study.on_data_changed(col_name)
            
            # Emit data changed for entire table (dependent columns may have changed)
            emit_full_model_update(self)
            
            return True
        except (ValueError, TypeError):
            return False
    
    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole) -> Any:  # type: ignore
        """Get header data.
        
        Args:
            section: Row/column index
            orientation: Horizontal or vertical
            role: Data role
            
        Returns:
            Header value or None
        """
        if role == Qt.DisplayRole:  # type: ignore
            if orientation == Qt.Horizontal:  # type: ignore
                if section < len(self.study.table.columns):
                    col_name = self.study.table.columns[section]
                    col_type = self.study.get_column_type(col_name)
                    symbol = COLUMN_SYMBOLS.get(col_type, "")
                    
                    # Show column name with type symbol
                    header = f"{symbol} {col_name}" if symbol else col_name
                    
                    # Add unit if present
                    unit = self.study.get_column_unit(col_name)
                    if unit:
                        header += f" [{unit}]"
                    
                    return header
            else:
                return str(section + 1)
        
        # Bold font for headers
        if role == Qt.FontRole and orientation == Qt.Horizontal:  # type: ignore
            font = QFont()
            font.setBold(True)
            return font
        
        # Tooltip with column info
        if role == Qt.ToolTipRole and orientation == Qt.Horizontal:  # type: ignore
            if section < len(self.study.table.columns):
                col_name = self.study.table.columns[section]
                col_type = self.study.get_column_type(col_name)
                
                symbol = COLUMN_SYMBOLS.get(col_type, "")
                type_display = f"{symbol} {col_type.upper()}" if symbol else col_type.upper()
                tooltip = f"Column: {col_name}\nType: {type_display}"
                
                # Add type-specific info
                col_meta = self.study.column_metadata.get(col_name, {})
                if col_type == "calculated":
                    formula = col_meta.get("formula", "")
                    tooltip += f"\nFormula: {formula}"
                elif col_type == "derivative":
                    derivative_of = col_meta.get("derivative_of", "")
                    order = col_meta.get("derivative_order", 1)
                    tooltip += f"\nDerivative of: {derivative_of}\nOrder: {order}"
                elif col_type == "range":
                    range_type = col_meta.get("range_type", "")
                    tooltip += f"\nRange type: {range_type}"
                elif col_type == "uncertainty":
                    ref_col = col_meta.get("uncertainty_reference")
                    if ref_col:
                        tooltip += f"\nUncertainty for: {ref_col}"
                        # Show propagated formula if auto-created
                        if ref_col in self.study.column_metadata:
                            ref_meta = self.study.column_metadata[ref_col]
                            if ref_meta.get("propagate_uncertainty"):
                                formula = ref_meta.get("formula", "")
                                if formula:
                                    tooltip += f"\n\nPropagated from: {formula}"
                                    # Try to show simplified formula
                                    try:
                                        deps = self.study.formula_engine.extract_dependencies(formula)
                                        has_uncert = [d for d in deps if f"{d}_u" in self.study.table.columns]
                                        if has_uncert:
                                            tooltip += f"\nContributions from: {', '.join([f'δ{d}' for d in has_uncert])}"
                                    except:
                                        pass
                
                unit = self.study.get_column_unit(col_name)
                if unit:
                    tooltip += f"\nUnit: {unit}"
                
                return tooltip
        
        return None
    
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:  # type: ignore
        """Get cell flags.
        
        Args:
            index: Cell index
            
        Returns:
            Item flags
        """
        if not index.isValid():
            return Qt.NoItemFlags  # type: ignore
        
        col_name = self.study.table.columns[index.column()]
        col_type = self.study.get_column_type(col_name)
        
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable  # type: ignore
        
        # Data columns are always editable
        # Uncertainty columns are editable only if manually created (not auto-propagated)
        if col_type == ColumnType.DATA:
            flags |= Qt.ItemIsEditable  # type: ignore
        elif col_type == ColumnType.UNCERTAINTY:
            # Check if this is an auto-propagated uncertainty column
            col_meta = self.study.column_metadata.get(col_name, {})
            ref_col = col_meta.get("uncertainty_reference")
            # If referenced column has propagate_uncertainty=True, this is auto-created
            if ref_col and ref_col in self.study.column_metadata:
                if not self.study.column_metadata[ref_col].get("propagate_uncertainty", False):
                    # Manual uncertainty column - editable
                    flags |= Qt.ItemIsEditable  # type: ignore
            else:
                # No reference or orphaned - treat as manual, editable
                flags |= Qt.ItemIsEditable  # type: ignore
        
        return flags
