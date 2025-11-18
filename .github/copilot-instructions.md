# DataManip - Copilot Instructions

**Be concise. No verbose summaries. Track changes in todo list only.**

## Project

PySide6 data manipulation app for experimental sciences.

**Run**: `uv run datamanip`
**Test**: `uv run pytest tests/widgets/DataTableV2/`

## Key Components

### DataTableV2 (New, Active Development)
- **Location**: `src/widgets/DataTableV2/`
- **Model**: `model.py` - Data storage, formulas, uncertainty propagation
- **View**: `view.py` - Qt table view
- **Dialogs**: `dialogs.py` - AddDataColumnDialog, AddCalculatedColumnDialog, AddRangeColumnDialog
- **Uncertainty**: `uncertainty_propagator.py` - SymPy-based error propagation
- **Tests**: `tests/widgets/DataTableV2/` - 348+ tests

### AdvancedDataTableWidget (Legacy)
- **Location**: `src/widgets/AdvancedDataTableWidget/`
- Original implementation, kept for reference
  - `VariablesDialog`: Manage global constants for formulas
- `context_menu.py`: Right-click menu for column operations
- `toolbar.py`: Toolbar with quick-action buttons (uses dialogs for all operations)

**Column Metadata System** (`models.py`):
```python
@dataclass
class ColumnMetadata:
    column_type: AdvancedColumnType  # DATA, CALCULATED, UNCERTAINTY, DERIVATIVE
    data_type: AdvancedColumnDataType  # NUMERICAL, CATEGORICAL, TEXT
    diminutive: str  # Short name for formulas and display (e.g., "T", "P", "V")
    description: Optional[str]  # Full description (tooltip)
    unit: Optional[str]  # Unit of measurement (e.g., "°C", "kPa")
    formula: Optional[str]  # Formula for calculated columns
    uncertainty_reference: Optional[int]  # Column index for uncertainty columns
    propagate_uncertainty: bool  # Whether to calculate uncertainty for calculated columns
    derivative_numerator: Optional[int]  # Numerator column for derivative columns
    derivative_denominator: Optional[int]  # Denominator column for derivative columns
```

**Column Type Visual Indicators**:
Headers display scientific symbols to indicate column type at a glance:
- `●` (black circle) - DATA columns: measured/input data points
- `ƒ` (script f) - CALCULATED columns: values derived from formulas/functions
- `∂` (partial derivative) - DERIVATIVE columns: discrete differences dy/dx

**Column Metadata System** (`models.py`):
```python
@dataclass
class ColumnMetadata:
    column_type: AdvancedColumnType  # DATA, CALCULATED, UNCERTAINTY, DERIVATIVE
    data_type: AdvancedColumnDataType  # NUMERICAL, CATEGORICAL, TEXT
    diminutive: str  # Short name for formulas (e.g., "T", "P")
    description: Optional[str]  # Tooltip
    unit: Optional[str]  # Unit (e.g., "°C", "kPa")
    formula: Optional[str]  # For calculated columns
    uncertainty_reference: Optional[int]  # Column index for uncertainty
    propagate_uncertainty: bool  # Auto-calculate uncertainty
    derivative_numerator/denominator: Optional[int]  # For derivatives
```

**Column Type Symbols**:
- `●` DATA, `ƒ` CALCULATED, `∂` DERIVATIVE, `σ` UNCERTAINTY

**Formula System**:
- Reference columns: `{name}` syntax
- Operators: `+`, `-`, `*`, `/`, `**`
- Functions: `abs`, `sqrt`, `sin`, `cos`, `tan`, `log`, `exp`
- Constants: `pi`, `e`
- Unit propagation via Pint

**Uncertainty Propagation**:
- Formula: δf = √(Σ(∂f/∂xᵢ · δxᵢ)²)
- SymPy for symbolic differentiation
- Auto-creates `_u` columns (read-only)
- Recalculates on data/uncertainty changes

**Example Use Cases**:
- Velocity: distance/time
- Acceleration: velocity/time (derivative of derivative!)
- Rate of change: any quantity vs. time or position
- Complex formulas using derivatives: `{x}**2 + {dydx}**2`

**Formula Integration**:
- Derivative columns appear in formula editor with `[deriv]` label
- Can be referenced by diminutive: `{dydx}`, `{velocity}`, etc.
- Units propagate correctly through calculations
- Example: Create y=sin(x), then dydx as derivative, then use in formula: `{x}**2 + {dydx}**2`

**Dialog**: `DerivativeEditorDialog` provides column selection and unit preview

### 5. Configuration & Language Management

**Configuration System** (`src/utils/config.py`):
- JSON-based config stored in `config.json`
- Thread-safe with dot notation access (e.g., `config.get("lang")`)
- Auto-saves configuration on application exit
- **Usage**:
  ```python
  from utils.config import get_config
  config = get_config()
  lang = config.get_language()  # Returns "en_US", "fr_FR", etc.
  ```

**Language System** (`src/utils/lang.py`):
- JSON-based translations in `assets/lang/{lang_code}.json`
- Thread-safe singleton pattern
- **Usage**:
  ```python
  from utils.lang import tr
  text = tr("menu.file.open", "Open File")  # Returns translated text or default
  ```

**Paths Utility** (`src/utils/paths.py`):
- Centralized path definitions for config, assets, icons, languages

---

## Code Conventions

### Naming Conventions
- **Classes**: `PascalCase` (e.g., `AdvancedDataTableWidget`, `ColumnMetadata`)
- **Functions/Methods**: `snake_case` (e.g., `add_column`, `_recalculate_column`)
- **Private Methods**: Prefix with `_` (e.g., `_on_item_changed`, `_update_header`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_NUMERIC_PRECISION`, `ERROR_PREFIX`)

### Docstring Format
Use Google-style docstrings:
```python
def addColumn(self, header_label: str, col_type: AdvancedColumnType, 
              data_type: AdvancedColumnDataType, diminutive: Optional[str] = None,
              unit: Optional[str] = None, description: Optional[str] = None) -> int:
    """Add a new column to the table with specified header and types.
    
    Args:
        header_label: Initial name (replaced by diminutive in header)
        col_type: Column type (DATA, CALCULATED, UNCERTAINTY)
        data_type: Data type (NUMERICAL, CATEGORICAL, TEXT)
        diminutive: Short name used for display and formulas
        unit: Optional unit of measurement
        description: Full description shown as tooltip
        
    Returns:
        Index of the newly created column
        

## Code Conventions

- **Classes**: `PascalCase`
- **Functions/Methods**: `snake_case`
- **Private Methods**: Prefix with `_`
- **Constants**: `UPPER_SNAKE_CASE`
- **Type Hints**: Always use for parameters and return values
- **Docstrings**: Google style

## Running & Testing

```bash
uv sync              # Install dependencies
uv run datamanip     # Run application
uv run pytest tests/widgets/DataTableV2/  # Run tests
```

### Common Pitfalls
1. **Infinite Loops**: Modifying table items triggers `itemChanged`, which can cause recursion. Always use `_updating_calculations` flag.
2. **Diminutive Uniqueness**: Always validate that diminutives are unique before adding columns.
3. **Unit Compatibility**: Pint raises errors for incompatible unit operations (e.g., `m + kg`). Catch these and show user-friendly errors.
4. **SymPy Conversion**: Not all Python expressions convert cleanly to SymPy. Test edge cases.

---

## Debugging Tips

### Enable Qt Debug Output
```bash
# Set environment variable for detailed Qt warnings
set QT_LOGGING_RULES="qt.*=true"
uv run datamanip
```

### Common Debugging Scenarios
- **Formula Errors**: Check `formula_evaluator.py` - errors are caught and prefixed with `ERROR_PREFIX`
- **Uncertainty Issues**: Add logging in `uncertainty.py` to trace partial derivative calculations
- **UI Not Updating**: Ensure `_update_column_header()` is called after metadata changes
- **Recalculation Not Triggering**: Verify `itemChanged` signal is connected and `_updating_calculations` is managed correctly

---

## Future Development Areas

### Planned Features (Check TODO.md)
- File I/O (save/load data tables)
- More advanced plotting options
- Export to CSV/Excel
- More unit types and conversions
- Enhanced formula editor with syntax highlighting

### Known Limitations
- No undo/redo functionality yet
- Limited testing coverage
- No plugin system for custom column types
- Uncertainty propagation assumes independent variables (no covariance)

---

## Quick Reference

### Add a Data Column
```python
table.addColumn(
    header_label="Temperature",
    col_type=AdvancedColumnType.DATA,
    data_type=AdvancedColumnDataType.NUMERICAL,
    diminutive="T",
    unit="°C",
    description="Sample temperature"
)
```

### Add a Range Column (Evenly Spaced Values)
```python
# Via code
table.addRangeColumn(
    header_label="Time",
    start=0.0,
    end=10.0,
    points=11,  # Creates 11 points from 0 to 10 (step = 1.0)
    diminutive="t",
    unit="s",
    description="Time values"
)

# Via UI
# Click "Add Range Column" button in toolbar
# Enter start, end, number of points, and column properties
```

### Add a Calculated Column with Uncertainty
```python
# Via code
table.addCalculatedColumn(
    header_label="Pressure Difference",
    formula="{P1} - {P2}",
    diminutive="dP",
    unit="kPa",
