"""
AdvancedDataTableWidget - A sophisticated table widget for data manipulation.

This module contains the main widget class that provides:
- Data columns with units and diminutives
- Calculated columns with formula support
- Uncertainty columns linked to data columns
- Interactive editing and recalculation
"""

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QMessageBox, QInputDialog, QDialog
from PySide6.QtCore import Signal, Qt, QAbstractItemModel
from PySide6.QtGui import QColor
from typing import Optional, List, Union
import re
import math

from .models import (
    AdvancedColumnType,
    AdvancedColumnDataType,
    ColumnMetadata,
)
from .constants import (
    DEFAULT_NUMERIC_PRECISION,
    ERROR_PREFIX,
    FORMULA_REFERENCE_PATTERN,
    BACKWARD_COMPAT_PATTERN,
    SYMBOL_DATA,
    SYMBOL_CALCULATED,
    SYMBOL_DERIVATIVE,
    SYMBOL_UNCERTAINTY,
    SYMBOL_INTERPOLATION,
    SYMBOL_RANGE,
    UNCERTAINTY_HEADER_TEXT
)
from .formula_evaluator import SafeFormulaEvaluator
from .data_column_dialog import DataColumnEditorDialog
from .formula_dialog import FormulaEditorDialog
from .variables_dialog import VariablesDialog
from .derivative_dialog import DerivativeEditorDialog
from .context_menu import HeaderContextMenu, CellContextMenu, EmptyTableContextMenu
from utils.units import format_unit_pretty


class AdvancedDataTableWidget(QTableWidget):
    # Signals for external components
    columnAdded = Signal(int, str, AdvancedColumnType, AdvancedColumnDataType)
    columnRemoved = Signal(int)
    formulaChanged = Signal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Unified column metadata storage
        self._columns: List[ColumnMetadata] = []
        
        # Global variables/constants storage {diminutive: (value, unit)}
        self._variables: dict = {}

        # UI Setup
        self.horizontalHeader().sectionDoubleClicked.connect(self.edit_header)
        # Show a dedicated context menu on header right-click
        self.horizontalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.horizontalHeader().customContextMenuRequested.connect(self._on_header_context_menu)

        # Also enable a context menu on table body (column-based)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_table_context_menu)

        # Enable change tracking for calculated columns
        self.itemChanged.connect(self._on_item_changed)

        # Track when we're internally updating to avoid infinite loops
        self._updating_calculations = False

    def _on_header_context_menu(self, pos):
        """Show context menu for a header at header-local pos."""
        header = self.horizontalHeader()
        col = header.logicalIndexAt(pos)
        if col < 0:
            return
        global_pos = header.mapToGlobal(pos)
        menu = HeaderContextMenu(self, col, parent=self)
        menu.exec(global_pos)

    def _on_table_context_menu(self, pos):
        """Show context menu for table body - distinguishes between cell and empty area."""
        # Get the item at this position
        item = self.itemAt(pos)
        
        if item:
            # Clicked on a cell - show cell context menu
            row = item.row()
            col = item.column()
            global_pos = self.viewport().mapToGlobal(pos)
            menu = CellContextMenu(self, row, col, parent=self)
            menu.exec(global_pos)
        else:
            # Clicked on empty area - show empty table context menu
            global_pos = self.viewport().mapToGlobal(pos)
            menu = EmptyTableContextMenu(self, parent=self)
            menu.exec(global_pos)

    def keyPressEvent(self, event):
        """Handle key press events - auto-create new row when editing last cell and pressing Enter."""
        from PySide6.QtCore import Qt
        
        # Check if Return/Enter was pressed
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            current_row = self.currentRow()
            current_col = self.currentColumn()
            
            # Check if we're on the last row and there are columns
            if current_row == self.rowCount() - 1 and self.columnCount() > 0:
                # Call parent's keyPressEvent first to handle the default behavior
                super().keyPressEvent(event)
                
                # Check where we are after the default behavior
                new_row = self.currentRow()
                new_col = self.currentColumn()
                
                # If Enter moved us to a new column on the same row (last row)
                # OR if we're at the last column and would normally stay put
                if new_row == current_row and new_col != current_col:
                    # User is continuing entry on the last row, do nothing yet
                    pass
                elif new_row == current_row and new_col == current_col:
                    # We're at the last cell (last row, last column) or Enter didn't move us
                    # Check if we're at the last column
                    if current_col == self.columnCount() - 1:
                        # Add a new row and move to the first cell of that row
                        self.insertRow(self.rowCount())
                        self.setCurrentCell(self.rowCount() - 1, 0)
                return
        
        # For all other keys, use default behavior
        super().keyPressEvent(event)

    def addColumn(self, header_label: str, col_type: AdvancedColumnType, data_type: AdvancedColumnDataType,
                  diminutive: Optional[str] = None, unit: Optional[str] = None, description: Optional[str] = None, reference_column_index: Optional[int] = None, formula: Optional[str] = None, insert_position: Optional[int] = None) -> int:
        """Add a new column to the table with specified header and types.
        
        Args:
            header_label: Initial name (will be replaced by diminutive in header)
            diminutive: Short name used for display and formulas
            description: Full description shown as tooltip
            insert_position: If specified, insert at this position. Otherwise append at end.
        """
        # Determine insertion position
        if insert_position is not None:
            col_index = insert_position
        else:
            col_index = self.columnCount()
        
        self.insertColumn(col_index)

        # Generate diminutive if not provided - use header_label as base
        if diminutive is None:
            diminutive = self._generate_diminutive(header_label, col_index)

        # Ensure diminutive is unique
        diminutive = self._ensure_unique_diminutive(diminutive, col_index)
        
        # If no description provided, use header_label as description
        if description is None:
            description = header_label

        # For uncertainty columns, always use "±" as display
        if col_type == AdvancedColumnType.UNCERTAINTY:
            header_item = QTableWidgetItem(UNCERTAINTY_HEADER_TEXT)
        else:
            # Use diminutive as the display name (shown in header)
            header_item = QTableWidgetItem(diminutive)
            
        if description:
            header_item.setToolTip(description)
        self.setHorizontalHeaderItem(col_index, header_item)

        # Create metadata object
        metadata = ColumnMetadata(
            column_type=col_type,
            data_type=data_type,
            diminutive=diminutive,
            description=description,
            unit=unit,
            formula=formula,
            uncertainty_reference=reference_column_index
        )

        # Handle specific column types
        if col_type == AdvancedColumnType.UNCERTAINTY:
            if reference_column_index is None:
                raise ValueError("Uncertainty columns must have a reference column index")
            # Adjust reference index if we inserted before it
            adjusted_ref_index = reference_column_index
            if col_index <= reference_column_index:
                adjusted_ref_index = reference_column_index + 1
            
            if not (0 <= adjusted_ref_index < len(self._columns)):
                raise ValueError(f"Reference column {adjusted_ref_index} does not exist")
            
            # Allow uncertainty columns to reference both DATA and CALCULATED columns
            ref_type = self._columns[adjusted_ref_index].column_type
            if ref_type not in (AdvancedColumnType.DATA, AdvancedColumnType.CALCULATED):
                raise ValueError("Uncertainty columns can only reference DATA or CALCULATED columns")
            
            # Update the reference index
            metadata.uncertainty_reference = adjusted_ref_index

            # Uncertainty columns should be numerical
            metadata.data_type = AdvancedColumnDataType.NUMERICAL

        elif col_type == AdvancedColumnType.CALCULATED:
            # Calculated columns are typically numerical
            metadata.data_type = AdvancedColumnDataType.NUMERICAL

        # Insert metadata at the correct position
        self._columns.insert(col_index, metadata)
        
        # Update reference indices in other columns if we inserted before them
        if col_type == AdvancedColumnType.UNCERTAINTY or insert_position is not None:
            for i, col_meta in enumerate(self._columns):
                if i != col_index and col_meta.uncertainty_reference is not None:
                    # If the reference is at or after the insertion point, increment it
                    if col_meta.uncertainty_reference >= col_index:
                        col_meta.uncertainty_reference += 1

        # Ensure at least one row exists
        if self.rowCount() == 0:
            self.insertRow(0)

        # Emit signal
        self.columnAdded.emit(col_index, header_label, col_type, data_type)
        
        # Update column header to show unit (if applicable)
        self._update_column_header(col_index)

        # Recalculate columns as needed based on type
        if col_type == AdvancedColumnType.DATA:
            # Recalculate any existing calculated columns if this is a data column they might reference
            self._recalculate_all_calculated_columns()
        elif col_type == AdvancedColumnType.CALCULATED:
            # Recalculate the newly added calculated column
            self._recalculate_column(col_index)
        elif col_type == AdvancedColumnType.DERIVATIVE:
            # Recalculate the newly added derivative column
            self._recalculate_derivative_column(col_index)
        elif col_type == AdvancedColumnType.INTERPOLATION:
            # Recalculate the newly added interpolation column
            self._recalculate_interpolation_column(col_index)
        elif col_type == AdvancedColumnType.RANGE:
            # Recalculate the newly added range column
            self._recalculate_range_column(col_index)

        return col_index

    def addUncertaintyColumn(self, reference_column_index: int, header_label: Optional[str] = None, diminutive: Optional[str] = None) -> int:
        """Add an uncertainty column linked to a reference DATA column.
        
        This method is for creating user-editable uncertainty columns for DATA columns.
        For calculated columns with automatic uncertainty propagation, use the 
        formula editor dialog to enable uncertainty propagation instead.
        
        The uncertainty column will be inserted immediately after the reference column
        and will have "±" as its display name.
        
        Args:
            reference_column_index: Index of the DATA column to add uncertainty for
            header_label: Optional header label (always uses "±")
            diminutive: Optional diminutive (auto-generated if not provided)
            
        Returns:
            Index of the created uncertainty column
            
        Raises:
            ValueError: If reference column is not a DATA column
        """
        if not (0 <= reference_column_index < len(self._columns)):
            raise ValueError(f"Reference column {reference_column_index} does not exist")

        if self._columns[reference_column_index].column_type != AdvancedColumnType.DATA:
            raise ValueError("This method only works for DATA columns. For calculated columns, enable uncertainty propagation in the formula editor.")

        # Always use "+/-" as the header label
        header_label = UNCERTAINTY_HEADER_TEXT

        # Generate default diminutive if not provided
        if diminutive is None:
            ref_diminutive = self._columns[reference_column_index].diminutive
            diminutive = f"u_{ref_diminutive}" if ref_diminutive else f"u_col{reference_column_index}"

        # Use the same unit as the reference column
        ref_unit = self._columns[reference_column_index].unit

        # Insert immediately after the reference column
        insert_position = reference_column_index + 1

        return self.addColumn(
            header_label,
            AdvancedColumnType.UNCERTAINTY,
            AdvancedColumnDataType.NUMERICAL,
            diminutive=diminutive,
            unit=ref_unit,
            reference_column_index=reference_column_index,
            insert_position=insert_position
        )

    def addCalculatedColumn(self, header_label: str, formula: str, diminutive: Optional[str] = None, unit: Optional[str] = None, description: Optional[str] = None, propagate_uncertainty: bool = False) -> int:
        """Add a calculated column with a formula."""
        return self.addColumn(
            header_label,
            AdvancedColumnType.CALCULATED,
            AdvancedColumnDataType.NUMERICAL,
            diminutive=diminutive,
            unit=unit,
            description=description,
            formula=formula
        )
    
    def addDerivativeColumn(self, header_label: str, numerator_index: int, denominator_index: int, 
                           diminutive: Optional[str] = None, unit: Optional[str] = None, 
                           description: Optional[str] = None) -> int:
        """Add a derivative column that calculates discrete differences dy/dx.
        
        The derivative is calculated as:
        - For row i: result[i] = (y[i+1] - y[i]) / (x[i+1] - x[i])
        - Uses forward differences for all rows except the last
        - Uses backward difference for the last row
        
        Args:
            header_label: Header label for the column
            numerator_index: Index of the column to use as numerator (y)
            denominator_index: Index of the column to use as denominator (x)
            diminutive: Short name for formulas (auto-generated if None)
            unit: Unit of the derivative (auto-calculated if None)
            description: Description for tooltip
            
        Returns:
            Index of the created derivative column
            
        Raises:
            ValueError: If column indices are invalid or same
        """
        if not (0 <= numerator_index < len(self._columns)):
            raise ValueError(f"Numerator column {numerator_index} does not exist")
        
        if not (0 <= denominator_index < len(self._columns)):
            raise ValueError(f"Denominator column {denominator_index} does not exist")
        
        if numerator_index == denominator_index:
            raise ValueError("Numerator and denominator must be different columns")
        
        # Generate diminutive if not provided
        if diminutive is None:
            num_dim = self._columns[numerator_index].diminutive
            den_dim = self._columns[denominator_index].diminutive
            diminutive = f"d{num_dim}_d{den_dim}"
        
        # Create the column
        col_index = self.addColumn(
            header_label,
            AdvancedColumnType.DERIVATIVE,
            AdvancedColumnDataType.NUMERICAL,
            diminutive=diminutive,
            unit=unit,
            description=description
        )
        
        # Store derivative configuration
        self._columns[col_index].derivative_numerator = numerator_index
        self._columns[col_index].derivative_denominator = denominator_index
        
        # Calculate initial values
        self._recalculate_derivative_column(col_index)
        
        return col_index
    
    def addRangeColumn(self, header_label: str, start: float, end: float, points: int,
                      diminutive: Optional[str] = None, unit: Optional[str] = None,
                      description: Optional[str] = None) -> int:
        """Add a RANGE column that auto-generates evenly spaced values.
        
        Creates a column with N evenly spaced values from start to end (inclusive).
        Unlike DATA columns, RANGE columns automatically recalculate when parameters change.
        This is useful for creating independent variable columns (x-axis data).
        
        Args:
            header_label: Header label for the column
            start: Starting value (a)
            end: Ending value (b)
            points: Number of points (N) - must be at least 2
            diminutive: Short name for formulas (auto-generated if None)
            unit: Unit of measurement
            description: Description for tooltip
            
        Returns:
            Index of the created column
            
        Raises:
            ValueError: If points < 2 or points > 1000
        """
        if points < 2:
            raise ValueError("Number of points must be at least 2")
        
        if points > 1000:
            raise ValueError("Number of points is limited to 1000")
        
        # Create the column as RANGE type
        col_index = self.addColumn(
            header_label,
            AdvancedColumnType.RANGE,
            AdvancedColumnDataType.NUMERICAL,
            diminutive=diminutive,
            unit=unit,
            description=description
        )
        
        # Store range parameters in metadata
        metadata = self._columns[col_index]
        metadata.range_start = start
        metadata.range_end = end
        metadata.range_points = points
        
        # Calculate and populate values
        self._recalculate_range_column(col_index)
        
        return col_index
    
    def addInterpolationColumn(self, header_label: str, interpolation_x_column: int, 
                              interpolation_y_column: int, interpolation_method: str = 'linear',
                              interpolation_evaluation_column: Optional[int] = None,
                              diminutive: Optional[str] = None, unit: Optional[str] = None,
                              description: Optional[str] = None) -> int:
        """Add an INTERPOLATION column that interpolates values from source columns.
        
        Creates a column that uses scipy.interpolate to calculate values by interpolating
        between points defined by X and Y source columns, evaluated at positions from
        the evaluation column (or the X column if not specified).
        
        Args:
            header_label: Header label for the column
            interpolation_x_column: Index of the column containing X values for interpolation data
            interpolation_y_column: Index of the column containing Y values for interpolation data
            interpolation_method: Interpolation method ('linear', 'cubic', 'quadratic', 'nearest')
            interpolation_evaluation_column: Index of the column containing X values for evaluation (optional, defaults to interpolation_x_column)
            diminutive: Short name for formulas (auto-generated if None)
            unit: Unit of measurement (auto-detected from Y column if None)
            description: Description for tooltip
            
        Returns:
            Index of the created interpolation column
            
        Raises:
            ValueError: If column indices are invalid or same
        """
        if not (0 <= interpolation_x_column < len(self._columns)):
            raise ValueError(f"X column {interpolation_x_column} does not exist")
        
        if not (0 <= interpolation_y_column < len(self._columns)):
            raise ValueError(f"Y column {interpolation_y_column} does not exist")
        
        if interpolation_evaluation_column is not None and not (0 <= interpolation_evaluation_column < len(self._columns)):
            raise ValueError(f"Evaluation column {interpolation_evaluation_column} does not exist")
        
        if interpolation_evaluation_column is None:
            interpolation_evaluation_column = interpolation_x_column
        
        # Generate diminutive if not provided
        if diminutive is None:
            y_dim = self._columns[interpolation_y_column].diminutive
            diminutive = f"{y_dim}_interp"
        
        # Auto-detect unit from Y column if not provided
        if unit is None:
            unit = self._columns[interpolation_y_column].unit
        
        # Create the column
        col_index = self.addColumn(
            header_label,
            AdvancedColumnType.INTERPOLATION,
            AdvancedColumnDataType.NUMERICAL,
            diminutive=diminutive,
            unit=unit,
            description=description
        )
        
        # Store interpolation configuration
        metadata = self._columns[col_index]
        metadata.interpolation_x_column = interpolation_x_column
        metadata.interpolation_y_column = interpolation_y_column
        metadata.interpolation_evaluation_column = interpolation_evaluation_column
        metadata.interpolation_method = interpolation_method
        
        # Calculate initial values
        self._recalculate_interpolation_column(col_index)
        
        return col_index
    
    def _create_uncertainty_column_for_calculated(self, calculated_column_index: int) -> int:
        """Create an uncertainty column for a calculated column.
        
        This is similar to addUncertaintyColumn but works for calculated columns.
        The uncertainty values will be automatically calculated using uncertainty propagation.
        
        Args:
            calculated_column_index: Index of the calculated column
            
        Returns:
            Index of the created uncertainty column
        """
        if not (0 <= calculated_column_index < len(self._columns)):
            raise ValueError(f"Calculated column {calculated_column_index} does not exist")

        if self._columns[calculated_column_index].column_type != AdvancedColumnType.CALCULATED:
            raise ValueError("This method only works for CALCULATED columns")

        # Use "+/-" as the header label
        header_label = "±"

        # Generate diminutive
        ref_diminutive = self._columns[calculated_column_index].diminutive
        diminutive = f"u_{ref_diminutive}" if ref_diminutive else f"u_col{calculated_column_index}"

        # Use the same unit as the calculated column
        ref_unit = self._columns[calculated_column_index].unit

        # Insert immediately after the calculated column
        insert_position = calculated_column_index + 1

        return self.addColumn(
            header_label,
            AdvancedColumnType.UNCERTAINTY,
            AdvancedColumnDataType.NUMERICAL,
            diminutive=diminutive,
            unit=ref_unit,
            reference_column_index=calculated_column_index,
            insert_position=insert_position
        )

    def getColumnType(self, index: int) -> Optional[AdvancedColumnType]:
        """Get the type of the column at the given index."""
        if 0 <= index < len(self._columns):
            return self._columns[index].column_type
        return None
    
    def getColumnDataType(self, index: int) -> Optional[AdvancedColumnDataType]:
        """Get the data type of the column at the given index."""
        if 0 <= index < len(self._columns):
            return self._columns[index].data_type
        return None
    
    def getColumnFormula(self, index: int) -> Optional[str]:
        """Get the formula of a calculated column."""
        if 0 <= index < len(self._columns):
            return self._columns[index].formula
        return None
    
    def getUncertaintyReference(self, uncertainty_column_index: int) -> Optional[int]:
        """Get the reference column index for an uncertainty column."""
        if 0 <= uncertainty_column_index < len(self._columns):
            return self._columns[uncertainty_column_index].uncertainty_reference
        return None
    
    def getColumnDiminutive(self, index: int) -> Optional[str]:
        """Get the diminutive form of a column (used as the display name)."""
        if 0 <= index < len(self._columns):
            return self._columns[index].diminutive
        return None
    
    def getColumnUnit(self, index: int) -> Optional[str]:
        """Get the unit of a column."""
        if 0 <= index < len(self._columns):
            return self._columns[index].unit
        return None
    
    def getColumnDescription(self, index: int) -> Optional[str]:
        """Get the description of a column."""
        if 0 <= index < len(self._columns):
            return self._columns[index].description
        return None
    
    def setColumnDiminutive(self, index: int, diminutive: str) -> Optional[str]:
        """Set the diminutive form of a column."""
        if 0 <= index < len(self._columns):
            # Ensure uniqueness
            unique_dim = self._ensure_unique_diminutive(diminutive, index)
            self._columns[index].diminutive = unique_dim
            # Update any formulas that might reference this column
            self._update_formulas_after_diminutive_change(index, unique_dim)
            return unique_dim
        return None
    
    def setColumnUnit(self, index: int, unit: Optional[str]) -> None:
        """Set the unit of a column."""
        if 0 <= index < len(self._columns):
            self._columns[index].unit = unit
    
    def setColumnDescription(self, index: int, description: Optional[str]) -> None:
        """Set the description of a column."""
        if 0 <= index < len(self._columns):
            self._columns[index].description = description
            # Update tooltip
            self._update_column_header(index)
    
    def getColumnPropagateUncertainty(self, index: int) -> bool:
        """Get whether a calculated column should propagate uncertainty."""
        if 0 <= index < len(self._columns):
            return self._columns[index].propagate_uncertainty
        return False
    
    def setColumnPropagateUncertainty(self, index: int, propagate: bool) -> None:
        """Set whether a calculated column should propagate uncertainty."""
        if 0 <= index < len(self._columns):
            self._columns[index].propagate_uncertainty = propagate
    
    def hasUncertaintyColumn(self, data_column_index: int) -> tuple[bool, Optional[int]]:
        """Check if a data column has an associated uncertainty column."""
        for idx, metadata in enumerate(self._columns):
            if (metadata.column_type == AdvancedColumnType.UNCERTAINTY and
                metadata.uncertainty_reference == data_column_index):
                return True, idx
        return False, None
    
    def setColumnFormula(self, column_index: int, formula: str) -> None:
        """Set or update the formula for a calculated column.
        
        Recalculates the column and any dependent columns in left-to-right order.
        """
        if (0 <= column_index < len(self._columns) and
            self._columns[column_index].column_type != AdvancedColumnType.CALCULATED):
            raise ValueError("Can only set formulas for calculated columns")

        self._columns[column_index].formula = formula
        self._recalculate_column(column_index)
        # Recalculate any columns that depend on this calculated column
        self._recalculate_dependent_columns(column_index)
        self.formulaChanged.emit(column_index, formula)

    def _recalculate_column(self, column_index: int) -> None:
        """Recalculate all values in a calculated column based on its formula."""
        formula = self.getColumnFormula(column_index)
        if not formula:
            return

        # Prevent infinite loops during calculation updates
        self._updating_calculations = True
        calculated_unit = None  # Track the calculated unit from the first row
        
        try:
            for row in range(self.rowCount()):
                try:
                    result, result_unit = self._evaluate_formula_with_units(formula, row)
                    
                    # Store the calculated unit from the first successful calculation
                    if calculated_unit is None and result_unit:
                        calculated_unit = result_unit
                        # Update the column's unit metadata
                        if 0 <= column_index < len(self._columns):
                            self._columns[column_index].unit = calculated_unit
                            # Update the header to include the unit
                            self._update_calculated_column_header(column_index)
                    
                    # Format the result appropriately
                    if result is not None:
                        if isinstance(result, float):
                            # Check for inf or nan
                            if math.isinf(result) or math.isnan(result):
                                display_text = str(result)
                                item = QTableWidgetItem(display_text)
                                item.setData(0, result)
                                item.setForeground(QColor(255, 0, 0))  # Red text for inf/nan
                                item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                                self.setItem(row, column_index, item)
                                continue
                            # Round to reasonable precision for display
                            display_text = f"{result:{DEFAULT_NUMERIC_PRECISION}}"
                        else:
                            display_text = str(result)
                    else:
                        display_text = ""

                    item = QTableWidgetItem(display_text)
                    item.setData(0, result)  # Store actual numeric value
                    # Make calculated columns non-editable but selectable
                    item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                    self.setItem(row, column_index, item)
                    
                    # Calculate uncertainty if propagation is enabled
                    if 0 <= column_index < len(self._columns):
                        metadata = self._columns[column_index]
                        if metadata.propagate_uncertainty:
                            self._calculate_and_update_uncertainty(column_index, row, formula)
                            
                except Exception as e:
                    error_item = QTableWidgetItem(f"{ERROR_PREFIX}{str(e)}")
                    # Make error items non-editable but selectable and color them red
                    error_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                    error_item.setForeground(QColor(255, 0, 0))  # Red text for errors
                    self.setItem(row, column_index, error_item)
        finally:
            self._updating_calculations = False
    
    def _recalculate_derivative_column(self, column_index: int) -> None:
        """Recalculate all values in a derivative column using discrete differences.
        
        Calculates dy/dx where:
        - For row i (except last): derivative[i] = (y[i+1] - y[i]) / (x[i+1] - x[i])
        - For last row: derivative[n-1] = (y[n-1] - y[n-2]) / (x[n-1] - x[n-2])
        
        Args:
            column_index: Index of the derivative column to recalculate
        """
        if not (0 <= column_index < len(self._columns)):
            return
        
        metadata = self._columns[column_index]
        if metadata.column_type != AdvancedColumnType.DERIVATIVE:
            return
        
        num_idx = metadata.derivative_numerator
        den_idx = metadata.derivative_denominator
        
        if num_idx is None or den_idx is None:
            return
        
        # Prevent infinite loops during calculation updates
        self._updating_calculations = True
        
        try:
            num_rows = self.rowCount()
            if num_rows < 2:
                # Need at least 2 rows to calculate a derivative
                return
            
            for row in range(num_rows):
                try:
                    # Determine which rows to use for the difference
                    if row < num_rows - 1:
                        # Forward difference: use current and next row
                        row1, row2 = row, row + 1
                    else:
                        # Last row: use backward difference
                        row1, row2 = row - 1, row
                    
                    # Get values from numerator column
                    num_item1 = self.item(row1, num_idx)
                    num_item2 = self.item(row2, num_idx)
                    
                    # Get values from denominator column
                    den_item1 = self.item(row1, den_idx)
                    den_item2 = self.item(row2, den_idx)
                    
                    # Check if all items exist and have values
                    if not all([num_item1, num_item2, den_item1, den_item2]):
                        self.setItem(row, column_index, QTableWidgetItem(""))
                        continue
                    
                    # Extract numeric values
                    try:
                        num_text1 = num_item1.text() if num_item1 else ""
                        num_text2 = num_item2.text() if num_item2 else ""
                        den_text1 = den_item1.text() if den_item1 else ""
                        den_text2 = den_item2.text() if den_item2 else ""
                        
                        y1 = float(num_text1)
                        y2 = float(num_text2)
                        x1 = float(den_text1)
                        x2 = float(den_text2)
                    except (ValueError, AttributeError):
                        self.setItem(row, column_index, QTableWidgetItem(""))
                        continue
                    
                    # Calculate differences
                    dy = y2 - y1
                    dx = x2 - x1
                    
                    # Avoid division by zero
                    if abs(dx) < 1e-10:
                        error_item = QTableWidgetItem(f"{ERROR_PREFIX}dx=0")
                        error_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                        error_item.setForeground(QColor(255, 0, 0))  # Red text for errors
                        self.setItem(row, column_index, error_item)
                        continue
                    
                    # Calculate derivative
                    derivative = dy / dx
                    
                    # Check for inf or nan
                    if math.isinf(derivative) or math.isnan(derivative):
                        display_text = str(derivative)
                        item = QTableWidgetItem(display_text)
                        item.setData(0, derivative)
                        item.setForeground(QColor(255, 0, 0))  # Red text for inf/nan
                        item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                        self.setItem(row, column_index, item)
                        continue
                    
                    # Format and display
                    display_text = f"{derivative:{DEFAULT_NUMERIC_PRECISION}}"
                    item = QTableWidgetItem(display_text)
                    item.setData(0, derivative)  # Store actual numeric value
                    # Make derivative columns non-editable but selectable
                    item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                    self.setItem(row, column_index, item)
                    
                except Exception as e:
                    error_item = QTableWidgetItem(f"{ERROR_PREFIX}{str(e)}")
                    error_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                    error_item.setForeground(QColor(255, 0, 0))  # Red text for errors
                    self.setItem(row, column_index, error_item)
        finally:
            self._updating_calculations = False
    
    def _recalculate_range_column(self, column_index: int) -> None:
        """Recalculate all values in a RANGE column with evenly spaced values.
        
        Generates N evenly spaced values from start to end (inclusive).
        Ensures the table has enough rows to accommodate all points.
        
        Args:
            column_index: Index of the range column to recalculate
        """
        if not (0 <= column_index < len(self._columns)):
            return
        
        metadata = self._columns[column_index]
        if metadata.column_type != AdvancedColumnType.RANGE:
            return
        
        if metadata.range_start is None or metadata.range_end is None or metadata.range_points is None:
            return
        
        start = metadata.range_start
        end = metadata.range_end
        points = metadata.range_points
        
        # Prevent infinite loops during calculation updates
        self._updating_calculations = True
        
        try:
            # Ensure table has enough rows
            current_rows = self.rowCount()
            if current_rows < points:
                self.setRowCount(points)
            
            # Calculate step size
            step = (end - start) / (points - 1) if points > 1 else 0
            
            # Populate values
            for i in range(points):
                value = start + i * step
                display_text = f"{value:{DEFAULT_NUMERIC_PRECISION}}"
                item = QTableWidgetItem(display_text)
                item.setData(0, value)  # Store actual numeric value
                # Make range columns non-editable but selectable
                item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                self.setItem(i, column_index, item)
            
        finally:
            self._updating_calculations = False
    
    def _recalculate_interpolation_column(self, column_index: int) -> None:
        """Recalculate all values in an INTERPOLATION column.
        
        Uses scipy.interpolate to interpolate values from source X and Y columns.
        
        Args:
            column_index: Index of the interpolation column to recalculate
        """
        if not (0 <= column_index < len(self._columns)):
            return
        
        metadata = self._columns[column_index]
        if metadata.column_type != AdvancedColumnType.INTERPOLATION:
            return
        
        x_col_idx = metadata.interpolation_x_column
        y_col_idx = metadata.interpolation_y_column
        eval_col_idx = metadata.interpolation_evaluation_column
        if eval_col_idx is None:
            eval_col_idx = metadata.interpolation_x_column
        if eval_col_idx is None:
            return
        method = metadata.interpolation_method or 'linear'
        
        if x_col_idx is None or y_col_idx is None:
            return
        
        # Prevent infinite loops during calculation updates
        self._updating_calculations = True
        
        try:
            from scipy.interpolate import interp1d
            
            num_rows = self.rowCount()
            if num_rows < 2:
                return
            
            # Collect X and Y data points from source columns
            x_data = []
            y_data = []
            
            for row in range(num_rows):
                x_item = self.item(row, x_col_idx)
                y_item = self.item(row, y_col_idx)
                
                if x_item and y_item:
                    try:
                        x_text = x_item.text().strip()
                        y_text = y_item.text().strip()
                        
                        # Skip empty cells
                        if not x_text or not y_text:
                            continue
                        
                        x_val = float(x_text)
                        y_val = float(y_text)
                        x_data.append(x_val)
                        y_data.append(y_val)
                    except (ValueError, AttributeError):
                        continue
            
            # Need at least 2 points for interpolation
            if len(x_data) < 2:
                for row in range(num_rows):
                    error_item = QTableWidgetItem(f"{ERROR_PREFIX}Need ≥2 data points")
                    error_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                    error_item.setForeground(QColor(255, 0, 0))
                    self.setItem(row, column_index, error_item)
                return
            
            # Sort data by X values (required for interpolation)
            import numpy as np
            sorted_indices = np.argsort(x_data)
            x_data = [x_data[i] for i in sorted_indices]
            y_data = [y_data[i] for i in sorted_indices]
            
            # Create interpolation function
            try:
                # Map method names to scipy kind parameter
                kind_map = {
                    'linear': 'linear',
                    'cubic': 'cubic',
                    'quadratic': 'quadratic',
                    'nearest': 'nearest'
                }
                kind = kind_map.get(method, 'linear')
                
                # For cubic/quadratic, need at least 4/3 points respectively
                if kind == 'cubic' and len(x_data) < 4:
                    kind = 'linear'
                elif kind == 'quadratic' and len(x_data) < 3:
                    kind = 'linear'
                
                # Note: fill_value can be 'extrapolate' or a numeric value
                f_interp = interp1d(x_data, y_data, kind=kind, fill_value='extrapolate')  # type: ignore
                
            except Exception as e:
                for row in range(num_rows):
                    error_item = QTableWidgetItem(f"{ERROR_PREFIX}{str(e)}")
                    error_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                    error_item.setForeground(QColor(255, 0, 0))
                    self.setItem(row, column_index, error_item)
                return
            
            # Apply interpolation to each row using evaluation column
            for row in range(num_rows):
                try:
                    # Get X value for this row from evaluation column
                    eval_item = self.item(row, eval_col_idx)
                    if not eval_item:
                        self.setItem(row, column_index, QTableWidgetItem(""))
                        continue
                    
                    eval_text = eval_item.text().strip()
                    if not eval_text:
                        self.setItem(row, column_index, QTableWidgetItem(""))
                        continue
                    
                    x_val = float(eval_text)
                    
                    # Interpolate
                    y_interp = float(f_interp(x_val))
                    
                    # Check for inf or nan
                    if math.isinf(y_interp) or math.isnan(y_interp):
                        display_text = str(y_interp)
                        item = QTableWidgetItem(display_text)
                        item.setData(0, y_interp)
                        item.setForeground(QColor(255, 0, 0))
                        item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                        self.setItem(row, column_index, item)
                        continue
                    
                    # Format and display
                    display_text = f"{y_interp:{DEFAULT_NUMERIC_PRECISION}}"
                    item = QTableWidgetItem(display_text)
                    item.setData(0, y_interp)
                    # Make interpolation columns non-editable but selectable
                    item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                    self.setItem(row, column_index, item)
                    
                except Exception as e:
                    # More helpful error messages
                    error_msg = str(e)
                    if "out of bounds" in error_msg.lower():
                        error_msg = "Out of bounds"
                    error_item = QTableWidgetItem(f"{ERROR_PREFIX}{error_msg}")
                    error_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                    error_item.setForeground(QColor(255, 0, 0))
                    self.setItem(row, column_index, error_item)
        
        finally:
            self._updating_calculations = False
    
    def _update_column_header(self, column_index: int) -> None:
        """Update the header of any column to include its type symbol and unit."""
        if 0 <= column_index < len(self._columns):
            metadata = self._columns[column_index]
            
            # Get type symbol for visual indication
            type_symbol = self._get_column_type_symbol(metadata.column_type)
            
            # Handle uncertainty columns - they always show "±"
            if metadata.column_type == AdvancedColumnType.UNCERTAINTY:
                header_item = self.horizontalHeaderItem(column_index)
                if header_item:
                    header_item.setText(f"{type_symbol}±")
                    # Set tooltip to show which column this is the uncertainty for
                    if metadata.uncertainty_reference is not None and 0 <= metadata.uncertainty_reference < len(self._columns):
                        ref_metadata = self._columns[metadata.uncertainty_reference]
                        ref_diminutive = ref_metadata.diminutive
                        ref_unit = ref_metadata.unit
                        
                        if ref_unit and ref_unit.strip():
                            pretty_unit = format_unit_pretty(ref_unit, use_dot=True, use_superscript=True)
                            tooltip = f"Uncertainty of {ref_diminutive} [{pretty_unit}]"
                        else:
                            tooltip = f"Uncertainty of {ref_diminutive}"
                        
                        header_item.setToolTip(tooltip)
                return
            
            # Use diminutive as the header base
            diminutive = metadata.diminutive
            unit = metadata.unit
            
            # Add unit if present - format with pretty UTF-8 characters
            if unit and unit.strip():
                pretty_unit = format_unit_pretty(unit, use_dot=True, use_superscript=True)
                new_header = f"{type_symbol}{diminutive} [{pretty_unit}]"
            else:
                new_header = f"{type_symbol}{diminutive}"
            
            # Update header item
            header_item = self.horizontalHeaderItem(column_index)
            if header_item:
                header_item.setText(new_header)
                # Set tooltip to description
                if metadata.description:
                    header_item.setToolTip(metadata.description)
                else:
                    header_item.setToolTip("")

    def _get_column_type_symbol(self, column_type: AdvancedColumnType) -> str:
        """Get Unicode symbol for column type.
        
        Uses scientific/mathematical symbols to indicate column type:
        - ● (black circle) for DATA columns (measured/input data)
        - ƒ (script f) for CALCULATED columns (function/formula)
        - σ (sigma) for UNCERTAINTY columns (standard deviation/error)
        - ∂ (partial derivative) for DERIVATIVE columns (discrete differences dy/dx)
        - ⊶ for INTERPOLATION columns (interpolated values)
        - ⋯ (horizontal ellipsis) for RANGE columns (auto-generated evenly spaced values)
        
        Args:
            column_type: Type of column
            
        Returns:
            Unicode symbol as prefix with trailing space
        """
        symbol_map = {
            AdvancedColumnType.DATA: SYMBOL_DATA,
            AdvancedColumnType.CALCULATED: SYMBOL_CALCULATED,
            AdvancedColumnType.UNCERTAINTY: SYMBOL_UNCERTAINTY,
            AdvancedColumnType.DERIVATIVE: SYMBOL_DERIVATIVE,
            AdvancedColumnType.INTERPOLATION: SYMBOL_INTERPOLATION,
            AdvancedColumnType.RANGE: SYMBOL_RANGE,
        }
        return symbol_map.get(column_type, "")

    def _update_calculated_column_header(self, column_index: int) -> None:
        """Update the header of a calculated column to include its unit.
        
        Deprecated: Use _update_column_header instead.
        """
        self._update_column_header(column_index)

    def _evaluate_formula(self, formula: str, row_index: int) -> Union[int, float]:
        """Evaluate a formula for a specific row using diminutives (without unit support)."""
        result, _ = self._evaluate_formula_with_units(formula, row_index)
        return result

    def _evaluate_formula_with_units(self, formula: str, row_index: int) -> tuple[Union[int, float], str]:
        """Evaluate a formula for a specific row using diminutives, with unit-aware calculation.
        
        Returns:
            Tuple of (result_value, result_unit) where result_unit is the calculated unit string
        """
        from typing import Dict, Tuple, Optional
        
        # Build variables dict with values and units
        variables_with_units: Dict[str, Tuple[Union[int, float], Optional[str]]] = {}
        
        # First, add global variables/constants
        for var_name, (var_value, var_unit) in self._variables.items():
            variables_with_units[var_name] = (var_value, var_unit)
        
        # Extract all column references from the formula
        # Primary format: {diminutive}
        refs = re.findall(FORMULA_REFERENCE_PATTERN, formula)
        # Backward compatibility: [name_or_index]
        refs.extend(re.findall(BACKWARD_COMPAT_PATTERN, formula))
        
        # Remove duplicates
        refs = list(set(refs))
        
        for ref in refs:
            # Skip if this is already defined as a global variable
            if ref in self._variables:
                continue  # Already added to variables_with_units
                
            # Find the column index
            col_idx = self._find_column_by_diminutive(ref)
            if col_idx is None:
                # Fall back to trying as column index for backward compatibility
                try:
                    col_idx = int(ref)
                    if col_idx >= self.columnCount() or col_idx < 0:
                        raise ValueError(f"Column index {col_idx} out of range")
                except ValueError:
                    # Try as display name for backward compatibility
                    col_idx = self._find_column_by_name(ref)
                    if col_idx is None:
                        # Not a column, not a variable - this is an error
                        if ref not in self._variables:
                            raise ValueError(f"Column or variable '{ref}' not found")
                        else:
                            continue  # It's a variable, skip column processing
            
            # Get the value
            item = self.item(row_index, col_idx)
            value = 0.0
            if item is not None:
                try:
                    value = float(item.text())
                except ValueError:
                    value = 0.0
            
            # Get the unit for this column
            unit = None
            if 0 <= col_idx < len(self._columns):
                unit = self._columns[col_idx].unit
            
            # Column values override global variables with same name
            variables_with_units[ref] = (value, unit)
        
        # Replace column references in the formula
        def replace_column_ref(match):
            ref = match.group(1)
            return ref  # Just return the variable name, SafeFormulaEvaluator will handle it
        
        # Replace column references with simple variable names
        formula_evaluated = re.sub(FORMULA_REFERENCE_PATTERN, replace_column_ref, formula)
        formula_evaluated = re.sub(BACKWARD_COMPAT_PATTERN, replace_column_ref, formula_evaluated)
        
        # Evaluate with units
        try:
            result, result_unit = SafeFormulaEvaluator.evaluate_with_units(
                formula_evaluated,
                variables_with_units
            )
            return (result, result_unit)
        except Exception as e:
            # If unit-aware evaluation fails, try to fall back to simple evaluation
            # This happens if units are incompatible or not defined properly
            try:
                result = SafeFormulaEvaluator.evaluate(formula_evaluated, {
                    ref: value for ref, (value, _) in variables_with_units.items()
                })
                return (result, '')
            except Exception:
                # Both unit-aware and dimensionless evaluation failed
                # Re-raise the original unit-aware error as it's more informative
                raise e

    def _find_column_by_name(self, name):
        """Find column index by header name."""
        for col in range(self.columnCount()):
            header_item = self.horizontalHeaderItem(col)
            if header_item and header_item.text() == name:
                return col
        return None
    
    def _find_column_by_diminutive(self, diminutive: str) -> Optional[int]:
        """Find column index by diminutive form."""
        for idx, metadata in enumerate(self._columns):
            if metadata.diminutive == diminutive:
                return idx
        return None
    
    def _calculate_and_update_uncertainty(self, calculated_column_index: int, row_index: int, formula: str) -> None:
        """Calculate uncertainty for a calculated column using propagation of uncertainties.
        
        Args:
            calculated_column_index: Index of the calculated column
            row_index: Row to calculate uncertainty for
            formula: The formula used to calculate the value
        """
        from utils.uncertainty import UncertaintyCalculator
        from typing import Dict, Tuple, Optional
        
        # Find the uncertainty column for this calculated column
        has_uncertainty, uncertainty_col_index = self.hasUncertaintyColumn(calculated_column_index)
        if not has_uncertainty or uncertainty_col_index is None:
            return  # No uncertainty column to update
        
        try:
            # Build variables dict with values and units
            values: Dict[str, Tuple[float, Optional[str]]] = {}
            uncertainties: Dict[str, Tuple[float, Optional[str]]] = {}
            
            # First, add global variables/constants
            for var_name, (var_value, var_unit) in self._variables.items():
                values[var_name] = (var_value, var_unit)
                # Global variables have no uncertainty
            
            # Extract all column references from the formula
            refs = re.findall(FORMULA_REFERENCE_PATTERN, formula)
            refs.extend(re.findall(BACKWARD_COMPAT_PATTERN, formula))
            refs = list(set(refs))
            
            for ref in refs:
                # Skip if this is already defined as a global variable
                if ref in self._variables:
                    continue
                
                # Find the column index
                col_idx = self._find_column_by_diminutive(ref)
                if col_idx is None:
                    try:
                        col_idx = int(ref)
                        if col_idx >= self.columnCount() or col_idx < 0:
                            continue
                    except ValueError:
                        col_idx = self._find_column_by_name(ref)
                        if col_idx is None:
                            continue
                
                # Get the value
                item = self.item(row_index, col_idx)
                value = 0.0
                if item is not None:
                    try:
                        value = float(item.text())
                    except ValueError:
                        value = 0.0
                
                # Get the unit for this column
                unit = None
                if 0 <= col_idx < len(self._columns):
                    unit = self._columns[col_idx].unit
                
                values[ref] = (value, unit)
                
                # Check if this column has an uncertainty column
                has_unc, unc_col_idx = self.hasUncertaintyColumn(col_idx)
                if has_unc and unc_col_idx is not None:
                    # Get the uncertainty value
                    unc_item = self.item(row_index, unc_col_idx)
                    uncertainty_value = 0.0
                    if unc_item is not None:
                        try:
                            uncertainty_value = float(unc_item.text())
                        except ValueError:
                            uncertainty_value = 0.0
                    
                    uncertainties[ref] = (uncertainty_value, unit)
            
            # Replace column references with simple variable names
            def replace_column_ref(match):
                ref = match.group(1)
                return ref
            
            formula_evaluated = re.sub(FORMULA_REFERENCE_PATTERN, replace_column_ref, formula)
            formula_evaluated = re.sub(BACKWARD_COMPAT_PATTERN, replace_column_ref, formula_evaluated)
            
            # Calculate uncertainty if we have any input uncertainties
            if uncertainties:
                result_uncertainty, result_unit = UncertaintyCalculator.calculate_uncertainty_with_units(
                    formula_evaluated,
                    values,
                    uncertainties
                )
                
                # Format and set the uncertainty value
                if isinstance(result_uncertainty, float):
                    # Check for inf or nan
                    if math.isinf(result_uncertainty) or math.isnan(result_uncertainty):
                        display_text = str(result_uncertainty)
                        unc_item = QTableWidgetItem(display_text)
                        unc_item.setData(0, result_uncertainty)
                        unc_item.setForeground(QColor(255, 0, 0))  # Red text for inf/nan
                        unc_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                    else:
                        display_text = f"{result_uncertainty:{DEFAULT_NUMERIC_PRECISION}}"
                        unc_item = QTableWidgetItem(display_text)
                        unc_item.setData(0, result_uncertainty)
                        unc_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                else:
                    display_text = str(result_uncertainty)
                    unc_item = QTableWidgetItem(display_text)
                    unc_item.setData(0, result_uncertainty)
                    unc_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                
                # Temporarily allow setting without triggering recalculation
                old_updating = self._updating_calculations
                self._updating_calculations = True
                super().setItem(row_index, uncertainty_col_index, unc_item)
                self._updating_calculations = old_updating
            else:
                # No input uncertainties, set to empty or zero
                unc_item = QTableWidgetItem("")
                unc_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                
                old_updating = self._updating_calculations
                self._updating_calculations = True
                super().setItem(row_index, uncertainty_col_index, unc_item)
                self._updating_calculations = old_updating
                
        except Exception as e:
            # If uncertainty calculation fails, show error in uncertainty column
            error_item = QTableWidgetItem(f"{ERROR_PREFIX}{str(e)}")
            error_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            error_item.setForeground(QColor(255, 0, 0))  # Red text for errors
            
            old_updating = self._updating_calculations
            self._updating_calculations = True
            super().setItem(row_index, uncertainty_col_index, error_item)
            self._updating_calculations = old_updating

    def _on_item_changed(self, item):
        """Handle item changes to trigger recalculation of dependent calculated columns."""
        if item is None or self._updating_calculations:
            return
        
        changed_col = item.column()
        changed_row = item.row()
        
        col_type = self.getColumnType(changed_col)
        
        # If a data column changed, recalculate dependent calculated columns
        if col_type == AdvancedColumnType.DATA:
            self._recalculate_dependent_columns(changed_col)
        # If an uncertainty column changed, recalculate dependent calculated columns
        # that use the data column this uncertainty is for
        elif col_type == AdvancedColumnType.UNCERTAINTY:
            # Find the data/calculated column this uncertainty references
            if 0 <= changed_col < len(self._columns):
                metadata = self._columns[changed_col]
                if metadata.uncertainty_reference is not None:
                    # Recalculate all calculated columns that depend on the referenced column
                    self._recalculate_dependent_columns(metadata.uncertainty_reference)
    

    def _recalculate_dependent_columns(self, changed_column: int) -> None:
        """Recalculate all columns that depend on the changed column.
        
        This includes:
        - CALCULATED columns that reference the changed column in their formula
        - DERIVATIVE columns that use the changed column as numerator or denominator
        - INTERPOLATION columns that use the changed column as x_data, y_data, or x_eval
        
        Columns are recalculated in left-to-right order to respect dependencies.
        """
        for idx, metadata in enumerate(self._columns):
            should_recalculate = False
            
            # Check CALCULATED columns
            if (metadata.column_type == AdvancedColumnType.CALCULATED and
                metadata.formula and self._formula_references_column(metadata.formula, changed_column)):
                should_recalculate = True
            
            # Check DERIVATIVE columns
            elif (metadata.column_type == AdvancedColumnType.DERIVATIVE and
                  (metadata.derivative_numerator == changed_column or 
                   metadata.derivative_denominator == changed_column)):
                should_recalculate = True
            
            # Check INTERPOLATION columns
            elif (metadata.column_type == AdvancedColumnType.INTERPOLATION and
                  (metadata.interpolation_x_column == changed_column or
                   metadata.interpolation_y_column == changed_column or
                   metadata.interpolation_evaluation_column == changed_column)):
                should_recalculate = True
            
            if should_recalculate:
                if metadata.column_type == AdvancedColumnType.CALCULATED:
                    self._recalculate_column(idx)
                elif metadata.column_type == AdvancedColumnType.DERIVATIVE:
                    self._recalculate_derivative_column(idx)
                elif metadata.column_type == AdvancedColumnType.INTERPOLATION:
                    self._recalculate_interpolation_column(idx)

    def _recalculate_all_calculated_columns(self) -> None:
        """Recalculate all calculated, derivative, and interpolation columns."""
        for idx, metadata in enumerate(self._columns):
            if metadata.column_type == AdvancedColumnType.CALCULATED:
                self._recalculate_column(idx)
            elif metadata.column_type == AdvancedColumnType.DERIVATIVE:
                self._recalculate_derivative_column(idx)
            elif metadata.column_type == AdvancedColumnType.INTERPOLATION:
                self._recalculate_interpolation_column(idx)
    
    def _generate_diminutive(self, display_name: str, col_index: int) -> str:
        """Generate a diminutive form from the display name."""
        # Remove common units and symbols
        clean_name = display_name.lower()
        clean_name = clean_name.replace('(', '').replace(')', '').replace('°', '').replace('%', '')
        clean_name = clean_name.replace('/', '_').replace(' ', '_').replace('-', '_')
        
        # Extract meaningful parts
        words = [word.strip() for word in clean_name.split('_') if word.strip()]
        
        if not words:
            return f"col{col_index}"
        
        # Try to create a meaningful diminutive
        if len(words) == 1:
            word = words[0]
            if len(word) <= 4:
                return word
            elif word in ['temperature', 'temp']:
                return 'temp'
            elif word in ['pressure', 'press']:
                return 'press'
            elif word in ['voltage', 'volt']:
                return 'volt'
            elif word in ['current', 'amp', 'ampere']:
                return 'amp'
            elif word in ['time']:
                return 'time'
            elif word in ['distance', 'dist']:
                return 'dist'
            else:
                # Take first 4 characters
                return word[:4]
        else:
            # Multiple words - take first letter of each
            abbreviation = ''.join(word[0] for word in words if word)
            if len(abbreviation) <= 6:
                return abbreviation
            else:
                return abbreviation[:4]
    
    def _ensure_unique_diminutive(self, base_diminutive: str, current_col_index: int) -> str:
        """Ensure the diminutive is unique among existing columns."""
        existing_diminutives = {
            metadata.diminutive for idx, metadata in enumerate(self._columns)
            if idx != current_col_index
        }

        if base_diminutive not in existing_diminutives:
            return base_diminutive

        # Add numeric suffix to make it unique
        counter = 1
        while f"{base_diminutive}{counter}" in existing_diminutives:
            counter += 1

        return f"{base_diminutive}{counter}"
    
    def _update_formulas_after_diminutive_change(self, col_index: int, new_diminutive: str) -> None:
        """Update formulas when a diminutive changes."""
        # For now, just trigger recalculation of all calculated columns
        # In a more sophisticated implementation, we could update specific formulas
        self._recalculate_all_calculated_columns()

    def _formula_references_column(self, formula: str, column_index: int) -> bool:
        """Check if a formula references a specific column."""
        if 0 <= column_index < len(self._columns):
            diminutive = self._columns[column_index].diminutive
            if diminutive and f"{{{diminutive}}}" in formula:
                return True

        # Backward compatibility checks
        col_name = self.horizontalHeaderItem(column_index)
        col_name_text = col_name.text() if col_name else ""

        return (f"[{column_index}]" in formula or
                f"[{col_name_text}]" in formula)

    def edit_header(self, index):
        """Allow editing of the header label or formula."""
        column_type = self.getColumnType(index)
        
        # Don't allow editing uncertainty column headers directly
        if column_type == AdvancedColumnType.UNCERTAINTY:
            QMessageBox.information(
                self, 
                "Cannot Edit", 
                "Uncertainty column headers are automatically generated from their reference columns."
            )
            return
        
        # If it's a calculated column, show formula editor
        if column_type == AdvancedColumnType.CALCULATED:
            self._edit_formula(index)
            return
        
        # If it's a data column, show data column editor
        if column_type == AdvancedColumnType.DATA:
            self._edit_data_column(index)
            return
        
        # If it's a derivative column, show derivative editor
        if column_type == AdvancedColumnType.DERIVATIVE:
            self._edit_derivative_column(index)
            return
        
        # If it's an interpolation column, show interpolation editor
        if column_type == AdvancedColumnType.INTERPOLATION:
            self._edit_interpolation_column(index)
            return
        
        # If it's a range column, show range editor
        if column_type == AdvancedColumnType.RANGE:
            self._edit_range_column(index)
            return
    
    def _edit_data_column(self, column_index):
        """Open data column editor dialog for data columns."""
        dialog = DataColumnEditorDialog(self, column_index, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            results = dialog.get_results()
            self._apply_data_column_changes(column_index, results)
    
    def _apply_data_column_changes(self, column_index, changes):
        """Apply changes from the data column editor."""
        # Update diminutive
        if changes['diminutive']:
            self.setColumnDiminutive(column_index, changes['diminutive'])
        
        # Update description
        if 'description' in changes:
            self.setColumnDescription(column_index, changes['description'])
        
        # Update unit
        self.setColumnUnit(column_index, changes['unit'])
        
        # Update header using the standard method which handles unit display
        self._update_column_header(column_index)
        
        # Handle uncertainty column
        has_uncertainty, uncertainty_col = self.hasUncertaintyColumn(column_index)
        
        if changes['enable_uncertainty'] and not has_uncertainty:
            # Create uncertainty column
            self.addUncertaintyColumn(column_index)
        elif not changes['enable_uncertainty'] and has_uncertainty:
            # Remove uncertainty column (user already confirmed in dialog via checkbox)
            if uncertainty_col is not None:
                self.removeColumn(uncertainty_col)
    
    def _edit_formula(self, column_index):
        """Open formula editor dialog for calculated columns."""
        dialog = FormulaEditorDialog(self, column_index, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            results = dialog.get_results()

            # Apply changes
            changed = False

            # Update diminutive
            if results['diminutive'] != (self.getColumnDiminutive(column_index) or ""):
                self.setColumnDiminutive(column_index, results['diminutive'])
                changed = True

            # Update description
            if 'description' in results and results['description'] != (self.getColumnDescription(column_index) or ""):
                self.setColumnDescription(column_index, results['description'])
                changed = True

            # Update unit
            if results['unit'] != (self.getColumnUnit(column_index) or ""):
                self.setColumnUnit(column_index, results['unit'])
                changed = True

            # Update formula
            current_formula = self.getColumnFormula(column_index) or ""
            if results['formula'] != current_formula:
                self.setColumnFormula(column_index, results['formula'])
                changed = True

            # Update uncertainty propagation flag
            if 'propagate_uncertainty' in results:
                current_propagate = self.getColumnPropagateUncertainty(column_index)
                if results['propagate_uncertainty'] != current_propagate:
                    self.setColumnPropagateUncertainty(column_index, results['propagate_uncertainty'])
                    changed = True
                    
                    # Handle uncertainty column creation/removal
                    has_uncertainty, unc_col_idx = self.hasUncertaintyColumn(column_index)
                    if results['propagate_uncertainty'] and not has_uncertainty:
                        # Create uncertainty column
                        self._create_uncertainty_column_for_calculated(column_index)
                    elif not results['propagate_uncertainty'] and has_uncertainty:
                        # Remove uncertainty column
                        if unc_col_idx is not None:
                            self.removeColumn(unc_col_idx)

            # Update the column header to show the new diminutive and unit
            if changed:
                self._update_column_header(column_index)

    def _edit_derivative_column(self, column_index):
        """Open derivative editor dialog for derivative columns."""
        from .derivative_dialog import DerivativeEditorDialog
        
        dialog = DerivativeEditorDialog(self, column_index, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            results = dialog.get_results()
            
            # Apply changes
            changed = False
            
            # Update diminutive
            if results['diminutive'] != (self.getColumnDiminutive(column_index) or ""):
                self.setColumnDiminutive(column_index, results['diminutive'])
                changed = True
            
            # Update description
            if 'description' in results and results['description'] != (self.getColumnDescription(column_index) or ""):
                self.setColumnDescription(column_index, results['description'])
                changed = True
            
            # Update unit
            if results['unit'] != (self.getColumnUnit(column_index) or ""):
                self.setColumnUnit(column_index, results['unit'])
                changed = True
            
            # Update numerator and denominator columns
            metadata = self._columns[column_index]
            if (results['numerator_index'] != metadata.derivative_numerator or 
                results['denominator_index'] != metadata.derivative_denominator):
                metadata.derivative_numerator = results['numerator_index']
                metadata.derivative_denominator = results['denominator_index']
                changed = True
                # Recalculate the derivative column
                self._recalculate_derivative_column(column_index)
                # Recalculate any columns that depend on this derivative column
                self._recalculate_dependent_columns(column_index)
            
            # Update the column header
            if changed:
                self._update_column_header(column_index)
    
    def _edit_interpolation_column(self, column_index):
        """Open interpolation editor dialog for interpolation columns."""
        from .interpolation_dialog import InterpolationDialog
        
        dialog = InterpolationDialog(self, self, column_index)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            results = dialog.get_results()
            
            # Apply changes
            changed = False
            
            # Update diminutive
            if results['diminutive'] != (self.getColumnDiminutive(column_index) or ""):
                self.setColumnDiminutive(column_index, results['diminutive'])
                changed = True
            
            # Update description
            if 'description' in results and results['description'] != (self.getColumnDescription(column_index) or ""):
                self.setColumnDescription(column_index, results['description'])
                changed = True
            
            # Update unit
            if results['unit'] != (self.getColumnUnit(column_index) or ""):
                self.setColumnUnit(column_index, results['unit'])
                changed = True
            
            # Update interpolation settings
            metadata = self._columns[column_index]
            if (results['interpolation_x_column'] != metadata.interpolation_x_column or 
                results['interpolation_y_column'] != metadata.interpolation_y_column or
                results.get('interpolation_evaluation_column') != metadata.interpolation_evaluation_column or
                results['interpolation_method'] != metadata.interpolation_method):
                metadata.interpolation_x_column = results['interpolation_x_column']
                metadata.interpolation_y_column = results['interpolation_y_column']
                metadata.interpolation_evaluation_column = results.get('interpolation_evaluation_column')
                metadata.interpolation_method = results['interpolation_method']
                changed = True
                # Recalculate the interpolation column
                self._recalculate_interpolation_column(column_index)
                # Recalculate any columns that depend on this interpolation column
                self._recalculate_dependent_columns(column_index)
            
            # Update the column header
            if changed:
                self._update_column_header(column_index)
    
    def _edit_range_column(self, column_index):
        """Open range editor dialog for range columns."""
        from .range_dialog import RangeColumnDialog
        
        dialog = RangeColumnDialog(self, self)
        
        # Load existing range parameters
        metadata = self._columns[column_index]
        if metadata.range_start is not None:
            dialog.start_edit.setText(str(metadata.range_start))
        if metadata.range_end is not None:
            dialog.end_edit.setText(str(metadata.range_end))
        if metadata.range_points is not None:
            dialog.points_edit.setText(str(metadata.range_points))
        dialog.diminutive_edit.setText(metadata.diminutive)
        if metadata.description:
            dialog.description_edit.setText(metadata.description)
        if metadata.unit:
            dialog.unit_edit.setText(metadata.unit)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            results = dialog.get_results()
            
            # Apply changes
            changed = False
            
            # Update diminutive
            if results['diminutive'] != metadata.diminutive:
                self.setColumnDiminutive(column_index, results['diminutive'])
                changed = True
            
            # Update description
            if results.get('description') != metadata.description:
                self.setColumnDescription(column_index, results['description'])
                changed = True
            
            # Update unit
            if results.get('unit') != metadata.unit:
                self.setColumnUnit(column_index, results['unit'])
                changed = True
            
            # Update range parameters
            if (results['start'] != metadata.range_start or 
                results['end'] != metadata.range_end or
                results['points'] != metadata.range_points):
                metadata.range_start = results['start']
                metadata.range_end = results['end']
                metadata.range_points = results['points']
                changed = True
                # Recalculate the range column
                self._recalculate_range_column(column_index)
                # Recalculate any columns that depend on this range column
                self._recalculate_dependent_columns(column_index)
            
            # Update the column header
            if changed:
                self._update_column_header(column_index)

    def manage_variables(self):
        """Open dialog to manage global variables/constants."""
        dialog = VariablesDialog(self, self._variables)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._variables = dialog.get_variables()
            # Recalculate all calculated columns since variables may have changed
            self._recalculate_all_calculated_columns()
            print(f"Variables updated: {len(self._variables)} variable(s) defined")

    def convert_column_to_data(self, column_index: int) -> bool:
        """Convert a CALCULATED, DERIVATIVE, INTERPOLATION, or RANGE column to a DATA column.
        
        This preserves the current values in the column but removes the calculation/formula,
        making it a regular editable data column.
        
        Args:
            column_index: Index of the column to convert
            
        Returns:
            True if conversion was successful, False otherwise
        """
        if column_index < 0 or column_index >= len(self._columns):
            return False
        
        metadata = self._columns[column_index]
        
        # Only allow conversion of CALCULATED, DERIVATIVE, INTERPOLATION, and RANGE columns
        if metadata.column_type not in [AdvancedColumnType.CALCULATED, 
                                         AdvancedColumnType.DERIVATIVE,
                                         AdvancedColumnType.INTERPOLATION,
                                         AdvancedColumnType.RANGE]:
            QMessageBox.warning(
                self, 
                "Cannot Convert",
                f"Only CALCULATED, DERIVATIVE, INTERPOLATION, and RANGE columns can be converted to DATA columns."
            )
            return False
        
        # Confirm conversion
        reply = QMessageBox.question(
            self,
            "Convert to Data Column",
            f"Convert '{metadata.diminutive}' to a DATA column?\n\n"
            f"This will preserve current values but remove the formula/calculation.\n"
            f"The column will become editable and no longer auto-update.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return False
        
        # Handle uncertainty column if it exists
        linked_uncertainty_col = None
        if metadata.column_type == AdvancedColumnType.CALCULATED and metadata.propagate_uncertainty:
            # Find the linked uncertainty column
            for idx, col_meta in enumerate(self._columns):
                if (col_meta.column_type == AdvancedColumnType.UNCERTAINTY and
                    col_meta.uncertainty_reference == column_index):
                    linked_uncertainty_col = idx
                    break
        
        # Update metadata - clear calculation-specific fields
        metadata.column_type = AdvancedColumnType.DATA
        metadata.formula = None
        metadata.propagate_uncertainty = False
        metadata.derivative_numerator = None
        metadata.derivative_denominator = None
        metadata.interpolation_x_column = None
        metadata.interpolation_y_column = None
        metadata.interpolation_evaluation_column = None
        metadata.interpolation_method = None
        metadata.range_start = None
        metadata.range_end = None
        metadata.range_points = None
        
        # Remove linked uncertainty column if it exists
        if linked_uncertainty_col is not None:
            reply_unc = QMessageBox.question(
                self,
                "Remove Uncertainty Column",
                f"Remove the linked uncertainty column as well?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply_unc == QMessageBox.StandardButton.Yes:
                self.removeColumn(linked_uncertainty_col)
        
        # Update header to reflect new column type
        self._update_column_header(column_index)
        
        # Make cells editable
        for row in range(self.rowCount()):
            item = self.item(row, column_index)
            if item:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        
        return True

    def removeColumn(self, column_index: int) -> bool:
        """Remove a column and clean up associated metadata."""
        if column_index >= self.columnCount() or column_index < 0:
            return False

        column_type = self._columns[column_index].column_type

        # Check if this is a data column with uncertainty columns
        if column_type == AdvancedColumnType.DATA:
            dependent_uncertainty_cols = [
                idx for idx, metadata in enumerate(self._columns)
                if (metadata.column_type == AdvancedColumnType.UNCERTAINTY and
                    metadata.uncertainty_reference == column_index)
            ]
            if dependent_uncertainty_cols:
                reply = QMessageBox.question(
                    self,
                    "Remove Dependent Columns?",
                    f"This data column has {len(dependent_uncertainty_cols)} uncertainty column(s). "
                    "Remove them as well?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
                )
                if reply == QMessageBox.StandardButton.Cancel:
                    return False
                elif reply == QMessageBox.StandardButton.Yes:
                    # Remove uncertainty columns first (in reverse order to maintain indices)
                    for unc_col in sorted(dependent_uncertainty_cols, reverse=True):
                        self.removeColumn(unc_col)

        # Remove the column from the table
        super().removeColumn(column_index)

        # Remove metadata (no need to shift indices since we're using a list)
        del self._columns[column_index]

        # Update uncertainty references that pointed to columns after the removed one
        for metadata in self._columns:
            if (metadata.uncertainty_reference is not None and
                metadata.uncertainty_reference > column_index):
                metadata.uncertainty_reference -= 1

        self.columnRemoved.emit(column_index)
        return True

    def insertRow(self, row: int) -> None:
        """Override insertRow to recalculate calculated, derivative, and interpolation columns.
        
        Note: DERIVATIVE and INTERPOLATION columns require full column recalculation
        since they depend on multiple rows, not just the new one.
        """
        super().insertRow(row)
        
        # Recalculate CALCULATED columns for the new row (row-by-row is efficient)
        self._recalculate_row_calculated_values(row)
        
        # Recalculate DERIVATIVE and INTERPOLATION columns fully
        # (they depend on multiple rows, can't calculate just one row)
        for idx, metadata in enumerate(self._columns):
            if metadata.column_type == AdvancedColumnType.DERIVATIVE:
                self._recalculate_derivative_column(idx)
            elif metadata.column_type == AdvancedColumnType.INTERPOLATION:
                self._recalculate_interpolation_column(idx)
    
    def removeRow(self, row: int) -> None:
        """Override removeRow - no additional calculation needed as row is gone."""
        return super().removeRow(row)
    
    def setRowCount(self, rows: int) -> None:
        """Override setRowCount to handle calculated, derivative, and interpolation columns.
        
        Processes columns in left-to-right order to respect dependencies.
        """
        old_row_count = self.rowCount()
        super().setRowCount(rows)
        
        # If we added rows, recalculate all dependent columns
        if rows > old_row_count:
            # Recalculate CALCULATED columns for new rows (row-by-row is efficient)
            for row in range(old_row_count, rows):
                self._recalculate_row_calculated_values(row)
            
            # Recalculate DERIVATIVE and INTERPOLATION columns fully
            # (they depend on multiple rows, can't calculate just new rows)
            for idx, metadata in enumerate(self._columns):
                if metadata.column_type == AdvancedColumnType.DERIVATIVE:
                    self._recalculate_derivative_column(idx)
                elif metadata.column_type == AdvancedColumnType.INTERPOLATION:
                    self._recalculate_interpolation_column(idx)
    
    def _recalculate_row_calculated_values(self, row_index: int) -> None:
        """Recalculate calculated, derivative, and interpolation column values for a specific row.
        
        Processes columns in left-to-right order to respect dependencies.
        """
        if self._updating_calculations:
            return

        self._updating_calculations = True
        try:
            for idx, metadata in enumerate(self._columns):
                # Handle CALCULATED columns
                if (metadata.column_type == AdvancedColumnType.CALCULATED and
                    metadata.formula):
                    try:
                        result = self._evaluate_formula(metadata.formula, row_index)
                        # Format the result appropriately
                        if result is not None:
                            if isinstance(result, float):
                                # Check for inf or nan
                                if math.isinf(result) or math.isnan(result):
                                    display_text = str(result)
                                    item = QTableWidgetItem(display_text)
                                    item.setData(0, result)
                                    item.setForeground(QColor(255, 0, 0))  # Red text for inf/nan
                                    item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                                    self.setItem(row_index, idx, item)
                                    continue
                                display_text = f"{result:{DEFAULT_NUMERIC_PRECISION}}"
                            else:
                                display_text = str(result)
                        else:
                            display_text = ""

                        item = QTableWidgetItem(display_text)
                        item.setData(0, result)
                        # Make calculated columns non-editable but selectable
                        item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                        self.setItem(row_index, idx, item)
                        
                        # Calculate uncertainty if propagation is enabled
                        if metadata.propagate_uncertainty:
                            self._calculate_and_update_uncertainty(idx, row_index, metadata.formula)
                            
                    except Exception as e:
                        error_item = QTableWidgetItem(f"{ERROR_PREFIX}{str(e)}")
                        # Make error items non-editable but selectable
                        error_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                        error_item.setForeground(QColor(255, 0, 0))  # Red text for errors
                        self.setItem(row_index, idx, error_item)
                
                # Handle DERIVATIVE columns
                elif metadata.column_type == AdvancedColumnType.DERIVATIVE:
                    # Derivative columns need full recalculation since they depend on adjacent rows
                    # We can't just calculate one row in isolation
                    pass  # Will be handled by full column recalculation
                
                # Handle INTERPOLATION columns  
                elif metadata.column_type == AdvancedColumnType.INTERPOLATION:
                    # Interpolation columns need full recalculation since they depend on all data points
                    # We can't just calculate one row in isolation
                    pass  # Will be handled by full column recalculation
        finally:
            self._updating_calculations = False
    
    def recalculateAll(self) -> None:
        """Public method to manually trigger recalculation of all calculated columns."""
        self._recalculate_all_calculated_columns()
    
    def setItem(self, row: int, column: int, item: QTableWidgetItem) -> None:
        """Override setItem to trigger recalculation when data is set programmatically."""
        super().setItem(row, column, item)
        
        # If we're already updating calculations, don't trigger recalculation
        if self._updating_calculations:
            return
        
        col_type = self.getColumnType(column)
        
        # If this is a data column, trigger recalculation
        if col_type == AdvancedColumnType.DATA:
            self._recalculate_dependent_columns(column)
        # If this is an uncertainty column, trigger recalculation for its reference column
        elif col_type == AdvancedColumnType.UNCERTAINTY:
            if 0 <= column < len(self._columns):
                metadata = self._columns[column]
                if metadata.uncertainty_reference is not None:
                    self._recalculate_dependent_columns(metadata.uncertainty_reference)
    
    def clear(self) -> None:
        """Override clear to reset all metadata when table is cleared."""
        super().clear()
        self._columns.clear()
    
    def clearContents(self) -> None:
        """Override clearContents to trigger recalculation after clearing."""
        super().clearContents()
        # Recalculate all calculated columns after clearing contents
        self._recalculate_all_calculated_columns()
    
    def _update_uncertainty_column_headers(self, data_column_index: int) -> None:
        """Update headers of uncertainty columns that reference the given data column.
        
        Note: This method is deprecated. Use _update_column_header instead,
        which properly handles uncertainty column headers with tooltips.
        """
        # Find all uncertainty columns that reference this data column
        for idx, metadata in enumerate(self._columns):
            if (metadata.column_type == AdvancedColumnType.UNCERTAINTY and
                metadata.uncertainty_reference == data_column_index):
                # Update using the standard header update method
                self._update_column_header(idx)
    
    def appendColumn(self, data_list: List[Union[int, float, str, None]], column_index: int) -> None:
        """
        Populate rows with data from a list at the specified column index.
        
        Args:
            data_list: List of values to populate
            column_index: Column index to populate
        """
        if column_index < 0 or column_index >= self.columnCount():
            raise ValueError(f"Column index {column_index} out of range")
        
        # Ensure we have enough rows
        required_rows = len(data_list)
        if self.rowCount() < required_rows:
            self.setRowCount(required_rows)
        
        # Populate the column with data
        self._updating_calculations = True
        try:
            for row, value in enumerate(data_list):
                if row < self.rowCount():
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    if isinstance(value, (int, float)):
                        # Use UserRole to avoid overwriting the display text
                        item.setData(Qt.ItemDataRole.UserRole, value)
                    self.setItem(row, column_index, item)
        finally:
            self._updating_calculations = False
        
        # Trigger recalculation if this is a data column
        if self.getColumnType(column_index) == AdvancedColumnType.DATA:
            self._recalculate_dependent_columns(column_index)

