"""
Unit tests for custom functions in calculated columns.
"""

import pytest
import numpy as np
from studies.data_table_study import DataTableStudy, ColumnType
from core.workspace import Workspace


class TestCustomFunctions:
    """Test custom function usage in calculated columns."""
    
    def test_simple_function_in_formula(self):
        """Test using a simple custom function in a calculated column."""
        workspace = Workspace("Test", "general")
        
        # Add custom function: square(x) = x^2
        workspace.add_function("square", "{x}**2", ["x"])
        
        # Create data table study
        study = DataTableStudy("Data", workspace=workspace)
        workspace.add_study(study)
        
        # Add data column
        study.add_column("x", initial_data=np.array([1.0, 2.0, 3.0, 4.0, 5.0]))
        
        # Add calculated column using custom function
        study.add_column("y", ColumnType.CALCULATED, formula="square({x})")
        
        # Verify results
        y_values = study.table.data["y"].values
        expected = np.array([1.0, 4.0, 9.0, 16.0, 25.0])
        np.testing.assert_array_almost_equal(y_values, expected)
    
    def test_function_with_multiple_parameters(self):
        """Test using a custom function with multiple parameters."""
        workspace = Workspace("Test", "general")
        
        # Add custom function: distance(x, y) = sqrt(x^2 + y^2)
        workspace.add_function("distance", "sqrt({x}**2 + {y}**2)", ["x", "y"])
        
        study = DataTableStudy("Data", workspace=workspace)
        workspace.add_study(study)
        
        # Add data columns
        study.add_column("a", initial_data=np.array([3.0, 5.0, 8.0]))
        study.add_column("b", initial_data=np.array([4.0, 12.0, 15.0]))
        
        # Use custom function
        study.add_column("d", ColumnType.CALCULATED, formula="distance({a}, {b})")
        
        # Verify results
        d_values = study.table.data["d"].values
        expected = np.array([5.0, 13.0, 17.0])
        np.testing.assert_array_almost_equal(d_values, expected)
    
    def test_function_with_constants(self):
        """Test custom function with constants."""
        workspace = Workspace("Test", "general")
        
        # Add constant
        workspace.add_constant("g", 9.81, "m/s^2")
        
        # Add custom function: kinetic_energy(m, v) = 0.5 * m * v^2
        workspace.add_function("kinetic_energy", "0.5 * {m} * {v}**2", ["m", "v"])
        
        study = DataTableStudy("Data", workspace=workspace)
        workspace.add_study(study)
        
        # Add data
        study.add_column("mass", initial_data=np.array([1.0, 2.0, 3.0]))
        study.add_column("velocity", initial_data=np.array([10.0, 20.0, 30.0]))
        
        # Use custom function
        study.add_column("KE", ColumnType.CALCULATED, formula="kinetic_energy({mass}, {velocity})")
        
        # Verify
        ke_values = study.table.data["KE"].values
        expected = 0.5 * np.array([1.0, 2.0, 3.0]) * np.array([10.0, 20.0, 30.0])**2
        np.testing.assert_array_almost_equal(ke_values, expected)
    
    def test_nested_function_calls(self):
        """Test using custom function as parameter to another function."""
        workspace = Workspace("Test", "general")
        
        # Add functions
        workspace.add_function("double", "{x} * 2", ["x"])
        workspace.add_function("triple", "{x} * 3", ["x"])
        
        study = DataTableStudy("Data", workspace=workspace)
        workspace.add_study(study)
        
        study.add_column("x", initial_data=np.array([1.0, 2.0, 3.0]))
        
        # Use nested function calls
        study.add_column("y", ColumnType.CALCULATED, formula="double({x}) + triple({x})")
        
        # Verify: double(x) + triple(x) = 2x + 3x = 5x
        y_values = study.table.data["y"].values
        expected = np.array([5.0, 10.0, 15.0])
        np.testing.assert_array_almost_equal(y_values, expected)
    
    def test_function_with_numpy_functions(self):
        """Test custom function using numpy functions."""
        workspace = Workspace("Test", "general")
        
        # Add function using numpy
        workspace.add_function("magnitude", "sqrt({x}**2 + {y}**2 + {z}**2)", ["x", "y", "z"])
        
        study = DataTableStudy("Data", workspace=workspace)
        workspace.add_study(study)
        
        study.add_column("x", initial_data=np.array([1.0, 2.0, 3.0]))
        study.add_column("y", initial_data=np.array([2.0, 3.0, 4.0]))
        study.add_column("z", initial_data=np.array([3.0, 4.0, 5.0]))
        
        study.add_column("mag", ColumnType.CALCULATED, formula="magnitude({x}, {y}, {z})")
        
        # Verify
        mag_values = study.table.data["mag"].values
        expected = np.sqrt(np.array([1.0, 2.0, 3.0])**2 + 
                          np.array([2.0, 3.0, 4.0])**2 + 
                          np.array([3.0, 4.0, 5.0])**2)
        np.testing.assert_array_almost_equal(mag_values, expected)
