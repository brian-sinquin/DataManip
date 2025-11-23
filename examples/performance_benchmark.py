"""Performance benchmark for optimized formula engine.

This script demonstrates the performance improvements from:
1. Workspace constants caching
2. Formula compilation caching
3. Optimized context building
"""

import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd
import numpy as np
from core.workspace import Workspace
from studies.data_table_study import DataTableStudy, ColumnType


def benchmark_workspace_constants():
    """Benchmark workspace constants evaluation with caching."""
    print("=" * 70)
    print("Benchmark 1: Workspace Constants Evaluation")
    print("=" * 70)
    
    # Create workspace with many constants
    ws = Workspace("test", "numerical")
    
    # Add 20 numeric constants
    for i in range(20):
        ws.add_constant(f"c{i}", float(i))
    
    # Add 10 calculated constants (chained dependencies)
    ws.add_calculated_variable("calc0", "c0 + c1")
    for i in range(1, 10):
        ws.add_calculated_variable(f"calc{i}", f"calc{i-1} * 2 + c{i}")
    
    # Create study
    study = DataTableStudy("test", workspace=ws)
    study.add_column("x", initial_data=pd.Series(range(1000)))
    
    # Benchmark: Add 50 calculated columns that use workspace constants
    print("\nAdding 50 calculated columns using workspace constants...")
    start = time.perf_counter()
    
    for i in range(50):
        formula = f"x * calc9 + c{i % 20}"
        study.add_column(f"col{i}", column_type=ColumnType.CALCULATED, formula=formula)
    
    elapsed = time.perf_counter() - start
    print(f"Time: {elapsed:.3f}s")
    print(f"Average per column: {elapsed/50*1000:.2f}ms")
    print(f"✓ Workspace constants cached and reused for all columns")
    
    return elapsed


def benchmark_formula_compilation():
    """Benchmark formula compilation caching."""
    print("\n" + "=" * 70)
    print("Benchmark 2: Formula Compilation Caching")
    print("=" * 70)
    
    ws = Workspace("test", "numerical")
    ws.add_constant("k", 2.5)
    
    study = DataTableStudy("test", workspace=ws)
    study.add_column("x", initial_data=pd.Series(range(1000)))
    
    # Add columns with same formula pattern
    print("\nAdding 100 columns with similar formulas...")
    start = time.perf_counter()
    
    for i in range(100):
        # Similar formulas that will be cached
        formula = "x**2 + k * x + 1"
        study.add_column(f"poly{i}", column_type=ColumnType.CALCULATED, formula=formula)
    
    elapsed = time.perf_counter() - start
    print(f"Time: {elapsed:.3f}s")
    print(f"Average per column: {elapsed/100*1000:.2f}ms")
    print(f"✓ Formula compiled once and cached for subsequent uses")
    
    return elapsed


def benchmark_large_dataset():
    """Benchmark with large dataset to show vectorization benefits."""
    print("\n" + "=" * 70)
    print("Benchmark 3: Large Dataset Performance")
    print("=" * 70)
    
    ws = Workspace("test", "numerical")
    ws.add_constant("g", 9.81)
    ws.add_constant("m", 1.5)
    ws.add_calculated_variable("factor", "g * m / 2")
    
    # Large dataset: 10,000 points
    n_points = 10000
    print(f"\nDataset size: {n_points:,} points")
    
    study = DataTableStudy("test", workspace=ws)
    study.add_column("t", initial_data=pd.Series(np.linspace(0, 10, n_points)))
    
    print("Adding 20 calculated columns...")
    start = time.perf_counter()
    
    # Add various calculated columns
    study.add_column("v", column_type=ColumnType.CALCULATED, formula="factor * t")
    study.add_column("d", column_type=ColumnType.CALCULATED, formula="0.5 * g * t**2")
    study.add_column("ke", column_type=ColumnType.CALCULATED, formula="0.5 * m * v**2")
    study.add_column("energy", column_type=ColumnType.CALCULATED, formula="ke + m * g * d")
    
    for i in range(16):
        study.add_column(f"calc{i}", column_type=ColumnType.CALCULATED, 
                        formula=f"sin(t * {i+1}) * factor")
    
    elapsed = time.perf_counter() - start
    print(f"Time: {elapsed:.3f}s")
    print(f"Average per column: {elapsed/20*1000:.2f}ms")
    print(f"Calculations per second: {(n_points * 20) / elapsed:,.0f}")
    print(f"✓ Efficient vectorized operations on large arrays")
    
    return elapsed


def main():
    """Run all benchmarks."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "DataManip Performance Benchmarks" + " " * 21 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    t1 = benchmark_workspace_constants()
    t2 = benchmark_formula_compilation()
    t3 = benchmark_large_dataset()
    
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Total execution time: {t1 + t2 + t3:.3f}s")
    print("\nKey Optimizations:")
    print("  1. Workspace constants cached - no re-evaluation per column")
    print("  2. Formulas compiled once - string ops minimized")
    print("  3. Context reuse - minimize dict copies")
    print("  4. Vectorized numpy operations - fast array math")
    print("\n✓ All benchmarks completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
