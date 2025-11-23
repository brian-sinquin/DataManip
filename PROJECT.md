# DataManip - Project Documentation

**Version**: 0.2.0  
**Status**: Active Development  
**Last Updated**: November 23, 2025

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Completed Features](#completed-features)
3. [Current Status](#current-status)
4. [Known Issues](#known-issues)
5. [Testing](#testing)
6. [Development Roadmap](#development-roadmap)
7. [Running & Building](#running--building)

---

## Architecture Overview

### Design Principles

**Core Principle**: Single DataObject abstraction across all workspace types
- Use pandas DataFrame as universal data representation
- Unified formula engine for scalars, arrays, and tables
- Unit-aware calculations with uncertainty propagation
- Workspace → Studies → DataObjects hierarchy

### Layer Architecture

```
┌─────────────────────────────────────────────────┐
│              Application Layer                   │
│  (main.py, MainWindow, WorkspaceTabs)           │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│               UI Layer                           │
│  (DataTableWidget, ConstantsWidget, etc.)       │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│             Studies Layer                        │
│  (DataTableStudy, VisualizationStudy, etc.)     │
│  - Business logic for each study type           │
│  - Column metadata & formulas                   │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│              Core Layer                          │
│  (DataObject, FormulaEngine, Study, Workspace)  │
│  - Qt-independent                               │
│  - Pure Python + pandas/numpy                   │
└─────────────────────────────────────────────────┘
```

### Module Structure

```
src/
├── core/                    # Qt-independent core (4 files)
│   ├── data_object.py      # Universal data container
│   ├── formula_engine.py   # Unified formula evaluation
│   ├── study.py           # Abstract base for study types
│   └── workspace.py       # Container for studies + constants
├── studies/                 # Study implementations (1 file)
│   └── data_table_study.py # DataTable with 4 column types
├── ui/                      # User interface
│   ├── main_window.py      # Main application window
│   └── widgets/            # UI widgets (8 files)
│       ├── data_table_widget.py
│       ├── constants_widget.py
│       ├── column_dialogs.py
│       └── dialog_utils.py
└── main.py                 # Entry point

examples/                    # Working examples (5 files)
tests/unit/                  # Unit tests (40 tests passing)
```

**Statistics**: 
- **13 core Python files** (down from 62 in legacy)
- **5x code reduction** through clean architecture
- **97 unit tests** (all passing)

---

## Completed Features

### ✅ Core Architecture (100%)

**DataObject** - Universal container:
```python
obj = DataObject.from_dict("data", {"x": [1,2,3], "y": [4,5,6]})
obj.add_column("z", [7,8,9])
obj["z"]  # Access like dictionary
```

**FormulaEngine** - Smart evaluation with dependency tracking:
```python
engine = FormulaEngine()
engine.register_formula("velocity", "{position} / {time}")
engine.register_formula("energy", "0.5 * {mass} * {velocity}**2")
order = engine.get_calculation_order(["position"])  # ["velocity", "energy"]
```

**Features**:
- ✅ DataObject creation (dict, array, empty)
- ✅ Column operations (get, set, add, remove)
- ✅ Formula evaluation (scalar, array, mixed)
- ✅ Dependency tracking with topological sort
- ✅ Circular dependency detection
- ✅ Scalar broadcasting in formulas
- ✅ Serialization (to_dict/from_dict)

### ✅ DataTableStudy (100%)

```python
study = DataTableStudy("Physics Experiment")
study.add_column("time", unit="s")
study.add_column("position", unit="m") 
study.add_column("velocity", ColumnType.CALCULATED, formula="d({position})/d({time})", unit="m/s")
study.add_variable("g", 9.81, "m/s^2")
```

**4 Column Types**:

1. **DATA** - Manual entry (editable cells)
   - Direct user input
   - CSV import
   - Copy/paste operations

2. **CALCULATED** - Formula-based (read-only)
   - Uses {variable} syntax
   - Auto-recalculates on dependencies
   - Supports numpy functions (sin, cos, sqrt, exp, log, etc.)

3. **DERIVATIVE** - Numerical differentiation (read-only)
   - First order: dy/dx
   - Second order: d²y/dx²
   - Nth order supported
   - Uses numpy.gradient (centered differences)

4. **RANGE** - Generated sequences (read-only)
   - `linspace(start, stop, num)` - evenly spaced
   - `arange(start, stop, step)` - fixed step
   - `logspace(start, stop, num)` - logarithmic scale

**Features**:
- ✅ Add/remove rows and columns
- ✅ Formula validation and editing
- ✅ Automatic recalculation on data changes
- ✅ Unit tracking (ready for Pint integration)
- ✅ Column metadata (name, type, formula, unit)

### ✅ Enhanced Constants System (NEW)

**Three Types**:

1. **Numeric Constants** - Simple values
   ```python
   workspace.add_constant("g", 9.81, "m/s^2")
   workspace.add_constant("pi", 3.14159, None)
   ```

2. **Calculated Variables** - Formula-based
   ```python
   workspace.add_calculated_variable("v", "sqrt(2*{g}*{h})", "m/s")
   ```

3. **Custom Functions** - Parameterized
   ```python
   workspace.add_function("distance", "{x}^2 + {y}^2", ["x", "y"], "m")
   ```

**UI Features**:
- ✅ `ConstantsWidget` with 5-column table
- ✅ `AddConstantDialog` for all 3 types
- ✅ Edit, remove, clear operations
- ✅ Quick add common constants (g, pi, e, c, h, k_B)
- ✅ Tab renamed to "Constants & Functions"

### ✅ UI Layer (95%)

**Main Window**:
- ✅ Single workspace with study tabs (no nested tabs)
- ✅ Menu bar (File, Edit, Help)
- ✅ Keyboard shortcuts (Ctrl+N, Ctrl+Q)
- ✅ Study management (new, close, rename)
- ✅ Dedicated "Constants & Functions" tab

**DataTable Widget**:
- ✅ Inline cell editing (DATA columns)
- ✅ Enhanced toolbar with all column types
- ✅ Context menu (right-click operations)
- ✅ Visual column differentiation (header symbols):
  - ✎ DATA columns (editable)
  - ƒ CALCULATED columns
  - d/dx DERIVATIVE columns
  - ⋯ RANGE columns

**Dialogs**:
- ✅ AddDataColumnDialog
- ✅ AddCalculatedColumnDialog (with formula editor)
- ✅ AddDerivativeColumnDialog (with order selection)
- ✅ AddRangeColumnDialog (linspace/arange/logspace)
- ✅ AddConstantDialog (3 types: constant/calculated/function)
- ✅ All dialogs have help text and validation

**Code Quality**:
- ✅ Utility modules: `dialog_utils.py`, `model_utils.py`
- ✅ Reduced 29 QMessageBox duplication patterns
- ✅ Centralized dialogs: `show_warning`, `show_info`, `confirm_action`

### ✅ Examples (100%)

**5 Working Examples**:

1. **core_api_example.py** - Basic API demonstration
2. **basic_usage.py** - Simple table with formulas
3. **projectile_motion.py** - Physics with derivatives
4. **custom_formulas.py** - Mathematical functions
5. **complete_workflow.py** - Damped oscillator (ranges + calculations + derivatives)

All examples updated to new architecture and tested.

---

## Current Status

### What Works ✅

- ✅ Create/edit data tables with inline editing
- ✅ Add data columns (manual entry)
- ✅ Add calculated columns with formulas
- ✅ Add derivative columns (numerical differentiation)
- ✅ Add range columns (linspace/arange/logspace)
- ✅ Define workspace-level constants (3 types)
- ✅ Formula evaluation with {variable} syntax
- ✅ Automatic recalculation on changes
- ✅ Dependency tracking and calculation order
- ✅ Circular dependency detection
- ✅ Unit tracking across columns
- ✅ Visual column type differentiation
- ✅ Study tabs with management
- ✅ Context menus for operations
- ✅ All 40 unit tests passing

### Recent Achievements (Nov 23, 2025)

- ✅ **Enhanced Constants System** - 3 types (constants, calculated, functions)
- ✅ **New ConstantsWidget** - Rich UI with AddConstantDialog
- ✅ **Code Quality** - Utility modules reducing duplication
- ✅ **Bug Fixes** - Derivative dialog combo boxes
- ✅ **Examples Updated** - All working with new architecture

---

## Known Issues

### Critical Bugs 🔴
- [x] Recalculation works automatically (verified) ✅
- [x] Derivative columns work correctly (verified) ✅
- [x] Uncertainty propagation implemented ✅

### Feature Gaps 🟡
- [ ] No keyboard shortcuts for table operations (partially done: Ctrl+R/D/F/V)
- [ ] No undo/redo functionality
- [ ] Unit printing has formatting issues

### Architecture Cleanup 🟢
- [ ] Migrate or delete 407 legacy tests (tests/_legacy/)
- [ ] Complete PySide6 type stub installation
- [ ] Translation updates for snake_case modules
- [ ] Complete translation coverage for dialogs

---

## Testing

### Current Coverage

**88/88 Unit Tests Passing** (100% success rate) ✅

**Core Layer** (53 tests - ALL PASSING ✅):
- `test_data_object.py` - 8 tests ✅
  - Creation (dict, array, empty)
  - Operations (get, set, add, remove)
  - Serialization
  
- `test_formula_engine.py` - 17 tests ✅
  - Dependency extraction
  - Formula evaluation (scalar, array, mixed)
  - Dependency tracking and calculation order
  - Circular dependency detection
  - Formula validation

- `test_workspace.py` - 28 tests ✅ (NEW!)
  - Workspace creation and repr
  - Study management (add, remove, get, list)
  - Constants system (3 types: constant, calculated, function)
  - Serialization (to_dict, from_dict, roundtrip)
  - Legacy variables compatibility

**Studies Layer** (35 tests - ALL PASSING ✅):
- `test_derivatives.py` - 6 tests ✅
  - First/second order derivatives
  - Sine wave differentiation
  - Recalculation on data changes
  - Velocity from position
  
- `test_ranges.py` - 9 tests ✅
  - linspace, arange, logspace
  - Table size management
  - Multiple range columns
  - Metadata preservation
  - Time series generation

- `test_data_table_study.py` - 20 tests ✅
  - Study creation and type
  - Column management (add, remove, metadata)
  - Row management (add, remove)
  - Data manipulation
  - Variables system
  - Serialization
  - Column types

### Test Summary

**Working Tests**: 88/88 (100%) ✅
- Core layer: 53/53 (100%) ✅
- Studies layer: 35/35 (100%) ✅

**Coverage**:
- ✅ Core architecture fully tested
- ✅ Studies layer fully tested
- ⏸️ UI widget tests (future)
- ⏸️ Integration tests (future)

**Achievement**: All implemented functionality is tested and passing!

### Test Execution

```bash
# Run all tests
uv run pytest tests/unit/ -v

# Run specific test file
uv run pytest tests/unit/core/test_formula_engine.py -v

# Run with coverage
uv run pytest tests/unit/ --cov=src --cov-report=html
```

### Coverage Gaps (To Be Added)

**Missing Test Files**:
- [ ] `test_workspace.py` - Workspace operations and constants system
- [ ] `test_data_table_study.py` - Study-level operations
- [ ] `test_column_metadata.py` - Column metadata management
- [ ] `test_variables.py` - Variable management and synchronization
- [ ] UI widget tests (integration level)

**Target**: 100+ tests covering all core functionality

---

## Development Roadmap

### Phase 1: Core Features ✅ COMPLETE
- [x] DataObject, FormulaEngine, Study, Workspace
- [x] DataTableStudy with 4 column types
- [x] UI with inline editing
- [x] Enhanced constants system
- [x] 40 unit tests passing
- [x] 5 working examples

### Phase 2: File I/O & Persistence 🔄 IN PROGRESS
- [ ] Save/load workspaces (JSON format)
- [ ] Export to CSV/Excel
- [ ] Import from CSV/Excel
- [ ] Auto-save and recovery
- [ ] Recent files list

### Phase 3: Advanced Features 📋 PLANNED
- [ ] Interpolation columns (linear, cubic spline)
- [ ] Uncertainty columns (error propagation)
- [ ] Pint integration (unit-aware calculations)
- [ ] Undo/redo system (command pattern)
- [ ] Keyboard shortcuts for all operations

### Phase 4: Visualization 📋 PLANNED
- [ ] Plotting study (multi-series plots)
- [ ] Curve fitting (linear, polynomial, exponential)
- [ ] Export plots (PNG/SVG)
- [ ] Plot styling and customization

### Phase 5: Statistics 📋 PLANNED
- [ ] Statistics study (descriptive stats)
- [ ] Correlation analysis
- [ ] Regression analysis
- [ ] Hypothesis testing
- [ ] Export statistics reports

### Phase 6: Polish & Distribution 📋 FUTURE
- [ ] Complete unit/integration tests (200+ tests)
- [ ] User documentation
- [ ] Performance optimization (10k+ rows)
- [ ] Portable executables (PyInstaller)
- [ ] Package distribution (pip, conda)

### Long-Term Vision 🌟
- Plugin system for custom column types
- Multi-table support (relationships)
- Database connectivity (SQLite, PostgreSQL)
- Real-time data streaming
- Collaborative editing
- Web version (PyScript/WASM)
- GPU acceleration for large computations

---

## Running & Building

### Development

```bash
# Install dependencies
uv sync

# Run application
uv run datamanip

# Run tests
uv run pytest tests/unit/ -v

# Run specific example
uv run python examples/projectile_motion.py

# Run with hot reload
uv run python src/main.py
```

### Project Structure

```
DataManip/
├── src/                    # Source code
│   ├── core/              # Core layer (Qt-independent)
│   ├── studies/           # Study implementations
│   ├── ui/                # UI layer (PySide6)
│   └── main.py           # Entry point
├── tests/                 # Tests
│   ├── unit/             # Unit tests (40 passing)
│   └── _legacy/          # Archived tests (407 old)
├── examples/             # Working examples (5 files)
├── assets/               # Icons, translations
├── pyproject.toml        # Project configuration
├── PROJECT.md            # This file
└── README.md             # User-facing readme
```

### Dependencies

**Core**:
- Python 3.10+
- PySide6 6.10.0 (Qt for UI)
- pandas 2.3.3 (data structures)
- numpy 2.3.4 (numerical operations)

**Future**:
- pint (unit-aware calculations)
- scipy (interpolation, statistics)
- matplotlib (plotting backend)

### Commands

```bash
# Development
uv run datamanip              # Launch app
uv run pytest tests/unit/ -v  # Run tests
uv run python examples/*.py   # Run examples

# Testing
uv run pytest --cov=src       # Coverage report
uv run pytest -k test_name    # Run specific test
uv run pytest -x              # Stop on first failure

# Code Quality
uv run ruff check src/        # Linting
uv run mypy src/              # Type checking
uv run black src/             # Formatting
```

---

## Key Improvements Over Legacy

1. **Unified Data Model** - Single DataObject vs. multiple specialized containers
2. **Cleaner Separation** - Core logic fully Qt-independent
3. **Simpler Formula Engine** - 150 lines vs. 350+ in old code
4. **Better Testing** - 40 comprehensive unit tests (all passing)
5. **Flexibility** - Easy to add new study types and column types
6. **Less Boilerplate** - No circular imports, cleaner modules
7. **Code Quality** - Utility modules reducing duplication by 29 patterns
8. **Enhanced Constants** - 3 types (constants, calculated, functions)
9. **Better UX** - Fixed dialogs, improved visual differentiation
10. **5x Code Reduction** - 62 files → 13 files

---

## Contributing

See `CONTRIBUTING.md` for development guidelines.

**Philosophy**:
- Prioritize code clarity and maintainability
- Optimize for performance without sacrificing readability
- Ensure modularity and separation of concerns
- Focus on user experience and responsiveness

**Branch**: `release-v0.2.0` (active development)

---

**Last Updated**: November 23, 2025  
**Maintained By**: Brian Sinquin
