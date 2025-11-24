"""
Tests for automatic unit propagation in uncertainty columns.

Tests:
- Unit inheritance from parent columns
- Auto-creation of uncertainty columns
- Enable/disable propagation per column
- Recalculation triggers for uncertainty updates
- Serialization round-trip with units
"""

import pytest
import numpy as np
from core.workspace import Workspace
from studies.data_table_study import DataTableStudy, ColumnType


class TestUnitPropagation:
    """Test automatic unit propagation features."""
    
    def test_uncertainty_column_inherits_unit_from_parent(self):
        """Test that uncertainty columns automatically inherit units from parent columns."""
        workspace = Workspace("Test", "numerical")
        study = DataTableStudy("Test Study", workspace)
        study.add_rows(5)
        
        # Add data column with unit
        study.add_column("voltage", unit="V")
        study.table.set_column("voltage", [1.0, 2.0, 3.0, 4.0, 5.0])
        
        # Add uncertainty column referencing voltage (no explicit unit)
        study.add_column("voltage_u", column_type=ColumnType.UNCERTAINTY, uncertainty_reference="voltage")
        
        # Check that uncertainty column inherited the unit
        assert study.column_metadata["voltage_u"]["unit"] == "V"
    
    def test_uncertainty_column_explicit_unit_overrides_inheritance(self):
        """Test that explicit unit specification overrides auto-inheritance."""
        workspace = Workspace("Test", "numerical")
        study = DataTableStudy("Test Study", workspace)
        study.add_rows(5)
        
        # Add data column with unit
        study.add_column("distance", unit="m")
        study.table.set_column("distance", [10.0, 20.0, 30.0, 40.0, 50.0])
        
        # Add uncertainty column with explicit different unit (override)
        study.add_column("δdistance", column_type=ColumnType.UNCERTAINTY, 
                        uncertainty_reference="distance", unit="cm")
        
        # Check that explicit unit was preserved (not inherited)
        assert study.column_metadata["δdistance"]["unit"] == "cm"
    
    def test_auto_create_uncertainty_column_for_calculated_with_propagation(self):
        """Test that calculated columns auto-create uncertainty columns when propagate_uncertainty=True."""
        workspace = Workspace("Test", "numerical")
        study = DataTableStudy("Test Study", workspace)
        study.add_rows(5)
        
        # Add data columns with uncertainties
        study.add_column("x", unit="m")
        study.table.set_column("x", [1.0, 2.0, 3.0, 4.0, 5.0])
        study.add_column("δx", column_type=ColumnType.UNCERTAINTY, uncertainty_reference="x")
        study.table.set_column("δx", [0.1, 0.1, 0.1, 0.1, 0.1])
        
        study.add_column("y", unit="m")
        study.table.set_column("y", [2.0, 4.0, 6.0, 8.0, 10.0])
        study.add_column("δy", column_type=ColumnType.UNCERTAINTY, uncertainty_reference="y")
        study.table.set_column("δy", [0.2, 0.2, 0.2, 0.2, 0.2])
        
        # Add calculated column with propagate_uncertainty=True
        study.add_column("sum", column_type=ColumnType.CALCULATED, 
                        formula="{x} + {y}", unit="m", propagate_uncertainty=True)
        
        # Check that δsum was auto-created
        assert "sum_u" in study.table.columns
        assert study.column_metadata["sum_u"]["type"] == ColumnType.UNCERTAINTY
        assert study.column_metadata["sum_u"]["uncertainty_reference"] == "sum"
        assert study.column_metadata["sum_u"]["unit"] == "m"  # Inherited from parent
        
        # Check that sum has reference to uncertainty column
        assert study.column_metadata["sum"]["uncertainty"] == "sum_u"
    
    def test_propagate_uncertainty_defaults_to_false(self):
        """Test that propagate_uncertainty defaults to False."""
        workspace = Workspace("Test", "numerical")
        study = DataTableStudy("Test Study", workspace)
        study.add_rows(5)
        
        # Add calculated column without specifying propagate_uncertainty
        study.add_column("x", unit="m")
        study.table.set_column("x", [1.0, 2.0, 3.0, 4.0, 5.0])
        study.add_column("double_x", column_type=ColumnType.CALCULATED, formula="{x} * 2", unit="m")
        
        # Check that no uncertainty column was auto-created
        assert "double_x_u" not in study.table.columns
        assert study.column_metadata["double_x"]["uncertainty"] is None
    
    def test_recalculation_triggers_uncertainty_update(self):
        """Test that recalculating a column automatically updates its uncertainty column."""
        workspace = Workspace("Test", "numerical")
        study = DataTableStudy("Test Study", workspace)
        study.add_rows(5)
        
        # Add data columns
        study.add_column("a", unit="V")
        study.table.set_column("a", [1.0, 2.0, 3.0, 4.0, 5.0])
        study.add_column("δa", column_type=ColumnType.UNCERTAINTY, uncertainty_reference="a")
        study.table.set_column("δa", [0.1, 0.1, 0.1, 0.1, 0.1])
        
        study.add_column("b", unit="V")
        study.table.set_column("b", [2.0, 3.0, 4.0, 5.0, 6.0])
        study.add_column("δb", column_type=ColumnType.UNCERTAINTY, uncertainty_reference="b")
        study.table.set_column("δb", [0.05, 0.05, 0.05, 0.05, 0.05])
        
        # Add calculated column with auto-uncertainty
        study.add_column("product", column_type=ColumnType.CALCULATED,
                        formula="{a} * {b}", unit="V^2", propagate_uncertainty=True)
        
        # Get initial uncertainty values
        initial_uncertainties = study.table.get_column("product_u").tolist()
        
        # Modify input data
        study.table.set_column("a", [2.0, 3.0, 4.0, 5.0, 6.0])
        
        # Recalculate (should trigger uncertainty update)
        study.recalculate_all()
        
        # Get updated uncertainty values
        updated_uncertainties = study.table.get_column("product_u").tolist()
        
        # Uncertainties should have changed
        assert initial_uncertainties != updated_uncertainties
        # Check that values are reasonable (non-zero, non-NaN)
        assert all(u > 0 for u in updated_uncertainties)
    
    def test_uncertainty_column_not_created_if_already_exists(self):
        """Test that auto-creation skips if uncertainty column already exists."""
        workspace = Workspace("Test", "numerical")
        study = DataTableStudy("Test Study", workspace)
        study.add_rows(5)
        
        # Add data column
        study.add_column("temp", unit="K")
        study.table.set_column("temp", [300.0, 310.0, 320.0, 330.0, 340.0])
        
        # Manually create uncertainty column first
        study.add_column("δtemp", column_type=ColumnType.UNCERTAINTY, 
                        uncertainty_reference="temp")
        study.table.set_column("δtemp", [1.0, 1.0, 1.0, 1.0, 1.0])
        
        # Add calculated column with propagate_uncertainty=True
        # This should NOT create a second δtemp column
        study.add_column("temp_squared", column_type=ColumnType.CALCULATED,
                        formula="{temp} ** 2", unit="K^2", propagate_uncertainty=True)
        
        # Should auto-create δtemp_squared but not overwrite existing δtemp
        assert "temp_squared_u" in study.table.columns
        assert study.table.get_column("δtemp").tolist() == [1.0, 1.0, 1.0, 1.0, 1.0]
    
    def test_unit_inheritance_with_missing_parent_column(self):
        """Test that unit inheritance fails gracefully if parent column doesn't exist."""
        workspace = Workspace("Test", "numerical")
        study = DataTableStudy("Test Study", workspace)
        study.add_rows(5)
        
        # Add uncertainty column referencing non-existent parent
        study.add_column("δnonexistent", column_type=ColumnType.UNCERTAINTY,
                        uncertainty_reference="nonexistent")
        
        # Should not crash, unit should be None
        assert study.column_metadata["δnonexistent"]["unit"] is None
    
    def test_unit_propagation_with_complex_formula(self):
        """Test unit propagation with complex multi-variable formula."""
        workspace = Workspace("Test", "numerical")
        study = DataTableStudy("Test Study", workspace)
        study.add_rows(5)
        
        # Add data columns with different units
        study.add_column("mass", unit="kg")
        study.table.set_column("mass", [1.0, 2.0, 3.0, 4.0, 5.0])
        study.add_column("δmass", column_type=ColumnType.UNCERTAINTY, uncertainty_reference="mass")
        study.table.set_column("δmass", [0.01, 0.01, 0.01, 0.01, 0.01])
        
        study.add_column("velocity", unit="m/s")
        study.table.set_column("velocity", [10.0, 20.0, 30.0, 40.0, 50.0])
        study.add_column("δvelocity", column_type=ColumnType.UNCERTAINTY, 
                        uncertainty_reference="velocity")
        study.table.set_column("δvelocity", [0.1, 0.1, 0.1, 0.1, 0.1])
        
        # Add kinetic energy calculation (KE = 0.5 * m * v^2)
        study.add_column("kinetic_energy", column_type=ColumnType.CALCULATED,
                        formula="0.5 * {mass} * {velocity} ** 2",
                        unit="J", propagate_uncertainty=True)
        
        # Check uncertainty column was created with correct unit
        assert "kinetic_energy_u" in study.table.columns
        assert study.column_metadata["kinetic_energy_u"]["unit"] == "J"
        
        # Check that uncertainties were propagated
        uncertainties = study.table.get_column("kinetic_energy_u").tolist()
        assert all(u > 0 for u in uncertainties)
        assert not any(np.isnan(u) for u in uncertainties)
    
    def test_serialization_preserves_unit_propagation_metadata(self):
        """Test that unit propagation metadata survives save/load cycle."""
        workspace = Workspace("Test", "numerical")
        study = DataTableStudy("Test Study", workspace)
        study.add_rows(3)
        
        # Add columns with unit propagation
        study.add_column("current", unit="A")
        study.table.set_column("current", [1.0, 2.0, 3.0])
        study.add_column("resistance", unit="Ω")
        study.table.set_column("resistance", [100.0, 200.0, 300.0])
        study.add_column("δcurrent", column_type=ColumnType.UNCERTAINTY, 
                        uncertainty_reference="current")
        study.table.set_column("δcurrent", [0.01, 0.01, 0.01])
        study.add_column("δresistance", column_type=ColumnType.UNCERTAINTY,
                        uncertainty_reference="resistance")
        study.table.set_column("δresistance", [1.0, 1.0, 1.0])
        
        study.add_column("voltage", column_type=ColumnType.CALCULATED,
                        formula="{current} * {resistance}",
                        unit="V", propagate_uncertainty=True)
        
        # Serialize
        data = study.to_dict()
        
        # Recreate from serialized data
        workspace2 = Workspace("Test2", "numerical")
        study2 = DataTableStudy.from_dict(data, workspace2)
        
        # Check metadata preserved
        assert study2.column_metadata["voltage"]["propagate_uncertainty"] is True
        assert study2.column_metadata["voltage"]["uncertainty"] == "voltage_u"
        assert study2.column_metadata["voltage_u"]["unit"] == "V"
        assert study2.column_metadata["voltage_u"]["uncertainty_reference"] == "voltage"
        
        # Check data preserved
        assert "voltage_u" in study2.table.columns
        assert len(study2.table.get_column("voltage_u")) == 3
    
    def test_disable_propagation_per_column(self):
        """Test that propagate_uncertainty=False disables auto-creation."""
        workspace = Workspace("Test", "numerical")
        study = DataTableStudy("Test Study", workspace)
        study.add_rows(5)
        
        study.add_column("x", unit="m")
        study.table.set_column("x", [1.0, 2.0, 3.0, 4.0, 5.0])
        study.add_column("y", unit="m")
        study.table.set_column("y", [2.0, 4.0, 6.0, 8.0, 10.0])
        
        # Add with propagation enabled
        study.add_column("sum_with_uncert", column_type=ColumnType.CALCULATED,
                        formula="{x} + {y}", unit="m", propagate_uncertainty=True)
        
        # Add with propagation disabled
        study.add_column("sum_no_uncert", column_type=ColumnType.CALCULATED,
                        formula="{x} + {y}", unit="m", propagate_uncertainty=False)
        
        # Check that only the first has uncertainty column
        assert "sum_with_uncert_u" in study.table.columns
        assert "sum_no_uncert_u" not in study.table.columns
    
    def test_uncertainty_column_calculation_with_legacy_suffix(self):
        """Test that uncertainty calculation works with both δ prefix and _u suffix."""
        workspace = Workspace("Test", "numerical")
        study = DataTableStudy("Test Study", workspace)
        study.add_rows(5)
        
        # Add data columns with legacy _u suffix
        study.add_column("x", unit="m")
        study.table.set_column("x", [1.0, 2.0, 3.0, 4.0, 5.0])
        study.add_column("x_u", column_type=ColumnType.UNCERTAINTY, uncertainty_reference="x")
        study.table.set_column("x_u", [0.1, 0.1, 0.1, 0.1, 0.1])
        
        # Add calculated column (will create δdouble_x)
        study.add_column("double_x", column_type=ColumnType.CALCULATED,
                        formula="{x} * 2", unit="m", propagate_uncertainty=True)
        
        # Should successfully propagate using x_u
        uncertainties = study.table.get_column("double_x_u").tolist()
        assert all(u > 0 for u in uncertainties)
        # Uncertainty should be approximately 2 * 0.1 = 0.2 for linear scaling
        assert all(abs(u - 0.2) < 0.01 for u in uncertainties)
