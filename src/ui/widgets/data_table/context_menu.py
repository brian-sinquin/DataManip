"""Context menu for DataTable widget."""

from PySide6.QtWidgets import QMenu
from studies.data_table_study import ColumnType
from constants import COLUMN_SYMBOLS


def show_data_table_context_menu(widget, position):
    """Show context menu for data table.
    
    Args:
        widget: DataTableWidget instance
        position: Menu position
    """
    menu = QMenu(widget.view)
    
    # Get clicked index
    index = widget.view.indexAt(position)
    
    if index.isValid():
        # Cell context menu
        col_name = widget.study.table.columns[index.column()]
        col_type = widget.study.get_column_type(col_name)
        
        symbol = COLUMN_SYMBOLS.get(col_type, "")
        type_display = f"{symbol} {col_type.upper()}" if symbol else col_type.upper()
        
        menu.addAction(f"Column: {col_name}").setEnabled(False)
        menu.addAction(f"Type: {type_display}").setEnabled(False)
        menu.addSeparator()
        
        # Column actions
        rename_action = menu.addAction("Rename Column")
        rename_action.triggered.connect(lambda: widget._rename_column(index.column()))
        
        if col_type == ColumnType.CALCULATED:
            edit_action = menu.addAction("Edit Formula")
            edit_action.triggered.connect(lambda: widget._edit_column(col_name))
        
        delete_col_action = menu.addAction("Delete Column")
        delete_col_action.triggered.connect(lambda: widget._delete_column(col_name))
        
        # Convert column option (for non-DATA columns)
        if col_type != ColumnType.DATA:
            menu.addSeparator()
            convert_action = menu.addAction("Convert to DATA Column")
            convert_action.triggered.connect(widget._convert_column_to_data)
        
        menu.addSeparator()
        
        # Row actions
        insert_row_action = menu.addAction("Insert Row Above")
        insert_row_action.triggered.connect(lambda: widget._insert_row(index.row()))
        
        delete_row_action = menu.addAction("Delete This Row")
        delete_row_action.triggered.connect(lambda: widget._delete_row(index.row()))
        
        menu.addSeparator()
        
        # Data operations
        copy_action = menu.addAction("Copy Cell")
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(lambda: widget._copy_selection())
        
        if col_type == ColumnType.DATA:
            paste_action = menu.addAction("Paste")
            paste_action.setShortcut("Ctrl+V")
            paste_action.triggered.connect(lambda: widget._paste_data())
    else:
        # General context menu
        add_row_action = menu.addAction("Add Row")
        add_row_action.triggered.connect(widget._add_row)
        
        menu.addSeparator()
        
        resize_action = menu.addAction("Auto-resize Columns")
        resize_action.triggered.connect(widget._auto_resize_columns)
    
    menu.exec(widget.view.viewport().mapToGlobal(position))
