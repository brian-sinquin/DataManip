"""
Tests for calculated constants in formulas.

Calculated constants are formula-based constants that can reference
other constants and be used in column formulas.
"""

import pytest
import numpy as np
import pandas as pd
from core.workspace import Workspace
from studies.data_table_study import DataTableStudy, ColumnType


class TestCalculatedConstantsInFormulas:
    """Test using calculated constants in column formulas."""
    
    def test_simple_calculated_constant(self):
        """Test calculated constant referencing a numeric constant."""
        # Setup
        workspace = Workspace("test_workspace", "numerical")
        
        # Add constants
        workspace.add_constant("g", 9.81)
        workspace.add_calculated_variable("double_g", "2 * g")
        
        study = DataTableStudy("test_study", workspace=workspace)
        study.add_column("time", initial_data=pd.Series([1.0, 2.0, 3.0]))
        study.add_column("distance", column_type=ColumnType.CALCULATED, formula="0.5 * double_g * time**2")
        
        # Expected: 0.5 * (2*9.81) * t^2 = 9.81 * t^2
        expected = np.array([9.81, 39.24, 88.29])
        result = study.table.get_column("distance").values
        
        np.testing.assert_array_almost_equal(result, expected, decimal=2)
    
    def test_calculated_constant_with_formula(self):
        """Test calculated constant with complex formula."""
        workspace = Workspace("test_workspace", "numerical")
        
        # Add constants
        workspace.add_constant("pi", 3.14159)
        workspace.add_constant("r", 2.0)
        workspace.add_calculated_variable("area", "pi * r**2")
        
        study = DataTableStudy("test_study", workspace=workspace)
        study.add_column("height", initial_data=pd.Series([1.0, 2.0, 3.0]))
        study.add_column("volume", column_type=ColumnType.CALCULATED, formula="area * height")
        
        # Expected: pi * r^2 * h = 3.14159 * 4 * h = 12.56636 * h
        expected = np.array([12.56636, 25.13272, 37.69908])
        result = study.table.get_column("volume").values
        
        np.testing.assert_array_almost_equal(result, expected, decimal=4)
    
    def test_calculated_constant_referencing_calculated(self):
        """Test calculated constant referencing another calculated constant."""
        workspace = Workspace("test_workspace", "numerical")
        
        # Chain of calculated constants
        workspace.add_constant("x", 10.0)
        workspace.add_calculated_variable("y", "x * 2")
        workspace.add_calculated_variable("z", "y + 5")
        
        study = DataTableStudy("test_study", workspace=workspace)
        study.add_column("multiplier", initial_data=pd.Series([1.0, 2.0, 3.0]))
        study.add_column("result", column_type=ColumnType.CALCULATED, formula="z * multiplier")
        
        # Expected: z = (10*2) + 5 = 25, result = 25 * multiplier
        expected = np.array([25.0, 50.0, 75.0])
        result = study.table.get_column("result").values
        
        np.testing.assert_array_almost_equal(result, expected, decimal=1)
    
    def test_calculated_constant_with_custom_function(self):
        """Test calculated constant using a custom function."""
        workspace = Workspace("test_workspace", "numerical")
        
        # Add function and calculated constant
        workspace.add_function("square", "{x}**2", ["x"])
        workspace.add_constant("base", 5.0)
        workspace.add_calculated_variable("squared_base", "square(base)")
        
        study = DataTableStudy("test_study", workspace=workspace)
        study.add_column("factor", initial_data=pd.Series([1.0, 2.0, 3.0]))
        study.add_column("scaled", column_type=ColumnType.CALCULATED, formula="squared_base * factor")
        
        # Expected: squared_base = 5^2 = 25, scaled = 25 * factor
        expected = np.array([25.0, 50.0, 75.0])
        result = study.table.get_column("scaled").values
        
        np.testing.assert_array_almost_equal(result, expected, decimal=1)
    
    def test_calculated_constant_with_numpy_functions(self):
        """Test calculated constant using numpy functions."""
        workspace = Workspace("test_workspace", "numerical")
        
        # Add calculated constant with numpy function
        workspace.add_constant("angle_deg", 90.0)
        workspace.add_calculated_variable("angle_rad", "angle_deg * pi / 180")
        
        study = DataTableStudy("test_study", workspace=workspace)
        study.add_column("amplitude", initial_data=pd.Series([1.0, 2.0, 3.0]))
        study.add_column("y", column_type=ColumnType.CALCULATED, formula="amplitude * sin(angle_rad)")
        
        # Expected: angle_rad = 90 * pi/180 = pi/2, sin(pi/2) = 1.0
        expected = np.array([1.0, 2.0, 3.0])
        result = study.table.get_column("y").values
        
        np.testing.assert_array_almost_equal(result, expected, decimal=4)
