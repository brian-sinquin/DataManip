"""
Plot model for managing plot series and configuration.

This module implements the data model for plots, handling series management,
configuration, and data extraction from DataTable.
"""

from typing import Optional, List, Dict, Tuple
import numpy as np
from PySide6.QtCore import QObject, Signal

from .series_metadata import SeriesMetadata, get_default_color
from .plot_config import PlotConfig, AxisConfig
from widgets.data_table import DataTableWidget
from constants import DataType


class PlotModel(QObject):
    """Model for managing plot series and configuration.
    
    This model is Qt-independent at its core and handles:
    - Series metadata management
    - Plot configuration
    - Data extraction from DataTable
    - Series validation
    
    Signals:
        seriesAdded: Emitted when a series is added (series_name)
        seriesRemoved: Emitted when a series is removed (series_name)
        seriesUpdated: Emitted when a series is modified (series_name)
        configUpdated: Emitted when plot config changes
        dataChanged: Emitted when underlying data changes
        errorOccurred: Emitted on errors (error_message)
    """
    
    # Signals
    seriesAdded = Signal(str)       # series_name
    seriesRemoved = Signal(str)     # series_name
    seriesUpdated = Signal(str)     # series_name
    configUpdated = Signal()
    dataChanged = Signal()
    errorOccurred = Signal(str)     # error_message
    
    def __init__(self, datatable: Optional[DataTableWidget] = None, parent=None):
        """Initialize plot model.
        
        Args:
            datatable: Reference to DataTableWidget
            parent: Parent QObject
        """
        super().__init__(parent)
        
        # Data source
        self._datatable = datatable
        
        # Series storage (ordered)
        self._series: Dict[str, SeriesMetadata] = {}
        self._series_order: List[str] = []
        
        # Plot configuration
        self._config = PlotConfig()
        
        # Connect to datatable signals
        if self._datatable:
            self._connect_datatable_signals()
    
    def _connect_datatable_signals(self):
        """Connect to datatable model signals."""
        if not self._datatable:
            return
        
        model = self._datatable.model()
        model.dataChanged.connect(self._on_datatable_data_changed)
        model.columnAdded.connect(self._on_datatable_column_added)
        model.columnRemoved.connect(self._on_datatable_column_removed)
        model.columnRenamed.connect(self._on_datatable_column_renamed)
    
    def set_datatable(self, datatable: DataTableWidget):
        """Set or update the datatable reference.
        
        Args:
            datatable: DataTableWidget to plot from
        """
        # Disconnect old signals
        if self._datatable:
            try:
                model = self._datatable.model()
                model.dataChanged.disconnect(self._on_datatable_data_changed)
                model.columnAdded.disconnect(self._on_datatable_column_added)
                model.columnRemoved.disconnect(self._on_datatable_column_removed)
                model.columnRenamed.disconnect(self._on_datatable_column_renamed)
            except Exception:
                pass
        
        # Set new datatable
        self._datatable = datatable
        
        # Connect new signals
        if self._datatable:
            self._connect_datatable_signals()
        
        # Validate existing series
        self._validate_all_series()
    
    # ========================================================================
    # Series Management
    # ========================================================================
    
    def add_series(self, series: SeriesMetadata) -> None:
        """Add a new series to the plot.
        
        Args:
            series: SeriesMetadata instance
            
        Raises:
            ValueError: If series name already exists, columns are invalid, or units incompatible
        """
        # Check for duplicate name
        if series.name in self._series:
            raise ValueError(f"Series '{series.name}' already exists")
        
        # Validate columns exist in datatable
        if not self._validate_series_columns(series):
            raise ValueError(f"Invalid columns for series '{series.name}'")
        
        # Validate unit compatibility
        if not self._validate_unit_compatibility(series):
            # Get detailed error message
            model = self._datatable.model()
            new_y_unit = model.get_column_metadata(series.y_column).unit or "dimensionless"
            new_x_unit = model.get_column_metadata(series.x_column).unit or "dimensionless"
            
            axis_type = "secondary Y" if series.use_secondary_y_axis else "primary Y"
            raise ValueError(
                f"Cannot add series: incompatible units.\n"
                f"Y-axis ({axis_type}): {new_y_unit}\n"
                f"X-axis: {new_x_unit}\n"
                f"\nTip: Use 'Secondary Y-axis' to plot different units."
            )
        
        # Add series
        self._series[series.name] = series
        self._series_order.append(series.name)
        
        # Auto-configure axes with units from first series
        if len(self._series_order) == 1:
            self._auto_set_axis_units(series)
        
        # Emit signal
        self.seriesAdded.emit(series.name)
    
    def remove_series(self, series_name: str) -> None:
        """Remove a series from the plot.
        
        Args:
            series_name: Name of series to remove
            
        Raises:
            KeyError: If series doesn't exist
        """
        if series_name not in self._series:
            raise KeyError(f"Series '{series_name}' not found")
        
        # Remove series
        del self._series[series_name]
        self._series_order.remove(series_name)
        
        # Emit signal
        self.seriesRemoved.emit(series_name)
    
    def update_series(self, series_name: str, series: SeriesMetadata) -> None:
        """Update an existing series.
        
        Args:
            series_name: Current name of series
            series: New SeriesMetadata (can have different name)
            
        Raises:
            KeyError: If series doesn't exist
            ValueError: If new name conflicts, columns invalid, or units incompatible
        """
        if series_name not in self._series:
            raise KeyError(f"Series '{series_name}' not found")
        
        # Check for name conflict (if name changed)
        if series.name != series_name and series.name in self._series:
            raise ValueError(f"Series '{series.name}' already exists")
        
        # Validate columns
        if not self._validate_series_columns(series):
            raise ValueError(f"Invalid columns for series '{series.name}'")
        
        # Validate unit compatibility (temporarily remove current series from check)
        old_series = self._series[series_name]
        del self._series[series_name]
        self._series_order.remove(series_name)
        
        try:
            if not self._validate_unit_compatibility(series):
                # Restore old series
                self._series[series_name] = old_series
                self._series_order.append(series_name)
                
                # Get detailed error message
                model = self._datatable.model()
                new_y_unit = model.get_column_metadata(series.y_column).unit or "dimensionless"
                axis_type = "secondary Y" if series.use_secondary_y_axis else "primary Y"
                raise ValueError(
                    f"Cannot update series: incompatible units on {axis_type}-axis ({new_y_unit})"
                )
            
            # Handle name change
            if series.name != series_name:
                # Add with new name
                self._series[series.name] = series
                self._series_order.append(series.name)
            else:
                # Just update metadata
                self._series[series_name] = series
                self._series_order.append(series_name)
            
            # Emit signal
            self.seriesUpdated.emit(series.name)
            
        except ValueError:
            # Restore old series and re-raise
            self._series[series_name] = old_series
            self._series_order.append(series_name)
            raise
    
    def get_series(self, series_name: str) -> SeriesMetadata:
        """Get series metadata by name.
        
        Args:
            series_name: Name of series
            
        Returns:
            SeriesMetadata instance
            
        Raises:
            KeyError: If series doesn't exist
        """
        if series_name not in self._series:
            raise KeyError(f"Series '{series_name}' not found")
        return self._series[series_name]
    
    def get_all_series(self) -> List[SeriesMetadata]:
        """Get all series in order.
        
        Returns:
            List of SeriesMetadata instances
        """
        return [self._series[name] for name in self._series_order]
    
    def get_series_names(self) -> List[str]:
        """Get all series names in order.
        
        Returns:
            List of series names
        """
        return self._series_order.copy()
    
    def has_series(self, series_name: str) -> bool:
        """Check if series exists.
        
        Args:
            series_name: Name of series
            
        Returns:
            True if series exists
        """
        return series_name in self._series
    
    def series_count(self) -> int:
        """Get number of series.
        
        Returns:
            Number of series
        """
        return len(self._series)
    
    def clear_all_series(self) -> None:
        """Remove all series from plot."""
        series_names = self._series_order.copy()
        for name in series_names:
            self.remove_series(name)
    
    def _validate_series_columns(self, series: SeriesMetadata) -> bool:
        """Validate that series columns exist in datatable.
        
        Args:
            series: SeriesMetadata to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not self._datatable:
            return False
        
        model = self._datatable.model()
        column_names = model.get_column_names()
        
        # Check required columns
        if series.x_column not in column_names:
            return False
        if series.y_column not in column_names:
            return False
        
        # Check optional error columns
        if series.x_error_column and series.x_error_column not in column_names:
            return False
        if series.y_error_column and series.y_error_column not in column_names:
            return False
        
        # Check that columns are numerical
        try:
            x_meta = model.get_column_metadata(series.x_column)
            y_meta = model.get_column_metadata(series.y_column)
            
            if x_meta.dtype not in (DataType.FLOAT, DataType.INTEGER):
                return False
            if y_meta.dtype not in (DataType.FLOAT, DataType.INTEGER):
                return False
        except Exception:
            return False
        
        return True
    
    def _validate_unit_compatibility(self, series: SeriesMetadata) -> bool:
        """Validate that series units are compatible with existing series on same axis.
        
        Args:
            series: SeriesMetadata to validate
            
        Returns:
            True if compatible, False otherwise
        """
        if not self._datatable or not self._series_order:
            return True  # First series or no datatable
        
        model = self._datatable.model()
        
        try:
            # Get units for the new series
            new_x_meta = model.get_column_metadata(series.x_column)
            new_y_meta = model.get_column_metadata(series.y_column)
            new_x_unit = new_x_meta.unit
            new_y_unit = new_y_meta.unit
            
            # Check against existing series
            for existing_name in self._series_order:
                existing = self._series[existing_name]
                
                # Get units for existing series
                existing_x_meta = model.get_column_metadata(existing.x_column)
                existing_y_meta = model.get_column_metadata(existing.y_column)
                existing_x_unit = existing_x_meta.unit
                existing_y_unit = existing_y_meta.unit
                
                # Check X-axis unit compatibility (always shared)
                if new_x_unit != existing_x_unit:
                    # Allow dimensionless (None) to mix with any unit
                    if new_x_unit is not None and existing_x_unit is not None:
                        return False
                
                # Check Y-axis unit compatibility
                # Series on different axes (primary vs secondary) can have different units
                if series.use_secondary_y_axis == existing.use_secondary_y_axis:
                    if new_y_unit != existing_y_unit:
                        # Allow dimensionless (None) to mix with any unit
                        if new_y_unit is not None and existing_y_unit is not None:
                            return False
            
            return True
            
        except Exception:
            # If we can't get metadata, allow the series (fail open)
            return True
    
    def _validate_all_series(self):
        """Validate all series against current datatable state."""
        invalid_series = []
        
        for series_name in self._series_order:
            series = self._series[series_name]
            if not self._validate_series_columns(series):
                invalid_series.append(series_name)
        
        # Remove invalid series
        for series_name in invalid_series:
            try:
                self.remove_series(series_name)
                self.errorOccurred.emit(f"Series '{series_name}' removed: columns no longer valid")
            except Exception:
                pass
    
    # ========================================================================
    # Data Extraction
    # ========================================================================
    
    def get_series_data(self, series_name: str) -> Tuple[np.ndarray, np.ndarray,
                                                          Optional[np.ndarray], Optional[np.ndarray]]:
        """Extract data for a series from datatable.
        
        Args:
            series_name: Name of series
            
        Returns:
            Tuple of (x_data, y_data, x_error, y_error) as numpy arrays
            Error arrays are None if not specified
            
        Raises:
            KeyError: If series doesn't exist
            ValueError: If data extraction fails
        """
        if series_name not in self._series:
            raise KeyError(f"Series '{series_name}' not found")
        
        if not self._datatable:
            raise ValueError("No datatable connected")
        
        series = self._series[series_name]
        model = self._datatable.model()
        
        # Extract X and Y data
        try:
            x_series = model.get_column_data(series.x_column)
            y_series = model.get_column_data(series.y_column)
            
            # Drop NaN values and convert to numpy
            x_data = x_series.dropna().to_numpy()
            y_data = y_series.dropna().to_numpy()
            
            # Ensure equal length
            min_len = min(len(x_data), len(y_data))
            x_data = x_data[:min_len]
            y_data = y_data[:min_len]
            
        except Exception as e:
            raise ValueError(f"Failed to extract data for series '{series_name}': {str(e)}")
        
        # Extract error data if specified
        x_error = None
        y_error = None
        
        try:
            if series.x_error_column:
                x_error_series = model.get_column_data(series.x_error_column)
                x_error = x_error_series.dropna().to_numpy()[:min_len]
            
            if series.y_error_column:
                y_error_series = model.get_column_data(series.y_error_column)
                y_error = y_error_series.dropna().to_numpy()[:min_len]
        except Exception:
            # Error columns are optional, don't fail if they can't be extracted
            pass
        
        return x_data, y_data, x_error, y_error
    
    def get_all_series_data(self) -> List[Tuple[str, np.ndarray, np.ndarray,
                                                 Optional[np.ndarray], Optional[np.ndarray]]]:
        """Extract data for all visible series.
        
        Returns:
            List of tuples: (series_name, x_data, y_data, x_error, y_error)
            Only includes visible series with valid data
        """
        result = []
        
        for series_name in self._series_order:
            series = self._series[series_name]
            
            # Skip invisible series
            if not series.visible:
                continue
            
            # Extract data
            try:
                x_data, y_data, x_error, y_error = self.get_series_data(series_name)
                result.append((series_name, x_data, y_data, x_error, y_error))
            except Exception as e:
                self.errorOccurred.emit(f"Failed to extract data for '{series_name}': {str(e)}")
                continue
        
        return result
    
    # ========================================================================
    # Configuration Management
    # ========================================================================
    
    def get_config(self) -> PlotConfig:
        """Get current plot configuration.
        
        Returns:
            PlotConfig instance
        """
        return self._config
    
    def set_config(self, config: PlotConfig) -> None:
        """Set plot configuration.
        
        Args:
            config: New PlotConfig instance
        """
        self._config = config
        self.configUpdated.emit()
    
    def update_config(self, **kwargs) -> None:
        """Update specific config attributes.
        
        Args:
            **kwargs: Config attributes to update
        """
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
        
        self.configUpdated.emit()
    
    def update_x_axis(self, **kwargs) -> None:
        """Update X-axis configuration.
        
        Args:
            **kwargs: AxisConfig attributes to update
        """
        for key, value in kwargs.items():
            if hasattr(self._config.x_axis, key):
                setattr(self._config.x_axis, key, value)
        
        self.configUpdated.emit()
    
    def update_y_axis(self, **kwargs) -> None:
        """Update Y-axis configuration.
        
        Args:
            **kwargs: AxisConfig attributes to update
        """
        for key, value in kwargs.items():
            if hasattr(self._config.y_axis, key):
                setattr(self._config.y_axis, key, value)
        
        self.configUpdated.emit()
    
    def update_y2_axis(self, **kwargs) -> None:
        """Update secondary Y-axis configuration.
        
        Args:
            **kwargs: AxisConfig attributes to update
        """
        for key, value in kwargs.items():
            if hasattr(self._config.y2_axis, key):
                setattr(self._config.y2_axis, key, value)
        
        self.configUpdated.emit()
    
    def update_legend(self, **kwargs) -> None:
        """Update legend configuration.
        
        Args:
            **kwargs: LegendConfig attributes to update
        """
        for key, value in kwargs.items():
            if hasattr(self._config.legend, key):
                setattr(self._config.legend, key, value)
        
        self.configUpdated.emit()
    
    # ========================================================================
    # DataTable Event Handlers
    # ========================================================================
    
    def _on_datatable_data_changed(self):
        """Handle datatable data changes."""
        self.dataChanged.emit()
    
    def _on_datatable_column_added(self, column_name: str):
        """Handle datatable column added."""
        # No action needed, but could auto-suggest adding series
        pass
    
    def _on_datatable_column_removed(self, column_name: str):
        """Handle datatable column removed."""
        # Check if any series use this column
        affected_series = []
        
        for series_name in self._series_order:
            series = self._series[series_name]
            if (series.x_column == column_name or
                series.y_column == column_name or
                series.x_error_column == column_name or
                series.y_error_column == column_name):
                affected_series.append(series_name)
        
        # Remove affected series
        for series_name in affected_series:
            try:
                self.remove_series(series_name)
                self.errorOccurred.emit(
                    f"Series '{series_name}' removed: column '{column_name}' was deleted"
                )
            except Exception:
                pass
    
    def _on_datatable_column_renamed(self, old_name: str, new_name: str):
        """Handle datatable column renamed."""
        # Update series that reference the renamed column
        for series_name in self._series_order:
            series = self._series[series_name]
            updated = False
            
            if series.x_column == old_name:
                series.x_column = new_name
                updated = True
            
            if series.y_column == old_name:
                series.y_column = new_name
                updated = True
            
            if series.x_error_column == old_name:
                series.x_error_column = new_name
                updated = True
            
            if series.y_error_column == old_name:
                series.y_error_column = new_name
                updated = True
            
            if updated:
                self.seriesUpdated.emit(series_name)
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def get_available_columns(self) -> List[Tuple[str, str]]:
        """Get list of available numerical columns from datatable.
        
        Returns:
            List of tuples: (column_name, display_text_with_unit)
        """
        if not self._datatable:
            return []
        
        model = self._datatable.model()
        result = []
        
        for col_name in model.get_column_names():
            try:
                metadata = model.get_column_metadata(col_name)
                
                # Only include numerical columns
                if metadata.dtype in (DataType.FLOAT, DataType.INTEGER):
                    display_text = col_name
                    if metadata.unit:
                        display_text += f" [{metadata.unit}]"
                    
                    result.append((col_name, display_text))
            except Exception:
                continue
        
        return result
    
    def suggest_series_name(self, y_column: str, x_column: str) -> str:
        """Suggest a unique name for a new series.
        
        Args:
            y_column: Y column name
            x_column: X column name
            
        Returns:
            Suggested unique series name
        """
        base_name = f"{y_column} vs {x_column}"
        
        if base_name not in self._series:
            return base_name
        
        # Add number suffix to make unique
        counter = 2
        while f"{base_name} ({counter})" in self._series:
            counter += 1
        
        return f"{base_name} ({counter})"
    
    def _auto_set_axis_units(self, series: SeriesMetadata):
        """Automatically set axis units from series column metadata.
        
        Args:
            series: Series to extract units from
        """
        if not self._datatable:
            return
        
        model = self._datatable.model()
        
        try:
            # Get column metadata
            x_meta = model.get_column_metadata(series.x_column)
            y_meta = model.get_column_metadata(series.y_column)
            
            # Set axis labels to column names (overwrite default labels)
            if not self._config.x_axis.label or self._config.x_axis.label == "X-axis":
                self._config.x_axis.label = series.x_column
            
            if not self._config.y_axis.label or self._config.y_axis.label == "Y-axis":
                self._config.y_axis.label = series.y_column
            
            # Set units from column metadata
            if x_meta.unit and not self._config.x_axis.unit:
                self._config.x_axis.unit = x_meta.unit
            
            if y_meta.unit and not self._config.y_axis.unit:
                self._config.y_axis.unit = y_meta.unit
            
            # Emit config update
            self.configUpdated.emit()
        except Exception:
            # Silently fail if metadata retrieval fails
            pass
    
    def auto_configure_axes(self):
        """Automatically configure axes labels from first series."""
        if not self._series_order or not self._datatable:
            return
        
        # Use first series to set axis labels
        first_series = self._series[self._series_order[0]]
        model = self._datatable.model()
        
        try:
            x_meta = model.get_column_metadata(first_series.x_column)
            y_meta = model.get_column_metadata(first_series.y_column)
            
            # Update axis labels and units
            self._config.x_axis.label = first_series.x_column
            self._config.x_axis.unit = x_meta.unit
            
            self._config.y_axis.label = first_series.y_column
            self._config.y_axis.unit = y_meta.unit
            
            self.configUpdated.emit()
        except Exception:
            pass
    
    # ========================================================================
    # Serialization
    # ========================================================================
    
    def to_dict(self) -> dict:
        """Convert model state to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            'series': [self._series[name].to_dict() for name in self._series_order],
            'config': self._config.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: dict, datatable: Optional[DataTableWidget] = None) -> 'PlotModel':
        """Create PlotModel from dictionary.
        
        Args:
            data: Dictionary representation
            datatable: DataTableWidget reference
            
        Returns:
            PlotModel instance
        """
        model = cls(datatable=datatable)
        
        # Restore configuration
        if 'config' in data:
            model._config = PlotConfig.from_dict(data['config'])
        
        # Restore series
        if 'series' in data:
            for series_dict in data['series']:
                try:
                    series = SeriesMetadata.from_dict(series_dict)
                    model.add_series(series)
                except Exception:
                    # Skip invalid series
                    continue
        
        return model
