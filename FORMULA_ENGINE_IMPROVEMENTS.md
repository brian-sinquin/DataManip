# Formula Engine Improvements - Array Operations & Constants

## Changes Made

### 1. Fixed Pandas FutureWarning
**File**: `src/studies/data_table_study.py`

**Issue**: Pandas 2.x warns about DataFrame concatenation with empty DataFrames affecting dtype inference.

**Fix**: Check if DataFrame is empty before concatenating:
```python
if len(self.table.data) > 0:
    self.table.data = pd.concat([self.table.data, new_rows], ignore_index=True)
else:
    self.table.data = new_rows
```

---

### 2. Calculated Constants Now Work in Formulas
**File**: `src/ui/widgets/data_table/widget.py`

**Issue**: Only numeric constants (`type="constant"`) were available in formulas. Calculated constants (`type="calculated"`) were not included.

**Before**:
```python
available_vars = [name for name, data in self.study.workspace.constants.items()
                  if data.get("type") == "constant"]
```

**After**:
```python
available_vars = [name for name, data in self.study.workspace.constants.items()
                  if data.get("type") in ["constant", "calculated"]]
```

**Example Usage**:
```python
# Define constants in workspace
g = 9.81  # Numeric constant
g_doubled = g * 2  # Calculated constant

# Use in column formula
{mass} * {g_doubled}  # Works! Uses calculated constant
```

---

### 3. Array Operations Documentation
**File**: `src/core/formula_engine.py`

**Clarification**: Python/NumPy operators already work element-wise on arrays. No special syntax needed.

**How It Works**:
- ✅ `{velocity} * 2` - Multiplies each element by 2
- ✅ `{position} - {offset}` - Element-wise subtraction if both arrays
- ✅ `{data} - np.mean({data})` - Subtracts scalar from each element
- ✅ `{force} / {mass}` - Element-wise division

**Broadcasting**:
- Scalar + Array → Scalar broadcasts to array length
- Array + Array → Element-wise operation (must be same length)

**Why No Dot Operators**:
MATLAB uses `.+`, `.-`, `.*` for element-wise operations because default `+`, `-`, `*` are matrix operations. Python/NumPy defaults to element-wise, so dot operators are:
- ❌ NOT needed
- ❌ NOT supported
- ❌ Would be confusing

**Matrix Operations** (if ever needed):
Use explicit functions instead:
- `np.dot(a, b)` for matrix multiplication
- `np.matmul(a, b)` or `a @ b` for matrix multiply

---

## Testing

### Manual Test
Created `tests/manual_test_constants_in_formulas.py` demonstrating:
1. ✅ Calculated constants in formulas
2. ✅ Scalar - Array operations
3. ✅ Array * Calculated constant

### Unit Tests
All 26 tests pass:
- ✅ `test_calculated_constants.py` - 5 tests
- ✅ `test_formula_engine.py` - 21 tests

---

## Summary

| Feature | Before | After |
|---------|--------|-------|
| Pandas concat warning | ⚠️ Warning on empty DataFrame | ✅ Fixed |
| Calculated constants | ❌ Not available in formulas | ✅ Available |
| Array operations | ✅ Already working | ✅ Documented |
| Element-wise operators | ✅ Standard `+`, `-`, `*`, `/` | ✅ No change needed |
| Dot operators `.+`, `.-` | ❌ Not needed | ❌ Not needed |

**Key Insight**: Python/NumPy already does what MATLAB's dot operators do by default. The formula engine correctly handles element-wise operations, scalar broadcasting, and mixing scalars with arrays without any special syntax.
