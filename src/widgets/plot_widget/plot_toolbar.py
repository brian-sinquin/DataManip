"""
Toolbar for plot widget.

This module provides toolbar actions for plot management:
- Add/remove series
- Configure axes and plot
- Export plot
- Refresh plot
"""

from PySide6.QtWidgets import QToolBar, QToolButton, QMenu, QFileDialog, QMessageBox
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt, Slot
from typing import TYPE_CHECKING

from .plot_dialogs import AddSeriesDialog, AxisConfigDialog, PlotConfigDialog
from .series_metadata import SeriesMetadata

if TYPE_CHECKING:
    from .plot_view import PlotView


class PlotToolbar(QToolBar):
    """Toolbar for plot widget operations.
    
    Provides actions for:
    - Adding/editing/removing series
    - Configuring axes
    - Configuring plot appearance
    - Exporting plots
    - Refreshing view
    """
    
    def __init__(self, plot_view: 'PlotView', parent=None):
        """Initialize toolbar.
        
        Args:
            plot_view: PlotView instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.plot_view = plot_view
        self.plot_model = plot_view.get_model()
        
        self.setWindowTitle("Plot Toolbar")
        self.setObjectName("PlotToolbar")
        
        self._create_actions()
    
    def _create_actions(self):
        """Create toolbar actions."""
        # Add Series (with dropdown for quick add)
        add_series_button = QToolButton()
        add_series_button.setText("Add Series")
        add_series_button.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        add_series_button.clicked.connect(self._add_series)
        
        # Quick add menu (if there are multiple column pairs)
        add_menu = QMenu(self)
        add_menu.aboutToShow.connect(lambda: self._populate_quick_add_menu(add_menu))
        add_series_button.setMenu(add_menu)
        
        self.addWidget(add_series_button)
        
        # Manage Series
        manage_series_button = QToolButton()
        manage_series_button.setText("Manage Series")
        manage_series_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        
        manage_menu = QMenu(self)
        manage_menu.aboutToShow.connect(lambda: self._populate_manage_menu(manage_menu))
        manage_series_button.setMenu(manage_menu)
        
        self.addWidget(manage_series_button)
        
        self.addSeparator()
        
        # Configure Axes
        axes_button = QToolButton()
        axes_button.setText("Axes")
        axes_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        
        axes_menu = QMenu(self)
        axes_menu.addAction("Configure X-Axis...", self._configure_x_axis)
        axes_menu.addAction("Configure Y-Axis (Primary)...", self._configure_y_axis)
        axes_menu.addAction("Configure Y-Axis (Secondary)...", self._configure_y2_axis)
        axes_menu.addSeparator()
        axes_menu.addAction("Auto-Configure from Data", self._auto_configure_axes)
        axes_button.setMenu(axes_menu)
        
        self.addWidget(axes_button)
        
        # Configure Plot
        config_action = QAction("Plot Config...", self)
        config_action.triggered.connect(self._configure_plot)
        self.addAction(config_action)
        
        self.addSeparator()
        
        # Refresh
        refresh_action = QAction("Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._refresh_plot)
        self.addAction(refresh_action)
        
        # Clear
        clear_action = QAction("Clear", self)
        clear_action.triggered.connect(self._clear_plot)
        self.addAction(clear_action)
        
        self.addSeparator()
        
        # Export
        export_button = QToolButton()
        export_button.setText("Export")
        export_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        
        export_menu = QMenu(self)
        export_menu.addAction("Export as PNG...", lambda: self._export_plot("png"))
        export_menu.addAction("Export as PDF...", lambda: self._export_plot("pdf"))
        export_menu.addAction("Export as SVG...", lambda: self._export_plot("svg"))
        export_button.setMenu(export_menu)
        
        self.addWidget(export_button)
    
    # ========================================================================
    # Series Management
    # ========================================================================
    
    @Slot()
    def _add_series(self):
        """Add new series via dialog."""
        if not self.plot_model:
            QMessageBox.warning(self, "No Model", "No plot model available")
            return
        
        dialog = AddSeriesDialog(self.plot_model, self)
        
        if dialog.exec():
            series = dialog.get_results()
            try:
                self.plot_model.add_series(series)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to add series: {str(e)}")
    
    def _populate_quick_add_menu(self, menu: QMenu):
        """Populate quick add menu with column pair suggestions.
        
        Args:
            menu: Menu to populate
        """
        menu.clear()
        
        if not self.plot_model:
            menu.addAction("(No model available)").setEnabled(False)
            return
        
        available = self.plot_model.get_available_columns()
        
        if len(available) < 2:
            menu.addAction("(Insufficient columns)").setEnabled(False)
            return
        
        # Suggest some common pairings (first column as X, others as Y)
        if len(available) >= 2:
            x_col_name, x_display = available[0]
            
            for i in range(1, min(6, len(available))):  # Limit to 5 suggestions
                y_col_name, y_display = available[i]
                
                action = menu.addAction(f"{y_display} vs {x_display}")
                action.triggered.connect(
                    lambda checked=False, x=x_col_name, y=y_col_name: self._quick_add_series(x, y)
                )
        
        menu.addSeparator()
        menu.addAction("Custom...", self._add_series)
    
    def _quick_add_series(self, x_column: str, y_column: str):
        """Quickly add a series with default settings.
        
        Args:
            x_column: X column name
            y_column: Y column name
        """
        if not self.plot_model:
            return
        
        try:
            # Generate unique name
            series_name = self.plot_model.suggest_series_name(y_column, x_column)
            
            # Get auto color
            color_index = self.plot_model.series_count()
            from .series_metadata import get_default_color
            color = get_default_color(color_index)
            
            # Create series with defaults
            series = SeriesMetadata(
                name=series_name,
                x_column=x_column,
                y_column=y_column,
                color=color
            )
            
            self.plot_model.add_series(series)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to add series: {str(e)}")
    
    def _populate_manage_menu(self, menu: QMenu):
        """Populate manage series menu.
        
        Args:
            menu: Menu to populate
        """
        menu.clear()
        
        if not self.plot_model:
            menu.addAction("(No model available)").setEnabled(False)
            return
        
        series_names = self.plot_model.get_series_names()
        
        if not series_names:
            menu.addAction("(No series)").setEnabled(False)
            return
        
        for series_name in series_names:
            series_menu = menu.addMenu(series_name)
            
            # Edit
            edit_action = series_menu.addAction("Edit...")
            edit_action.triggered.connect(
                lambda checked=False, name=series_name: self._edit_series(name)
            )
            
            # Toggle visibility
            series = self.plot_model.get_series(series_name)
            visibility_text = "Hide" if series.visible else "Show"
            visibility_action = series_menu.addAction(visibility_text)
            visibility_action.triggered.connect(
                lambda checked=False, name=series_name: self._toggle_series_visibility(name)
            )
            
            series_menu.addSeparator()
            
            # Remove
            remove_action = series_menu.addAction("Remove")
            remove_action.triggered.connect(
                lambda checked=False, name=series_name: self._remove_series(name)
            )
        
        menu.addSeparator()
        menu.addAction("Clear All Series", self._clear_all_series)
    
    @Slot(str)
    def _edit_series(self, series_name: str):
        """Edit existing series.
        
        Args:
            series_name: Name of series to edit
        """
        if not self.plot_model:
            return
        
        try:
            series = self.plot_model.get_series(series_name)
            dialog = AddSeriesDialog(self.plot_model, self, series_metadata=series)
            
            if dialog.exec():
                updated_series = dialog.get_results()
                self.plot_model.update_series(series_name, updated_series)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to edit series: {str(e)}")
    
    @Slot(str)
    def _toggle_series_visibility(self, series_name: str):
        """Toggle series visibility.
        
        Args:
            series_name: Name of series
        """
        if not self.plot_model:
            return
        
        try:
            series = self.plot_model.get_series(series_name)
            series.visible = not series.visible
            self.plot_model.update_series(series_name, series)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to toggle visibility: {str(e)}")
    
    @Slot(str)
    def _remove_series(self, series_name: str):
        """Remove series.
        
        Args:
            series_name: Name of series to remove
        """
        if not self.plot_model:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Remove",
            f"Remove series '{series_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.plot_model.remove_series(series_name)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to remove series: {str(e)}")
    
    @Slot()
    def _clear_all_series(self):
        """Clear all series from plot."""
        if not self.plot_model:
            return
        
        if self.plot_model.series_count() == 0:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Clear",
            "Remove all series from plot?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.plot_model.clear_all_series()
    
    # ========================================================================
    # Configuration
    # ========================================================================
    
    @Slot()
    def _configure_x_axis(self):
        """Configure X-axis."""
        if not self.plot_model:
            return
        
        config = self.plot_model.get_config()
        dialog = AxisConfigDialog(config.x_axis, "X-axis", self)
        
        if dialog.exec():
            new_axis_config = dialog.get_config()
            self.plot_model.update_x_axis(**new_axis_config.__dict__)
    
    @Slot()
    def _configure_y_axis(self):
        """Configure Y-axis."""
        if not self.plot_model:
            return
        
        config = self.plot_model.get_config()
        dialog = AxisConfigDialog(config.y_axis, "Y-axis (Primary)", self)
        
        if dialog.exec():
            new_axis_config = dialog.get_config()
            self.plot_model.update_y_axis(**new_axis_config.__dict__)
    
    @Slot()
    def _configure_y2_axis(self):
        """Configure secondary Y-axis."""
        if not self.plot_model:
            return
        
        config = self.plot_model.get_config()
        dialog = AxisConfigDialog(config.y2_axis, "Y-axis (Secondary)", self)
        
        if dialog.exec():
            new_axis_config = dialog.get_config()
            self.plot_model.update_y2_axis(**new_axis_config.__dict__)
    
    @Slot()
    def _configure_plot(self):
        """Configure general plot settings."""
        if not self.plot_model:
            return
        
        config = self.plot_model.get_config()
        dialog = PlotConfigDialog(config, self)
        
        if dialog.exec():
            updated_config = dialog.get_config()
            self.plot_model.set_config(updated_config)
    
    @Slot()
    def _auto_configure_axes(self):
        """Auto-configure axes from data."""
        if not self.plot_model:
            return
        
        self.plot_model.auto_configure_axes()
    
    # ========================================================================
    # View Actions
    # ========================================================================
    
    @Slot()
    def _refresh_plot(self):
        """Refresh plot view."""
        if self.plot_view:
            self.plot_view.refresh()
    
    @Slot()
    def _clear_plot(self):
        """Clear plot (remove all series)."""
        self._clear_all_series()
    
    # ========================================================================
    # Export
    # ========================================================================
    
    @Slot(str)
    def _export_plot(self, format: str):
        """Export plot to file.
        
        Args:
            format: File format (png, pdf, svg)
        """
        if not self.plot_view:
            return
        
        # Get save file path
        filter_map = {
            "png": "PNG Image (*.png)",
            "pdf": "PDF Document (*.pdf)",
            "svg": "SVG Vector (*.svg)"
        }
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            f"Export Plot as {format.upper()}",
            f"plot.{format}",
            filter_map.get(format, "All Files (*)")
        )
        
        if not filepath:
            return
        
        # Ensure correct extension
        if not filepath.endswith(f".{format}"):
            filepath += f".{format}"
        
        # Export
        try:
            self.plot_view.export_image(filepath)
            QMessageBox.information(
                self,
                "Export Successful",
                f"Plot exported to:\n{filepath}"
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Export Failed",
                f"Failed to export plot:\n{str(e)}"
            )
