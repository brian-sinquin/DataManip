"""
Dialog classes for plot widget.

This module provides UI dialogs for plot configuration:
- AddSeriesDialog: Add/edit plot series
- AxisConfigDialog: Configure axis properties
- LegendConfigDialog: Configure legend
- PlotStyleDialog: Configure plot appearance
- ExportDialog: Export plot options
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QCheckBox, QGroupBox,
    QComboBox, QTextEdit, QDoubleSpinBox, QSpinBox, QColorDialog,
    QDialogButtonBox, QTabWidget, QWidget, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from typing import Optional, Dict, Any, List

from .series_metadata import (
    SeriesMetadata, PlotStyle, MarkerStyle, LineStyle,
    get_default_color, DEFAULT_COLORS
)
from .plot_config import (
    PlotConfig, AxisConfig, LegendConfig, GridStyle,
    LegendLocation, AxisScale
)
from .plot_model import PlotModel
class AddSeriesDialog(QDialog):
    """Dialog for adding or editing a plot series.
    
    This dialog allows users to:
    - Select X and Y columns from DataTable
    - Configure error bars
    - Set plot style and appearance
    - Customize colors, markers, lines
    """
    
    def __init__(self, plot_model: PlotModel, parent=None,
                 series_metadata: Optional[SeriesMetadata] = None):
        """Initialize dialog.
        
        Args:
            plot_model: PlotModel instance for column selection
            parent: Parent widget
            series_metadata: If provided, edit mode for this series
        """
        super().__init__(parent)
        
        self.plot_model = plot_model
        self.series_metadata = series_metadata
        self.is_edit_mode = series_metadata is not None
        
        # Set title
        if self.is_edit_mode and series_metadata:
            title = f"Edit Series - {series_metadata.name}"
        else:
            title = "Add Series"
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(600, 500)
        
        # Setup UI
        self._setup_ui()
        
        if self.is_edit_mode:
            self._load_existing_values()
    
    def _setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel(
            "Configure a data series to plot from DataTable columns.\n"
            "Select X and Y columns, optionally add error bars, and customize appearance."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(instructions)
        
        # Tab widget for organization
        tabs = QTabWidget()
        
        # Data tab
        data_tab = QWidget()
        data_layout = QVBoxLayout(data_tab)
        self._create_data_tab(data_layout)
        tabs.addTab(data_tab, "Data")
        
        # Style tab
        style_tab = QWidget()
        style_layout = QVBoxLayout(style_tab)
        self._create_style_tab(style_layout)
        tabs.addTab(style_tab, "Style")
        
        # Advanced tab
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(advanced_tab)
        self._create_advanced_tab(advanced_layout)
        tabs.addTab(advanced_tab, "Advanced")
        
        layout.addWidget(tabs)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self._ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
    
    def _create_data_tab(self, layout: QVBoxLayout):
        """Create data selection tab."""
        # Series identification
        id_group = QGroupBox("Series Identification")
        id_layout = QFormLayout(id_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., Position vs Time")
        self.name_edit.textChanged.connect(self._on_data_changed)
        id_layout.addRow("Series Name*:", self.name_edit)
        
        layout.addWidget(id_group)
        
        # Column selection
        cols_group = QGroupBox("Data Columns")
        cols_layout = QFormLayout(cols_group)
        
        # Get available columns from model
        available_columns = self.plot_model.get_available_columns()
        
        # X column
        self.x_column_combo = QComboBox()
        for col_name, display_text in available_columns:
            self.x_column_combo.addItem(display_text, col_name)
        self.x_column_combo.currentIndexChanged.connect(self._on_data_changed)
        cols_layout.addRow("X Column*:", self.x_column_combo)
        
        # Y column
        self.y_column_combo = QComboBox()
        for col_name, display_text in available_columns:
            self.y_column_combo.addItem(display_text, col_name)
        self.y_column_combo.currentIndexChanged.connect(self._on_data_changed)
        cols_layout.addRow("Y Column*:", self.y_column_combo)
        
        layout.addWidget(cols_group)
        
        # Error bars
        error_group = QGroupBox("Error Bars (Optional)")
        error_layout = QFormLayout(error_group)
        
        self.show_error_bars_checkbox = QCheckBox("Show error bars")
        self.show_error_bars_checkbox.setChecked(True)
        error_layout.addRow("", self.show_error_bars_checkbox)
        
        # X error column
        self.x_error_combo = QComboBox()
        self.x_error_combo.addItem("(None)", None)
        for col_name, display_text in available_columns:
            self.x_error_combo.addItem(display_text, col_name)
        error_layout.addRow("X Error Column:", self.x_error_combo)
        
        # Y error column
        self.y_error_combo = QComboBox()
        self.y_error_combo.addItem("(None)", None)
        for col_name, display_text in available_columns:
            self.y_error_combo.addItem(display_text, col_name)
        error_layout.addRow("Y Error Column:", self.y_error_combo)
        
        layout.addWidget(error_group)
        
        # Axis selection
        axis_group = QGroupBox("Axis Selection")
        axis_layout = QFormLayout(axis_group)
        
        self.use_secondary_y_checkbox = QCheckBox("Use secondary Y-axis (right side)")
        self.use_secondary_y_checkbox.setToolTip(
            "Plot this series on a secondary Y-axis (right side).\n"
            "Useful for plotting data with different units."
        )
        axis_layout.addRow("", self.use_secondary_y_checkbox)
        
        layout.addWidget(axis_group)
        layout.addStretch()
        
        # Auto-suggest series name based on columns
        if not self.is_edit_mode:
            self.x_column_combo.currentIndexChanged.connect(self._suggest_series_name)
            self.y_column_combo.currentIndexChanged.connect(self._suggest_series_name)
    
    def _create_style_tab(self, layout: QVBoxLayout):
        """Create style configuration tab."""
        # Plot style
        style_group = QGroupBox("Plot Style")
        style_layout = QFormLayout(style_group)
        
        self.plot_style_combo = QComboBox()
        for style in PlotStyle:
            self.plot_style_combo.addItem(style.value.title(), style)
        style_layout.addRow("Style*:", self.plot_style_combo)
        
        layout.addWidget(style_group)
        
        # Color
        color_group = QGroupBox("Color")
        color_layout = QHBoxLayout(color_group)
        
        self.color_button = QPushButton("Choose Color")
        self.color_button.clicked.connect(self._choose_color)
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(50, 30)
        self.color_preview.setStyleSheet("border: 1px solid #ccc; background: #1f77b4;")
        self._current_color = "#1f77b4"
        
        color_layout.addWidget(self.color_button)
        color_layout.addWidget(self.color_preview)
        color_layout.addStretch()
        
        layout.addWidget(color_group)
        
        # Line properties
        line_group = QGroupBox("Line Properties")
        line_layout = QFormLayout(line_group)
        
        self.line_style_combo = QComboBox()
        for style in LineStyle:
            display = style.name.title() if style != LineStyle.NONE else "None"
            self.line_style_combo.addItem(display, style)
        line_layout.addRow("Line Style:", self.line_style_combo)
        
        self.line_width_spin = QDoubleSpinBox()
        self.line_width_spin.setRange(0.5, 10.0)
        self.line_width_spin.setSingleStep(0.5)
        self.line_width_spin.setValue(2.0)
        line_layout.addRow("Line Width:", self.line_width_spin)
        
        layout.addWidget(line_group)
        
        # Marker properties
        marker_group = QGroupBox("Marker Properties")
        marker_layout = QFormLayout(marker_group)
        
        self.marker_style_combo = QComboBox()
        marker_names = {
            MarkerStyle.CIRCLE: "Circle",
            MarkerStyle.SQUARE: "Square",
            MarkerStyle.TRIANGLE: "Triangle",
            MarkerStyle.DIAMOND: "Diamond",
            MarkerStyle.PLUS: "Plus",
            MarkerStyle.CROSS: "Cross",
            MarkerStyle.STAR: "Star",
            MarkerStyle.NONE: "None"
        }
        for style in MarkerStyle:
            self.marker_style_combo.addItem(marker_names[style], style)
        marker_layout.addRow("Marker Style:", self.marker_style_combo)
        
        self.marker_size_spin = QDoubleSpinBox()
        self.marker_size_spin.setRange(1.0, 20.0)
        self.marker_size_spin.setSingleStep(0.5)
        self.marker_size_spin.setValue(6.0)
        marker_layout.addRow("Marker Size:", self.marker_size_spin)
        
        layout.addWidget(marker_group)
        layout.addStretch()
    
    def _create_advanced_tab(self, layout: QVBoxLayout):
        """Create advanced options tab."""
        # Transparency
        alpha_group = QGroupBox("Transparency")
        alpha_layout = QFormLayout(alpha_group)
        
        self.alpha_spin = QDoubleSpinBox()
        self.alpha_spin.setRange(0.0, 1.0)
        self.alpha_spin.setSingleStep(0.1)
        self.alpha_spin.setValue(1.0)
        self.alpha_spin.setToolTip("0.0 = fully transparent, 1.0 = fully opaque")
        alpha_layout.addRow("Alpha:", self.alpha_spin)
        
        layout.addWidget(alpha_group)
        
        # Error bar styling
        error_style_group = QGroupBox("Error Bar Styling")
        error_layout = QFormLayout(error_style_group)
        
        self.error_cap_size_spin = QDoubleSpinBox()
        self.error_cap_size_spin.setRange(0.0, 20.0)
        self.error_cap_size_spin.setValue(5.0)
        error_layout.addRow("Cap Size:", self.error_cap_size_spin)
        
        self.error_cap_width_spin = QDoubleSpinBox()
        self.error_cap_width_spin.setRange(0.5, 5.0)
        self.error_cap_width_spin.setSingleStep(0.5)
        self.error_cap_width_spin.setValue(1.5)
        error_layout.addRow("Cap Width:", self.error_cap_width_spin)
        
        self.error_line_width_spin = QDoubleSpinBox()
        self.error_line_width_spin.setRange(0.5, 5.0)
        self.error_line_width_spin.setSingleStep(0.5)
        self.error_line_width_spin.setValue(1.5)
        error_layout.addRow("Line Width:", self.error_line_width_spin)
        
        layout.addWidget(error_style_group)
        
        # Legend
        legend_group = QGroupBox("Legend")
        legend_layout = QFormLayout(legend_group)
        
        self.show_in_legend_checkbox = QCheckBox("Show in legend")
        self.show_in_legend_checkbox.setChecked(True)
        legend_layout.addRow("", self.show_in_legend_checkbox)
        
        self.legend_label_edit = QLineEdit()
        self.legend_label_edit.setPlaceholderText("Leave empty to use series name")
        legend_layout.addRow("Custom Label:", self.legend_label_edit)
        
        layout.addWidget(legend_group)
        
        # Display
        display_group = QGroupBox("Display")
        display_layout = QFormLayout(display_group)
        
        self.visible_checkbox = QCheckBox("Visible")
        self.visible_checkbox.setChecked(True)
        display_layout.addRow("", self.visible_checkbox)
        
        self.z_order_spin = QSpinBox()
        self.z_order_spin.setRange(-100, 100)
        self.z_order_spin.setValue(1)
        self.z_order_spin.setToolTip("Drawing order (higher = drawn on top)")
        display_layout.addRow("Z-Order:", self.z_order_spin)
        
        layout.addWidget(display_group)
        layout.addStretch()
    
    def _on_accept(self):
        """Handle OK button click with validation."""
        is_valid, error_msg = self._validate()
        
        if is_valid:
            self.accept()
        else:
            QMessageBox.warning(self, "Invalid Input", error_msg)
    
    def _validate(self) -> tuple[bool, str]:
        """Validate dialog inputs.
        
        Returns:
            (is_valid, error_message)
        """
        # Check series name
        name = self.name_edit.text().strip()
        if not name:
            return False, "Series name is required"
        
        # Check for duplicate names (if not edit mode or name changed)
        if not self.is_edit_mode or (self.series_metadata and name != self.series_metadata.name):
            if self.plot_model.has_series(name):
                return False, f"Series '{name}' already exists"
        
        # Check columns selected
        if self.x_column_combo.currentData() is None:
            return False, "X column must be selected"
        if self.y_column_combo.currentData() is None:
            return False, "Y column must be selected"
        
        return True, ""
    
    def _validate_input(self):
        """Update OK button state based on validation."""
        is_valid, _ = self._validate()
        if hasattr(self, '_ok_button') and self._ok_button:
            self._ok_button.setEnabled(is_valid)
    
    def get_results(self) -> SeriesMetadata:
        """Get configured series metadata.
        
        Returns:
            SeriesMetadata instance
        """
        return SeriesMetadata(
            name=self.name_edit.text().strip(),
            x_column=self.x_column_combo.currentData(),
            y_column=self.y_column_combo.currentData(),
            x_error_column=self.x_error_combo.currentData(),
            y_error_column=self.y_error_combo.currentData(),
            plot_style=self.plot_style_combo.currentData(),
            color=self._current_color,
            line_style=self.line_style_combo.currentData(),
            line_width=self.line_width_spin.value(),
            marker_style=self.marker_style_combo.currentData(),
            marker_size=self.marker_size_spin.value(),
            alpha=self.alpha_spin.value(),
            show_error_bars=self.show_error_bars_checkbox.isChecked(),
            error_bar_cap_size=self.error_cap_size_spin.value(),
            error_bar_cap_width=self.error_cap_width_spin.value(),
            error_bar_line_width=self.error_line_width_spin.value(),
            show_in_legend=self.show_in_legend_checkbox.isChecked(),
            legend_label=self.legend_label_edit.text().strip() or None,
            visible=self.visible_checkbox.isChecked(),
            z_order=self.z_order_spin.value(),
            use_secondary_y_axis=self.use_secondary_y_checkbox.isChecked()
        )
    
    def _load_existing_values(self):
        """Load existing series metadata into fields."""
        if not self.series_metadata:
            return
        
        s = self.series_metadata
        
        # Data tab
        self.name_edit.setText(s.name)
        
        # Find and select columns
        x_idx = self.x_column_combo.findData(s.x_column)
        if x_idx >= 0:
            self.x_column_combo.setCurrentIndex(x_idx)
        
        y_idx = self.y_column_combo.findData(s.y_column)
        if y_idx >= 0:
            self.y_column_combo.setCurrentIndex(y_idx)
        
        # Error columns
        if s.x_error_column:
            x_err_idx = self.x_error_combo.findData(s.x_error_column)
            if x_err_idx >= 0:
                self.x_error_combo.setCurrentIndex(x_err_idx)
        
        if s.y_error_column:
            y_err_idx = self.y_error_combo.findData(s.y_error_column)
            if y_err_idx >= 0:
                self.y_error_combo.setCurrentIndex(y_err_idx)
        
        self.show_error_bars_checkbox.setChecked(s.show_error_bars)
        
        # Axis selection
        self.use_secondary_y_checkbox.setChecked(s.use_secondary_y_axis)
        
        # Style tab
        style_idx = self.plot_style_combo.findData(s.plot_style)
        if style_idx >= 0:
            self.plot_style_combo.setCurrentIndex(style_idx)
        
        self._current_color = s.color
        self.color_preview.setStyleSheet(f"border: 1px solid #ccc; background: {s.color};")
        
        line_style_idx = self.line_style_combo.findData(s.line_style)
        if line_style_idx >= 0:
            self.line_style_combo.setCurrentIndex(line_style_idx)
        
        self.line_width_spin.setValue(s.line_width)
        
        marker_style_idx = self.marker_style_combo.findData(s.marker_style)
        if marker_style_idx >= 0:
            self.marker_style_combo.setCurrentIndex(marker_style_idx)
        
        self.marker_size_spin.setValue(s.marker_size)
        
        # Advanced tab
        self.alpha_spin.setValue(s.alpha)
        self.error_cap_size_spin.setValue(s.error_bar_cap_size)
        self.error_cap_width_spin.setValue(s.error_bar_cap_width)
        self.error_line_width_spin.setValue(s.error_bar_line_width)
        self.show_in_legend_checkbox.setChecked(s.show_in_legend)
        if s.legend_label:
            self.legend_label_edit.setText(s.legend_label)
        self.visible_checkbox.setChecked(s.visible)
        self.z_order_spin.setValue(s.z_order)
    
    def _choose_color(self):
        """Open color picker dialog."""
        color = QColorDialog.getColor(
            QColor(self._current_color),
            self,
            "Choose Series Color"
        )
        
        if color.isValid():
            self._current_color = color.name()
            self.color_preview.setStyleSheet(f"border: 1px solid #ccc; background: {self._current_color};")
    
    def _suggest_series_name(self):
        """Auto-suggest series name based on column selection."""
        if self.is_edit_mode:
            return
        
        x_col = self.x_column_combo.currentData()
        y_col = self.y_column_combo.currentData()
        
        if x_col and y_col and not self.name_edit.text():
            suggested_name = self.plot_model.suggest_series_name(y_col, x_col)
            self.name_edit.setText(suggested_name)
    
    def _on_data_changed(self):
        """Handle data field changes."""
        if hasattr(self, '_ok_button'):
            is_valid, _ = self._validate()
            if self._ok_button:
                self._ok_button.setEnabled(is_valid)


class AxisConfigDialog(QDialog):
    """Dialog for configuring axis properties."""
    
    def __init__(self, axis_config: AxisConfig, axis_name: str, parent=None):
        """Initialize dialog.
        
        Args:
            axis_config: Current AxisConfig
            axis_name: "X-axis" or "Y-axis"
            parent: Parent widget
        """
        super().__init__(parent)
        self.axis_config = axis_config
        self.axis_name = axis_name
        
        self.setWindowTitle(f"Configure {axis_name}")
        self.setModal(True)
        self.resize(400, 350)
        
        self._setup_ui()
        self._load_values()
    
    def _setup_ui(self):
        """Set up UI."""
        layout = QVBoxLayout(self)
        
        # Label
        label_group = QGroupBox("Label")
        label_layout = QFormLayout(label_group)
        
        self.label_edit = QLineEdit()
        label_layout.addRow("Label:", self.label_edit)
        
        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText("e.g., m, s, kg")
        label_layout.addRow("Unit:", self.unit_edit)
        
        layout.addWidget(label_group)
        
        # Scale
        scale_group = QGroupBox("Scale")
        scale_layout = QFormLayout(scale_group)
        
        self.scale_combo = QComboBox()
        for scale in AxisScale:
            self.scale_combo.addItem(scale.value.title(), scale)
        scale_layout.addRow("Scale Type:", self.scale_combo)
        
        self.invert_checkbox = QCheckBox("Invert axis direction")
        scale_layout.addRow("", self.invert_checkbox)
        
        layout.addWidget(scale_group)
        
        # Range
        range_group = QGroupBox("Range")
        range_layout = QFormLayout(range_group)
        
        self.auto_range_checkbox = QCheckBox("Auto-calculate from data")
        self.auto_range_checkbox.setChecked(True)
        self.auto_range_checkbox.toggled.connect(self._on_auto_range_toggled)
        range_layout.addRow("", self.auto_range_checkbox)
        
        self.min_spin = QDoubleSpinBox()
        self.min_spin.setRange(-1e10, 1e10)
        self.min_spin.setDecimals(6)
        self.min_spin.setEnabled(False)
        range_layout.addRow("Minimum:", self.min_spin)
        
        self.max_spin = QDoubleSpinBox()
        self.max_spin.setRange(-1e10, 1e10)
        self.max_spin.setDecimals(6)
        self.max_spin.setEnabled(False)
        range_layout.addRow("Maximum:", self.max_spin)
        
        layout.addWidget(range_group)
        
        # Grid
        grid_group = QGroupBox("Grid")
        grid_layout = QFormLayout(grid_group)
        
        self.show_grid_checkbox = QCheckBox("Show grid lines")
        self.show_grid_checkbox.setChecked(True)
        grid_layout.addRow("", self.show_grid_checkbox)
        
        self.grid_alpha_spin = QDoubleSpinBox()
        self.grid_alpha_spin.setRange(0.0, 1.0)
        self.grid_alpha_spin.setSingleStep(0.1)
        self.grid_alpha_spin.setValue(0.3)
        grid_layout.addRow("Grid Alpha:", self.grid_alpha_spin)
        
        layout.addWidget(grid_group)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _load_values(self):
        """Load current axis config."""
        self.label_edit.setText(self.axis_config.label)
        self.unit_edit.setText(self.axis_config.unit or "")
        
        scale_idx = self.scale_combo.findData(self.axis_config.scale)
        if scale_idx >= 0:
            self.scale_combo.setCurrentIndex(scale_idx)
        
        self.invert_checkbox.setChecked(self.axis_config.invert)
        self.auto_range_checkbox.setChecked(self.axis_config.auto_range)
        
        if self.axis_config.min_value is not None:
            self.min_spin.setValue(self.axis_config.min_value)
        if self.axis_config.max_value is not None:
            self.max_spin.setValue(self.axis_config.max_value)
        
        self.show_grid_checkbox.setChecked(self.axis_config.show_grid)
        self.grid_alpha_spin.setValue(self.axis_config.grid_alpha)
    
    def _on_auto_range_toggled(self, checked: bool):
        """Handle auto range toggle."""
        self.min_spin.setEnabled(not checked)
        self.max_spin.setEnabled(not checked)
    
    def get_config(self) -> AxisConfig:
        """Get updated axis config.
        
        Returns:
            Updated AxisConfig
        """
        return AxisConfig(
            label=self.label_edit.text(),
            unit=self.unit_edit.text() or None,
            scale=self.scale_combo.currentData(),
            auto_range=self.auto_range_checkbox.isChecked(),
            min_value=self.min_spin.value() if not self.auto_range_checkbox.isChecked() else None,
            max_value=self.max_spin.value() if not self.auto_range_checkbox.isChecked() else None,
            invert=self.invert_checkbox.isChecked(),
            show_grid=self.show_grid_checkbox.isChecked(),
            grid_alpha=self.grid_alpha_spin.value()
        )


class PlotConfigDialog(QDialog):
    """Dialog for general plot configuration (title, legend, etc.)."""
    
    def __init__(self, plot_config: PlotConfig, parent=None):
        """Initialize dialog.
        
        Args:
            plot_config: Current PlotConfig
            parent: Parent widget
        """
        super().__init__(parent)
        self.plot_config = plot_config
        
        self.setWindowTitle("Plot Configuration")
        self.setModal(True)
        self.resize(450, 400)
        
        self._setup_ui()
        self._load_values()
    
    def _setup_ui(self):
        """Set up UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title_group = QGroupBox("Title")
        title_layout = QFormLayout(title_group)
        
        self.title_edit = QLineEdit()
        title_layout.addRow("Title:", self.title_edit)
        
        self.title_fontsize_spin = QSpinBox()
        self.title_fontsize_spin.setRange(8, 32)
        self.title_fontsize_spin.setValue(14)
        title_layout.addRow("Font Size:", self.title_fontsize_spin)
        
        layout.addWidget(title_group)
        
        # Legend
        legend_group = QGroupBox("Legend")
        legend_layout = QFormLayout(legend_group)
        
        self.show_legend_checkbox = QCheckBox("Show legend")
        self.show_legend_checkbox.setChecked(True)
        self.show_legend_checkbox.toggled.connect(self._on_legend_toggled)
        legend_layout.addRow("", self.show_legend_checkbox)
        
        self.legend_location_combo = QComboBox()
        for loc in LegendLocation:
            self.legend_location_combo.addItem(loc.value.title(), loc)
        legend_layout.addRow("Location:", self.legend_location_combo)
        
        self.legend_fontsize_spin = QSpinBox()
        self.legend_fontsize_spin.setRange(6, 20)
        self.legend_fontsize_spin.setValue(10)
        legend_layout.addRow("Font Size:", self.legend_fontsize_spin)
        
        layout.addWidget(legend_group)
        
        # Grid
        grid_group = QGroupBox("Grid")
        grid_layout = QFormLayout(grid_group)
        
        self.grid_style_combo = QComboBox()
        for style in GridStyle:
            self.grid_style_combo.addItem(style.value.title(), style)
        grid_layout.addRow("Grid Style:", self.grid_style_combo)
        
        layout.addWidget(grid_group)
        
        # Figure
        figure_group = QGroupBox("Figure")
        figure_layout = QFormLayout(figure_group)
        
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(4.0, 20.0)
        self.width_spin.setSingleStep(0.5)
        self.width_spin.setValue(8.0)
        self.width_spin.setSuffix(" in")
        figure_layout.addRow("Width:", self.width_spin)
        
        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(3.0, 15.0)
        self.height_spin.setSingleStep(0.5)
        self.height_spin.setValue(6.0)
        self.height_spin.setSuffix(" in")
        figure_layout.addRow("Height:", self.height_spin)
        
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(50, 300)
        self.dpi_spin.setSingleStep(10)
        self.dpi_spin.setValue(100)
        figure_layout.addRow("DPI:", self.dpi_spin)
        
        layout.addWidget(figure_group)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _load_values(self):
        """Load current config."""
        self.title_edit.setText(self.plot_config.title)
        self.title_fontsize_spin.setValue(self.plot_config.title_fontsize)
        
        self.show_legend_checkbox.setChecked(self.plot_config.legend.show)
        
        loc_idx = self.legend_location_combo.findData(self.plot_config.legend.location)
        if loc_idx >= 0:
            self.legend_location_combo.setCurrentIndex(loc_idx)
        
        self.legend_fontsize_spin.setValue(self.plot_config.legend.fontsize)
        
        grid_idx = self.grid_style_combo.findData(self.plot_config.grid_style)
        if grid_idx >= 0:
            self.grid_style_combo.setCurrentIndex(grid_idx)
        
        self.width_spin.setValue(self.plot_config.figure_width)
        self.height_spin.setValue(self.plot_config.figure_height)
        self.dpi_spin.setValue(self.plot_config.dpi)
    
    def _on_legend_toggled(self, checked: bool):
        """Handle legend checkbox toggle."""
        self.legend_location_combo.setEnabled(checked)
        self.legend_fontsize_spin.setEnabled(checked)
    
    def get_config(self) -> PlotConfig:
        """Get updated plot config.
        
        Returns:
            Updated PlotConfig (modifies original)
        """
        self.plot_config.title = self.title_edit.text()
        self.plot_config.title_fontsize = self.title_fontsize_spin.value()
        
        self.plot_config.legend.show = self.show_legend_checkbox.isChecked()
        self.plot_config.legend.location = self.legend_location_combo.currentData()
        self.plot_config.legend.fontsize = self.legend_fontsize_spin.value()
        
        self.plot_config.grid_style = self.grid_style_combo.currentData()
        
        self.plot_config.figure_width = self.width_spin.value()
        self.plot_config.figure_height = self.height_spin.value()
        self.plot_config.dpi = self.dpi_spin.value()
        
        return self.plot_config
