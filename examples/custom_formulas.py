"""
Custom formulas example.

Demonstrates:
- Using mathematical functions in formulas (sin, cos, exp, log)
- Working with physical constants as variables
- Range columns for generating sequences
- Complex formula expressions
"""

import sys
from pathlib import Path
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from studies.data_table_study import DataTableStudy, ColumnType


def main():
    """Demonstrate custom formulas."""
    print("=" * 70)
    print("CUSTOM FORMULAS EXAMPLE")
    print("=" * 70)
    
    # Create study
    study = DataTableStudy("Custom Formulas")
    
    # Set up mathematical and physical constants
    study.add_variable("pi", np.pi)
    study.add_variable("e", np.e)
    study.add_variable("c", 299792458, "m/s")  # Speed of light
    
    print("\nConstants defined:")
    print("  pi = 3.14159...")
    print("  e = 2.71828...")
    print("  c = 299792458 m/s")
    
    # Create range of x values
    print("\n" + "-" * 70)
    print("Creating x range (0 to 10, 21 points)")
    study.add_column(
        "x",
        ColumnType.RANGE,
        range_type="linspace",
        range_start=0.0,
        range_stop=10.0,
        range_count=21
    )
    print("✓ x column created")
    
    # Trigonometric functions
    print("\n" + "-" * 70)
    print("Adding trigonometric functions")
    study.add_column(
        "sin_x",
        ColumnType.CALCULATED,
        formula="sin({x})"
    )
    print("✓ sin_x = sin(x)")
    
    study.add_column(
        "cos_x",
        ColumnType.CALCULATED,
        formula="cos({x})"
    )
    print("✓ cos_x = cos(x)")
    
    # Exponential and logarithmic
    print("\n" + "-" * 70)
    print("Adding exponential and logarithmic functions")
    study.add_column(
        "exp_x",
        ColumnType.CALCULATED,
        formula="{e} ** {x}"
    )
    print("✓ exp_x = e^x")
    
    study.add_column(
        "log_x",
        ColumnType.CALCULATED,
        formula="log({x} + 1)"  # +1 to avoid log(0)
    )
    print("✓ log_x = ln(x+1)")
    
    # Complex expression
    print("\n" + "-" * 70)
    print("Adding complex expression")
    study.add_column(
        "complex",
        ColumnType.CALCULATED,
        formula="sin({x}) * {e}**(-{x}/5) + cos(2*{x})/2"
    )
    print("✓ complex = sin(x)·e^(-x/5) + cos(2x)/2")
    
    # Using constants
    print("\n" + "-" * 70)
    print("Adding circle area formula")
    study.add_column(
        "circle_area",
        ColumnType.CALCULATED,
        formula="{pi} * {x}**2",
        unit="m²"
    )
    print("✓ circle_area = π·x² [m²]")
    
    # Show results
    print("\n" + "=" * 70)
    print("Data sample (first 10 rows):")
    print("=" * 70)
    print(study.table.data[["x", "sin_x", "cos_x", "exp_x", "complex"]].head(10))
    
    print("\n" + "=" * 70)
    print("Example complete!")
    print("=" * 70)
    
    print(f"\nTotal columns: {len(study.table.columns)}")
    print(f"Total rows: {len(study.table.data)}")


if __name__ == "__main__":
    main()
