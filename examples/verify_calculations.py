"""Verify that examples load with correct calculated values."""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.workspace import Workspace


def verify_05_custom_functions():
    """Verify example 05 has correct sine wave values."""
    filepath = Path(__file__).parent / "05_custom_functions.dmw"
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    workspace = Workspace.from_dict(data)
    study = workspace.get_study("Signal Analysis")
    
    # Debug: Check if constants are loaded
    print("Example 05 - Custom Functions")
    print("-" * 60)
    print(f"Workspace constants: {list(workspace.constants.keys())}")
    print(f"Constants values:")
    for name, const_data in workspace.constants.items():
        print(f"  {name}: {const_data}")
    
    # Debug: Try manual formula evaluation
    print(f"\nTrying manual formula evaluation...")
    try:
        formula = study.column_metadata["s1"]["formula"]
        print(f"Formula: {formula}")
        
        # Build context
        context = {}
        for col_name in study.table.columns:
            context[col_name] = study.table.get_column(col_name).values
        
        # Add workspace constants
        context = study.formula_engine.build_context_with_workspace(
            context, workspace.constants, id(workspace), workspace._version
        )
        
        print(f"Context keys: {list(context.keys())}")
        print(f"  f1 = {context.get('f1')}")
        print(f"  A1 = {context.get('A1')}")
        print(f"  sine_wave = {context.get('sine_wave')}")
        
        result = study.formula_engine.evaluate(formula, context)
        print(f"Manual evaluation result (first 5): {result[:5]}")
    except Exception as e:
        print(f"Manual evaluation failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Get sine wave column
    s1_data = study.table.get_column("s1").values
    
    print(f"\nFirst 5 s1 values from table: {s1_data[:5]}")
    print(f"Expected: sine wave with A=1, f=5Hz")
    print(f"Values should oscillate between -1 and 1")
    
    # Check if values are reasonable (not all near-zero)
    import numpy as np
    max_val = np.max(np.abs(s1_data))
    print(f"Max absolute value: {max_val}")
    
    if max_val > 0.5:
        print("✓ Sine wave values look correct!")
        return True
    else:
        print("✗ Sine wave values are too small (near zero)")
        return False


def verify_04_uncertainty():
    """Verify example 04 has calculated uncertainties."""
    filepath = Path(__file__).parent / "04_uncertainty_propagation.dmw"
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    workspace = Workspace.from_dict(data)
    study = workspace.get_study("Ohm's Law")
    
    print("\nExample 04 - Uncertainty Propagation")
    print("-" * 60)
    
    # Get uncertainty columns
    dV_data = study.table.get_column("dV").values
    dP_data = study.table.get_column("dP").values
    
    import numpy as np
    
    # Check if values are calculated (not None)
    dV_valid = not any(v is None or (isinstance(v, float) and np.isnan(v)) for v in dV_data)
    dP_valid = not any(v is None or (isinstance(v, float) and np.isnan(v)) for v in dP_data)
    
    if dV_valid and dP_valid:
        print(f"First 3 dV values: {dV_data[:3]}")
        print(f"First 3 dP values: {dP_data[:3]}")
        print("✓ Uncertainty values are calculated!")
        return True
    else:
        print("✗ Uncertainty values contain None/NaN")
        return False


if __name__ == "__main__":
    results = []
    
    results.append(verify_05_custom_functions())
    results.append(verify_04_uncertainty())
    
    print("\n" + "=" * 60)
    if all(results):
        print("✓ All verifications passed!")
        sys.exit(0)
    else:
        print("✗ Some verifications failed")
        sys.exit(1)
