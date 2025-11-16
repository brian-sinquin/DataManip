# DataManip - AI Coding Agent Instructions

## Project Overview

**DataManip** is a PySide6-based data manipulation application for experimental sciences. It features a sophisticated table widget (`AdvancedDataTableWidget`) that supports:

- **Data columns** with units and diminutives (short names)
- **Calculated columns** with formula support and automatic unit propagation
- **Uncertainty columns** with automatic uncertainty propagation using discrete differential forms
- **Auto-recalculation** when data or uncertainty values change

### Key Technologies
- **PySide6 (Qt 6.10.0)**: UI framework for widget-based desktop application
- **SymPy 1.14.0**: Symbolic mathematics for automatic differentiation in uncertainty propagation
- **Pint 0.25.2**: Unit-aware calculations and conversions
- **NumPy, Matplotlib**: Data manipulation and visualization
- **Python 3.12+**: Modern Python with dataclasses
- **UV Package Manager**: Fast Python package/project manager

---

## Architecture

### Application Entry Point
- **File**: `src/main.py`
- Initializes configuration (`utils/config.py`) and language system (`utils/lang.py`)
- Creates `MainWindow` with workspace containing `AdvancedDataTableWidget`
- Entry command: `uv run datamanip`

### Main UI Structure
```
MainWindow (src/ui/MainWindow/main_window.py)
├── MenuBar (menu_bar.py)
└── Workspace (workspace.py)
    ├── AdvancedDataTableWidget (src/widgets/AdvancedDataTableWidget/)
    └── Matplotlib canvas for plotting
```

### Core Widget: AdvancedDataTableWidget

**Location**: `src/widgets/AdvancedDataTableWidget/`

**Key Files**:
- `advanced_datatable.py`: Main widget implementation (~1400 lines)
- `models.py`: Column metadata dataclasses and enums
- `formula_evaluator.py`: Safe AST-based formula evaluation with unit support
- `dialogs.py`: Type-specific column editor dialogs (~1260 lines)
  - `DataColumnEditorDialog`: Edit DATA columns (diminutive, unit, uncertainty toggle)
  - `FormulaEditorDialog`: Edit CALCULATED columns (formula, units, uncertainty propagation)
  - `DerivativeEditorDialog`: Edit DERIVATIVE columns (numerator/denominator selection, unit calculation)
  - `RangeColumnDialog`: Create DATA columns with evenly spaced values
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
- `σ` (sigma) - UNCERTAINTY columns: standard deviation/error values

Example header display: `● T [°C]`, `ƒ T_K [K]`, `∂ v [m/s]`, `σ ±`

**Important**: The widget previously had a `display_name` field, but it was **removed** entirely. Only `diminutive` is used for display and formulas. Header text is now formatted as `"{symbol}{diminutive} [{unit}]"`.

---

## Key Subsystems

### 1. Column Metadata & Formula System

**Diminutive-Based Referencing**:
- Columns are referenced in formulas using `{diminutive}` syntax (e.g., `{T}`, `{P}`)
- Backward compatibility exists for `[diminutive]` syntax
- Diminutives must be unique and are used for both display and formula evaluation

**Formula Evaluation** (`formula_evaluator.py`):
- Safe AST-based evaluation (no `eval()`)
- Supports operators: `+`, `-`, `*`, `/`, `**`
- Supported functions: `abs`, `sqrt`, `sin`, `cos`, `tan`, `log`, `log10`, `exp`, `pi`, `e`
- Automatic unit propagation using Pint

**Example Formula**:
```python
# Formula: "{P} * {V} / ({R} * {T})"
# Where P=pressure[kPa], V=volume[L], R=constant, T=temperature[K]
```

### 2. Uncertainty Propagation System

**Location**: `src/utils/uncertainty.py` (~437 lines)

**Key Classes**:
- `FormulaToSymPy`: Converts AST expressions to SymPy symbolic expressions
- `UncertaintyCalculator`: Calculates combined uncertainty using discrete differential forms

**Uncertainty Propagation Formula**:
```
δf = sqrt(Σ(∂f/∂xᵢ * δxᵢ)²)
```
Where:
- `δf` = combined uncertainty of result
- `∂f/∂xᵢ` = partial derivatives (calculated symbolically using SymPy)
- `δxᵢ` = uncertainties of input variables

**Workflow**:
1. User enables uncertainty propagation for a calculated column via dialog
2. System creates a linked uncertainty column automatically
3. When data or uncertainty values change, `_on_item_changed()` triggers recalculation
4. `_calculate_and_update_uncertainty()` uses `UncertaintyCalculator` to compute values

**Example**:
```python
# For formula: "{A} + {B}"
# If A=10±0.5, B=20±0.3
# Result: 30±0.583 (sqrt(0.5² + 0.3²))
```

### 3. Auto-Recalculation System

**Location**: `advanced_datatable.py`

**Trigger Points**:
- `_on_item_changed()`: Connected to `itemChanged` signal
- `setItem()`: Overridden to detect changes to DATA or UNCERTAINTY columns

**Recalculation Flow**:
```python
def _on_item_changed(self, item):
    if self._updating_calculations:
        return  # Prevent infinite loops
    
    col = item.column()
    metadata = self._columns[col]
    
    # Trigger recalculation if DATA or UNCERTAINTY column changed
    if metadata.is_data_column() or metadata.is_uncertainty_column():
        self._recalculate_all_calculated_columns()
```

**Important**: The `_updating_calculations` flag prevents infinite recalculation loops.

### 4. Derivative Columns System

**Location**: `advanced_datatable.py`, `dialogs.py`

**Purpose**: Calculate discrete differences (numerical derivatives) dy/dx between two columns

**Calculation Method**:
```python
# For row i (except last): derivative[i] = (y[i+1] - y[i]) / (x[i+1] - x[i])
# For last row: uses backward difference
```

**Workflow**:
1. User selects "Add Derivative Column..." from context menu
2. Dialog allows selection of numerator (dy) and denominator (dx) columns
3. System automatically calculates unit (e.g., m/s from distance[m] and time[s])
4. Recalculates when either source column changes
5. **Derivative columns can be used in formulas** - they appear in the formula editor's column list

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
        
    Raises:
        ValueError: If diminutive is not unique
    """
```

### Type Hints
- Always use type hints for function parameters and return values
- Use `Optional[T]` for nullable types
- Use `Union[T1, T2]` for multiple possible types
- Import from `typing` module

### Error Handling
- Use specific exceptions (e.g., `ValueError`, `KeyError`)
- Provide descriptive error messages
- Show user-friendly dialogs via `QMessageBox` or `ui/message_boxes.py`

---

## Common Development Workflows

### Running the Application
```bash
# Install dependencies
uv sync

# Run application
uv run datamanip

# Run a test file (delete file after analysis)
uv run python path/to/test_file.py
```

### Adding a New Column Type
1. Add enum value to `AdvancedColumnType` in `models.py`
2. Update `ColumnMetadata` dataclass with any new fields
3. Modify `addColumn()` in `advanced_datatable.py` to handle new type
4. Update dialogs in `dialogs.py` to support editing the new type
5. Add context menu actions in `context_menu.py` if needed

### Adding Uncertainty Propagation to Calculated Column
1. Open column editor dialog (double-click header or context menu)
2. Check "Propagate uncertainty" checkbox
3. System automatically:
   - Creates linked uncertainty column
   - Calculates partial derivatives using SymPy
   - Updates uncertainty values when data changes

### Testing
- **Manual Testing**: Run `uv run datamanip` and test features interactively
- **Unit Tests**: Located in `test_units.py` (currently minimal)
- **Future**: Expand test coverage for uncertainty calculations and formula evaluation

---

## Integration Points & Dependencies

### External Libraries
- **PySide6**: All UI components inherit from Qt widgets (`QTableWidget`, `QDialog`, etc.)
- **SymPy**: Used exclusively in `utils/uncertainty.py` for symbolic differentiation
- **Pint**: Used in `formula_evaluator.py` and `utils/units.py` for unit handling
- **Matplotlib**: Used in `workspace.py` for plotting (backend: `qt5agg`)

### Internal Dependencies
```
main.py
├── utils/config.py (init_config)
├── utils/lang.py (init_language)
├── utils/paths.py (ICONS_DIR, CONFIG_FILE)
└── ui/MainWindow/main_window.py
    ├── ui/MainWindow/workspace.py
    │   └── widgets/AdvancedDataTableWidget/advanced_datatable.py
    │       ├── models.py
    │       ├── formula_evaluator.py
    │       ├── dialogs.py
    │       └── context_menu.py
    └── ui/MainWindow/menu_bar.py
```

### Signal/Slot Patterns
- `columnAdded`, `columnRemoved`, `formulaChanged` signals in `AdvancedDataTableWidget`
- `itemChanged` connected to `_on_item_changed()` for auto-recalculation
- `sectionDoubleClicked` on header for editing dialogs

---

## Important Implementation Notes

### Recent Refactoring (Critical Context)
- **Removed `display_name` field**: Previously, columns had both `diminutive` and `display_name`. This was removed to simplify the data model. All references now use `diminutive` for both formulas and display.
- **Auto-recalculation**: Calculated columns now recalculate automatically when any DATA or UNCERTAINTY column changes. This is handled in `_on_item_changed()` and `setItem()`.
- **Dialog-based UX**: All column operations use type-specific dialogs for consistency:
  - Double-clicking headers opens the appropriate dialog (DataColumnEditorDialog, FormulaEditorDialog, DerivativeEditorDialog)
  - Toolbar creation buttons use dialogs instead of simple QInputDialog message boxes
  - This provides better validation, preview functionality, and user guidance

### Known Patterns
- **Metadata Access**: Use `self._columns[col_index]` to get `ColumnMetadata`
- **Header Updates**: Use `_update_column_header()` to sync header text with metadata
- **Loop Prevention**: Always check `self._updating_calculations` before triggering recalculations
- **Unit Formatting**: Use `format_unit_pretty()` from `utils/units.py` for consistent unit display
- **Dialog Routing**: `edit_header()` method routes to type-specific dialogs based on column type

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
    description="Difference between P1 and P2",
    propagate_uncertainty=True
)

# Via UI
# 1. Right-click header -> "Add Calculated Column..."
# 2. Enter formula: {P1} - {P2}
# 3. Check "Propagate uncertainty"
# 4. System auto-creates dP and dP_u columns
```

### Access Column Metadata
```python
metadata = table._columns[col_index]
print(f"Diminutive: {metadata.diminutive}")
print(f"Unit: {metadata.unit}")
print(f"Is calculated: {metadata.is_calculated_column()}")
```

### Manually Trigger Recalculation
```python
table._recalculate_all_calculated_columns()
```

### Add a Derivative Column and Use in Formula
```python
# Via code - complete example
# 1. Create range column for x
x_col = table.addRangeColumn(
    header_label="x",
    start=0.0,
    end=10.0,
    points=100,
    diminutive="x",
    unit=""
)

# 2. Create y = sin(x)
y_col = table.addCalculatedColumn(
    header_label="y",
    formula="sin({x})",
    diminutive="y",
    unit=""
)

# 3. Create derivative dy/dx
dydx_col = table.addDerivativeColumn(
    header_label="dydx",
    numerator_index=y_col,
    denominator_index=x_col,
    diminutive="dydx",
    unit=""
)

# 4. Use derivative in a formula
final_col = table.addCalculatedColumn(
    header_label="final",
    formula="{x}**2 + {dydx}**2",  # Derivative column in formula!
    diminutive="final",
    unit=""
)

# Force recalculation to populate all values
table._recalculate_all_calculated_columns()

# Via UI
# 1. Create columns using toolbar/context menu
# 2. Derivative columns appear in formula editor with [deriv] label
# 3. Double-click to insert into formula
```

---

## Resources

- **PySide6 Docs**: https://doc.qt.io/qtforpython-6/
- **SymPy Docs**: https://docs.sympy.org/
- **Pint Docs**: https://pint.readthedocs.io/
- **UV Package Manager**: https://docs.astral.sh/uv/

---

## Contact & Contribution

See `CONTRIBUTING.md` for contribution guidelines. Questions or issues? Open a GitHub issue or check existing discussions.
