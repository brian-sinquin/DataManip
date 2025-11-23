"""Test script for lazy evaluation and parallel execution optimizations."""

import time
import numpy as np
import pandas as pd
from src.core.workspace import Workspace
from src.studies.data_table_study import DataTableStudy, ColumnType


def test_batch_operations():
    """Test batch column addition performance."""
    print("=" * 70)
    print("BATCH OPERATIONS TEST")
    print("=" * 70)
    
    # Create workspace and study
    ws = Workspace("test", "numerical")
    study = DataTableStudy("performance", workspace=ws)
    
    # Add base data column
    n_rows = 10000
    study.add_column("x", initial_data=pd.Series(np.linspace(0, 10, n_rows)))
    
    # Test 1: Individual adds (baseline)
    study1 = DataTableStudy("individual", workspace=ws)
    study1.add_column("x", initial_data=pd.Series(np.linspace(0, 10, n_rows)))
    
    start = time.perf_counter()
    for i in range(50):
        study1.add_column(f"y{i}", column_type=ColumnType.CALCULATED, formula="{x} ** 2")
    time_individual = time.perf_counter() - start
    
    # Test 2: Batch add
    study2 = DataTableStudy("batch", workspace=ws)
    study2.add_column("x", initial_data=pd.Series(np.linspace(0, 10, n_rows)))
    
    columns = [
        {"name": f"y{i}", "column_type": ColumnType.CALCULATED, "formula": "{x} ** 2"}
        for i in range(50)
    ]
    
    start = time.perf_counter()
    study2.add_columns_batch(columns)
    time_batch = time.perf_counter() - start
    
    # Verify results are identical
    for i in range(50):
        col1 = study1.table.get_column(f"y{i}")
        col2 = study2.table.get_column(f"y{i}")
        assert np.allclose(col1, col2), f"Column y{i} mismatch"
    
    print(f"Rows: {n_rows:,}")
    print(f"Columns added: 50")
    print(f"\nIndividual adds: {time_individual:.4f}s")
    print(f"Batch add:       {time_batch:.4f}s")
    print(f"Speedup:         {time_individual/time_batch:.2f}x")
    print(f"\n✓ Results verified identical\n")


def test_parallel_execution():
    """Test parallel column evaluation."""
    print("=" * 70)
    print("PARALLEL EXECUTION TEST")
    print("=" * 70)
    
    ws = Workspace("test", "numerical")
    study = DataTableStudy("parallel_test", workspace=ws)
    
    # Add base column
    n_rows = 10000
    study.add_column("x", initial_data=pd.Series(np.linspace(0, 100, n_rows)))
    
    # Add multiple independent calculated columns (can be parallelized)
    columns = [
        {"name": "y1", "column_type": ColumnType.CALCULATED, "formula": "np.sin({x})"},
        {"name": "y2", "column_type": ColumnType.CALCULATED, "formula": "np.cos({x})"},
        {"name": "y3", "column_type": ColumnType.CALCULATED, "formula": "np.tan({x})"},
        {"name": "y4", "column_type": ColumnType.CALCULATED, "formula": "np.exp({x}/100)"},
        {"name": "y5", "column_type": ColumnType.CALCULATED, "formula": "np.log({x}+1)"},
        {"name": "y6", "column_type": ColumnType.CALCULATED, "formula": "{x} ** 2"},
        {"name": "y7", "column_type": ColumnType.CALCULATED, "formula": "{x} ** 3"},
        {"name": "y8", "column_type": ColumnType.CALCULATED, "formula": "np.sqrt({x})"},
    ]
    
    start = time.perf_counter()
    study.add_columns_batch(columns)
    time_parallel = time.perf_counter() - start
    
    print(f"Rows: {n_rows:,}")
    print(f"Independent columns: {len(columns)}")
    print(f"Time: {time_parallel:.4f}s")
    print(f"\n✓ All columns calculated successfully\n")


def test_dependency_levels():
    """Test dependency level grouping and evaluation."""
    print("=" * 70)
    print("DEPENDENCY LEVELS TEST")
    print("=" * 70)
    
    ws = Workspace("test", "numerical")
    study = DataTableStudy("deps", workspace=ws)
    
    # Create dependency chain
    n_rows = 1000
    study.add_column("x", initial_data=pd.Series(np.linspace(0, 10, n_rows)))
    
    # Level 0: a, b (both depend on x)
    # Level 1: c, d (c depends on a,b; d depends on a)
    # Level 2: e (depends on c,d)
    columns = [
        {"name": "a", "column_type": ColumnType.CALCULATED, "formula": "{x} * 2"},
        {"name": "b", "column_type": ColumnType.CALCULATED, "formula": "{x} + 10"},
        {"name": "c", "column_type": ColumnType.CALCULATED, "formula": "{a} + {b}"},
        {"name": "d", "column_type": ColumnType.CALCULATED, "formula": "{a} * 2"},
        {"name": "e", "column_type": ColumnType.CALCULATED, "formula": "{c} + {d}"},
    ]
    
    start = time.perf_counter()
    study.add_columns_batch(columns)
    time_deps = time.perf_counter() - start
    
    # Verify dependency levels
    dirty = {"a", "b", "c", "d", "e"}
    levels = study._get_dependency_levels(dirty)
    
    print(f"Rows: {n_rows:,}")
    print(f"Dependency chain:")
    for i, level in enumerate(levels):
        print(f"  Level {i}: {', '.join(level)}")
    
    print(f"\nTime: {time_deps:.4f}s")
    
    # Verify calculations are correct
    x_vals = study.table.get_column("x").values
    a_expected = x_vals * 2
    b_expected = x_vals + 10
    c_expected = a_expected + b_expected
    d_expected = a_expected * 2
    e_expected = c_expected + d_expected
    
    assert np.allclose(study.table.get_column("a"), a_expected)
    assert np.allclose(study.table.get_column("b"), b_expected)
    assert np.allclose(study.table.get_column("c"), c_expected)
    assert np.allclose(study.table.get_column("d"), d_expected)
    assert np.allclose(study.table.get_column("e"), e_expected)
    
    print(f"✓ All dependency calculations correct\n")


def test_dirty_flag_lazy_evaluation():
    """Test that dirty flags enable lazy evaluation."""
    print("=" * 70)
    print("DIRTY FLAG LAZY EVALUATION TEST")
    print("=" * 70)
    
    ws = Workspace("test", "numerical")
    study = DataTableStudy("lazy", workspace=ws)
    
    # Setup columns
    study.add_column("x", initial_data=pd.Series([1, 2, 3, 4, 5]))
    study.add_column("y", column_type=ColumnType.CALCULATED, formula="{x} * 2")
    study.add_column("z", column_type=ColumnType.CALCULATED, formula="{y} + 10")
    
    # All should be clean
    assert not study.is_dirty("x")
    assert not study.is_dirty("y")
    assert not study.is_dirty("z")
    print("✓ Initially all columns clean")
    
    # Modify x
    study.table.set_column("x", pd.Series([10, 20, 30, 40, 50]))
    study.mark_dirty("x")
    
    # x, y, z should all be dirty now
    assert study.is_dirty("x")
    assert study.is_dirty("y")
    assert study.is_dirty("z")
    print("✓ Dirty flag propagated through dependency chain")
    
    # Recalculate
    study._recalculate_dirty_columns()
    
    # y and z should be clean after recalculation (x stays dirty since it's DATA)
    assert study.is_dirty("x")  # DATA column stays dirty
    assert not study.is_dirty("y")
    assert not study.is_dirty("z")
    print("✓ Calculated columns clean after recalculation")
    
    # Verify values
    y_vals = study.table.get_column("y")
    z_vals = study.table.get_column("z")
    assert list(y_vals) == [20, 40, 60, 80, 100]
    assert list(z_vals) == [30, 50, 70, 90, 110]
    print("✓ Recalculated values correct\n")


def test_overall_performance():
    """Test overall calculation performance."""
    print("=" * 70)
    print("OVERALL PERFORMANCE TEST")
    print("=" * 70)
    
    ws = Workspace("perf", "numerical")
    ws.add_constant("g", 9.81, "m/s^2")
    ws.add_constant("pi", 3.14159, "rad")
    
    study = DataTableStudy("performance", workspace=ws)
    
    # Large dataset
    n_rows = 50000
    study.add_column("t", initial_data=pd.Series(np.linspace(0, 10, n_rows)))
    
    # Add many calculated columns
    columns = [
        {"name": "x", "column_type": ColumnType.CALCULATED, "formula": "{t} ** 2"},
        {"name": "v", "column_type": ColumnType.CALCULATED, "formula": "2 * {t}"},
        {"name": "a", "column_type": ColumnType.CALCULATED, "formula": "2"},
        {"name": "sin_t", "column_type": ColumnType.CALCULATED, "formula": "np.sin({t})"},
        {"name": "cos_t", "column_type": ColumnType.CALCULATED, "formula": "np.cos({t})"},
        {"name": "energy", "column_type": ColumnType.CALCULATED, "formula": "0.5 * {g} * {t} ** 2"},
        {"name": "complex", "column_type": ColumnType.CALCULATED, "formula": "np.sqrt({x}) * {sin_t} + {cos_t}"},
    ]
    
    start = time.perf_counter()
    study.add_columns_batch(columns)
    total_time = time.perf_counter() - start
    
    total_calcs = n_rows * len(columns)
    calcs_per_sec = total_calcs / total_time
    
    print(f"Rows: {n_rows:,}")
    print(f"Columns: {len(columns)}")
    print(f"Total calculations: {total_calcs:,}")
    print(f"Time: {total_time:.4f}s")
    print(f"Throughput: {calcs_per_sec:,.0f} calculations/second")
    print(f"             {calcs_per_sec/1e6:.2f}M calc/sec\n")


if __name__ == "__main__":
    test_batch_operations()
    test_parallel_execution()
    test_dependency_levels()
    test_dirty_flag_lazy_evaluation()
    test_overall_performance()
    
    print("=" * 70)
    print("ALL TESTS PASSED ✓")
    print("=" * 70)
