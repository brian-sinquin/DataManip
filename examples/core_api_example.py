"""
Simple example demonstrating DataManip core API.

Shows how to:
- Create DataObjects
- Use FormulaEngine
- Build a DataTableStudy
- Perform calculations
"""

import pandas as pd
from core.data_object import DataObject
from core.formula_engine import FormulaEngine
from studies.data_table_study import DataTableStudy, ColumnType


def main():
    """Run example."""
    
    print("=" * 60)
    print("DataManip Core API Example")
    print("=" * 60)
    print()
    
    # ========================================================================
    # Example 1: DataObject basics
    # ========================================================================
    print("1. DataObject Basics")
    print("-" * 60)
    
    # Create from dictionary
    obj = DataObject.from_dict(
        "measurements",
        {"time": [0, 1, 2, 3, 4], "position": [0, 2, 8, 18, 32]},
        unit_time="s",
        unit_position="m"
    )
    
    print(f"Created: {obj}")
    print(f"Columns: {obj.columns}")
    print(f"Shape: {obj.shape}")
    print()
    print("Data:")
    print(obj.data)
    print()
    
    # ========================================================================
    # Example 2: FormulaEngine
    # ========================================================================
    print("2. FormulaEngine Evaluation")
    print("-" * 60)
    
    engine = FormulaEngine()
    
    # Scalar formula
    result = engine.evaluate("{a} + {b}", {"a": 5, "b": 10})
    print(f"Scalar: {{a}} + {{b}} = {result}")
    
    # Array formula
    result = engine.evaluate(
        "{x} ** 2",
        {"x": pd.Series([1, 2, 3, 4, 5])}
    )
    print(f"Array: {{x}} ** 2 = {result.tolist()}")
    
    # Mixed scalar and array
    result = engine.evaluate(
        "{x} * {c}",
        {"x": pd.Series([1, 2, 3]), "c": 10}
    )
    print(f"Mixed: {{x}} * {{c}} = {result.tolist()}")
    print()
    
    # ========================================================================
    # Example 3: Dependency tracking
    # ========================================================================
    print("3. Formula Dependencies")
    print("-" * 60)
    
    engine = FormulaEngine()
    engine.register_formula("velocity", "{position} / {time}")
    engine.register_formula("acceleration", "{velocity} / {time}")
    engine.register_formula("energy", "0.5 * {mass} * {velocity} ** 2")
    
    print("Registered formulas:")
    print("  velocity = {position} / {time}")
    print("  acceleration = {velocity} / {time}")
    print("  energy = 0.5 * {mass} * {velocity} ** 2")
    print()
    
    # Get calculation order when 'position' changes
    order = engine.get_calculation_order(["position"])
    print(f"If 'position' changes, recalculate in order: {order}")
    print()
    
    # ========================================================================
    # Example 4: DataTableStudy
    # ========================================================================
    print("4. DataTableStudy - Free Fall Example")
    print("-" * 60)
    
    # Create study
    study = DataTableStudy("Free Fall")
    
    # Add data columns
    study.add_column("t", unit="s")
    study.add_column("h", unit="m")
    
    # Add calculated column
    study.add_column(
        "v",
        column_type=ColumnType.CALCULATED,
        formula="{h} * 2",  # Simpler formula first
        unit="m"
    )
    
    # Add rows
    study.add_rows(5)
    
    # Set data
    for i in range(5):
        study.table.data.iloc[i, 0] = i  # time
        study.table.data.iloc[i, 1] = 4.905 * i * i  # height = 0.5 * g * t^2
    
    # Trigger recalculation
    study.on_data_changed("h")
    
    print("Columns:")
    print(f"  t [{study.get_column_unit('t')}] - {study.get_column_type('t')}")
    print(f"  h [{study.get_column_unit('h')}] - {study.get_column_type('h')}")
    print(f"  v [{study.get_column_unit('v')}] - {study.get_column_type('v')}")
    print(f"     Formula: {study.get_column_formula('v')}")
    print()
    
    print("Data:")
    print(study.table.data)
    print()
    
    # ========================================================================
    # Example 5: Variables
    # ========================================================================
    print("5. Variables and Constants")
    print("-" * 60)
    
    # Add variable
    study.add_variable("g", 9.81, "m/s^2")
    
    # Update formula to use variable
    study.column_metadata["v"]["formula"] = "{g} * {h}"
    study.formula_engine.register_formula("v", study.column_metadata["v"]["formula"])
    
    print(f"Added variable: g = {study.get_variable('g')}")
    print(f"Updated formula: v = {study.get_column_formula('v')}")
    print()
    
    # Recalculate with new formula
    study.recalculate_all()
    
    print("Recalculated data:")
    print(study.table.data)
    print()
    
    print("=" * 60)
    print("Example complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
