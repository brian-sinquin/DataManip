# DataManip - Copilot Instructions

**Be concise. No verbose summaries. Track changes in todo list only.**

## Project

PySide6 data manipulation app for experimental sciences.

**Run**: `uv run datamanip`
**Test**: `uv run pytest tests/unit/widgets/data_table/`

## Project Structure (Updated 2025)

```
src/
├── config/              # Configuration management
│   ├── app_config.py    # Application settings
│   └── model_config.py  # DataTable model config
├── constants/           # Centralized constants
│   ├── column_types.py  # ColumnType enum
│   ├── data_types.py    # DataType enum
│   ├── symbols.py       # UI symbols (●, ƒ, ∂, etc.)
│   └── units.py         # Common physical units
├── models/              # Pure domain logic (future)
├── ui/                  # UI components
│   ├── main_window/
│   ├── about_window/
│   ├── preference_window/
│   └── notifications.py # User dialogs/messages
├── utils/               # Utilities
│   ├── base_dialogs.py  # Base dialog classes
│   ├── commands.py      # Command pattern for undo/redo
│   ├── delegates.py     # Qt table delegates
│   ├── exceptions.py    # Custom exceptions
│   ├── formula_parser.py
│   ├── qt_helpers.py    # QAction helpers
│   ├── uncertainty.py
│   └── validators.py    # Input validation
└── widgets/             # Reusable widgets
    ├── data_table/      # Main data table
    │   ├── column_dialogs.py
    │   ├── column_metadata.py
    │   ├── commands.py
    │   ├── context_menu.py
    │   ├── delegates.py
    │   ├── model.py
    │   ├── toolbar.py
    │   ├── variables_dialog.py
    │   └── view.py
    ├── plot_widget/
    └── statistics_widget/

tests/
├── unit/               # Unit tests
│   └── widgets/
│       └── data_table/
├── integration/        # Integration tests
└── fixtures/           # Test fixtures

examples/               # Usage examples
├── basic_usage.py
├── projectile_motion.py
└── custom_formulas.py
```

## Key Components

### DataTable (Primary Implementation)
- **Location**: `src/widgets/data_table/`
- **Model**: `model.py` - Pandas/NumPy backend, formulas, uncertainty propagation
- **View**: `view.py` - QTableView with `DataTableWidget` wrapper
- **Dialogs**: `column_dialogs.py` - All column creation/editing dialogs
- **Column Metadata**: `column_metadata.py` - `ColumnType`, `DataType`, `ColumnMetadata`
- **Toolbar**: `toolbar.py` - Dropdown menu for all column types
- **Context Menus**: `context_menu.py` - Header, cell, row, and empty table menus
- **Variables**: `variables_dialog.py` - Global constants for formulas (g, pi, etc.)
- **Commands**: `commands.py` - DataTable-specific command implementations (SetCellValue, Paste, Clear)
- **Delegates**: `delegates.py` - Factory for creating column-specific delegates
- **Tests**: `tests/unit/widgets/data_table/` - 343+ tests passing

### Reusable Utilities (Extracted from DataTable)
- **Exceptions** (`src/utils/exceptions.py`):
  - `DataManipError` - Base exception
  - `DataTableError`, `ColumnExistsError`, `ColumnNotFoundError`, `ColumnInUseError`
  - `ValidationError`, `InvalidNameError`, `InvalidValueError`
  
- **Commands** (`src/utils/commands.py`):
  - `Command` - Abstract base class for undo/redo
  - `CommandManager` - Manages undo/redo stacks
  - Use: Implement concrete commands in widget-specific modules
  
- **Delegates** (`src/utils/delegates.py`):
  - `NumericDelegate`, `IntegerDelegate`, `StringDelegate`, `BooleanDelegate`
  - Reusable across any Qt table widgets
  - Use: Import and customize for specific needs

- **Qt Helpers** (`src/utils/qt_helpers.py`):
  - `add_action()` - Simplified QAction creation
  - `add_actions()` - Batch action creation
  - Use: Reduce boilerplate in context menus

- **Base Dialogs** (`src/utils/base_dialogs.py`):
  - `ValidatedDialog` - Base class with validation UI pattern
  - `NameValidatedDialog` - Specialized for name validation
  - Use: Create dialogs with built-in validation feedback

**Column Metadata System** (`column_metadata.py`):
```python
@dataclass
class ColumnMetadata:
    name: str                              # Column name (display and formulas)
    column_type: ColumnType                # DATA, CALCULATED, DERIVATIVE, RANGE, INTERPOLATION, UNCERTAINTY
    dtype: DataType                        # FLOAT, INTEGER, STRING, CATEGORY, BOOLEAN
    unit: Optional[str]                    # Unit (e.g., "m", "s", "kg")
    description: Optional[str]             # Tooltip description
    
    # Formula properties
    formula: Optional[str]                 # Formula using {name} syntax
    propagate_uncertainty: bool            # Auto-calculate uncertainty
    
    # Derivative properties
    derivative_numerator: Optional[str]    # Numerator column name (dy)
    derivative_denominator: Optional[str]  # Denominator column name (dx)
    
    # Range properties
    range_start: Optional[float]           # Start value
    range_end: Optional[float]             # End value
    range_points: Optional[int]            # Number of points
    
    # Interpolation properties
    interp_x_column: Optional[str]         # X data column name
    interp_y_column: Optional[str]         # Y data column name
    interp_method: Optional[str]           # Method: 'linear', 'cubic', etc.
    
    # Uncertainty properties
    uncertainty_reference: Optional[str]   # Column name this uncertainty belongs to
    
    # Display properties
    precision: int                         # Decimal places for display
    editable: bool                         # Calculated in __post_init__
```

**Column Type Symbols**:
- `●` DATA - User-editable data
- `ƒ` CALCULATED - Formula-based
- `∂` DERIVATIVE - Discrete dy/dx
- `▬` RANGE - Evenly spaced
- `⌇` INTERPOLATION - Interpolated values
- `σ` UNCERTAINTY - Error/uncertainty

**Formula System**:
- Reference columns: `{name}` syntax (e.g., `{x}`, `{velocity}`)
- Operators: `+`, `-`, `*`, `/`, `**` (power)
- Functions: `abs`, `sqrt`, `sin`, `cos`, `tan`, `log`, `log10`, `exp`, `asin`, `acos`, `atan`
- Constants: Defined in Variables dialog (e.g., `g`, `pi`, `e`)
- Unit propagation: Automatic via Pint library

**Uncertainty Propagation**:
- Formula: δf = √(Σ(∂f/∂xᵢ · δxᵢ)²)
- SymPy for symbolic differentiation
- Auto-creates `{name}_u` columns (read-only)
- Recalculates on data/uncertainty changes
- Manual uncertainty columns also supported

**Derivative Columns**:
- Discrete differences: dy/dx ≈ Δy/Δx
- Can be used in formulas: `{dydx}`, `{velocity}`, etc.
- Units propagate correctly (e.g., m/s from m and s)
- Example: velocity (dx/dt), acceleration (dv/dt)

**Range Columns**:
- Evenly spaced values from start to end
- Specified by: start, end, number of points
- Useful for time series, independent variables
- Example: t = [0, 0.1, 0.2, ..., 3.0] (31 points)

**Interpolation Columns**:
- Interpolate Y values at new X points
- Methods: linear, cubic, quadratic
- Requires: X data, Y data, target X column
- Automatically updates when data changes

### UI Components

**MainWindow** (`src/ui/main_window/`):
- `main_window.py` - Main application window
- `menu_bar.py` - File, Edit, View, Help menus
- `workspace.py` - Tab widget with Data, Plot, Statistics tabs

**Workspace Layout**:
1. **Data Table Tab**: DataTableWidget with toolbar
2. **Plotting Tab**: Plot widget (scatter plots, uncertainty bars)
3. **Statistics Tab**: Statistics widget (descriptive stats, histograms)

**Example Data** (`src/utils/example_data.py`):
- `load_projectile_motion()` - Baseball trajectory (default on startup)
- `load_ideal_gas()` - PV=nRT gas law calculations
- `load_harmonic_oscillator()` - Mass-spring system
- `load_rc_circuit()` - Capacitor charging

### Configuration & Language Management

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
- **Classes**: `PascalCase` (e.g., `DataTableWidget`, `ColumnMetadata`)
- **Functions/Methods**: `snake_case` (e.g., `add_column`, `_recalculate_column`)
- **Private Methods**: Prefix with `_` (e.g., `_on_item_changed`, `_update_header`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_PRECISION`, `ERROR_PREFIX`)
- **Type Hints**: Always use for parameters and return values
- **Docstrings**: Google style

### Docstring Format
Use Google-style docstrings:
```python
def add_data_column(self, name: str, dtype: DataType = DataType.FLOAT,
                   unit: Optional[str] = None, description: Optional[str] = None,
                   data: Optional[pd.Series] = None) -> None:
    """Add a new data column to the table.
    
    Args:
        name: Column name (used for display and formulas)
        dtype: Data type (FLOAT, INTEGER, STRING, etc.)
        unit: Optional unit of measurement
        description: Full description shown as tooltip
        data: Optional initial data (Pandas Series)
        
    Raises:
        ColumnExistsError: If column name already exists
    """
```

## Running & Testing

```bash
uv sync              # Install dependencies
uv run datamanip     # Run application
uv run pytest tests/widgets/DataTable/  # Run tests (351 tests)
```

### Common Pitfalls
1. **Column Name Uniqueness**: Always validate that column names are unique before adding columns.
2. **Unit Compatibility**: Pint raises errors for incompatible unit operations (e.g., `m + kg`). Catch these and show user-friendly errors.
3. **SymPy Conversion**: Not all Python expressions convert cleanly to SymPy. Test edge cases.
4. **Dependency Management**: When deleting columns, check for dependents first to avoid breaking formulas.
5. **Data Type Consistency**: Ensure data matches column's declared DataType (FLOAT, INTEGER, etc.).

---

## Debugging Tips

### Enable Qt Debug Output
```bash
# Set environment variable for detailed Qt warnings
set QT_LOGGING_RULES="qt.*=true"
uv run datamanip
```

### Common Debugging Scenarios
- **Formula Errors**: Check `formula_parser.py` - errors are caught and raised as `FormulaError`, `FormulaSyntaxError`, or `FormulaEvaluationError`
- **Uncertainty Issues**: Add logging in `utils/uncertainty.py` to trace partial derivative calculations
- **UI Not Updating**: Check model signals (`dataChanged`, `headerDataChanged`) are emitted properly
- **Column Operations Failing**: Verify dependencies are resolved correctly in `model.py`'s dependency graph

---

## Future Development Areas

### Planned Features (Check TODO.md)
- Additional physics examples (free fall with air resistance, damped oscillator, etc.)
- Multi-series plotting with curve fitting overlay
- Advanced statistics (correlation analysis, regression, normality tests)
- Expanded unit test coverage to 500+ tests
- CI/CD pipeline (GitHub Actions)
- Performance profiling for large datasets (10k+ rows)

### Known Limitations
- Translation updates for DataTable not complete (low priority)
- Better new row injection UX needed
- Some unit printing issues remain
- Uncertainty propagation assumes independent variables (no covariance)

---

## Quick Reference

### Add a Data Column
```python
# Via code (using model directly)
model.add_data_column(
    name="Temperature",
    dtype=DataType.FLOAT,
    unit="°C",
    description="Sample temperature",
    data=pd.Series([20.0, 25.0, 30.0])
)

# Via UI
# Click "Add Column" → "Data Column..." in toolbar
# Fill in the dialog with column properties
```

### Add a Range Column (Evenly Spaced Values)
```python
# Via code
model.add_range_column(
    name="Time",
    start=0.0,
    end=10.0,
    points=11,  # Creates 11 points from 0 to 10 (step = 1.0)
    unit="s",
    description="Time values"
)

# Via UI
# Click "Add Column" → "Range Column..." in toolbar
# Enter start, end, number of points, and column properties
```

### Add a Calculated Column with Uncertainty
```python
# Via code
model.add_calculated_column(
    name="Pressure_Difference",
    formula="{P1} - {P2}",
    unit="kPa",
    propagate_uncertainty=True  # Auto-creates Pressure_Difference_u column
)

# Via UI
# Click "Add Column" → "Calculated Column..." in toolbar
# Enter formula using {column_name} syntax
# Check "Propagate uncertainty" to auto-create uncertainty column
```

### Add a Derivative Column
```python
# Via code
model.add_derivative_column(
    name="velocity",
    numerator="position",  # dy column
    denominator="time",    # dx column
    description="Velocity = dp/dt"
)

# Via UI
# Click "Add Column" → "Derivative Column..." in toolbar
# Select numerator (dy) and denominator (dx) columns
```

### Add an Interpolation Column
```python
# Via code
model.add_interpolation_column(
    name="y_interp",
    x_data_column="x_data",
    y_data_column="y_data",
    x_target_column="x_new",
    method="cubic",  # 'linear', 'cubic', 'quadratic'
    description="Interpolated Y values at new X points"
)

# Via UI
# Click "Add Column" → "Interpolation Column..." in toolbar
# Select X data, Y data, target X column, and method
```

### Working with Variables
```python
# Via code
model.set_variables({
    'g': 9.81,  # Gravity (m/s²)
    'pi': 3.14159265359,
    'c': 299792458  # Speed of light (m/s)
})

# Use in formulas: {x} * g or 2 * pi * {r}

# Via UI
# Click "Variables..." button in toolbar
# Add/edit/remove global constants
```

### File I/O
```python
# Save to JSON
model.save_to_file("experiment_data.json")

# Load from JSON
model.load_from_file("experiment_data.json")

# Export to CSV (data only, no metadata)
model.export_to_csv("data.csv")

# Via UI
# File menu → Save / Open
```

### Undo/Redo
```python
# Via code
model.undo()
model.redo()

# Via UI
# Edit menu → Undo (Ctrl+Z) / Redo (Ctrl+Y)
# Or keyboard shortcuts
```
