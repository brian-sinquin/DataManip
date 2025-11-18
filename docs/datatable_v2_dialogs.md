# DataTableV2 Dialog System

## Overview

The DataTableV2 dialog system provides user-friendly interfaces for creating and configuring different column types. The dialogs offer validation, preview, helpful guidance, and a polished user experience.

## Features

### Common Features Across All Dialogs

- ✅ **Name validation** - Prevents duplicates and invalid characters
- ✅ **Live preview** - Shows how the column will appear
- ✅ **Helpful tooltips** - Explains each field and option
- ✅ **Error messages** - Clear feedback when input is invalid
- ✅ **OK button state** - Only enabled when all required fields are valid
- ✅ **Cancel support** - Can back out without making changes

## Dialog Types

### 1. AddDataColumnDialog

Creates a new data column for entering measured or input values.

**Fields:**
- **Name*** (required) - Column identifier used in formulas and display
- **Data Type*** (required) - FLOAT, INTEGER, STRING, CATEGORY, or BOOLEAN
- **Unit** - Unit of measurement (for numeric types only)
- **Description** - Tooltip text shown on column header
- **Precision** - Number of decimal places (for FLOAT only)
- **Create Uncertainty** - Option to create associated uncertainty column (name_u)

**Validation:**
- Name must be unique
- Name can only contain letters, numbers, _, -
- Unit and precision only shown for numeric types

**Example Usage:**
```python
from widgets.DataTableV2.dialogs import AddDataColumnDialog

dialog = AddDataColumnDialog(
    parent=main_window,
    existing_names=model.get_column_names()
)

if dialog.exec():
    results = dialog.get_results()
    model.add_data_column(
        name=results['name'],
        dtype=results['dtype'],
        unit=results['unit'],
        description=results['description'],
        precision=results['precision']
    )
    
    # Create uncertainty column if requested
    if results['create_uncertainty']:
        model.add_data_column(
            name=f"{results['name']}_u",
            dtype=results['dtype'],
            unit=results['unit']
        )
```

**Screenshot/Preview:**
```
┌─ Add Data Column ────────────────────────────┐
│ Create a new data column for entering        │
│ measured or input values.                    │
├───────────────────────────────────────────────┤
│ Column Properties                             │
│ ┌──────────────────────────────────────────┐ │
│ │ Name*:        [temperature____________]  │ │
│ │ ✓ Valid name                             │ │
│ │ Data Type*:   [FLOAT ▼]                  │ │
│ │ Unit:         [°C___] Quick: [°C ▼]      │ │
│ │ Description:  [Sample temperature_____]  │ │
│ │ Precision:    [6]                        │ │
│ └──────────────────────────────────────────┘ │
│                                              │
│ Uncertainty (Optional)                        │
│ ┌──────────────────────────────────────────┐ │
│ │ ☑ Create uncertainty column (name_u)     │ │
│ └──────────────────────────────────────────┘ │
│                                              │
│ Preview                                       │
│ ┌──────────────────────────────────────────┐ │
│ │ Header:      temperature [°C]            │ │
│ │ In formulas: {temperature}               │ │
│ └──────────────────────────────────────────┘ │
│                                              │
│                       [OK]  [Cancel]         │
└───────────────────────────────────────────────┘
```

---

### 2. AddCalculatedColumnDialog

Creates a calculated column with formula and optional uncertainty propagation.

**Fields:**
- **Name*** (required) - Column identifier
- **Description** - Tooltip text
- **Unit (Auto)** - Read-only, calculated from formula (requires Pint)
- **Precision** - Number of decimal places
- **Formula*** (required) - Expression using {name} syntax
- **Propagate Uncertainty** - Enable automatic uncertainty calculation

**Formula Syntax:**
- **Column references**: `{column_name}`
- **Operators**: `+`, `-`, `*`, `/`, `**` (power)
- **Functions**: `sin`, `cos`, `tan`, `sqrt`, `log`, `log10`, `exp`, `abs`
- **Constants**: `pi`, `e`

**Examples:**
```
{distance} / {time}
{mass} * {velocity}**2 / 2
sqrt({x}**2 + {y}**2)
sin({angle}) * {amplitude}
```

**Features:**
- **Column list** - Shows all available columns with types and units
- **Double-click to insert** - Easy column reference insertion
- **Formula validation** - Checks for balanced braces and unknown columns
- **Uncertainty info** - Explains which columns have uncertainties
- **Preview panel** - Shows column properties

**Example Usage:**
```python
from widgets.DataTableV2.dialogs import AddCalculatedColumnDialog

dialog = AddCalculatedColumnDialog(
    parent=main_window,
    model=model,  # Provides column list
    existing_names=model.get_column_names()
)

if dialog.exec():
    results = dialog.get_results()
    model.add_calculated_column(
        name=results['name'],
        formula=results['formula'],
        description=results['description'],
        precision=results['precision'],
        propagate_uncertainty=results['propagate_uncertainty']
    )
```

**Screenshot/Preview:**
```
┌─ Add Calculated Column ──────────────────────────────────────────┐
│ Create a calculated column using a formula.                      │
│ Reference other columns using {name} syntax.                     │
├───────────────────────────────────────────────────────────────────┤
│ Column Properties                                                 │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ Name*:        [velocity__________________________]           │ │
│ │ ✓ Valid name                                                 │ │
│ │ Description:  [Speed in m/s____________________]             │ │
│ │ Unit (Auto):  [Auto-calculated from formula]                │ │
│ │ Precision:    [6]                                            │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                   │
│ Formula (use {name} to reference columns)                        │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ {distance} / {time}                                          │ │
│ │                                                              │ │
│ │                                                              │ │
│ └──────────────────────────────────────────────────────────────┘ │
│ Operators: + - * / ** | Functions: sin, cos, sqrt... | pi, e    │
│ ✓ Valid formula                                                  │
│                                                                   │
│ Uncertainty Propagation                                           │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ ☑ Automatically calculate propagated uncertainty             │ │
│ │   Columns with uncertainty: distance, time                   │ │
│ │   A read-only column 'velocity_u' will be created.           │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                   │
│ ┌────── Available Columns ──┐  ┌────── Preview ──────────────┐ │
│ │ ● distance [m] (data)     │  │ Column Name: velocity        │ │
│ │ ● time [s] (data)         │  │ Formula: {distance}/{time}   │ │
│ │ σ distance_u (unc)        │  │ Type: CALCULATED (read-only) │ │
│ │ σ time_u (unc)            │  │ Uncertainty: velocity_u      │ │
│ │ (double-click to insert)  │  │                              │ │
│ └───────────────────────────┘  └──────────────────────────────┘ │
│                                                                   │
│                                [OK]  [Cancel]                    │
└───────────────────────────────────────────────────────────────────┘
```

---

### 3. AddRangeColumnDialog

Creates a column with evenly-spaced values (e.g., time series, x-axis data).

**Fields:**
- **Name*** (required) - Column identifier
- **Unit** - Unit of measurement
- **Description** - Tooltip text
- **Start Value*** (required) - First value in range
- **End Value*** (required) - Last value in range
- **Method** - Choose "Number of Points" or "Step Size"
  - **Number of Points** - Specify how many values to generate
  - **Step Size** - Specify the increment between values
- **Precision** - Number of decimal places

**Features:**
- **Live preview** - Shows first 10 values and calculated step/points
- **Dual input methods** - Specify points OR step size
- **Flexible ranges** - Supports negative and fractional values
- **Large datasets** - Can generate up to 1,000,000 points

**Example Usage:**
```python
from widgets.DataTableV2.dialogs import AddRangeColumnDialog

dialog = AddRangeColumnDialog(
    parent=main_window,
    existing_names=model.get_column_names()
)

if dialog.exec():
    results = dialog.get_results()
    model.add_range_column(
        name=results['name'],
        start=results['start'],
        end=results['end'],
        points=results['points'],
        unit=results['unit'],
        description=results['description'],
        precision=results['precision']
    )
```

**Screenshot/Preview:**
```
┌─ Add Range Column ───────────────────────────┐
│ Create a column with evenly-spaced values.   │
│ Useful for time series or x-axis data.       │
├───────────────────────────────────────────────┤
│ Column Properties                             │
│ ┌──────────────────────────────────────────┐ │
│ │ Name*:        [time___________________]  │ │
│ │ ✓ Valid name                             │ │
│ │ Unit:         [s____] Quick: [s ▼]       │ │
│ │ Description:  [Time values___________]   │ │
│ └──────────────────────────────────────────┘ │
│                                              │
│ Range Parameters                              │
│ ┌──────────────────────────────────────────┐ │
│ │ Start Value*:     [0.0______________]    │ │
│ │ End Value*:       [10.0_____________]    │ │
│ │ Method:           [Number of Points ▼]   │ │
│ │ Number of Points: [101______________]    │ │
│ │ Precision:        [6]                    │ │
│ └──────────────────────────────────────────┘ │
│                                              │
│ Preview                                       │
│ ┌──────────────────────────────────────────┐ │
│ │ Range: 0 to 10                           │ │
│ │ Points: 101                              │ │
│ │ Step: 0.1                                │ │
│ │                                          │ │
│ │ Values (first 10):                       │ │
│ │   [0] 0                                  │ │
│ │   [1] 0.1                                │ │
│ │   [2] 0.2                                │ │
│ │   [3] 0.3                                │ │
│ │   ... (91 more values)                   │ │
│ └──────────────────────────────────────────┘ │
│                                              │
│                       [OK]  [Cancel]         │
└───────────────────────────────────────────────┘
```

---

## Testing

Comprehensive test suite with 27 tests covering:

- Dialog creation and initialization
- Name validation (empty, duplicate, invalid characters)
- Field visibility based on selections
- Formula validation and error detection
- Column reference insertion
- Uncertainty propagation UI
- Preview updates
- Result extraction

**Run tests:**
```bash
uv run pytest tests/widgets/DataTableV2/test_dialogs.py -v
```

**Result:** ✅ 27/27 tests passing (100%)

---

## Interactive Demo

A demo application shows all dialogs in action:

```bash
uv run python tests/widgets/DataTableV2/demo_dialogs.py
```

**Features:**
- Pre-loaded with sample data
- Buttons to open each dialog type
- Status messages showing what was created
- Live table view showing results

**Demo Screenshot:**
```
┌─ DataTableV2 Dialog Demo ─────────────────────────────────┐
│ DataTableV2 Dialog Demo                                   │
│                                                            │
│ Click the buttons below to open dialogs for creating      │
│ different column types...                                 │
│                                                            │
│ [➕ Add Data Column] [ƒ Add Calculated] [▬ Add Range]     │
│                                                            │
│ ┌── Data Table ─────────────────────────────────────────┐ │
│ │ x [0 to 10] │ y │ y_u │ ...                          │ │
│ │ 0.0         │ 1.0 │ 0.1 │                            │ │
│ │ 1.0         │ 2.0 │ 0.15│                            │ │
│ │ ...         │ ... │ ... │                            │ │
│ └───────────────────────────────────────────────────────┘ │
│                                                            │
│ ✓ Added calculated column 'velocity' with uncertainty     │
└────────────────────────────────────────────────────────────┘
```

---

## Integration with DataTableV2

The dialogs are designed to work seamlessly with the DataTableV2 model:

```python
from widgets.DataTableV2.model import DataTableModel
from widgets.DataTableV2.view import DataTableView
from widgets.DataTableV2.dialogs import (
    AddDataColumnDialog,
    AddCalculatedColumnDialog,
    AddRangeColumnDialog
)

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.model = DataTableModel()
        self.view = DataTableView()
        self.view.setModel(self.model)
        
    def add_data_column(self):
        dialog = AddDataColumnDialog(
            parent=self,
            existing_names=self.model.get_column_names()
        )
        
        if dialog.exec():
            results = dialog.get_results()
            self.model.add_data_column(**results)
    
    def add_calculated_column(self):
        dialog = AddCalculatedColumnDialog(
            parent=self,
            model=self.model,
            existing_names=self.model.get_column_names()
        )
        
        if dialog.exec():
            results = dialog.get_results()
            self.model.add_calculated_column(**results)
```

---

## Future Enhancements

Potential improvements for the dialog system:

1. **VariablesDialog** - Manage global constants/variables for formulas
2. **EditColumnDialog** - Edit existing column properties
3. **DerivativeColumnDialog** - Create discrete derivative columns (dy/dx)
4. **InterpolationColumnDialog** - Create interpolated columns
5. **Formula syntax highlighting** - Color code formula text
6. **Unit calculator** - Live unit calculation in formula dialog
7. **Formula templates** - Common formulas library (e.g., "Kinetic Energy", "Ideal Gas Law")
8. **Import/Export** - Save/load column configurations
9. **Batch operations** - Create multiple columns at once
10. **Keyboard shortcuts** - Quick access to dialogs (Ctrl+D, Ctrl+F, Ctrl+R)

---

## Summary

The DataTableV2 dialog system provides:

✅ **3 comprehensive dialogs** for all column creation needs
✅ **Extensive validation** prevents user errors
✅ **Helpful guidance** makes complex features accessible
✅ **Live preview** shows results before committing
✅ **27 passing tests** ensure reliability
✅ **Interactive demo** for exploration and testing
✅ **Clean integration** with DataTableV2 model

The dialogs transform DataTableV2 from a programmatic-only interface into a user-friendly application component ready for end-user deployment! 🎯
