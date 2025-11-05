from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QComboBox
from PySide6.QtCore import Qt

from utils.lang import get_lang_manager, tr
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView


class Workspace(QWidget):
    """Workspace area for data manipulation tasks."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.lang = get_lang_manager()
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the UI for the workspace."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create matplotlib figure and canvas
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # Create a default plot
        self.ax = self.figure.add_subplot(111)
        
        # Create axis selection layout
        axis_layout = QHBoxLayout()
        
        axis_layout.addWidget(QLabel("X-axis:"))
        self.x_axis_combo = QComboBox()
        self.x_axis_combo.currentTextChanged.connect(self.update_plot)
        axis_layout.addWidget(self.x_axis_combo)
        
        axis_layout.addWidget(QLabel("Y-axis:"))
        self.y_axis_combo = QComboBox()
        self.y_axis_combo.currentTextChanged.connect(self.update_plot)
        axis_layout.addWidget(self.y_axis_combo)
        
        axis_layout.addStretch()
        layout.addLayout(axis_layout)
        
        # Create button layout
        button_layout = QHBoxLayout()
        
        self.add_row_button = QPushButton("Add Row")
        self.remove_row_button = QPushButton("Remove Row")
        self.add_column_button = QPushButton("Add Column")
        
        self.add_row_button.clicked.connect(self.add_row)
        self.remove_row_button.clicked.connect(self.remove_row)
        self.add_column_button.clicked.connect(self.add_column)
        
        button_layout.addWidget(self.add_row_button)
        button_layout.addWidget(self.remove_row_button)
        button_layout.addWidget(self.add_column_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Create table widget 
        self.table = QTableWidget()
        self.table.setRowCount(4)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(['X', 'Y'])
        
        # Make headers editable
        self.table.horizontalHeader().sectionDoubleClicked.connect(self.edit_header)
        
        # Connect table changes to plot update
        self.table.itemChanged.connect(self.update_plot)
        
        # Populate with sample data
        x_data = [1, 2, 3, 4]
        y_data = [1, 4, 2, 3]
        
        for i in range(len(x_data)):
            self.table.setItem(i, 0, QTableWidgetItem(str(x_data[i])))
            self.table.setItem(i, 1, QTableWidgetItem(str(y_data[i])))
        
        # Resize columns to content
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.table)
        
        # Initialize combo boxes
        self.update_combo_boxes()
        
        # Initial plot
        self.update_plot()
    
    def update_combo_boxes(self):
        """Update combo boxes with current column headers."""
        # Store current selections
        x_current = self.x_axis_combo.currentText()
        y_current = self.y_axis_combo.currentText()
        
        # Clear and repopulate
        self.x_axis_combo.clear()
        self.y_axis_combo.clear()
        
        for i in range(self.table.columnCount()):
            header_item = self.table.horizontalHeaderItem(i)
            header_text = header_item.text() if header_item else f"Column {i+1}"
            self.x_axis_combo.addItem(header_text)
            self.y_axis_combo.addItem(header_text)
        
        # Restore selections if they still exist
        x_index = self.x_axis_combo.findText(x_current)
        y_index = self.y_axis_combo.findText(y_current)
        
        if x_index >= 0:
            self.x_axis_combo.setCurrentIndex(x_index)
        else:
            self.x_axis_combo.setCurrentIndex(0)
            
        if y_index >= 0:
            self.y_axis_combo.setCurrentIndex(y_index)
        else:
            self.y_axis_combo.setCurrentIndex(min(1, self.y_axis_combo.count() - 1))
    
    def add_row(self):
        """Add a new row to the table."""
        current_rows = self.table.rowCount()
        self.table.setRowCount(current_rows + 1)
    
    def remove_row(self):
        """Remove the last row from the table."""
        current_rows = self.table.rowCount()
        if current_rows > 0:
            self.table.setRowCount(current_rows - 1)
            self.update_plot()
    
    def add_column(self):
        """Add a new column to the table."""
        current_cols = self.table.columnCount()
        self.table.setColumnCount(current_cols + 1)
        
        # Set header for new column
        new_header = f"Column {current_cols + 1}"
        self.table.setHorizontalHeaderItem(current_cols, QTableWidgetItem(new_header))
        
        # Update combo boxes with new column
        self.update_combo_boxes()
    
    def edit_header(self, logical_index):
        """Edit header name when double-clicked."""
        current_text = self.table.horizontalHeaderItem(logical_index).text()
        
        from PySide6.QtWidgets import QInputDialog
        new_text, ok = QInputDialog.getText(self, "Edit Header", 
                                          "Header name:", text=current_text)
        
        if ok and new_text:
            self.table.setHorizontalHeaderLabels([
                new_text if i == logical_index else self.table.horizontalHeaderItem(i).text()
                for i in range(self.table.columnCount())
            ])
            # Update combo boxes after header change
            self.update_combo_boxes()
    
    def check_table_data(self):
        # Check it is numbers or color in red else default color
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item is not None:
                    try:
                        float(item.text())
                      # else default color 
                        item.setForeground(Qt.GlobalColor.color0)
                    except ValueError:
                        item.setForeground(Qt.GlobalColor.red)
                        

    def update_plot(self):
        self.check_table_data()

        """Update the plot with current table data."""
        # Get selected column indices
        x_col_name = self.x_axis_combo.currentText()
        y_col_name = self.y_axis_combo.currentText()
        
        x_col_index = -1
        y_col_index = -1
        
        # Find column indices by header name
        for i in range(self.table.columnCount()):
            header_item = self.table.horizontalHeaderItem(i)
            header_text = header_item.text() if header_item else f"Column {i+1}"
            if header_text == x_col_name:
                x_col_index = i
            if header_text == y_col_name:
                y_col_index = i
        
        x_data = []
        y_data = []
        
        # Extract data from selected columns
        if x_col_index >= 0 and y_col_index >= 0:
            for row in range(self.table.rowCount()):
                x_item = self.table.item(row, x_col_index)
                y_item = self.table.item(row, y_col_index)
                
                if x_item and y_item and x_item.text() and y_item.text():
                    try:
                        x_val = float(x_item.text())
                        y_val = float(y_item.text())
                        x_data.append(x_val)
                        y_data.append(y_val)
                    except ValueError:
                        continue
        
        # Clear and update plot
        self.ax.clear()
        if x_data and y_data:
            self.ax.plot(x_data, y_data, 'bo-')
            self.ax.set_title('Data Plot')
            self.ax.set_xlabel(x_col_name)
            self.ax.set_ylabel(y_col_name)
        else:
            self.ax.set_title('No Valid Data')
        
        self.canvas.draw()
