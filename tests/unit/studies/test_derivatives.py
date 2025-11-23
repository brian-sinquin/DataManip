"""
Tests for derivative column functionality in DataTableStudy.
"""

import numpy as np
import pytest

from studies.data_table_study import DataTableStudy, ColumnType


class TestDerivativeColumns:
    """Test derivative column calculations."""
    
    def test_first_derivative_linear(self):
        """Test first derivative of linear function."""
        study = DataTableStudy("test")
        
        # Create x and y = 2x + 3
        x_data = np.linspace(0, 10, 11)
        y_data = 2 * x_data + 3
        
        study.add_column("x", ColumnType.DATA, initial_data=x_data)
        study.add_column("y", ColumnType.DATA, initial_data=y_data)
        study.add_column(
            "dy_dx",
            ColumnType.DERIVATIVE,
            derivative_of="y",
            with_respect_to="x",
            order=1
        )
        
        # Check derivative is approximately 2
        dy_dx = study.table.get_column("dy_dx").values
        assert np.allclose(dy_dx, 2.0, atol=0.01)
    
    def test_first_derivative_quadratic(self):
        """Test first derivative of quadratic function."""
        study = DataTableStudy("test")
        
        # Create x and y = x^2
        x_data = np.linspace(0, 10, 101)
        y_data = x_data ** 2
        
        study.add_column("x", ColumnType.DATA, initial_data=x_data)
        study.add_column("y", ColumnType.DATA, initial_data=y_data)
        study.add_column(
            "dy_dx",
            ColumnType.DERIVATIVE,
            derivative_of="y",
            with_respect_to="x",
            order=1
        )
        
        # Check derivative is approximately 2x (skip edge points)
        dy_dx = study.table.get_column("dy_dx").values
        expected = 2 * x_data
        # np.gradient has edge effects, check middle 80% of points
        mid_start, mid_end = 10, 90
        assert np.allclose(dy_dx[mid_start:mid_end], expected[mid_start:mid_end], rtol=0.02)
    
    def test_second_derivative(self):
        """Test second derivative."""
        study = DataTableStudy("test")
        
        # Create x and y = x^2
        x_data = np.linspace(0, 10, 101)
        y_data = x_data ** 2
        
        study.add_column("x", ColumnType.DATA, initial_data=x_data)
        study.add_column("y", ColumnType.DATA, initial_data=y_data)
        study.add_column(
            "d2y_dx2",
            ColumnType.DERIVATIVE,
            derivative_of="y",
            with_respect_to="x",
            order=2
        )
        
        # Check second derivative is approximately 2 (skip edges)
        d2y_dx2 = study.table.get_column("d2y_dx2").values
        # Check middle points only
        assert np.allclose(d2y_dx2[10:-10], 2.0, atol=0.05)
    
    def test_derivative_of_sine(self):
        """Test derivative of sine function."""
        study = DataTableStudy("test")
        
        # Create x and y = sin(x)
        x_data = np.linspace(0, 2*np.pi, 201)
        y_data = np.sin(x_data)
        
        study.add_column("x", ColumnType.DATA, initial_data=x_data)
        study.add_column("y", ColumnType.DATA, initial_data=y_data)
        study.add_column(
            "dy_dx",
            ColumnType.DERIVATIVE,
            derivative_of="y",
            with_respect_to="x",
            order=1
        )
        
        # Check derivative is approximately cos(x)
        dy_dx = study.table.get_column("dy_dx").values
        expected = np.cos(x_data)
        assert np.allclose(dy_dx, expected, atol=0.05)
    
    def test_derivative_recalculates_on_data_change(self):
        """Test that derivative updates when source data changes."""
        study = DataTableStudy("test")
        
        # Initial data
        x_data = np.linspace(0, 10, 11)
        y_data = 2 * x_data
        
        study.add_column("x", ColumnType.DATA, initial_data=x_data)
        study.add_column("y", ColumnType.DATA, initial_data=y_data)
        study.add_column(
            "dy_dx",
            ColumnType.DERIVATIVE,
            derivative_of="y",
            with_respect_to="x",
            order=1
        )
        
        # Change y data
        new_y = 3 * x_data
        study.table.set_column("y", new_y)
        study.recalculate_all()
        
        # Check derivative updated to 3
        dy_dx = study.table.get_column("dy_dx").values
        assert np.allclose(dy_dx, 3.0, atol=0.01)
    
    def test_velocity_from_position(self):
        """Test computing velocity from position (physics example)."""
        study = DataTableStudy("test")
        
        # Constant acceleration: x = 0.5 * a * t^2
        t_data = np.linspace(0, 5, 51)
        a = 9.81  # m/s^2
        x_data = 0.5 * a * t_data ** 2
        
        study.add_column("t", ColumnType.DATA, initial_data=t_data, unit="s")
        study.add_column("x", ColumnType.DATA, initial_data=x_data, unit="m")
        study.add_column(
            "v",
            ColumnType.DERIVATIVE,
            derivative_of="x",
            with_respect_to="t",
            unit="m/s"
        )
        study.add_column(
            "a",
            ColumnType.DERIVATIVE,
            derivative_of="v",
            with_respect_to="t",
            unit="m/s^2"
        )
        
        # Velocity should be v = a * t (skip edge points)
        v = study.table.get_column("v").values
        expected_v = a * t_data
        assert np.allclose(v[5:-5], expected_v[5:-5], rtol=0.02)
        
        # Acceleration should be constant a (skip more edge points)
        accel = study.table.get_column("a").values
        assert np.allclose(accel[10:-10], a, atol=0.2)
