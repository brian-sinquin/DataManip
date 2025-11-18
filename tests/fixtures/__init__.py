"""Test fixtures for DataManip tests."""

import pytest
import pandas as pd
from widgets import DataTableModel
from constants import DataType


@pytest.fixture
def empty_model():
    """Create an empty DataTableModel."""
    return DataTableModel()


@pytest.fixture
def sample_data_model():
    """Create a DataTableModel with sample data."""
    model = DataTableModel()
    
    # Add time column
    model.add_data_column(
        name="time",
        unit="s",
        data=pd.Series([0, 1, 2, 3, 4, 5])
    )
    
    # Add position column
    model.add_data_column(
        name="position",
        unit="m",
        data=pd.Series([0, 5, 20, 45, 80, 125])
    )
    
    return model


@pytest.fixture
def physics_model():
    """Create a model with physics data (projectile motion)."""
    model = DataTableModel()
    
    # Constants
    model.set_variables({'g': 9.81})
    
    # Time range
    model.add_range_column(
        name="t",
        start=0.0,
        end=3.0,
        points=31,
        unit="s"
    )
    
    # Position formula
    model.add_calculated_column(
        name="x",
        formula="20 * {t}",
        unit="m"
    )
    
    model.add_calculated_column(
        name="y",
        formula="20 * {t} - 0.5 * g * {t}**2",
        unit="m"
    )
    
    return model
