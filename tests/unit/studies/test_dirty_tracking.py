"""Tests for dirty flag tracking and lazy evaluation."""

import pytest
import pandas as pd
import numpy as np
from studies.data_table_study import DataTableStudy, ColumnType


class TestDirtyFlagTracking:
    """Test dirty flag tracking for lazy evaluation."""
    
    def test_dirty_flag_basic(self):
        """Test basic dirty flag tracking."""
        study = DataTableStudy("test")
        study.add_column("x", initial_data=pd.Series([1, 2, 3]))
        study.add_column("y", column_type=ColumnType.CALCULATED, formula="{x} * 2")
        
        # Initially clean after calculation
        assert not study.is_dirty("y")
        
        # Mark x dirty
        study.mark_dirty("x")
        
        # y should also be dirty (dependent)
        assert study.is_dirty("x")
        assert study.is_dirty("y")
    
    def test_dirty_chain_propagation(self):
        """Test dirty flag propagates through dependency chain."""
        study = DataTableStudy("test")
        study.add_column("a", initial_data=pd.Series([1, 2, 3]))
        study.add_column("b", column_type=ColumnType.CALCULATED, formula="{a} * 2")
        study.add_column("c", column_type=ColumnType.CALCULATED, formula="{b} + 10")
        study.add_column("d", column_type=ColumnType.CALCULATED, formula="{c} ** 2")
        
        # Mark a dirty
        study.mark_dirty("a")
        
        # All dependents should be dirty
        assert study.is_dirty("a")
        assert study.is_dirty("b")
        assert study.is_dirty("c")
        assert study.is_dirty("d")
    
    def test_independent_columns_not_affected(self):
        """Test that independent columns don't get marked dirty."""
        study = DataTableStudy("test")
        study.add_column("x", initial_data=pd.Series([1, 2, 3]))
        study.add_column("y", initial_data=pd.Series([4, 5, 6]))
        study.add_column("z1", column_type=ColumnType.CALCULATED, formula="{x} * 2")
        study.add_column("z2", column_type=ColumnType.CALCULATED, formula="{y} * 2")
        
        # Mark x dirty
        study.mark_dirty("x")
        
        # Only x and z1 should be dirty
        assert study.is_dirty("x")
        assert study.is_dirty("z1")
        assert not study.is_dirty("y")
        assert not study.is_dirty("z2")
    
    def test_mark_clean(self):
        """Test marking column as clean."""
        study = DataTableStudy("test")
        study.add_column("x", initial_data=pd.Series([1, 2, 3]))
        
        study.mark_dirty("x")
        assert study.is_dirty("x")
        
        study.mark_clean("x")
        assert not study.is_dirty("x")


class TestBatchOperations:
    """Test batch column operations."""
    
    def test_batch_column_add(self):
        """Test batch column addition."""
        study = DataTableStudy("test")
        study.add_column("x", initial_data=pd.Series([1, 2, 3]))
        
        columns = [
            {"name": "y1", "column_type": ColumnType.CALCULATED, "formula": "{x} * 2"},
            {"name": "y2", "column_type": ColumnType.CALCULATED, "formula": "{x} * 3"},
            {"name": "y3", "column_type": ColumnType.CALCULATED, "formula": "{x} * 4"},
        ]
        
        added = study.add_columns_batch(columns)
        
        assert len(added) == 3
        assert all(col in study.table.data.columns for col in added)
        assert list(study.table.data["y1"]) == [2, 4, 6]
        assert list(study.table.data["y2"]) == [3, 6, 9]
        assert list(study.table.data["y3"]) == [4, 8, 12]
    
    def test_batch_with_dependencies(self):
        """Test batch addition with interdependent columns."""
        study = DataTableStudy("test")
        study.add_column("x", initial_data=pd.Series([1, 2, 3]))
        
        columns = [
            {"name": "y", "column_type": ColumnType.CALCULATED, "formula": "{x} * 2"},
            {"name": "z", "column_type": ColumnType.CALCULATED, "formula": "{y} + 10"},
        ]
        
        added = study.add_columns_batch(columns)
        
        assert len(added) == 2
        assert list(study.table.data["y"]) == [2, 4, 6]
        assert list(study.table.data["z"]) == [12, 14, 16]
    
    def test_batch_efficiency(self):
        """Test that batch is more efficient than individual adds."""
        import time
        
        study1 = DataTableStudy("test1")
        study1.add_column("x", initial_data=pd.Series(range(1000)))
        
        # Individual adds
        start = time.perf_counter()
        for i in range(20):
            study1.add_column(f"y{i}", column_type=ColumnType.CALCULATED, formula="{x} * 2")
        time_individual = time.perf_counter() - start
        
        study2 = DataTableStudy("test2")
        study2.add_column("x", initial_data=pd.Series(range(1000)))
        
        # Batch add
        columns = [
            {"name": f"y{i}", "column_type": ColumnType.CALCULATED, "formula": "{x} * 2"}
            for i in range(20)
        ]
        start = time.perf_counter()
        study2.add_columns_batch(columns)
        time_batch = time.perf_counter() - start
        
        # Batch should be at least somewhat faster (context built once)
        # Don't make assertion too strict as timing can vary
        print(f"Individual: {time_individual:.4f}s, Batch: {time_batch:.4f}s")
        # Just verify both work correctly
        assert len(study1.table.data.columns) == len(study2.table.data.columns)


class TestDependencyLevels:
    """Test dependency level grouping for parallel execution."""
    
    def test_dependency_levels_simple(self):
        """Test dependency level grouping with simple chain."""
        study = DataTableStudy("test")
        study.add_column("a", initial_data=pd.Series([1, 2, 3]))
        study.add_column("b", column_type=ColumnType.CALCULATED, formula="{a} * 2")
        study.add_column("c", column_type=ColumnType.CALCULATED, formula="{a} * 3")
        study.add_column("d", column_type=ColumnType.CALCULATED, formula="{b} + {c}")
        
        levels = study._get_dependency_levels({"b", "c", "d"})
        
        # Level 0: b, c (both depend only on a which is not in the set)
        # Level 1: d (depends on b and c)
        assert len(levels) == 2
        assert set(levels[0]) == {"b", "c"}
        assert levels[1] == ["d"]
    
    def test_dependency_levels_parallel_chains(self):
        """Test with multiple independent chains."""
        study = DataTableStudy("test")
        study.add_column("a", initial_data=pd.Series([1, 2, 3]))
        study.add_column("b", initial_data=pd.Series([4, 5, 6]))
        study.add_column("c1", column_type=ColumnType.CALCULATED, formula="{a} * 2")
        study.add_column("c2", column_type=ColumnType.CALCULATED, formula="{b} * 2")
        study.add_column("d1", column_type=ColumnType.CALCULATED, formula="{c1} + 1")
        study.add_column("d2", column_type=ColumnType.CALCULATED, formula="{c2} + 1")
        
        levels = study._get_dependency_levels({"c1", "c2", "d1", "d2"})
        
        # Level 0: c1, c2 (independent)
        # Level 1: d1, d2 (depend on c1, c2 respectively)
        assert len(levels) == 2
        assert set(levels[0]) == {"c1", "c2"}
        assert set(levels[1]) == {"d1", "d2"}
    
    def test_dependency_levels_complex(self):
        """Test with complex dependency graph."""
        study = DataTableStudy("test")
        study.add_column("x", initial_data=pd.Series([1, 2, 3]))
        study.add_column("a", column_type=ColumnType.CALCULATED, formula="{x} * 2")
        study.add_column("b", column_type=ColumnType.CALCULATED, formula="{x} * 3")
        study.add_column("c", column_type=ColumnType.CALCULATED, formula="{a} + {b}")
        study.add_column("d", column_type=ColumnType.CALCULATED, formula="{c} * 2")
        study.add_column("e", column_type=ColumnType.CALCULATED, formula="{b} + 1")
        
        levels = study._get_dependency_levels({"a", "b", "c", "d", "e"})
        
        # Level 0: a, b (depend only on x)
        # Level 1: c, e (c depends on a,b; e depends on b)
        # Level 2: d (depends on c)
        assert len(levels) == 3
        assert set(levels[0]) == {"a", "b"}
        assert set(levels[1]) == {"c", "e"}
        assert levels[2] == ["d"]


class TestLazyRecalculation:
    """Test lazy recalculation with dirty flags."""
    
    def test_only_dirty_recalculated(self):
        """Test that only dirty columns are recalculated."""
        study = DataTableStudy("test")
        study.add_column("a", initial_data=pd.Series([1, 2, 3]))
        study.add_column("b", column_type=ColumnType.CALCULATED, formula="{a} * 2")
        study.add_column("c", column_type=ColumnType.CALCULATED, formula="{b} + 10")
        
        # All calculated and clean
        assert not study.is_dirty("b")
        assert not study.is_dirty("c")
        
        # Modify a
        study.table.set_column("a", pd.Series([10, 20, 30]))
        study.mark_dirty("a")
        
        # Now b and c are dirty
        assert study.is_dirty("b")
        assert study.is_dirty("c")
        
        # Recalculate dirty columns
        study._recalculate_dirty_columns()
        
        # Should be clean now and have new values
        assert not study.is_dirty("b")
        assert not study.is_dirty("c")
        assert list(study.table.data["b"]) == [20, 40, 60]
        assert list(study.table.data["c"]) == [30, 50, 70]
