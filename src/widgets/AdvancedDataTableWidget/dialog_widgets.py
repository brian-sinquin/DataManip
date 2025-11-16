"""Reusable widget components for dialogs.

This module provides specialized QListWidget and QComboBox subclasses that
automatically populate themselves with columns and variables from an
AdvancedDataTableWidget.
"""

from typing import Optional, List
from PySide6.QtWidgets import QListWidget, QComboBox
from PySide6.QtCore import Signal

from .dialog_utils import (
    populate_formula_columns_list,
    populate_column_combo_boxes,
    populate_interpolation_column_combos
)


class FormulaColumnsListWidget(QListWidget):
    """List widget that displays available columns and variables for formula editing.
    
    This widget automatically populates with:
    - Global variables (if any)
    - Available columns (excluding UNCERTAINTY and optionally the edited column)
    
    Emits:
    - referenceRequested(str): When user double-clicks to insert a reference
    """
    
    referenceRequested = Signal(str)  # Emits the reference text like "{varname}"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.table_widget = None
        self.column_index_to_skip = None
        
        # Connect double-click to insert reference
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
    
    def setTableWidget(self, table_widget, column_index_to_skip: Optional[int] = None):
        """Set the table widget and populate the list.
        
        Args:
            table_widget: The AdvancedDataTableWidget instance
            column_index_to_skip: Optional column index to skip (for edit mode)
        """
        self.table_widget = table_widget
        self.column_index_to_skip = column_index_to_skip
        self.populate()
    
    def populate(self):
        """Populate the list with variables and columns."""
        if self.table_widget is None:
            return
        
        populate_formula_columns_list(
            self,
            self.table_widget,
            column_index_to_skip=self.column_index_to_skip
        )
    
    def _on_item_double_clicked(self, item):
        """Handle double-click to insert reference."""
        text = item.text()
        # Skip header/separator items
        if text.startswith("---") or not text.strip():
            return
        
        # Extract reference from "... → {reference}"
        if "→ {" in text and "}" in text:
            start = text.find("→ {") + 2
            end = text.find("}", start) + 1
            reference = text[start:end]
            self.referenceRequested.emit(reference)


class ColumnSelectionComboBox(QComboBox):
    """Combo box for selecting a column (e.g., for derivatives, interpolation).
    
    This widget automatically populates with available columns, excluding
    UNCERTAINTY columns and optionally the column being edited.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.table_widget = None
        self.column_index_to_skip = None
        self._include_type_labels = True
        self._include_units = True
        self._placeholder_text = "-- Select Column --"
    
    def setTableWidget(self, table_widget, column_index_to_skip: Optional[int] = None):
        """Set the table widget and populate the combo box.
        
        Args:
            table_widget: The AdvancedDataTableWidget instance
            column_index_to_skip: Optional column index to skip (for edit mode)
        """
        self.table_widget = table_widget
        self.column_index_to_skip = column_index_to_skip
        self.populate()
    
    def setIncludeTypeLabels(self, include: bool):
        """Set whether to include type labels like [calc], [deriv]."""
        self._include_type_labels = include
    
    def setIncludeUnits(self, include: bool):
        """Set whether to include unit information like [m/s]."""
        self._include_units = include
    
    def setPlaceholderText(self, text: str):
        """Set the placeholder text for the first item."""
        self._placeholder_text = text
    
    def populate(self):
        """Populate the combo box with available columns."""
        if self.table_widget is None:
            return
        
        populate_column_combo_boxes(
            combo_boxes=[self],
            table_widget=self.table_widget,
            column_index_to_skip=self.column_index_to_skip,
            include_type_labels=self._include_type_labels,
            include_units=self._include_units,
            placeholder_text=self._placeholder_text
        )


class InterpolationColumnComboBox(QComboBox):
    """Combo box for selecting numeric columns for interpolation.
    
    This widget only shows NUMERICAL columns, excluding UNCERTAINTY.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.table_widget = None
        self.column_index_to_skip = None
    
    def setTableWidget(self, table_widget, column_index_to_skip: Optional[int] = None):
        """Set the table widget and populate the combo box.
        
        Args:
            table_widget: The AdvancedDataTableWidget instance
            column_index_to_skip: Optional column index to skip (for edit mode)
        """
        self.table_widget = table_widget
        self.column_index_to_skip = column_index_to_skip
        self.populate()
    
    def populate(self):
        """Populate the combo box with available numeric columns."""
        if self.table_widget is None:
            return
        
        populate_interpolation_column_combos(
            combo_boxes=[self],
            table_widget=self.table_widget,
            column_index_to_skip=self.column_index_to_skip
        )


class ColumnPairWidget:
    """Helper class to manage a pair of column combo boxes (e.g., numerator/denominator).
    
    This is useful for derivative dialogs where you need to select two columns.
    """
    
    def __init__(self, combo1: QComboBox, combo2: QComboBox):
        self.combo1 = combo1
        self.combo2 = combo2
    
    def populate(self, table_widget, column_index_to_skip: Optional[int] = None,
                 include_type_labels: bool = True, include_units: bool = True):
        """Populate both combo boxes with the same columns."""
        populate_column_combo_boxes(
            combo_boxes=[self.combo1, self.combo2],
            table_widget=table_widget,
            column_index_to_skip=column_index_to_skip,
            include_type_labels=include_type_labels,
            include_units=include_units
        )
    
    def getSelectedIndices(self) -> tuple[Optional[int], Optional[int]]:
        """Get the selected column indices from both combo boxes.
        
        Returns:
            Tuple of (combo1_index, combo2_index), None if not selected
        """
        return (self.combo1.currentData(), self.combo2.currentData())
    
    def setSelectedIndices(self, index1: Optional[int], index2: Optional[int]):
        """Set the selected column indices in both combo boxes."""
        if index1 is not None:
            for i in range(self.combo1.count()):
                if self.combo1.itemData(i) == index1:
                    self.combo1.setCurrentIndex(i)
                    break
        
        if index2 is not None:
            for i in range(self.combo2.count()):
                if self.combo2.itemData(i) == index2:
                    self.combo2.setCurrentIndex(i)
                    break
