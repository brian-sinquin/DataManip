# DataTableV2 - Quick Reference

High-performance PySide6 data table with formulas, uncertainty propagation, and ranges.

## Key Features

- **Fast**: Pandas backend, Qt Model/View architecture
- **Formulas**: 30+ math functions, auto-recalculation, {name} syntax
- **Uncertainty**: Automatic error propagation via SymPy
- **Derivatives**: Discrete differentiation (dy/dx)
- **Ranges**: Auto-generated sequences
- **UI Dialogs**: User-friendly column creation

## Quick Start

```python
from widgets.DataTableV2.model import DataTableModel
from widgets.DataTableV2.view import DataTableView

model = DataTableModel()
view = DataTableView()
view.setModel(model)

# Add columns
model.add_range_column("t", start=0, end=5, points=51, unit="s")
model.add_data_column("v0", unit="m/s")
model.add_calculated_column("x", formula="{v0} * {t}", unit="m")

view.show()
```

## Column Types

**DATA** - User-editable values
```python
model.add_data_column("temp", unit="°C", precision=2)
```

**CALCULATED** - Formula-based with optional uncertainty propagation
```python
model.add_calculated_column("result", formula="{A} + {B}", 
                           propagate_uncertainty=True)
```

**RANGE** - Auto-generated sequences
```python
model.add_range_column("x", start=0, end=10, points=101)
```

## Formula Syntax

- **References**: `{column_name}`
- **Operators**: `+`, `-`, `*`, `/`, `**`
- **Functions**: `sin`, `cos`, `tan`, `sqrt`, `log`, `exp`, `abs`
- **Constants**: `pi`, `e`

## Uncertainty Propagation

```python
# Create data with uncertainty
model.add_data_column("x", data=pd.Series([1, 2, 3]))
model.add_data_column("x_u", data=pd.Series([0.1, 0.1, 0.15]))

# Auto-propagate uncertainty
model.add_calculated_column("y", formula="{x}**2", 
                           propagate_uncertainty=True)
# Creates y and y_u (read-only) columns
```

Formula: δf = √(Σ(∂f/∂xᵢ · δxᵢ)²)

## UI Dialogs

```python
from widgets.DataTableV2.dialogs import (
    AddDataColumnDialog,
    AddCalculatedColumnDialog,
    AddRangeColumnDialog
)

dialog = AddCalculatedColumnDialog(model=model)
if dialog.exec():
    results = dialog.get_results()
    model.add_calculated_column(**results)
```

## File I/O

```python
# Save
model.save_to_file("data.json")

# Load
model.load_from_file("data.json")
```

## Testing

```bash
uv run pytest tests/widgets/DataTableV2/ -v
```

348+ tests covering all features.

## Demos

```bash
uv run python tests/widgets/DataTableV2/demo_uncertainty.py
uv run python tests/widgets/DataTableV2/demo_dialogs.py
```