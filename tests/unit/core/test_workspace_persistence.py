"""
Unit tests for workspace save/load functionality.

Tests JSON serialization/deserialization of workspaces with:
- Multiple studies (DataTable, Plot)
- Constants and calculated variables
- Formulas and metadata
- Numpy/pandas data types
"""

import pytest
import json
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np

from core.workspace import Workspace
from studies.data_table_study import DataTableStudy, ColumnType


class TestWorkspacePersistence:
    """Test workspace save/load operations."""
    
    def test_empty_workspace_roundtrip(self):
        """Empty workspace should save and load correctly."""
        ws1 = Workspace("Empty", "numerical")
        
        # Save and load
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dmw', delete=False) as f:
            json.dump(ws1.to_dict(), f)
            tmp = f.name
        
        try:
            with open(tmp, 'r') as f:
                data = json.load(f)
            ws2 = Workspace.from_dict(data)
            
            assert ws2.name == "Empty"
            assert ws2.workspace_type == "numerical"
            assert len(ws2.studies) == 0
            assert len(ws2.constants) == 0
        finally:
            Path(tmp).unlink()
    
    def test_single_study_roundtrip(self):
        """Single study with data should roundtrip correctly."""
        ws1 = Workspace("Test", "numerical")
        study = DataTableStudy("data1", workspace=ws1)
        study.add_rows(3)
        study.add_column("x", ColumnType.DATA, initial_data=pd.Series([1, 2, 3]))
        ws1.add_study(study)
        
        # Save and load
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dmw', delete=False) as f:
            json.dump(ws1.to_dict(), f)
            tmp = f.name
        
        try:
            with open(tmp, 'r') as f:
                data = json.load(f)
            ws2 = Workspace.from_dict(data)
            
            assert len(ws2.studies) == 1
            study2 = ws2.get_study("data1")
            assert study2 is not None
            assert study2.get_type() == "data_table"
            assert list(study2.table.columns) == ["x"]
            assert study2.table.get_column("x").tolist() == [1, 2, 3]
        finally:
            Path(tmp).unlink()
    
    def test_multiple_studies_roundtrip(self):
        """Multiple studies should all be preserved."""
        ws1 = Workspace("Multi", "numerical")
        
        # Add first study
        study1 = DataTableStudy("table1", workspace=ws1)
        study1.add_rows(2)
        study1.add_column("a", ColumnType.DATA, initial_data=pd.Series([10, 20]))
        ws1.add_study(study1)
        
        # Add second study
        study2 = DataTableStudy("table2", workspace=ws1)
        study2.add_rows(3)
        study2.add_column("b", ColumnType.DATA, initial_data=pd.Series([30, 40, 50]))
        ws1.add_study(study2)
        
        # Save and load
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dmw', delete=False) as f:
            json.dump(ws1.to_dict(), f)
            tmp = f.name
        
        try:
            with open(tmp, 'r') as f:
                data = json.load(f)
            ws2 = Workspace.from_dict(data)
            
            assert len(ws2.studies) == 2
            assert "table1" in ws2.studies
            assert "table2" in ws2.studies
            
            # Verify study1
            s1 = ws2.get_study("table1")
            assert s1.table.get_column("a").tolist() == [10, 20]
            
            # Verify study2
            s2 = ws2.get_study("table2")
            assert s2.table.get_column("b").tolist() == [30, 40, 50]
        finally:
            Path(tmp).unlink()
    
    def test_calculated_columns_roundtrip(self):
        """Calculated columns with formulas should be preserved."""
        ws1 = Workspace("Calc", "numerical")
        study = DataTableStudy("calc_study", workspace=ws1)
        study.add_rows(3)
        study.add_column("x", ColumnType.DATA, initial_data=pd.Series([1.0, 2.0, 3.0]))
        study.add_column("y", ColumnType.CALCULATED, formula="x**2", unit="m^2")
        ws1.add_study(study)
        
        # Save and load
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dmw', delete=False) as f:
            json.dump(ws1.to_dict(), f)
            tmp = f.name
        
        try:
            with open(tmp, 'r') as f:
                data = json.load(f)
            ws2 = Workspace.from_dict(data)
            
            study2 = ws2.get_study("calc_study")
            assert "y" in study2.column_metadata
            
            meta = study2.column_metadata["y"]
            assert meta["type"] == ColumnType.CALCULATED
            assert meta["formula"] == "x**2"
            assert meta["unit"] == "m^2"
            
            # Verify calculated values
            assert study2.table.get_column("y").tolist() == [1.0, 4.0, 9.0]
        finally:
            Path(tmp).unlink()
    
    def test_constants_roundtrip(self):
        """Workspace constants should be preserved."""
        ws1 = Workspace("Constants", "numerical")
        ws1.add_constant("g", 9.81, "m/s^2")
        ws1.add_constant("pi", 3.14159, "")
        
        # Save and load
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dmw', delete=False) as f:
            json.dump(ws1.to_dict(), f)
            tmp = f.name
        
        try:
            with open(tmp, 'r') as f:
                data = json.load(f)
            ws2 = Workspace.from_dict(data)
            
            assert len(ws2.constants) == 2
            assert "g" in ws2.constants
            assert "pi" in ws2.constants
            
            g_info = ws2.get_constant_info("g")
            assert g_info["type"] == "constant"
            assert g_info["value"] == 9.81
            assert g_info["unit"] == "m/s^2"
            
            pi_info = ws2.get_constant_info("pi")
            assert pi_info["value"] == 3.14159
        finally:
            Path(tmp).unlink()
    
    def test_numpy_float_roundtrip(self):
        """Numpy floats should serialize correctly via pandas."""
        ws1 = Workspace("NumPy", "numerical")
        study = DataTableStudy("numpy_test", workspace=ws1)
        study.add_rows(3)
        
        # Use numpy arrays directly
        data = np.array([1.5, 2.5, 3.5])
        study.add_column("vals", ColumnType.DATA, initial_data=pd.Series(data))
        ws1.add_study(study)
        
        # Save and load
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dmw', delete=False) as f:
            json.dump(ws1.to_dict(), f)
            tmp = f.name
        
        try:
            with open(tmp, 'r') as f:
                data_loaded = json.load(f)
            ws2 = Workspace.from_dict(data_loaded)
            
            study2 = ws2.get_study("numpy_test")
            vals = study2.table.get_column("vals").tolist()
            
            assert vals == [1.5, 2.5, 3.5]
        finally:
            Path(tmp).unlink()
    
    def test_metadata_preservation(self):
        """Column metadata should be fully preserved."""
        ws1 = Workspace("Meta", "numerical")
        study = DataTableStudy("meta_test", workspace=ws1)
        study.add_rows(2)
        study.add_column("x", ColumnType.DATA, initial_data=pd.Series([10, 20]), unit="kg")
        ws1.add_study(study)
        
        # Save and load
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dmw', delete=False) as f:
            json.dump(ws1.to_dict(), f)
            tmp = f.name
        
        try:
            with open(tmp, 'r') as f:
                data = json.load(f)
            ws2 = Workspace.from_dict(data)
            
            study2 = ws2.get_study("meta_test")
            meta = study2.column_metadata["x"]
            
            assert meta["type"] == ColumnType.DATA
            assert meta["unit"] == "kg"
        finally:
            Path(tmp).unlink()
    
    def test_complex_workspace_roundtrip(self):
        """Complex workspace with multiple features."""
        ws1 = Workspace("Complex", "numerical")
        
        # Add constants
        ws1.add_constant("g", 9.81, "m/s^2")
        
        # Add study with multiple column types
        study = DataTableStudy("physics", workspace=ws1)
        study.add_rows(3)
        study.add_column("t", ColumnType.DATA, initial_data=pd.Series([0.0, 1.0, 2.0]), unit="s")
        study.add_column("v", ColumnType.CALCULATED, formula="g*t", unit="m/s")
        study.add_column("d", ColumnType.CALCULATED, formula="0.5*g*t**2", unit="m")
        ws1.add_study(study)
        
        # Save and load
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dmw', delete=False) as f:
            json.dump(ws1.to_dict(), f)
            tmp = f.name
        
        try:
            with open(tmp, 'r') as f:
                data = json.load(f)
            ws2 = Workspace.from_dict(data)
            
            # Verify constants
            assert ws2.constants["g"]["value"] == 9.81
            
            # Verify study
            study2 = ws2.get_study("physics")
            assert len(study2.table.columns) == 3
            
            # Verify formulas preserved
            assert study2.column_metadata["v"]["formula"] == "g*t"
            assert study2.column_metadata["d"]["formula"] == "0.5*g*t**2"
            
            # Verify units
            assert study2.column_metadata["t"]["unit"] == "s"
            assert study2.column_metadata["v"]["unit"] == "m/s"
            assert study2.column_metadata["d"]["unit"] == "m"
            
            # Verify calculated values
            assert study2.table.get_column("t").tolist() == [0.0, 1.0, 2.0]
            v_vals = study2.table.get_column("v").tolist()
            assert v_vals == pytest.approx([0.0, 9.81, 19.62])
            d_vals = study2.table.get_column("d").tolist()
            assert d_vals == pytest.approx([0.0, 4.905, 19.62])
        finally:
            Path(tmp).unlink()
    
    def test_json_format_validity(self):
        """Saved JSON should be valid and human-readable."""
        ws1 = Workspace("Format", "numerical")
        study = DataTableStudy("test", workspace=ws1)
        study.add_rows(1)
        study.add_column("x", ColumnType.DATA, initial_data=pd.Series([42]))
        ws1.add_study(study)
        
        # Save to string
        data = ws1.to_dict()
        json_str = json.dumps(data, indent=2)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["name"] == "Format"
        assert "studies" in parsed
        assert "constants" in parsed
        
        # Should have proper structure
        assert "test" in parsed["studies"]
        assert parsed["studies"]["test"]["type"] == "data_table"
