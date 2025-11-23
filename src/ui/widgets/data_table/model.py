"""Qt model for DataTableStudy."""

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QBrush, QColor, QFont
from typing import Any

from studies.data_table_study import DataTableStudy, ColumnType
from ..shared import format_cell_value, emit_full_model_update
from .constants import COLUMN_SYMBOLS, COLUMN_TEXT_COLORS


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
        
        if role == Qt.DisplayRole or role == Qt.EditRole:  # type: ignore
            value = self.study.table.data.iloc[index.row(), index.column()]
            return format_cell_value(value)
        
        # Foreground color for non-editable columns
        if role == Qt.ForegroundRole:  # type: ignore
            col_name = self.study.table.columns[index.column()]
            col_type = self.study.get_column_type(col_name)
            if col_type != ColumnType.DATA:
                # Slightly dimmed for calculated columns
                return QBrush(QColor(80, 80, 80))
        
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
        if col_type != ColumnType.DATA:
            return False  # Can't edit calculated columns
        
        # Convert and set value
        try:
            if value == "":
                value = None
            else:
                value = float(value)
            
            self.study.table.data.iloc[index.row(), index.column()] = value
            
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
        
        # Header text color based on column type
        if role == Qt.ForegroundRole and orientation == Qt.Horizontal:  # type: ignore
            if section < len(self.study.table.columns):
                col_name = self.study.table.columns[section]
                col_type = self.study.get_column_type(col_name)
                color = COLUMN_TEXT_COLORS.get(col_type, QColor(0, 0, 0))
                return QBrush(color)
        
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
                
                tooltip = f"Column: {col_name}\nType: {col_type.upper()}"
                
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
        
        # Only data columns are editable
        if col_type == ColumnType.DATA:
            flags |= Qt.ItemIsEditable  # type: ignore
        
        return flags
