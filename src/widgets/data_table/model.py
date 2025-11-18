"""
Data model for DataTableV2.

This module implements QAbstractTableModel with Pandas/NumPy backend for
high-performance data manipulation.
"""

from typing import Optional, Any, List, Union
from dataclasses import dataclass
from difflib import get_close_matches
import pandas as pd
import numpy as np
from scipy import interpolate
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal

from .column_metadata import ColumnType, ColumnMetadata, DataType
from models.data_store import DataStore
from models.formula_engine import FormulaEngine
from models.column_registry import ColumnRegistry
from utils.formula_parser import FormulaParser, FormulaError, FormulaEvaluationError, FormulaSyntaxError
from utils.exceptions import DataTableError, ColumnExistsError, ColumnNotFoundError, ColumnInUseError


# ============================================================================
# Model Configuration
# ============================================================================

@dataclass
class ModelConfig:
    """Configuration for DataTableModel behavior.
    
    Attributes:
        default_precision: Default number of decimal places for display
        default_dtype: Default data type for new columns
        auto_recalculate: Whether to automatically recalculate formulas
        max_undo_steps: Maximum number of undo steps to keep (0 = disabled)
    """
    default_precision: int = 6
    default_dtype: DataType = DataType.FLOAT
    auto_recalculate: bool = True
    max_undo_steps: int = 0  # Disabled for now, will implement in Phase 4


# ============================================================================
# Data Table Model
# ============================================================================

class DataTableModel(QAbstractTableModel):
    """High-performance table model using Pandas backend.
    
    This model stores data in Pandas Series (one per column) for efficient
    vectorized operations. It implements Qt's QAbstractTableModel interface
    to provide data to views.
    
    Key features:
    - Columnar storage using Pandas Series
    - Vectorized calculations using NumPy
    - Automatic type inference
    - Efficient memory usage
    - Dependency tracking for formulas
    
    Example:
        >>> model = DataTableModel()
        >>> model.add_data_column("time", unit="s", data=[0, 1, 2, 3])
        >>> model.add_calculated_column("position", formula="{time} * 5", unit="m")
        >>> data = model.get_column_data("time")
    """
    
    # ========================================================================
    # Custom Signals
    # ========================================================================
    
    # Column management signals
    columnAdded = Signal(str)           # column_name
    columnRemoved = Signal(str)         # column_name
    columnRenamed = Signal(str, str)    # old_name, new_name
    
    # Calculation signals
    calculationStarted = Signal()
    calculationFinished = Signal()
    
    # Error signals
    errorOccurred = Signal(str, str)    # column_name, error_message
    
    def __init__(self, parent=None, config: Optional[ModelConfig] = None):
        """Initialize the data model.
        
        Args:
            parent: Optional parent QObject
            config: Model configuration (uses defaults if not provided)
        """
        super().__init__(parent)
        
        # Configuration
        self._config = config or ModelConfig()
        
        # Domain models (Qt-independent)
        self._data_store = DataStore()
        self._formula_engine = FormulaEngine()
        self._column_registry = ColumnRegistry()
        
        # Legacy references - delegate to domain models
        # These properties provide backward compatibility during transition
        
        # State tracking
        self._row_count: int = 0
        
        # Global variables/constants for formulas
        self._variables: dict[str, tuple[float, Optional[str]]] = {}  # {name: (value, unit)}
        
        # Formula parser (still used for some operations)
        self._formula_parser = FormulaParser()
        
        # Undo/redo system (Phase 6)
        from utils.commands import CommandManager
        self._command_manager = CommandManager(max_history=100)
        self._bypass_undo = False  # Flag to bypass undo for internal operations
    
    # ========================================================================
    # Legacy Property Accessors (for backward compatibility)
    # ========================================================================
    
    @property
    def _columns(self) -> dict[str, pd.Series]:
        """Access data store columns (backward compatibility)."""
        return self._data_store._columns
    
    @property
    def _metadata(self) -> dict[str, ColumnMetadata]:
        """Access column registry metadata (backward compatibility)."""
        return self._column_registry._metadata
    
    @property
    def _column_order(self) -> List[str]:
        """Access column registry order (backward compatibility)."""
        return self._column_registry._column_order
    
    @property
    def _dependencies(self) -> dict[str, set[str]]:
        """Access formula engine dependencies (backward compatibility)."""
        return self._formula_engine._dependencies
    
    @property
    def _dependents(self) -> dict[str, set[str]]:
        """Access formula engine dependents (backward compatibility)."""
        return self._formula_engine._dependents
    
    # ========================================================================
    # Qt Model Interface - Required Methods
    # ========================================================================
    
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of rows.
        
        Args:
            parent: Parent index (unused for table models)
            
        Returns:
            Number of rows in the table
        """
        if parent.isValid():
            return 0
        return self._row_count
    
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of columns.
        
        Args:
            parent: Parent index (unused for table models)
            
        Returns:
            Number of columns in the table
        """
        if parent.isValid():
            return 0
        return len(self._column_order)
    
    def insertRows(self, row: int, count: int, parent: QModelIndex = QModelIndex()) -> bool:
        """Insert rows into the model.
        
        Args:
            row: Starting row index
            count: Number of rows to insert
            parent: Parent index (unused for table models)
            
        Returns:
            True if rows were inserted successfully
        """
        if count <= 0:
            return False
        
        # Notify views that rows are being inserted
        self.beginInsertRows(parent, row, row + count - 1)
        
        # Determine default values for each dtype
        default_values = {
            DataType.FLOAT: np.nan,
            DataType.INTEGER: 0,
            DataType.STRING: "",
            DataType.CATEGORY: None,
            DataType.BOOLEAN: False
        }
        
        # Insert rows in each column
        for col_name in self._column_order:
            col_dtype = self._metadata[col_name].dtype
            default_val = default_values.get(col_dtype, np.nan)
            
            # Create new rows with default value
            new_rows = pd.Series([default_val] * count, dtype=col_dtype.value)
            
            # Split at insertion point and concatenate
            old_series = self._columns[col_name]
            if row == 0:
                # Insert at beginning
                self._columns[col_name] = pd.concat([new_rows, old_series], ignore_index=True)
            elif row >= len(old_series):
                # Append at end
                self._columns[col_name] = pd.concat([old_series, new_rows], ignore_index=True)
            else:
                # Insert in middle
                before = old_series.iloc[:row]
                after = old_series.iloc[row:]
                self._columns[col_name] = pd.concat([before, new_rows, after], ignore_index=True)
        
        # Update row count
        self._row_count += count
        
        # Notify views that rows have been inserted
        self.endInsertRows()
        
        return True
    
    def removeRows(self, row: int, count: int, parent: QModelIndex = QModelIndex()) -> bool:
        """Remove rows from the model.
        
        Args:
            row: Starting row index
            count: Number of rows to remove
            parent: Parent index (unused for table models)
            
        Returns:
            True if rows were removed successfully
        """
        if count <= 0 or row < 0 or row + count > self._row_count:
            return False
        
        # Notify views that rows are being removed
        self.beginRemoveRows(parent, row, row + count - 1)
        
        # Remove rows from each column
        for col_name in self._column_order:
            old_series = self._columns[col_name]
            # Keep rows before and after the removed range
            if row == 0 and count >= self._row_count:
                # Remove all rows
                self._columns[col_name] = pd.Series([], dtype=old_series.dtype)
            else:
                before = old_series.iloc[:row] if row > 0 else pd.Series([], dtype=old_series.dtype)
                after = old_series.iloc[row + count:] if row + count < self._row_count else pd.Series([], dtype=old_series.dtype)
                self._columns[col_name] = pd.concat([before, after], ignore_index=True)
        
        # Update row count
        self._row_count -= count
        
        # Notify views that rows have been removed
        self.endRemoveRows()
        
        return True
    
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Return data for the given index and role.
        
        This is called by Qt views to get data for display, editing, tooltips, etc.
        
        Args:
            index: Model index (row, column)
            role: Data role (DisplayRole, EditRole, etc.)
            
        Returns:
            Data for the requested role, or None
        """
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()
        
        # Check bounds
        if row < 0 or row >= self._row_count or col < 0 or col >= len(self._column_order):
            return None
        
        col_name = self._column_order[col]
        metadata = self._metadata[col_name]
        series = self._columns[col_name]
        
        # Get the value
        try:
            value = series.iloc[row]
        except (IndexError, KeyError):
            return None
        
        # Handle different roles
        if role == Qt.ItemDataRole.DisplayRole:
            # Format for display
            if pd.isna(value):
                return ""
            
            # Format based on dtype
            if metadata.dtype == DataType.FLOAT:
                return f"{value:.{metadata.precision}g}"
            elif metadata.dtype == DataType.INTEGER:
                return str(int(value))
            elif metadata.dtype == DataType.BOOLEAN:
                return "True" if value else "False"
            else:
                return str(value)
        
        elif role == Qt.ItemDataRole.EditRole:
            # Raw value for editing
            if pd.isna(value):
                return None
            return value
        
        elif role == Qt.ItemDataRole.ToolTipRole:
            # Show description as tooltip
            if metadata.description:
                return metadata.description
            return None
        
        return None
    
    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        """Set data at the given index.
        
        This is called when the user edits a cell.
        
        Args:
            index: Model index (row, column)
            value: New value
            role: Data role (typically EditRole)
            
        Returns:
            True if data was set successfully, False otherwise
        """
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
        
        row = index.row()
        col = index.column()
        
        # Check bounds
        if row < 0 or row >= self._row_count or col < 0 or col >= len(self._column_order):
            return False
        
        col_name = self._column_order[col]
        metadata = self._metadata[col_name]
        
        # Check if column is editable
        if not metadata.editable:
            return False
        
        # Convert value to appropriate type based on column dtype
        col_dtype = metadata.dtype
        try:
            if value is None or value == "":
                # Handle empty input
                if col_dtype == DataType.FLOAT:
                    new_value = np.nan
                elif col_dtype == DataType.INTEGER:
                    new_value = 0
                elif col_dtype == DataType.STRING:
                    new_value = ""
                elif col_dtype == DataType.BOOLEAN:
                    new_value = False
                else:
                    new_value = None
            else:
                # Convert to appropriate type
                if col_dtype == DataType.FLOAT:
                    new_value = float(value)
                elif col_dtype == DataType.INTEGER:
                    new_value = int(float(value))  # Handle "3.0" -> 3
                elif col_dtype == DataType.BOOLEAN:
                    new_value = bool(value)
                else:
                    new_value = str(value)
        except (ValueError, TypeError) as e:
            self.errorOccurred.emit(col_name, f"Invalid value: {e}")
            return False
        
        # If bypass_undo is set (internal operations), set value directly
        if self._bypass_undo:
            self._columns[col_name].iloc[row] = new_value
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])
        else:
            # Use command for undo/redo support
            from .commands import SetCellValueCommand
            command = SetCellValueCommand(self, row, col, new_value)
            self._command_manager.execute(command)
        
        # Trigger recalculation of dependent columns if auto-recalculate is enabled
        if self._config.auto_recalculate:
            try:
                recalc_cols = self._get_recalculation_order(col_name)
                if recalc_cols:
                    self.calculationStarted.emit()
                    for col in recalc_cols:
                        self._recalculate_column(col)
                    self.calculationFinished.emit()
                
                # If this is an uncertainty column, also recalculate dependent uncertainty columns
                metadata = self._metadata.get(col_name)
                if metadata and (metadata.is_uncertainty_column() or col_name.endswith("_u")):
                    # Find the data column this uncertainty belongs to
                    if metadata.is_uncertainty_column() and metadata.uncertainty_reference:
                        data_col = metadata.uncertainty_reference
                    elif col_name.endswith("_u"):
                        # Infer data column from name (e.g., "x_u" -> "x")
                        data_col = col_name[:-2]  # Remove "_u" suffix
                    else:
                        data_col = None
                    
                    if data_col and data_col in self._columns:
                        # Find calculated columns that depend on this data column and have uncertainty propagation
                        for calc_col_name, calc_meta in self._metadata.items():
                            if calc_meta.is_calculated_column() and calc_meta.propagate_uncertainty:
                                # Check if this calculated column depends on the data column
                                if calc_meta.formula:
                                    deps = self._formula_parser.extract_dependencies(calc_meta.formula)
                                    if data_col in deps:
                                        # Recalculate the uncertainty column
                                        uncert_name = f"{calc_col_name}_u"
                                        if uncert_name in self._columns:
                                            uncert_values = self._calculate_propagated_uncertainty(calc_col_name)
                                            self._columns[uncert_name] = uncert_values
                                            
                                            # Emit signal
                                            uncert_col_idx = self._column_order.index(uncert_name)
                                            first_idx = self.index(0, uncert_col_idx)
                                            last_idx = self.index(self._row_count - 1, uncert_col_idx)
                                            self.dataChanged.emit(first_idx, last_idx, [Qt.ItemDataRole.DisplayRole])
                
            except Exception as e:
                self.errorOccurred.emit(col_name, f"Recalculation error: {e}")
        
        return True
    
    def headerData(self, section: int, orientation: Qt.Orientation, 
                   role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Return header data.
        
        Args:
            section: Row or column number
            orientation: Horizontal (column headers) or Vertical (row headers)
            role: Data role
            
        Returns:
            Header data, or None
        """
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        
        if orientation == Qt.Orientation.Horizontal:
            # Column headers
            if 0 <= section < len(self._column_order):
                col_name = self._column_order[section]
                metadata = self._metadata[col_name]
                # Show symbol + name [unit]
                symbol = metadata.get_symbol()
                header = metadata.get_display_header()
                return f"{symbol} {header}"
            return None
        
        else:
            # Row headers (just row numbers)
            return str(section + 1)
    
    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        """Return item flags for the given index.
        
        This determines what the user can do with each cell (select, edit, etc.)
        
        Args:
            index: Model index
            
        Returns:
            Item flags
        """
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        
        col = index.column()
        if col < 0 or col >= len(self._column_order):
            return Qt.ItemFlag.NoItemFlags
        
        col_name = self._column_order[col]
        metadata = self._metadata[col_name]
        
        # Base flags: always selectable and enabled
        base_flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        
        # Add editable flag if column is editable
        if metadata.editable:
            return base_flags | Qt.ItemFlag.ItemIsEditable
        
        return base_flags
    
    # ========================================================================
    # Public API - Column Management
    # ========================================================================
    
    def add_data_column(self, name: str, unit: Optional[str] = None, 
                       description: Optional[str] = None,
                       data: Optional[Union[List, np.ndarray, pd.Series]] = None,
                       dtype: Optional[DataType] = None,
                       precision: Optional[int] = None,
                       insert_position: Optional[int] = None) -> None:
        """Add a new DATA column.
        
        Args:
            name: Column name
            unit: Physical unit (e.g., 'm', 's', 'kg')
            description: Human-readable description
            data: Initial data (optional)
            dtype: Data type (uses config default if not specified)
            precision: Number of decimal places for display (uses config default if not specified)
            insert_position: Position to insert column (None = append at end)
            
        Raises:
            ColumnExistsError: If column name already exists
            ValueError: If metadata is invalid
        """
        if name in self._columns:
            raise ColumnExistsError(name)
        
        # Use defaults from config
        if dtype is None:
            dtype = self._config.default_dtype
        if precision is None:
            precision = self._config.default_precision
        
        # Create metadata
        metadata = ColumnMetadata(
            name=name,
            column_type=ColumnType.DATA,
            dtype=dtype,
            unit=unit,
            description=description,
            precision=precision
        )
        
        # Validate metadata
        is_valid, error = metadata.validate()
        if not is_valid:
            raise ValueError(f"Invalid metadata: {error}")
        
        # Determine default value for this dtype
        default_values = {
            DataType.FLOAT: np.nan,
            DataType.INTEGER: 0,
            DataType.STRING: "",
            DataType.CATEGORY: None,
            DataType.BOOLEAN: False
        }
        default_val = default_values.get(dtype, np.nan)
        
        # Create Series with data or defaults
        if data is not None:
            series = pd.Series(data, dtype=dtype.value)
            new_row_count = len(series)
        else:
            # Create empty series with current row count
            new_row_count = self._row_count
            series = pd.Series([default_val] * new_row_count, dtype=dtype.value)
        
        # Synchronize row counts: extend ALL columns to match the maximum
        max_row_count = max(self._row_count, new_row_count)
        
        if max_row_count > self._row_count:
            # Extend all existing columns to new row count
            for col_name in self._column_order:
                old_series = self._columns[col_name]
                old_len = len(old_series)
                if old_len < max_row_count:
                    # Determine default for this column's dtype
                    col_dtype = self._metadata[col_name].dtype
                    col_default = default_values.get(col_dtype, np.nan)
                    # Create extension
                    extension = pd.Series([col_default] * (max_row_count - old_len), 
                                        dtype=col_dtype.value)
                    # Concatenate
                    self._columns[col_name] = pd.concat([old_series, extension], 
                                                        ignore_index=True)
        
        # Extend new series if needed
        if len(series) < max_row_count:
            extension = pd.Series([default_val] * (max_row_count - len(series)), 
                                dtype=dtype.value)
            series = pd.concat([series, extension], ignore_index=True)
        
        # Update row count
        self._row_count = max_row_count
        
        # Store column
        self._columns[name] = series
        self._metadata[name] = metadata
        
        # Insert into column order at specified position
        if insert_position is not None and 0 <= insert_position <= len(self._column_order):
            self._column_order.insert(insert_position, name)
        else:
            self._column_order.append(name)
        
        # Notify views and listeners
        self.layoutChanged.emit()
        self.columnAdded.emit(name)
    
    def add_calculated_column(self, name: str, formula: str,
                             unit: Optional[str] = None,
                             description: Optional[str] = None,
                             precision: Optional[int] = None,
                             propagate_uncertainty: bool = False,
                             insert_position: Optional[int] = None) -> None:
        """Add a CALCULATED column with a formula.
        
        The formula will be evaluated using the formula parser and automatically
        recalculated when dependent columns change.
        
        Args:
            name: Column name
            formula: Formula string using {column_name} syntax
                    Example: "{mass} * {velocity}**2 / 2"
            unit: Physical unit of result (optional)
            description: Human-readable description
            precision: Number of decimal places for display
            propagate_uncertainty: If True, automatically calculate and maintain
                                  an uncertainty column using error propagation
            insert_position: Position to insert column (None = append at end)
            
        Raises:
            ColumnExistsError: If column name already exists
            FormulaSyntaxError: If formula has invalid syntax
            ColumnNotFoundError: If formula references non-existent columns
            ValueError: If metadata is invalid
            
        Example:
            >>> model.add_data_column("x", data=[1, 2, 3])
            >>> model.add_calculated_column("y", "{x} * 2 + 5")
            >>> # y will be [7, 9, 11]
            >>> # With uncertainty propagation:
            >>> model.add_calculated_column("z", "{x} * 5", propagate_uncertainty=True)
            >>> # Creates both "z" and "z_u" columns
        """
        if name in self._columns:
            raise ColumnExistsError(name)
        
        # Use defaults from config
        if precision is None:
            precision = self._config.default_precision
        
        # Validate formula syntax
        valid, error = self._formula_parser.validate_syntax(formula)
        if not valid:
            raise FormulaSyntaxError(f"Invalid formula: {error}")
        
        # Extract dependencies from formula
        dependencies = self._formula_parser.extract_dependencies(formula)
        
        # Validate that all referenced columns/variables exist
        for dep in dependencies:
            if dep not in self._columns and dep not in self._variables:
                available_cols = self.get_column_names()
                available_vars = list(self._variables.keys())
                error_msg = f"'{dep}' not found in columns or variables."
                if available_vars:
                    error_msg += f" Available columns: {', '.join(available_cols)}."
                    error_msg += f" Available variables: {', '.join(available_vars)}."
                else:
                    error_msg += f" Available columns: {', '.join(available_cols)}."
                raise ColumnNotFoundError(dep, available_cols)
        
        # Create metadata
        metadata = ColumnMetadata(
            name=name,
            column_type=ColumnType.CALCULATED,
            dtype=DataType.FLOAT,  # Calculated columns are always float
            unit=unit,
            description=description,
            formula=formula,
            propagate_uncertainty=propagate_uncertainty,
            precision=precision
        )
        
        # Validate metadata
        is_valid, error = metadata.validate()
        if not is_valid:
            raise ValueError(f"Invalid metadata: {error}")
        
        # Register dependencies (only for columns, not variables)
        for dep in dependencies:
            if dep in self._columns:  # Only track column dependencies
                self._register_dependency(name, dep)
        
        # Calculate initial values
        try:
            result = self._evaluate_formula(name, formula)
        except FormulaError as e:
            raise FormulaEvaluationError(f"Failed to evaluate formula: {e}")
        
        # Store column
        self._columns[name] = result
        self._metadata[name] = metadata
        
        # Insert into column order at specified position
        if insert_position is not None and 0 <= insert_position <= len(self._column_order):
            self._column_order.insert(insert_position, name)
            # If propagating uncertainty, insert it right after the main column
            uncert_insert_pos = insert_position + 1
        else:
            self._column_order.append(name)
            uncert_insert_pos = None  # Will append to end
        
        # If uncertainty propagation is enabled, create uncertainty column
        if propagate_uncertainty:
            uncert_name = f"{name}_u"
            if uncert_name not in self._columns:
                # Calculate initial uncertainty
                uncert_values = self._calculate_propagated_uncertainty(name)
                
                # Create uncertainty column
                uncert_metadata = ColumnMetadata(
                    name=uncert_name,
                    column_type=ColumnType.UNCERTAINTY,
                    dtype=DataType.FLOAT,
                    unit=unit,  # Same unit as the calculated column
                    description=f"Propagated uncertainty for {name}",
                    uncertainty_reference=name,
                    precision=precision
                )
                
                self._columns[uncert_name] = uncert_values
                self._metadata[uncert_name] = uncert_metadata
                
                # Insert uncertainty column at specified position
                if uncert_insert_pos is not None and 0 <= uncert_insert_pos <= len(self._column_order):
                    self._column_order.insert(uncert_insert_pos, uncert_name)
                else:
                    self._column_order.append(uncert_name)
        
        # Notify views and listeners
        self.layoutChanged.emit()
        self.columnAdded.emit(name)
        if propagate_uncertainty:
            self.columnAdded.emit(uncert_name)
    
    def add_range_column(self, name: str, 
                        start: float, 
                        end: float,
                        points: Optional[int] = None,
                        step: Optional[float] = None,
                        mode: str = "linspace",
                        unit: Optional[str] = None,
                        description: Optional[str] = None,
                        precision: Optional[int] = None,
                        insert_position: Optional[int] = None) -> None:
        """Add a RANGE column with evenly-spaced or logarithmically-spaced values.
        
        This is useful for creating independent variables (time, position, angle, etc.)
        with controlled spacing.
        
        Args:
            name: Column name
            start: Starting value
            end: Ending value (inclusive for linspace/logspace)
            points: Number of points (required for linspace/logspace, optional for arange)
            step: Step size (required for arange, ignored for linspace/logspace)
            mode: Spacing mode - "linspace", "logspace", or "arange"
                  - linspace: Evenly spaced in linear scale (default)
                  - logspace: Evenly spaced in logarithmic scale
                  - arange: Fixed step size (like Python range)
            unit: Physical unit (optional)
            description: Human-readable description
            precision: Number of decimal places for display
            insert_position: Position to insert column (None = append at end)
            
        Raises:
            ColumnExistsError: If column name already exists
            ValueError: If parameters are invalid for the chosen mode
            
        Examples:
            >>> # Linear spacing: 0, 1, 2, 3, 4, 5
            >>> model.add_range_column("time", start=0, end=5, points=6, unit="s")
            
            >>> # Logarithmic spacing: 1, 10, 100, 1000
            >>> model.add_range_column("freq", start=1, end=1000, points=4, 
            ...                       mode="logspace", unit="Hz")
            
            >>> # Fixed step size: 0, 0.5, 1.0, 1.5, 2.0
            >>> model.add_range_column("x", start=0, end=2, step=0.5, 
            ...                       mode="arange", unit="m")
        """
        if name in self._columns:
            raise ColumnExistsError(name)
        
        # Use defaults from config
        if precision is None:
            precision = self._config.default_precision
        
        # Validate mode
        valid_modes = {"linspace", "logspace", "arange"}
        if mode not in valid_modes:
            raise ValueError(f"Invalid mode '{mode}'. Must be one of: {valid_modes}")
        
        # Generate data based on mode
        if mode == "linspace":
            if points is None:
                raise ValueError("linspace mode requires 'points' parameter")
            if points < 2:
                raise ValueError(f"linspace requires at least 2 points, got {points}")
            data = np.linspace(start, end, points)
            
        elif mode == "logspace":
            if points is None:
                raise ValueError("logspace mode requires 'points' parameter")
            if points < 2:
                raise ValueError(f"logspace requires at least 2 points, got {points}")
            if start <= 0 or end <= 0:
                raise ValueError("logspace requires positive start and end values")
            # np.logspace takes log10(start) and log10(end) as arguments
            data = np.logspace(np.log10(start), np.log10(end), points)
            
        elif mode == "arange":
            if step is None:
                raise ValueError("arange mode requires 'step' parameter")
            if step == 0:
                raise ValueError("arange step cannot be zero")
            if (end - start) / step < 0:
                raise ValueError("step sign must match (end - start) sign")
            data = np.arange(start, end + step/2, step)  # Add step/2 to include endpoint
            
        # Create metadata (RANGE columns are DATA type but with range metadata)
        metadata = ColumnMetadata(
            name=name,
            column_type=ColumnType.RANGE,
            dtype=DataType.FLOAT,  # Range columns are always float
            unit=unit,
            description=description,
            precision=precision,
            range_start=start,
            range_end=end,
            range_points=len(data)
        )
        
        # Validate metadata
        is_valid, error = metadata.validate()
        if not is_valid:
            raise ValueError(f"Invalid metadata: {error}")
        
        # Convert to Series
        series = pd.Series(data, dtype=DataType.FLOAT.value)
        new_row_count = len(series)
        
        # Synchronize row counts
        default_values = {
            DataType.FLOAT: np.nan,
            DataType.INTEGER: 0,
            DataType.STRING: "",
            DataType.CATEGORY: None,
            DataType.BOOLEAN: False
        }
        
        max_row_count = max(self._row_count, new_row_count)
        
        if max_row_count > self._row_count:
            # Extend all existing columns
            for col_name in self._column_order:
                old_series = self._columns[col_name]
                old_len = len(old_series)
                if old_len < max_row_count:
                    col_dtype = self._metadata[col_name].dtype
                    col_default = default_values.get(col_dtype, np.nan)
                    extension = pd.Series([col_default] * (max_row_count - old_len), 
                                        dtype=col_dtype.value)
                    self._columns[col_name] = pd.concat([old_series, extension], 
                                                        ignore_index=True)
        
        # Extend new series if needed
        if len(series) < max_row_count:
            extension = pd.Series([np.nan] * (max_row_count - len(series)), 
                                dtype=DataType.FLOAT.value)
            series = pd.concat([series, extension], ignore_index=True)
        
        # Update row count
        self._row_count = max_row_count
        
        # Store column
        self._columns[name] = series
        self._metadata[name] = metadata
        
        # Insert into column order at specified position
        if insert_position is not None and 0 <= insert_position <= len(self._column_order):
            self._column_order.insert(insert_position, name)
        else:
            self._column_order.append(name)
        
        # Notify views and listeners
        self.layoutChanged.emit()
        self.columnAdded.emit(name)
    
    def add_derivative_column(
        self,
        name: str,
        numerator: str,
        denominator: str,
        unit: Optional[str] = None,
        description: Optional[str] = None,
        method: str = "forward",
        precision: Optional[int] = None
    ) -> None:
        """Add a derivative column calculating discrete differences dy/dx.
        
        Computes numerical derivative using discrete differences:
        - forward: dy/dx[i] = (y[i+1] - y[i]) / (x[i+1] - x[i])
        - backward: dy/dx[i] = (y[i] - y[i-1]) / (x[i] - x[i-1])
        - central: dy/dx[i] = (y[i+1] - y[i-1]) / (x[i+1] - x[i-1])
        
        Args:
            name: Column name
            numerator: Name of numerator column (dy)
            denominator: Name of denominator column (dx)
            unit: Optional unit (auto-calculated if None)
            description: Optional description
            method: Difference method ('forward', 'backward', 'central')
            precision: Number of decimal places for display
            
        Raises:
            ColumnExistsError: If column name already exists
            ColumnNotFoundError: If numerator or denominator doesn't exist
            ValueError: If method is invalid or columns are incompatible
        """
        # Validate column name
        if name in self._columns:
            raise ColumnExistsError(name)
        
        # Validate source columns exist
        if numerator not in self._columns:
            raise ColumnNotFoundError(numerator, self.get_column_names())
        if denominator not in self._columns:
            raise ColumnNotFoundError(denominator, self.get_column_names())
        
        # Validate method
        valid_methods = ["forward", "backward", "central"]
        if method not in valid_methods:
            raise ValueError(f"Invalid method '{method}'. Must be one of: {valid_methods}")
        
        # Get source column data
        y_data = self._columns[numerator]
        x_data = self._columns[denominator]
        
        # Validate data types (must be numeric)
        if not pd.api.types.is_numeric_dtype(y_data):
            raise ValueError(f"Numerator column '{numerator}' must be numeric")
        if not pd.api.types.is_numeric_dtype(x_data):
            raise ValueError(f"Denominator column '{denominator}' must be numeric")
        
        # Calculate derivative using specified method
        if method == "forward":
            dy = y_data.diff().shift(-1)  # y[i+1] - y[i]
            dx = x_data.diff().shift(-1)  # x[i+1] - x[i]
        elif method == "backward":
            dy = y_data.diff()  # y[i] - y[i-1]
            dx = x_data.diff()  # x[i] - x[i-1]
        else:  # central
            dy = y_data.diff().shift(-1) + y_data.diff()  # y[i+1] - y[i-1]
            dx = x_data.diff().shift(-1) + x_data.diff()  # x[i+1] - x[i-1]
        
        # Compute derivative (handle division by zero)
        with np.errstate(divide='ignore', invalid='ignore'):
            dy_arr = np.asarray(dy, dtype=float)
            dx_arr = np.asarray(dx, dtype=float)
            derivative = pd.Series(dy_arr / dx_arr, dtype=float)
        
        # Replace inf/nan at boundaries with NaN
        derivative = derivative.replace([np.inf, -np.inf], np.nan)
        
        # Auto-calculate unit if not provided
        if unit is None:
            y_unit = self._metadata[numerator].unit
            x_unit = self._metadata[denominator].unit
            if y_unit and x_unit:
                unit = f"{y_unit}/{x_unit}"
            elif y_unit and not x_unit:
                unit = y_unit
            elif not y_unit and x_unit:
                unit = f"1/{x_unit}"
            # else: both None, unit remains None
        
        # Create metadata
        metadata = ColumnMetadata(
            name=name,
            column_type=ColumnType.DERIVATIVE,
            dtype=DataType.FLOAT,
            unit=unit,
            description=description,
            derivative_numerator=numerator,
            derivative_denominator=denominator,
            precision=precision if precision is not None else 6
        )
        
        # Store column
        self._columns[name] = derivative
        self._metadata[name] = metadata
        self._column_order.append(name)
        
        # Register dependencies
        self._register_dependency(name, numerator)
        self._register_dependency(name, denominator)
        
        # Notify views and listeners
        self.layoutChanged.emit()
        self.columnAdded.emit(name)
    
    def add_interpolation_column(
        self,
        name: str,
        x_column: str,
        y_column: str,
        eval_column: Optional[str] = None,
        method: str = "linear",
        unit: Optional[str] = None,
        description: Optional[str] = None,
        precision: Optional[int] = None
    ) -> None:
        """Add an interpolation column.
        
        Creates a new column by interpolating Y values based on X values from
        source data columns. The interpolation can be evaluated at:
        1. The X column points (if eval_column is None)
        2. Another column's points (if eval_column is specified)
        
        Supports multiple interpolation methods via scipy.interpolate.interp1d.
        
        Args:
            name: Column name
            x_column: Name of X data column (independent variable)
            y_column: Name of Y data column (dependent variable)
            eval_column: Optional column to evaluate interpolation at (uses x_column if None)
            method: Interpolation method ('linear', 'cubic', 'quadratic', 'nearest')
            unit: Optional unit (defaults to y_column's unit)
            description: Optional description
            precision: Number of decimal places for display
            
        Raises:
            ColumnExistsError: If column name already exists
            ColumnNotFoundError: If source columns don't exist
            ValueError: If method is invalid or data is incompatible
        """
        # Validate column name
        if name in self._columns:
            raise ColumnExistsError(name)
        
        # Validate source columns exist
        if x_column not in self._columns:
            raise ColumnNotFoundError(x_column, self.get_column_names())
        if y_column not in self._columns:
            raise ColumnNotFoundError(y_column, self.get_column_names())
        if eval_column and eval_column not in self._columns:
            raise ColumnNotFoundError(eval_column, self.get_column_names())
        
        # Validate method
        valid_methods = ["linear", "cubic", "quadratic", "nearest"]
        if method not in valid_methods:
            raise ValueError(f"Invalid method '{method}'. Must be one of: {valid_methods}")
        
        # Get source data
        x_data = self._columns[x_column]
        y_data = self._columns[y_column]
        
        # Validate numeric types
        if not pd.api.types.is_numeric_dtype(x_data):
            raise ValueError(f"X column '{x_column}' must be numeric")
        if not pd.api.types.is_numeric_dtype(y_data):
            raise ValueError(f"Y column '{y_column}' must be numeric")
        
        # Remove NaN values for interpolation
        mask = ~(x_data.isna() | y_data.isna())
        x_clean = x_data[mask]
        y_clean = y_data[mask]
        
        if len(x_clean) < 2:
            raise ValueError(f"Need at least 2 valid data points for interpolation, got {len(x_clean)}")
        
        # Check for duplicate X values (would break interpolation)
        if x_clean.duplicated().any():
            raise ValueError(f"X column '{x_column}' contains duplicate values. Interpolation requires unique X values.")
        
        # Sort by X values (required for interpolation)
        sort_idx = np.argsort(x_clean)
        x_sorted = x_clean.iloc[sort_idx]
        y_sorted = y_clean.iloc[sort_idx]
        
        # Create interpolation function
        try:
            # Map method names to scipy kind parameter
            kind_map = {
                "linear": "linear",
                "cubic": "cubic",
                "quadratic": "quadratic",
                "nearest": "nearest"
            }
            interp_func = interpolate.interp1d(
                x_sorted, 
                y_sorted, 
                kind=kind_map[method],
                fill_value=np.nan,
                bounds_error=False
            )
        except Exception as e:
            raise ValueError(f"Failed to create interpolation function: {e}")
        
        # Evaluate interpolation
        if eval_column:
            eval_data = self._columns[eval_column]
            if not pd.api.types.is_numeric_dtype(eval_data):
                raise ValueError(f"Evaluation column '{eval_column}' must be numeric")
            x_eval = eval_data
        else:
            x_eval = x_data
        
        # Compute interpolated values
        result = pd.Series(interp_func(x_eval), dtype=float)
        
        # Use Y column's unit if not specified
        if unit is None:
            unit = self._metadata[y_column].unit
        
        # Create metadata
        metadata = ColumnMetadata(
            name=name,
            column_type=ColumnType.INTERPOLATION,
            dtype=DataType.FLOAT,
            unit=unit,
            description=description,
            interp_x_column=x_column,
            interp_y_column=y_column,
            interp_method=method,
            precision=precision if precision is not None else 6
        )
        
        # Store column
        self._columns[name] = result
        self._metadata[name] = metadata
        self._column_order.append(name)
        
        # Register dependencies
        self._register_dependency(name, x_column)
        self._register_dependency(name, y_column)
        if eval_column:
            self._register_dependency(name, eval_column)
        
        # Notify views and listeners
        self.layoutChanged.emit()
        self.columnAdded.emit(name)
    
    def get_column_data(self, name: str) -> pd.Series:
        """Get data for a column.
        
        Args:
            name: Column name
            
        Returns:
            Pandas Series containing column data (copy, not view)
            
        Raises:
            ColumnNotFoundError: If column doesn't exist
            
        Note:
            Returns a copy for safety. If you need a view for performance,
            access _columns directly (with caution).
        """
        if name not in self._columns:
            raise ColumnNotFoundError(name, self.get_column_names())
        return self._columns[name].copy()
    
    def remove_column(self, name: str) -> None:
        """Remove a column from the table.
        
        Args:
            name: Name of column to remove
            
        Raises:
            ColumnNotFoundError: If column doesn't exist
            ColumnInUseError: If other columns depend on this one
        """
        if name not in self._columns:
            raise ColumnNotFoundError(name, self.get_column_names())
        
        # Check if other columns depend on this one
        dependent_cols = self._get_dependent_columns(name)
        if dependent_cols:
            raise ColumnInUseError(name, dependent_cols)
        
        # Remove from all structures
        del self._columns[name]
        del self._metadata[name]
        self._column_order.remove(name)
        
        # Clean up dependency tracking
        if name in self._dependencies:
            del self._dependencies[name]
        if name in self._dependents:
            del self._dependents[name]
        
        # Remove this column from other columns' dependency sets
        for col_deps in self._dependencies.values():
            col_deps.discard(name)
        for col_deps in self._dependents.values():
            col_deps.discard(name)
        
        # Notify views and listeners
        self.layoutChanged.emit()
        self.columnRemoved.emit(name)
    
    def edit_data_column(self, name: str, new_name: Optional[str] = None,
                        unit: Optional[str] = None,
                        description: Optional[str] = None,
                        precision: Optional[int] = None) -> None:
        """Edit properties of a DATA column.
        
        Args:
            name: Current column name
            new_name: New name (if renaming)
            unit: New unit (None to keep existing)
            description: New description (None to keep existing)
            precision: New precision (None to keep existing)
            
        Raises:
            ColumnNotFoundError: If column doesn't exist
            ColumnExistsError: If new_name already exists
            ValueError: If column is not a DATA column
        """
        if name not in self._columns:
            raise ColumnNotFoundError(name, self.get_column_names())
        
        metadata = self._metadata[name]
        if not metadata.is_data_column():
            raise ValueError(f"Column '{name}' is not a DATA column")
        
        # Handle rename if requested
        if new_name and new_name != name:
            self.rename_column(name, new_name)
            name = new_name  # Use new name for rest of updates
            metadata = self._metadata[name]  # Get updated metadata
        
        # Update properties
        if unit is not None:
            metadata.unit = unit
        if description is not None:
            metadata.description = description
        if precision is not None:
            metadata.precision = precision
        
        # Emit signals to update views
        self.headerDataChanged.emit(Qt.Orientation.Horizontal, 
                                    self._column_order.index(name), 
                                    self._column_order.index(name))
        self.layoutChanged.emit()
    
    def edit_calculated_column(self, name: str, new_name: Optional[str] = None,
                              formula: Optional[str] = None,
                              description: Optional[str] = None,
                              precision: Optional[int] = None,
                              propagate_uncertainty: Optional[bool] = None) -> None:
        """Edit properties of a CALCULATED column.
        
        Args:
            name: Current column name
            new_name: New name (if renaming)
            formula: New formula (None to keep existing)
            description: New description (None to keep existing)
            precision: New precision (None to keep existing)
            propagate_uncertainty: New uncertainty setting (None to keep existing)
            
        Raises:
            ColumnNotFoundError: If column doesn't exist
            ColumnExistsError: If new_name already exists
            ValueError: If column is not a CALCULATED column
            FormulaSyntaxError: If new formula has invalid syntax
        """
        if name not in self._columns:
            raise ColumnNotFoundError(name, self.get_column_names())
        
        metadata = self._metadata[name]
        if not metadata.is_calculated_column():
            raise ValueError(f"Column '{name}' is not a CALCULATED column")
        
        # Handle rename if requested
        if new_name and new_name != name:
            self.rename_column(name, new_name)
            name = new_name  # Use new name for rest of updates
            metadata = self._metadata[name]  # Get updated metadata
        
        # Handle formula change
        if formula is not None and formula != metadata.formula:
            # Validate new formula
            valid, error = self._formula_parser.validate_syntax(formula)
            if not valid:
                raise FormulaSyntaxError(f"Invalid formula: {error}")
            
            # Extract dependencies
            new_deps = self._formula_parser.extract_dependencies(formula)
            
            # Validate that all referenced columns exist
            for dep in new_deps:
                if dep not in self._columns:
                    raise ColumnNotFoundError(dep, self.get_column_names())
            
            # Update dependencies
            old_deps = self._dependencies.get(name, set())
            self._dependencies[name] = set(new_deps)
            
            # Update dependents tracking
            for old_dep in old_deps:
                if old_dep in self._dependents:
                    self._dependents[old_dep].discard(name)
            for new_dep in new_deps:
                if new_dep not in self._dependents:
                    self._dependents[new_dep] = set()
                self._dependents[new_dep].add(name)
            
            # Update formula in metadata
            metadata.formula = formula
            
            # Recalculate values
            try:
                result = self._evaluate_formula(name, formula)
                self._columns[name] = result
            except FormulaError as e:
                raise FormulaEvaluationError(f"Failed to evaluate formula: {e}")
        
        # Update other properties
        if description is not None:
            metadata.description = description
        if precision is not None:
            metadata.precision = precision
        if propagate_uncertainty is not None:
            metadata.propagate_uncertainty = propagate_uncertainty
            # TODO: Handle uncertainty column creation/deletion
        
        # Emit signals to update views
        self.dataChanged.emit(
            self.index(0, self._column_order.index(name)),
            self.index(self.rowCount() - 1, self._column_order.index(name))
        )
        self.headerDataChanged.emit(Qt.Orientation.Horizontal, 
                                    self._column_order.index(name), 
                                    self._column_order.index(name))
        self.layoutChanged.emit()
    
    def add_uncertainty_column(self, data_column_name: str, name: Optional[str] = None,
                              unit: Optional[str] = None, description: Optional[str] = None,
                              precision: Optional[int] = None) -> None:
        """Add an uncertainty column for a data column.
        
        Args:
            data_column_name: Name of the data column
            name: Custom name for uncertainty column (defaults to "{data_column_name}_u")
            unit: Custom unit (defaults to data column's unit)
            description: Custom description (defaults to "Uncertainty for {data_column_name}")
            precision: Display precision (defaults to data column's precision)
            
        Raises:
            ColumnNotFoundError: If data column doesn't exist
            ColumnExistsError: If uncertainty column already exists
        """
        if data_column_name not in self._columns:
            raise ColumnNotFoundError(data_column_name, self.get_column_names())
        
        uncert_name = name or f"{data_column_name}_u"
        if uncert_name in self._columns:
            raise ColumnExistsError(uncert_name)
        
        data_metadata = self._metadata[data_column_name]
        
        # Use custom values or defaults from data column
        final_unit = unit if unit is not None else data_metadata.unit
        final_description = description or f"Uncertainty for {data_column_name}"
        final_precision = precision if precision is not None else data_metadata.precision
        
        # Create uncertainty column with same unit as data column
        self.add_data_column(
            name=uncert_name,
            dtype=DataType.FLOAT,
            unit=final_unit,
            description=final_description,
            precision=final_precision
        )
        
        # Update metadata to mark it as an uncertainty column
        uncert_metadata = self._metadata[uncert_name]
        uncert_metadata.column_type = ColumnType.UNCERTAINTY
        uncert_metadata.uncertainty_reference = data_column_name
        uncert_metadata.editable = True  # Manual uncertainty columns are editable
    
    def edit_range_column(self, name: str, new_name: Optional[str] = None,
                         start: Optional[float] = None,
                         end: Optional[float] = None,
                         points: Optional[int] = None,
                         unit: Optional[str] = None,
                         description: Optional[str] = None,
                         precision: Optional[int] = None) -> None:
        """Edit properties of a RANGE column.
        
        Args:
            name: Current column name
            new_name: New name (if renaming)
            start: New start value
            end: New end value
            points: New number of points
            unit: New unit
            description: New description
            precision: New precision
            
        Raises:
            ColumnNotFoundError: If column doesn't exist
            ColumnExistsError: If new_name already exists
            ValueError: If column is not a RANGE column or invalid parameters
        """
        if name not in self._columns:
            raise ColumnNotFoundError(name, self.get_column_names())
        
        metadata = self._metadata[name]
        if not metadata.is_range_column():
            raise ValueError(f"Column '{name}' is not a RANGE column")
        
        # Handle rename if requested
        if new_name and new_name != name:
            self.rename_column(name, new_name)
            name = new_name
            metadata = self._metadata[name]
        
        # Check if range parameters changed
        range_changed = False
        if start is not None and start != metadata.range_start:
            metadata.range_start = start
            range_changed = True
        if end is not None and end != metadata.range_end:
            metadata.range_end = end
            range_changed = True
        if points is not None and points != metadata.range_points:
            metadata.range_points = points
            range_changed = True
        
        # Regenerate values if range changed
        if range_changed:
            if metadata.range_start is None or metadata.range_end is None or metadata.range_points is None:
                raise ValueError("Cannot generate range: missing start, end, or points")
            
            step = (metadata.range_end - metadata.range_start) / (metadata.range_points - 1) if metadata.range_points > 1 else 0
            values = [metadata.range_start + i * step for i in range(metadata.range_points)]
            
            # Update column data
            self._columns[name] = pd.Series(values, dtype='float64')
            
            # Update row count if needed
            if len(values) > self._row_count:
                old_count = self._row_count
                self._row_count = len(values)
                # Extend other columns
                for col_name, series in self._columns.items():
                    if col_name != name and len(series) < self._row_count:
                        # Pad with NaN
                        self._columns[col_name] = series.reindex(range(self._row_count))
        
        # Update other properties
        if unit is not None:
            metadata.unit = unit
        if description is not None:
            metadata.description = description
        if precision is not None:
            metadata.precision = precision
        
        # Emit signals
        if range_changed:
            self.dataChanged.emit(
                self.index(0, self._column_order.index(name)),
                self.index(self.rowCount() - 1, self._column_order.index(name))
            )
        self.headerDataChanged.emit(Qt.Orientation.Horizontal, 
                                    self._column_order.index(name), 
                                    self._column_order.index(name))
        self.layoutChanged.emit()
    
    def edit_derivative_column(self, name: str, new_name: Optional[str] = None,
                              numerator_column: Optional[str] = None,
                              denominator_column: Optional[str] = None,
                              description: Optional[str] = None,
                              precision: Optional[int] = None) -> None:
        """Edit properties of a DERIVATIVE column.
        
        Args:
            name: Current column name
            new_name: New name (if renaming)
            numerator_column: New numerator column name
            denominator_column: New denominator column name
            description: New description
            precision: New precision
            
        Raises:
            ColumnNotFoundError: If column doesn't exist
            ColumnExistsError: If new_name already exists
            ValueError: If column is not a DERIVATIVE column
        """
        if name not in self._columns:
            raise ColumnNotFoundError(name, self.get_column_names())
        
        metadata = self._metadata[name]
        if not metadata.is_derivative_column():
            raise ValueError(f"Column '{name}' is not a DERIVATIVE column")
        
        # Handle rename if requested
        if new_name and new_name != name:
            self.rename_column(name, new_name)
            name = new_name
            metadata = self._metadata[name]
        
        # Check if derivative configuration changed
        deriv_changed = False
        if numerator_column and numerator_column != metadata.derivative_numerator:
            if numerator_column not in self._columns:
                raise ColumnNotFoundError(numerator_column, self.get_column_names())
            metadata.derivative_numerator = numerator_column
            deriv_changed = True
        
        if denominator_column and denominator_column != metadata.derivative_denominator:
            if denominator_column not in self._columns:
                raise ColumnNotFoundError(denominator_column, self.get_column_names())
            metadata.derivative_denominator = denominator_column
            deriv_changed = True
        
        # Recalculate if configuration changed
        if deriv_changed:
            # Recalculate derivative
            num_col = metadata.derivative_numerator
            den_col = metadata.derivative_denominator
            
            if num_col and den_col:
                y_data = self._columns[num_col]
                x_data = self._columns[den_col]
                
                # Calculate derivative using forward difference
                dy = y_data.diff().shift(-1)
                dx = x_data.diff().shift(-1)
                
                with np.errstate(divide='ignore', invalid='ignore'):
                    dy_arr = np.asarray(dy, dtype=float)
                    dx_arr = np.asarray(dx, dtype=float)
                    derivative = pd.Series(dy_arr / dx_arr, dtype=float)
                
                derivative = derivative.replace([np.inf, -np.inf], np.nan)
                self._columns[name] = derivative
                
                # Update dependencies
                old_deps = self._dependencies.get(name, set())
                new_deps = {num_col, den_col}
                self._dependencies[name] = new_deps
                
                # Update dependents tracking
                for old_dep in old_deps:
                    if old_dep in self._dependents:
                        self._dependents[old_dep].discard(name)
                for new_dep in new_deps:
                    if new_dep not in self._dependents:
                        self._dependents[new_dep] = set()
                    self._dependents[new_dep].add(name)
        
        # Update other properties
        if description is not None:
            metadata.description = description
        if precision is not None:
            metadata.precision = precision
        
        # Emit signals
        if deriv_changed:
            self.dataChanged.emit(
                self.index(0, self._column_order.index(name)),
                self.index(self.rowCount() - 1, self._column_order.index(name))
            )
        self.headerDataChanged.emit(Qt.Orientation.Horizontal, 
                                    self._column_order.index(name), 
                                    self._column_order.index(name))
        self.layoutChanged.emit()
    
    def edit_interpolation_column(self, name: str, new_name: Optional[str] = None,
                                 x_column: Optional[str] = None,
                                 y_column: Optional[str] = None,
                                 method: Optional[str] = None,
                                 description: Optional[str] = None,
                                 precision: Optional[int] = None) -> None:
        """Edit properties of an INTERPOLATION column.
        
        Args:
            name: Current column name
            new_name: New name (if renaming)
            x_column: New X column name
            y_column: New Y column name
            method: New interpolation method
            description: New description
            precision: New precision
            
        Raises:
            ColumnNotFoundError: If column doesn't exist
            ColumnExistsError: If new_name already exists
            ValueError: If column is not an INTERPOLATION column or method is invalid
        """
        if name not in self._columns:
            raise ColumnNotFoundError(name, self.get_column_names())
        
        metadata = self._metadata[name]
        if not metadata.is_interpolation_column():
            raise ValueError(f"Column '{name}' is not an INTERPOLATION column")
        
        # Handle rename if requested
        if new_name and new_name != name:
            self.rename_column(name, new_name)
            name = new_name
            metadata = self._metadata[name]
        
        # Validate method if changed
        if method:
            valid_methods = ["linear", "cubic", "quadratic", "nearest"]
            if method not in valid_methods:
                raise ValueError(f"Invalid method '{method}'. Must be one of: {valid_methods}")
        
        # Check if interpolation configuration changed
        interp_changed = False
        
        if x_column and x_column != metadata.interp_x_column:
            if x_column not in self._columns:
                raise ColumnNotFoundError(x_column, self.get_column_names())
            metadata.interp_x_column = x_column
            interp_changed = True
        
        if y_column and y_column != metadata.interp_y_column:
            if y_column not in self._columns:
                raise ColumnNotFoundError(y_column, self.get_column_names())
            metadata.interp_y_column = y_column
            interp_changed = True
        
        if method and method != metadata.interp_method:
            metadata.interp_method = method
            interp_changed = True
        
        # Recalculate if configuration changed
        if interp_changed:
            x_col = metadata.interp_x_column
            y_col = metadata.interp_y_column
            method_str = metadata.interp_method or "linear"
            
            if x_col and y_col:
                # Get source data
                x_data = self._columns[x_col]
                y_data = self._columns[y_col]
                
                # Remove NaN values for interpolation
                mask = ~(x_data.isna() | y_data.isna())
                x_clean = x_data[mask]
                y_clean = y_data[mask]
                
                if len(x_clean) >= 2:
                    # Sort by X values
                    sort_idx = np.argsort(x_clean)
                    x_sorted = x_clean.iloc[sort_idx]
                    y_sorted = y_clean.iloc[sort_idx]
                    
                    # Create interpolation function
                    kind_map = {
                        "linear": "linear",
                        "cubic": "cubic",
                        "quadratic": "quadratic",
                        "nearest": "nearest"
                    }
                    interp_func = interpolate.interp1d(
                        x_sorted, 
                        y_sorted, 
                        kind=kind_map[method_str],
                        fill_value=np.nan,
                        bounds_error=False
                    )
                    
                    # Evaluate at x_data points
                    result = pd.Series(interp_func(x_data), dtype=float)
                    self._columns[name] = result
                    
                    # Update dependencies
                    old_deps = self._dependencies.get(name, set())
                    new_deps = {x_col, y_col}
                    self._dependencies[name] = new_deps
                    
                    # Update dependents tracking
                    for old_dep in old_deps:
                        if old_dep in self._dependents:
                            self._dependents[old_dep].discard(name)
                    for new_dep in new_deps:
                        if new_dep not in self._dependents:
                            self._dependents[new_dep] = set()
                        self._dependents[new_dep].add(name)
        
        # Update other properties
        if description is not None:
            metadata.description = description
        if precision is not None:
            metadata.precision = precision
        
        # Emit signals
        if interp_changed:
            self.dataChanged.emit(
                self.index(0, self._column_order.index(name)),
                self.index(self.rowCount() - 1, self._column_order.index(name))
            )
        self.headerDataChanged.emit(Qt.Orientation.Horizontal, 
                                    self._column_order.index(name), 
                                    self._column_order.index(name))
        self.layoutChanged.emit()
    
    def rename_column(self, old_name: str, new_name: str) -> None:
        """Rename a column.
        
        Args:
            old_name: Current column name
            new_name: New column name
            
        Raises:
            ColumnNotFoundError: If old_name doesn't exist
            ColumnExistsError: If new_name already exists
        """
        if old_name not in self._columns:
            raise ColumnNotFoundError(old_name, self.get_column_names())
        if new_name in self._columns:
            raise ColumnExistsError(new_name)
        
        # Update all structures
        self._columns[new_name] = self._columns.pop(old_name)
        self._metadata[new_name] = self._metadata.pop(old_name)
        self._metadata[new_name].name = new_name
        
        idx = self._column_order.index(old_name)
        self._column_order[idx] = new_name
        
        # Update dependency tracking
        if old_name in self._dependencies:
            self._dependencies[new_name] = self._dependencies.pop(old_name)
        if old_name in self._dependents:
            self._dependents[new_name] = self._dependents.pop(old_name)
        
        # Update references in other columns' dependencies
        for col_deps in self._dependencies.values():
            if old_name in col_deps:
                col_deps.remove(old_name)
                col_deps.add(new_name)
        for col_deps in self._dependents.values():
            if old_name in col_deps:
                col_deps.remove(old_name)
                col_deps.add(new_name)
        
        # TODO Phase 2: Update formulas that reference this column
        # self._update_formula_references(old_name, new_name)
        
        # Notify views and listeners
        self.layoutChanged.emit()
        self.columnRenamed.emit(old_name, new_name)
    
    def reorder_columns(self, new_order: List[str]) -> None:
        """Reorder columns.
        
        Args:
            new_order: List of column names in desired order
            
        Raises:
            ValueError: If new_order doesn't contain exactly the same columns
        """
        if set(new_order) != set(self._column_order):
            missing = set(self._column_order) - set(new_order)
            extra = set(new_order) - set(self._column_order)
            msg = "new_order must contain exactly the same columns. "
            if missing:
                msg += f"Missing: {', '.join(missing)}. "
            if extra:
                msg += f"Extra: {', '.join(extra)}."
            raise ValueError(msg)
        
        self._column_order = new_order.copy()
        
        # Notify views
        self.layoutChanged.emit()
    
    def get_column_names(self) -> List[str]:
        """Get list of all column names in order.
        
        Returns:
            List of column names
        """
        return self._column_order.copy()
    
    # ========================================================================
    # Global Variables Management
    # ========================================================================
    
    def set_variables(self, variables: dict[str, tuple[float, Optional[str]]]) -> None:
        """Set global variables/constants for use in formulas.
        
        Args:
            variables: Dictionary of {name: (value, unit)}
        
        Example:
            >>> model.set_variables({
            ...     'g': (9.81, 'm/s²'),
            ...     'pi': (3.14159, None),
            ...     'c': (299792458, 'm/s')
            ... })
        """
        self._variables = variables.copy()
        
        # Recalculate all calculated columns since constants may have changed
        for col_name in self._column_order:
            metadata = self._metadata[col_name]
            if metadata.is_calculated_column():
                self._recalculate_column(col_name)
    
    def get_variables(self) -> dict[str, tuple[float, Optional[str]]]:
        """Get current global variables.
        
        Returns:
            Dictionary of {name: (value, unit)}
        """
        return self._variables.copy()
    
    def add_variable(self, name: str, value: float, unit: Optional[str] = None) -> None:
        """Add or update a single global variable.
        
        Args:
            name: Variable name (e.g., 'g', 'pi')
            value: Numeric value
            unit: Optional physical unit
        """
        self._variables[name] = (value, unit)
        
        # Recalculate calculated columns that might use this variable
        for col_name in self._column_order:
            metadata = self._metadata[col_name]
            if metadata.is_calculated_column() and metadata.formula:
                if f"{{{name}}}" in metadata.formula:
                    self._recalculate_column(col_name)
    
    def remove_variable(self, name: str) -> None:
        """Remove a global variable.
        
        Args:
            name: Variable name to remove
            
        Raises:
            KeyError: If variable doesn't exist
        """
        if name not in self._variables:
            raise KeyError(f"Variable '{name}' not found")
        
        del self._variables[name]
        
        # Recalculate columns that used this variable
        for col_name in self._column_order:
            metadata = self._metadata[col_name]
            if metadata.is_calculated_column() and metadata.formula:
                if f"{{{name}}}" in metadata.formula:
                    self._recalculate_column(col_name)
    
    def get_column_metadata(self, name: str) -> ColumnMetadata:
        """Get metadata for a column.
        
        Args:
            name: Column name
            
        Returns:
            ColumnMetadata object
            
        Raises:
            ColumnNotFoundError: If column doesn't exist
        """
        if name not in self._metadata:
            raise ColumnNotFoundError(name, self.get_column_names())
        return self._metadata[name]
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert entire table to a Pandas DataFrame.
        
        Returns:
            DataFrame with all columns in display order
        """
        # Use column order to ensure consistent ordering
        return pd.DataFrame({name: self._columns[name] for name in self._column_order})
    
    # ========================================================================
    # Dependency Tracking (for Phase 2 formula engine)
    # ========================================================================
    
    def _register_dependency(self, dependent_col: str, depends_on_col: str) -> None:
        """Register that dependent_col depends on depends_on_col.
        
        This creates a directed edge in the dependency graph.
        
        Args:
            dependent_col: Name of column that depends on another
            depends_on_col: Name of column that is depended upon
        """
        if dependent_col not in self._dependencies:
            self._dependencies[dependent_col] = set()
        self._dependencies[dependent_col].add(depends_on_col)
        
        if depends_on_col not in self._dependents:
            self._dependents[depends_on_col] = set()
        self._dependents[depends_on_col].add(dependent_col)
    
    def _get_dependent_columns(self, name: str) -> List[str]:
        """Get list of columns that directly depend on this column.
        
        Args:
            name: Column name
            
        Returns:
            List of column names that depend on this column
        """
        return sorted(self._dependents.get(name, set()))
    
    def _get_recalculation_order(self, changed_col: str) -> List[str]:
        """Get columns to recalculate in dependency order.
        
        Uses breadth-first search to find all affected columns, then
        topologically sorts them to ensure correct calculation order.
        
        Args:
            changed_col: Name of column that changed
            
        Returns:
            List of column names in calculation order
            
        Note:
            This will be used in Phase 2 when formulas are implemented.
        """
        # Find all columns affected by this change (BFS)
        to_recalc = set()
        queue = [changed_col]
        visited = set()
        
        while queue:
            col = queue.pop(0)
            if col in visited:
                continue
            visited.add(col)
            
            if col in self._dependents:
                for dependent in self._dependents[col]:
                    if dependent not in to_recalc:
                        to_recalc.add(dependent)
                        queue.append(dependent)
        
        # Topological sort to get calculation order
        # Simple approach: repeatedly find columns with no dependencies in the subset
        sorted_cols = []
        remaining = to_recalc.copy()
        
        while remaining:
            # Find columns with no unresolved dependencies
            ready = []
            for col in remaining:
                deps = self._dependencies.get(col, set())
                unresolved_deps = deps & remaining
                if not unresolved_deps:
                    ready.append(col)
            
            if not ready:
                # Circular dependency detected
                raise ValueError(f"Circular dependency detected in columns: {remaining}")
            
            # Add ready columns to result and remove from remaining
            sorted_cols.extend(sorted(ready))
            remaining -= set(ready)
        
        return sorted_cols
    
    def _recalculate_column(self, name: str) -> None:
        """Recalculate a single column.
        
        Args:
            name: Column name to recalculate
        """
        metadata = self._metadata[name]
        
        # Recalculate CALCULATED columns
        if metadata.is_calculated_column():
            if not metadata.formula:
                return
            
            try:
                # Evaluate formula
                result = self._evaluate_formula(name, metadata.formula)
                
                # Update column data
                self._columns[name] = result
                
                # Emit signal for views to update
                first_idx = self.index(0, self._column_order.index(name))
                last_idx = self.index(self._row_count - 1, self._column_order.index(name))
                self.dataChanged.emit(first_idx, last_idx, [Qt.ItemDataRole.DisplayRole])
                
                # If uncertainty propagation is enabled, update uncertainty column
                if metadata.propagate_uncertainty:
                    uncert_name = f"{name}_u"
                    if uncert_name in self._columns:
                        uncert_values = self._calculate_propagated_uncertainty(name)
                        self._columns[uncert_name] = uncert_values
                        
                        # Emit signal for uncertainty column update
                        uncert_col_idx = self._column_order.index(uncert_name)
                        first_idx_u = self.index(0, uncert_col_idx)
                        last_idx_u = self.index(self._row_count - 1, uncert_col_idx)
                        self.dataChanged.emit(first_idx_u, last_idx_u, [Qt.ItemDataRole.DisplayRole])
                
            except Exception as e:
                self.errorOccurred.emit(name, f"Recalculation failed: {e}")
        
        # Recalculate DERIVATIVE columns
        elif metadata.is_derivative_column():
            if not metadata.derivative_numerator or not metadata.derivative_denominator:
                return
            
            try:
                numerator = metadata.derivative_numerator
                denominator = metadata.derivative_denominator
                
                # Get source column data
                y_data = self._columns[numerator]
                x_data = self._columns[denominator]
                
                # Calculate derivative (default to forward method for recalculation)
                dy = y_data.diff().shift(-1)  # y[i+1] - y[i]
                dx = x_data.diff().shift(-1)  # x[i+1] - x[i]
                
                # Compute derivative
                with np.errstate(divide='ignore', invalid='ignore'):
                    dy_arr = np.asarray(dy, dtype=float)
                    dx_arr = np.asarray(dx, dtype=float)
                    derivative = pd.Series(dy_arr / dx_arr, dtype=float)
                
                # Replace inf with NaN
                derivative = derivative.replace([np.inf, -np.inf], np.nan)
                
                # Update column data
                self._columns[name] = derivative
                
                # Emit signal for views to update
                first_idx = self.index(0, self._column_order.index(name))
                last_idx = self.index(self._row_count - 1, self._column_order.index(name))
                self.dataChanged.emit(first_idx, last_idx, [Qt.ItemDataRole.DisplayRole])
                
            except Exception as e:
                self.errorOccurred.emit(name, f"Derivative recalculation failed: {e}")
    
    def _evaluate_formula(self, column_name: str, formula: str) -> pd.Series:
        """Evaluate a formula and return the result as a Series.
        
        Args:
            column_name: Name of column being calculated (for error messages)
            formula: Formula string to evaluate
            
        Returns:
            Pandas Series with calculation results
            
        Raises:
            FormulaError: If evaluation fails
        """
        # Extract variable names from formula
        dependencies = self._formula_parser.extract_dependencies(formula)
        
        # Build variables dict from column data AND global variables
        variables = {}
        for dep in dependencies:
            if dep in self._columns:
                # Column reference
                variables[dep] = self._columns[dep]
            elif dep in self._variables:
                # Global variable/constant - broadcast scalar to all rows
                var_value, var_unit = self._variables[dep]
                variables[dep] = pd.Series([var_value] * self._row_count, dtype=float)
            else:
                # Check if it's a column or variable name
                available_cols = self.get_column_names()
                available_vars = list(self._variables.keys())
                error_msg = f"'{dep}' not found."
                if available_vars:
                    error_msg += f" Available columns: {', '.join(available_cols)}. "
                    error_msg += f"Available variables: {', '.join(available_vars)}."
                else:
                    error_msg += f" Available columns: {', '.join(available_cols)}."
                raise ColumnNotFoundError(dep, available_cols)
        
        # Evaluate formula (vectorized)
        result = self._formula_parser.evaluate(formula, variables)
        
        # Convert to Series if needed
        if not isinstance(result, pd.Series):
            if isinstance(result, np.ndarray):
                result = pd.Series(result, dtype=float)
            else:
                # Scalar result - broadcast to all rows
                result = pd.Series([result] * self._row_count, dtype=float)
        
        # Ensure correct length
        if len(result) != self._row_count:
            raise FormulaEvaluationError(
                f"Formula result length ({len(result)}) doesn't match table rows ({self._row_count})"
            )
        
        return result
    
    # ========================================================================
    # File I/O Methods
    # ========================================================================
    
    def save_to_json(self, filepath: str) -> None:
        """Save table to JSON format with full metadata preservation.
        
        This is the recommended native format for DataTableV2 as it preserves
        all metadata including formulas, column types, units, and configuration.
        
        Args:
            filepath: Path to JSON file to create
            
        Example:
            >>> model.save_to_json("data.json")
        """
        import json
        
        # Build JSON structure
        data_dict = {
            "version": "2.0.0",
            "config": {
                "default_precision": self._config.default_precision,
                "default_dtype": self._config.default_dtype.value,
                "auto_recalculate": self._config.auto_recalculate,
            },
            "columns": [],
            "data": {}
        }
        
        # Export column metadata
        for name in self._column_order:
            metadata = self._metadata[name]
            col_dict = {
                "name": metadata.name,
                "column_type": metadata.column_type.value,
                "dtype": metadata.dtype.value,
                "unit": metadata.unit,
                "description": metadata.description,
                "precision": metadata.precision,
                "editable": metadata.editable,
            }
            
            # Add type-specific fields
            if metadata.formula:
                col_dict["formula"] = metadata.formula
            
            if metadata.range_start is not None:
                col_dict["range_start"] = metadata.range_start
                col_dict["range_end"] = metadata.range_end
                col_dict["range_points"] = metadata.range_points
            
            if metadata.derivative_numerator is not None:
                # Already stored as column names
                col_dict["derivative_numerator"] = metadata.derivative_numerator
                col_dict["derivative_denominator"] = metadata.derivative_denominator
            
            data_dict["columns"].append(col_dict)
        
        # Export data
        for name in self._column_order:
            series = self._columns[name]
            # Convert to list, handling NaN/inf
            data_list = []
            for val in series:
                if pd.isna(val):
                    data_list.append(None)
                elif np.isinf(val):
                    data_list.append("inf" if val > 0 else "-inf")
                else:
                    data_list.append(val)
            data_dict["data"][name] = data_list
        
        # Write to file
        with open(filepath, 'w') as f:
            json.dump(data_dict, f, indent=2)
    
    def load_from_json(self, filepath: str) -> None:
        """Load table from JSON format.
        
        Clears existing data and loads from file. Recreates all columns
        with their metadata and data.
        
        Args:
            filepath: Path to JSON file to load
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If JSON format is invalid
            
        Example:
            >>> model.load_from_json("data.json")
        """
        import json
        
        # Read file
        with open(filepath, 'r') as f:
            data_dict = json.load(f)
        
        # Validate version (basic check)
        version = data_dict.get("version", "unknown")
        if not version.startswith("2."):
            raise ValueError(f"Unsupported file version: {version}")
        
        # Clear existing data
        self.beginResetModel()
        self._columns.clear()
        self._metadata.clear()
        self._column_order.clear()
        self._dependencies.clear()
        self._row_count = 0
        
        # Update config if present
        if "config" in data_dict:
            cfg = data_dict["config"]
            if "default_precision" in cfg:
                self._config.default_precision = cfg["default_precision"]
            if "default_dtype" in cfg:
                self._config.default_dtype = DataType(cfg["default_dtype"])
            if "auto_recalculate" in cfg:
                self._config.auto_recalculate = cfg["auto_recalculate"]
        
        # Track columns that need recalculation (CALCULATED/DERIVATIVE)
        columns_to_recalc = []
        
        # First pass: Create all columns with metadata
        for col_dict in data_dict["columns"]:
            name = col_dict["name"]
            col_type = ColumnType(col_dict["column_type"])
            dtype = DataType(col_dict["dtype"])
            
            # Build metadata
            metadata = ColumnMetadata(
                name=name,
                column_type=col_type,
                dtype=dtype,
                unit=col_dict.get("unit"),
                description=col_dict.get("description"),
                precision=col_dict.get("precision", self._config.default_precision),
                formula=col_dict.get("formula"),
                range_start=col_dict.get("range_start"),
                range_end=col_dict.get("range_end"),
                range_points=col_dict.get("range_points"),
                derivative_numerator=col_dict.get("derivative_numerator"),
                derivative_denominator=col_dict.get("derivative_denominator"),
            )
            
            # Store metadata
            self._metadata[name] = metadata
            self._column_order.append(name)
            
            # Load data
            data_list = data_dict["data"][name]
            # Convert None back to NaN, "inf" strings back to inf
            parsed_data = []
            for val in data_list:
                if val is None:
                    parsed_data.append(np.nan)
                elif val == "inf":
                    parsed_data.append(np.inf)
                elif val == "-inf":
                    parsed_data.append(-np.inf)
                else:
                    parsed_data.append(val)
            
            # Create Series with appropriate dtype
            if dtype == DataType.FLOAT:
                self._columns[name] = pd.Series(parsed_data, dtype=float)
            elif dtype == DataType.INTEGER:
                # Replace NaN with 0 for integers
                parsed_data = [0 if pd.isna(v) else int(v) for v in parsed_data]
                self._columns[name] = pd.Series(parsed_data, dtype='Int64')
            elif dtype == DataType.STRING:
                self._columns[name] = pd.Series(parsed_data, dtype=str)
            elif dtype == DataType.BOOLEAN:
                self._columns[name] = pd.Series(parsed_data, dtype=bool)
            elif dtype == DataType.CATEGORY:
                self._columns[name] = pd.Series(parsed_data, dtype='category')
            
            # Update row count
            if len(self._columns[name]) > self._row_count:
                self._row_count = len(self._columns[name])
            
            # Track CALCULATED/DERIVATIVE columns for recalculation
            if col_type in (ColumnType.CALCULATED, ColumnType.DERIVATIVE):
                columns_to_recalc.append(name)
        
        # Second pass: Derivative columns already have column names, no need to resolve
        
        # Third pass: Register dependencies for CALCULATED/DERIVATIVE columns
        for name in columns_to_recalc:
            metadata = self._metadata[name]
            if metadata.is_calculated_column() and metadata.formula:
                deps = self._formula_parser.extract_dependencies(metadata.formula)
                for dep in deps:
                    if dep in self._metadata:
                        if dep not in self._dependencies:
                            self._dependencies[dep] = set()
                        self._dependencies[dep].add(name)
            elif metadata.is_derivative_column():
                # Register dependencies for derivative columns
                if metadata.derivative_numerator is not None and metadata.derivative_denominator is not None:
                    if metadata.derivative_numerator not in self._dependencies:
                        self._dependencies[metadata.derivative_numerator] = set()
                    self._dependencies[metadata.derivative_numerator].add(name)
                    if metadata.derivative_denominator not in self._dependencies:
                        self._dependencies[metadata.derivative_denominator] = set()
                    self._dependencies[metadata.derivative_denominator].add(name)
        
        self.endResetModel()
        
        # Recalculate CALCULATED/DERIVATIVE columns
        for name in columns_to_recalc:
            self._recalculate_column(name)
    
    def save_to_csv(self, filepath: str, include_metadata: bool = True) -> None:
        """Save table to CSV format.
        
        Args:
            filepath: Path to CSV file to create
            include_metadata: If True, includes metadata as comment header
            
        Example:
            >>> model.save_to_csv("data.csv")
            >>> model.save_to_csv("data.csv", include_metadata=False)  # Data only
        """
        df = self.to_dataframe()
        
        if include_metadata:
            # Write metadata as comments, then data
            with open(filepath, 'w') as f:
                # Write metadata header
                f.write("# DataTableV2 CSV Export\n")
                f.write(f"# Version: 2.0.0\n")
                f.write("# Columns:\n")
                for name in self._column_order:
                    metadata = self._metadata[name]
                    f.write(f"#   {name}: type={metadata.column_type.value}, "
                           f"dtype={metadata.dtype.value}")
                    if metadata.unit:
                        f.write(f", unit={metadata.unit}")
                    if metadata.formula:
                        f.write(f", formula={metadata.formula}")
                    f.write("\n")
                f.write("#\n")
            
            # Append data
            df.to_csv(filepath, mode='a', index=False)
        else:
            # Just write data
            df.to_csv(filepath, index=False)
    
    def load_from_csv(self, filepath: str, has_metadata: bool = True) -> None:
        """Load table from CSV format.
        
        Args:
            filepath: Path to CSV file to load
            has_metadata: If True, expects metadata comment header
            
        Note:
            CSV format has limitations - only preserves data and basic metadata.
            For full metadata preservation, use JSON format.
            
        Example:
            >>> model.load_from_csv("data.csv")
            >>> model.load_from_csv("simple_data.csv", has_metadata=False)
        """
        if has_metadata:
            # Parse metadata from comments
            # For now, just load data - full metadata parsing is complex
            # TODO: Implement metadata parsing from CSV comments
            df = pd.read_csv(filepath, comment='#')
        else:
            df = pd.read_csv(filepath)
        
        # Clear existing data
        self.beginResetModel()
        self._columns.clear()
        self._metadata.clear()
        self._column_order.clear()
        self._dependencies.clear()
        self._row_count = len(df)
        
        # Create columns from DataFrame
        for col_name in df.columns:
            series = df[col_name]
            
            # Infer data type
            if pd.api.types.is_integer_dtype(series):
                dtype = DataType.INTEGER
            elif pd.api.types.is_float_dtype(series):
                dtype = DataType.FLOAT
            elif pd.api.types.is_bool_dtype(series):
                dtype = DataType.BOOLEAN
            elif pd.api.types.is_string_dtype(series):
                dtype = DataType.STRING
            else:
                # Default to STRING for unknown types
                dtype = DataType.STRING
            
            # Create metadata
            metadata = ColumnMetadata(
                name=col_name,
                column_type=ColumnType.DATA,
                dtype=dtype,
            )
            
            self._metadata[col_name] = metadata
            self._column_order.append(col_name)
            self._columns[col_name] = series.copy()
        
        self.endResetModel()
    
    def save_to_excel(self, filepath: str, sheet_name: str = "Data") -> None:
        """Save table to Excel format with formatting.
        
        Creates two sheets:
        - Data sheet with actual values
        - Metadata sheet with column properties
        
        Args:
            filepath: Path to Excel file to create (.xlsx)
            sheet_name: Name for the data sheet
            
        Example:
            >>> model.save_to_excel("data.xlsx")
            >>> model.save_to_excel("results.xlsx", sheet_name="Results")
        """
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment
        except ImportError:
            raise ImportError("openpyxl is required for Excel export. Install with: pip install openpyxl")
        
        # Get data as DataFrame
        df = self.to_dataframe()
        
        # Write to Excel with pandas
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Write data sheet
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Write metadata sheet
            metadata_rows = []
            metadata_rows.append(["Column Name", "Type", "Data Type", "Unit", "Formula", "Description"])
            for name in self._column_order:
                meta = self._metadata[name]
                metadata_rows.append([
                    meta.name,
                    meta.column_type.value,
                    meta.dtype.value,
                    meta.unit or "",
                    meta.formula or "",
                    meta.description or ""
                ])
            
            meta_df = pd.DataFrame(metadata_rows[1:], columns=metadata_rows[0])
            meta_df.to_excel(writer, sheet_name="Metadata", index=False)
            
            # Get workbook for formatting
            workbook = writer.book
            data_sheet = workbook[sheet_name]
            meta_sheet = workbook["Metadata"]
            
            # Format data sheet headers
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_font = Font(color="FFFFFF", bold=True)
            for cell in data_sheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center")
            
            # Format metadata sheet headers
            for cell in meta_sheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center")
            
            # Auto-adjust column widths
            for sheet in [data_sheet, meta_sheet]:
                for column in sheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    sheet.column_dimensions[column_letter].width = adjusted_width
    
    def load_from_excel(self, filepath: str, sheet_name: str = "Data") -> None:
        """Load table from Excel format.
        
        Loads data from specified sheet. If a Metadata sheet exists, attempts
        to restore column properties.
        
        Args:
            filepath: Path to Excel file to load (.xlsx)
            sheet_name: Name of the data sheet to load
            
        Note:
            For full metadata preservation, use JSON format.
            
        Example:
            >>> model.load_from_excel("data.xlsx")
            >>> model.load_from_excel("results.xlsx", sheet_name="Results")
        """
        # Read data sheet
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        
        # Try to read metadata sheet if it exists
        metadata_dict = {}
        try:
            meta_df = pd.read_excel(filepath, sheet_name="Metadata")
            for _, row in meta_df.iterrows():
                col_name = row["Column Name"]
                metadata_dict[col_name] = {
                    "column_type": row.get("Type", "data"),
                    "dtype": row.get("Data Type", "float64"),
                    "unit": row.get("Unit", None),
                    "formula": row.get("Formula", None),
                    "description": row.get("Description", None),
                }
        except:
            # No metadata sheet or error reading it
            pass
        
        # Clear existing data
        self.beginResetModel()
        self._columns.clear()
        self._metadata.clear()
        self._column_order.clear()
        self._dependencies.clear()
        self._row_count = len(df)
        
        # Create columns from DataFrame
        for col_name in df.columns:
            series = df[col_name]
            
            # Use metadata if available
            if col_name in metadata_dict:
                col_type = ColumnType(metadata_dict[col_name]["column_type"])
                dtype = DataType(metadata_dict[col_name]["dtype"])
                unit = metadata_dict[col_name]["unit"]
                formula = metadata_dict[col_name]["formula"]
                description = metadata_dict[col_name]["description"]
            else:
                # Infer from data
                col_type = ColumnType.DATA
                if pd.api.types.is_integer_dtype(series):
                    dtype = DataType.INTEGER
                elif pd.api.types.is_float_dtype(series):
                    dtype = DataType.FLOAT
                elif pd.api.types.is_bool_dtype(series):
                    dtype = DataType.BOOLEAN
                else:
                    dtype = DataType.STRING
                unit = None
                formula = None
                description = None
            
            # Create metadata
            metadata = ColumnMetadata(
                name=col_name,
                column_type=col_type,
                dtype=dtype,
                unit=unit,
                formula=formula,
                description=description,
            )
            
            self._metadata[col_name] = metadata
            self._column_order.append(col_name)
            self._columns[col_name] = series.copy()
        
        self.endResetModel()
    
    # ========================================================================
    # Clipboard Operations
    # ========================================================================
    
    def copy_selection_to_tsv(self, selection: list[tuple[int, int]]) -> str:
        """Convert selected cells to TSV format for clipboard.
        
        Args:
            selection: List of (row, col) tuples representing selected cells
            
        Returns:
            TSV-formatted string with selected cell values
        """
        if not selection:
            return ""
        
        # Group by row and column
        rows_dict = {}
        for row, col in selection:
            if row not in rows_dict:
                rows_dict[row] = {}
            rows_dict[row][col] = row, col
        
        # Build TSV output
        lines = []
        for row in sorted(rows_dict.keys()):
            cols_dict = rows_dict[row]
            min_col = min(cols_dict.keys())
            max_col = max(cols_dict.keys())
            
            # Build line with all columns in range (fill gaps with empty strings)
            values = []
            for col in range(min_col, max_col + 1):
                if col in cols_dict:
                    idx = self.index(row, col)
                    value = self.data(idx, Qt.ItemDataRole.DisplayRole)
                    values.append(str(value) if value is not None else "")
                else:
                    values.append("")
            
            lines.append("\t".join(values))
        
        return "\n".join(lines)
    
    def paste_from_tsv(
        self,
        tsv_data: str,
        start_row: int,
        start_col: int,
        skip_readonly: bool = True
    ) -> tuple[int, int, list[str]]:
        """Paste TSV data into table starting at given position.
        
        Uses undo/redo command pattern for the entire paste operation.
        
        Args:
            tsv_data: Tab-separated values string
            start_row: Starting row index
            start_col: Starting column index
            skip_readonly: If True, skip read-only columns (CALCULATED, RANGE, DERIVATIVE)
            
        Returns:
            Tuple of (rows_pasted, cells_pasted, errors)
            errors: List of error messages for cells that couldn't be pasted
        """
        if not tsv_data:
            return 0, 0, []
        
        # Use PasteCommand for undo/redo support
        from .commands import PasteCommand
        command = PasteCommand(self, tsv_data, start_row, start_col, skip_readonly)
        self._command_manager.execute(command)
        
        # Return stats
        rows_pasted = len(set(row for row, col in command.old_values.keys()))
        cells_pasted = len(command.old_values)
        errors = []  # Errors are handled during command execution
        
        return rows_pasted, cells_pasted, errors
    
    def clear_selection(self, selection: list[tuple[int, int]]) -> int:
        """Clear selected cells (set to NaN for numeric, empty string for text).
        
        Uses undo/redo command pattern for the entire clear operation.
        
        Args:
            selection: List of (row, col) tuples
            
        Returns:
            Number of cells cleared
        """
        # Use ClearSelectionCommand for undo/redo support
        from .commands import ClearSelectionCommand
        command = ClearSelectionCommand(self, selection)
        self._command_manager.execute(command)
        
        return len(command.old_values)
    
    # ========================================================================
    # Undo/Redo Operations
    # ========================================================================
    
    def undo(self) -> bool:
        """Undo the last operation.
        
        Returns:
            True if undo was successful, False if nothing to undo
        """
        # Set bypass flag to prevent creating new undo commands during undo
        self._bypass_undo = True
        try:
            return self._command_manager.undo()
        finally:
            self._bypass_undo = False
    
    def redo(self) -> bool:
        """Redo the last undone operation.
        
        Returns:
            True if redo was successful, False if nothing to redo
        """
        # Set bypass flag to prevent creating new undo commands during redo
        self._bypass_undo = True
        try:
            return self._command_manager.redo()
        finally:
            self._bypass_undo = False
    
    def can_undo(self) -> bool:
        """Check if undo is available.
        
        Returns:
            True if there are operations to undo
        """
        return self._command_manager.can_undo()
    
    def can_redo(self) -> bool:
        """Check if redo is available.
        
        Returns:
            True if there are operations to redo
        """
        return self._command_manager.can_redo()
    
    def clear_undo_history(self) -> None:
        """Clear all undo/redo history."""
        self._command_manager.clear()
    
    def get_undo_description(self) -> Optional[str]:
        """Get description of next undo operation.
        
        Returns:
            Description string or None if nothing to undo
        """
        return self._command_manager.get_undo_description()
    
    def get_redo_description(self) -> Optional[str]:
        """Get description of next redo operation.
        
        Returns:
            Description string or None if nothing to redo
        """
        return self._command_manager.get_redo_description()
    
    def _calculate_propagated_uncertainty(self, column_name: str) -> pd.Series:
        """Calculate propagated uncertainty for a calculated column.
        
        Args:
            column_name: Name of the calculated column
            
        Returns:
            Series of propagated uncertainties
        """
        # Import from centralized utils module
        from utils.uncertainty import FormulaToSymPy
        import sympy as sp
        
        metadata = self._metadata.get(column_name)
        if not metadata or not metadata.is_calculated_column() or not metadata.formula:
            # Return NaN series if not a calculated column
            return pd.Series([np.nan] * self._row_count)
        
        # Extract dependencies from formula
        dependencies = self._formula_parser.extract_dependencies(metadata.formula)
        
        # Collect values and uncertainties for each dependency
        values = {}
        uncertainties = {}
        
        for dep in dependencies:
            if dep not in self._columns:
                continue
            
            # Add the value series
            values[dep] = self._columns[dep]
            
            # Check if uncertainty column exists
            uncert_col_name = f"{dep}_u"
            if uncert_col_name in self._columns:
                uncertainties[dep] = self._columns[uncert_col_name]
        
        # If no uncertainties available, return zeros
        if not uncertainties:
            return pd.Series([0.0] * self._row_count)
        
        # Calculate propagated uncertainty using centralized function
        try:
            # Prepare formula by replacing {var} with var for SymPy
            formula_for_sympy = metadata.formula
            for dep in dependencies:
                formula_for_sympy = formula_for_sympy.replace(f"{{{dep}}}", dep)
            
            # Convert to SymPy expression
            sympy_expr = FormulaToSymPy.convert(formula_for_sympy, list(dependencies))
            
            # Calculate partial derivatives
            partial_derivs = {}
            for var_name in dependencies:
                var_symbol = sp.Symbol(var_name)
                partial_derivs[var_name] = sp.diff(sympy_expr, var_symbol)
            
            # Calculate uncertainty for each row
            result_uncertainties = []
            
            for i in range(self._row_count):
                # Get values for this row
                row_values = {var: values[var].iloc[i] for var in dependencies}
                row_uncerts = {var: uncertainties.get(var, pd.Series([0.0] * self._row_count)).iloc[i]
                              for var in dependencies}
                
                # If any input value is NaN, result uncertainty is NaN
                if any(pd.isna(row_values[var]) for var in dependencies):
                    result_uncertainties.append(np.nan)
                    continue
                
                # Calculate variance contributions
                variance = 0.0
                
                for var_name in dependencies:
                    # Skip if no uncertainty for this variable
                    if var_name not in uncertainties:
                        continue
                    
                    # Get value and uncertainty for this variable
                    var_uncert = row_uncerts[var_name]
                    
                    # Skip if uncertainty is NaN
                    if pd.isna(var_uncert):
                        continue
                    
                    # Evaluate partial derivative at this point
                    try:
                        # Substitute all variable values
                        subs_dict = {sp.Symbol(name): val for name, val in row_values.items()
                                    if not pd.isna(val)}
                        deriv_value = float(partial_derivs[var_name].evalf(subs=subs_dict))
                        
                        # Add contribution to variance: (∂f/∂xᵢ * δxᵢ)²
                        contribution = deriv_value * var_uncert
                        variance += contribution ** 2
                        
                    except Exception:
                        # If evaluation fails (e.g., division by zero), mark as NaN
                        variance = np.nan
                        break
                
                # Combined uncertainty = sqrt(variance)
                if pd.isna(variance):
                    result_uncertainties.append(np.nan)
                else:
                    result_uncertainties.append(np.sqrt(variance))
            
            return pd.Series(result_uncertainties)
        except Exception as e:
            # If calculation fails, return NaN
            self.errorOccurred.emit(column_name, f"Uncertainty calculation failed: {e}")
            return pd.Series([np.nan] * self._row_count)