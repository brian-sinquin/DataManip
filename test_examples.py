"""Test script to verify all physics examples load correctly."""

import sys
from PySide6.QtWidgets import QApplication
from widgets import DataTableWidget
from utils.example_data import get_example_names, load_example

def test_examples():
    """Test loading all available examples."""
    app = QApplication(sys.argv)
    
    # Create a DataTableWidget
    table = DataTableWidget()
    
    # Get all example names
    examples = get_example_names()
    print(f"\nTesting {len(examples)} physics examples:")
    print("=" * 70)
    
    results = []
    for example_name in examples:
        print(f"\nTesting: {example_name}")
        print("-" * 70)
        
        try:
            success = load_example(table, example_name)
            if success:
                model = table.model()
                num_cols = len(model.get_column_names())
                num_rows = model.rowCount()
                num_vars = len(model.get_variables())
                
                print(f"✓ SUCCESS")
                print(f"  Columns: {num_cols}")
                print(f"  Rows: {num_rows}")
                print(f"  Variables: {num_vars}")
                print(f"  Column names: {', '.join(model.get_column_names())}")
                
                results.append((example_name, True, num_cols, num_rows, num_vars))
            else:
                print(f"✗ FAILED: load_example returned False")
                results.append((example_name, False, 0, 0, 0))
                
        except Exception as e:
            print(f"✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append((example_name, False, 0, 0, 0))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    success_count = sum(1 for r in results if r[1])
    print(f"Total examples: {len(examples)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(examples) - success_count}")
    
    print("\nDetails:")
    for name, success, cols, rows, vars_count in results:
        status = "✓" if success else "✗"
        print(f"  {status} {name:30s} - {cols:2d} cols, {rows:3d} rows, {vars_count} vars")
    
    return success_count == len(examples)

if __name__ == "__main__":
    success = test_examples()
    sys.exit(0 if success else 1)
