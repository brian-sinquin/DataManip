# Uncertainty Propagation Feature

## Overview

DataTableV2 now supports automatic uncertainty propagation for calculated columns using the standard error propagation formula based on symbolic differentiation.

## Mathematical Foundation

The propagated uncertainty is calculated using:

**δf = √(Σ(∂f/∂xᵢ · δxᵢ)²)**

Where:
- `δf` = combined uncertainty of the result
- `∂f/∂xᵢ` = partial derivatives with respect to each variable (calculated symbolically using SymPy)
- `δxᵢ` = uncertainty of each input variable

## Implementation

### Core Components

1. **uncertainty_propagator.py** (288 lines)
   - `UncertaintyPropagator` class for symbolic differentiation
   - Converts formulas to SymPy expressions
   - Computes partial derivatives
   - Evaluates uncertainties row-by-row

2. **model.py** (modified)
   - `add_calculated_column()` accepts `propagate_uncertainty` parameter
   - Automatically creates `{name}_u` uncertainty column
   - Triggers recalculation when data or uncertainties change

3. **column_metadata.py** (modified)
   - Added `propagate_uncertainty: bool` field to column metadata

### Automatic Column Creation

When you create a calculated column with `propagate_uncertainty=True`, the system automatically:

1. Creates the calculated column (e.g., `y`)
2. Creates a linked uncertainty column (e.g., `y_u`)
3. **Makes the uncertainty column read-only** (it's automatically calculated)
4. Calculates partial derivatives symbolically
5. Evaluates uncertainty for each row
6. Updates uncertainties when data changes

**Important**: Propagated uncertainty columns are **read-only** and cannot be manually edited. They are automatically recalculated whenever the underlying data or uncertainties change. This ensures the uncertainties always reflect the current propagation calculation.

## Usage

### Basic Example

```python
from widgets.DataTableV2.model import DataTableModel
import pandas as pd

# Create model
model = DataTableModel()

# Add input data with uncertainties
model.add_data_column("x", data=pd.Series([1.0, 2.0, 3.0]))
model.add_data_column("x_u", data=pd.Series([0.1, 0.1, 0.15]))

# Create calculated column with uncertainty propagation
model.add_calculated_column(
    "y",
    formula="{x}**2",
    propagate_uncertainty=True
)

# Result:
# - Column 'y' contains calculated values: [1.0, 4.0, 9.0]
# - Column 'y_u' contains propagated uncertainties: [0.2, 0.4, 0.9]
#   (calculated as δy = |2x| · δx)
```

### Multi-Variable Example

```python
# Multiple input variables
model.add_data_column("A", data=pd.Series([10.0, 20.0]))
model.add_data_column("A_u", data=pd.Series([0.5, 0.3]))
model.add_data_column("B", data=pd.Series([5.0, 10.0]))
model.add_data_column("B_u", data=pd.Series([0.2, 0.4]))

# Complex formula
model.add_calculated_column(
    "result",
    formula="{A} * {B} / 2",
    propagate_uncertainty=True
)

# Uncertainty is calculated as:
# δresult = sqrt((B/2 · δA)² + (A/2 · δB)²)
```

### Chained Calculations

```python
# Create first calculated column
model.add_calculated_column("y", "{x}**2", propagate_uncertainty=True)

# Create second column that depends on first
model.add_calculated_column("z", "{y} + 10", propagate_uncertainty=True)

# Uncertainties propagate through the chain:
# x → x_u → y → y_u → z → z_u
```

## Supported Operations

### Arithmetic Operators
- Addition: `{A} + {B}` → δf = √(δA² + δB²)
- Subtraction: `{A} - {B}` → δf = √(δA² + δB²)
- Multiplication: `{A} * {B}` → δf = √((B·δA)² + (A·δB)²)
- Division: `{A} / {B}` → δf = √((1/B·δA)² + (-A/B²·δB)²)
- Power: `{A}**2` → δf = |2A| · δA

### Mathematical Functions
- `sqrt({x})` → δ(√x) = |1/(2√x)| · δx
- `sin({x})` → δ(sin x) = |cos x| · δx
- `cos({x})` → δ(cos x) = |sin x| · δx
- `log({x})` → δ(ln x) = |1/x| · δx
- `exp({x})` → δ(eˣ) = |eˣ| · δx

All standard Python math functions supported by the formula parser.

## Edge Cases

### Manual vs Propagated Uncertainty Columns

There are two types of uncertainty columns:

1. **Manual uncertainty columns**: Created as DATA columns (e.g., `model.add_data_column("x_u", ...)`). These are **editable** and allow you to enter measured uncertainties.

2. **Propagated uncertainty columns**: Created automatically when `propagate_uncertainty=True`. These are **read-only** because they're automatically calculated from other uncertainties.

```python
# Manual uncertainty (editable)
model.add_data_column("x_u", data=pd.Series([0.1, 0.2]))
# You can edit values in x_u

# Propagated uncertainty (read-only)
model.add_calculated_column("y", "{x}**2", propagate_uncertainty=True)
# y_u is created automatically and CANNOT be edited
```

### Missing Uncertainties

If a variable doesn't have an associated uncertainty column, it's treated as having zero uncertainty:

```python
model.add_data_column("x", data=pd.Series([1.0, 2.0]))
# No x_u column

model.add_calculated_column("y", "{x}**2", propagate_uncertainty=True)
# Result: y_u will be all zeros
```

### Partial Uncertainties

If only some variables have uncertainties, propagation uses available ones:

```python
model.add_data_column("A", data=pd.Series([10.0]))
model.add_data_column("A_u", data=pd.Series([0.5]))
model.add_data_column("B", data=pd.Series([5.0]))
# No B_u column

model.add_calculated_column("result", "{A} + {B}", propagate_uncertainty=True)
# Result: δresult = δA (contribution from B is zero)
```

### NaN Handling

If any input value is NaN, the propagated uncertainty is also NaN:

```python
model.add_data_column("x", data=pd.Series([1.0, float('nan'), 3.0]))
model.add_data_column("x_u", data=pd.Series([0.1, 0.1, 0.1]))

model.add_calculated_column("y", "{x}**2", propagate_uncertainty=True)
# Result: y = [1.0, nan, 9.0], y_u = [0.2, nan, 0.6]
```

## Automatic Recalculation

Uncertainties automatically recalculate when:

1. **Data values change**: Editing a value in a DATA column triggers recalculation of all dependent calculated columns and their uncertainties
2. **Uncertainty values change**: Editing an uncertainty column (e.g., `x_u`) triggers recalculation of all dependent propagated uncertainties

This ensures uncertainties stay synchronized with the data.

## Testing

The feature has comprehensive test coverage (16 tests, all passing):

- Basic arithmetic operations
- Power operations (nonlinear)
- Mathematical functions
- Complex multi-variable formulas
- Edge cases (missing uncertainties, NaN)
- Recalculation triggers
- Integration with multiple columns

Run tests:
```bash
uv run pytest tests/widgets/DataTableV2/test_uncertainty_propagation.py -v
```

## Demo

See the interactive demo:
```bash
uv run python tests/widgets/DataTableV2/demo_uncertainty.py
```

This opens a window showing:
- Live data table with editable values
- Automatic uncertainty recalculation
- Example of chained calculations (x → y → z)

## Implementation Details

### Formula Conversion

The system converts formulas to SymPy expressions using AST parsing:

1. Parse formula using Python's `ast` module
2. Convert AST nodes to SymPy expressions
3. Create symbolic variables for each data column
4. Build SymPy expression tree

Example:
```
Formula: "{A} * {B} + {C}"
→ AST: BinOp(Mult(Name(A), Name(B)), Add, Name(C))
→ SymPy: A*B + C
```

### Derivative Calculation

For each variable in the formula, compute the partial derivative symbolically:

```python
import sympy as sp

# Formula: A*B + C
# Variables: A, B, C
expr = A*B + C

# Partial derivatives:
∂f/∂A = sp.diff(expr, A) = B
∂f/∂B = sp.diff(expr, B) = A
∂f/∂C = sp.diff(expr, C) = 1
```

### Uncertainty Evaluation

For each row, evaluate the uncertainty using the quadrature formula:

```python
# For formula f(A, B, C)
# At row i with values A_i, B_i, C_i and uncertainties δA_i, δB_i, δC_i

# Evaluate partial derivatives at row values
∂f/∂A |ᵢ = evaluate(B, {A: A_i, B: B_i, C: C_i})
∂f/∂B |ᵢ = evaluate(A, {A: A_i, B: B_i, C: C_i})
∂f/∂C |ᵢ = evaluate(1, {A: A_i, B: B_i, C: C_i})

# Calculate variance contributions
variance = (∂f/∂A |ᵢ * δA_i)² + (∂f/∂B |ᵢ * δB_i)² + (∂f/∂C |ᵢ * δC_i)²

# Combined uncertainty
δf_i = √variance
```

## Limitations

1. **Independent variables**: Assumes all input variables are independent (no covariance)
2. **First-order approximation**: Uses first-order Taylor expansion (valid for small uncertainties)
3. **Symbolic differentiation**: Only works with functions supported by SymPy
4. **Performance**: May be slow for very complex formulas with many variables

## Future Enhancements

- Support for correlated variables (covariance matrix)
- Monte Carlo uncertainty propagation option
- Second-order uncertainty terms
- Custom derivative specification for unsupported functions
- UI dialog for enabling/disabling propagation (currently programmatic only)

## References

- [Error Propagation - Wikipedia](https://en.wikipedia.org/wiki/Propagation_of_uncertainty)
- [SymPy Documentation](https://docs.sympy.org/)
- Taylor, John R. "An Introduction to Error Analysis" (1997)
