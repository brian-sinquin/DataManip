# DataManip - Copilot Instructions

**Be concise. No verbose summaries. Track progress in TODO.md only.**

## Project Overview

PySide6 data manipulation app for experimental sciences (v0.2.0).

**Stack**: Python 3.12+, PySide6, pandas, numpy, matplotlib, sympy, pint
**Package Manager**: uv (NOT pip or conda)
**Architecture**: Core (Qt-independent) → Studies → UI widgets
**Test Count**: 300 unit tests (99%+ passing)

## Quick Commands

```bash
uv run datamanip                      # Launch app
uv run pytest tests/unit/ -v         # All tests
uv run pytest tests/unit/core/ -v    # Core layer only
uv run pytest tests/unit/studies/ -v # Studies layer only
uv run pytest tests/unit/ui/ -v      # UI layer only
uv run pytest --cov=src --cov-report=html  # Coverage
```

**Terminal**: PowerShell only. Always close with `exit` command.

## Architecture (3-Layer Design)

### Core Layer (Qt-independent, reusable)
- **DataObject**: pandas DataFrame wrapper with metadata
- **FormulaEngine**: Evaluates formulas (scalar/array), handles units (pint), uncertainty propagation (sympy), workspace constants caching
- **Workspace**: Container for studies + workspace-level constants
- **UndoManager**: Stack-based (50 max), supports column operations
- **Study (ABC)**: Base class for all study types

### Studies Layer (Business logic)
- **DataTableStudy**: 5 column types (data, calculated, derivative, range, uncertainty), formula evaluation, dependency tracking, parallel execution
- **PlotStudy**: Matplotlib plots, multiple series
- **StatisticsStudy**: Histogram, box plot, descriptive stats

### UI Layer (PySide6 widgets)
- **MainWindow**: Tab-based workspace with menu bar
- **DataTableWidget**: Table view with editable headers, context menus, keyboard shortcuts (8 modular files in `data_table/`)
- **ConstantsWidget**: 3 constant types (numeric, calculated, function), tab non-closable
- **PlotWidget**: Matplotlib canvas + toolbar
- **StatisticsWidget**: Dual visualizations (histogram + box plot)
- **Dialogs**: BaseDialog/BaseColumnDialog base classes, 7+ specialized dialogs

## MCP Tool Usage

**ALWAYS use these tools when available:**
- **Context7**: Generate code from up-to-date library docs (resolve-library-id first)
- **Pylance**: Syntax checking, refactoring (unused imports, import format), workspace analysis
- **Playwright**: Web automation (if needed for testing/scraping)
- **Memory**: Knowledge graph for project insights (if complex architecture questions arise)
- **MarkItDown**: Convert files/URLs to markdown

**Example workflow:**
1. Use Context7 for PySide6/pandas/matplotlib code generation
2. Use Pylance to check syntax before running
3. Run tests to verify changes

## Coding Standards

### Python Style (PEP 8 + Project-Specific)
- **Python Version**: 3.12+ (use modern features: match/case, type hints, dataclasses)
- **Type Hints**: Required for all function signatures
- **Docstrings**: Google-style for classes/methods ("""Brief. Extended description.""")
- **Imports**: Absolute imports preferred, group by stdlib/third-party/local
- **Line Length**: 100 chars (not 80)
- **Constants**: ALL_CAPS in `constants.py`, grouped by category

### Architecture Patterns
- **MVC**: Separate Model (DataTableModel) from View (QTableView) from Controller (DataTableWidget)
- **Separation of Concerns**: Core layer NEVER imports PySide6/UI code
- **Signal-Slot**: Use PySide6 signals for UI interactions (e.g., `constantsChanged = Signal()`)
- **Composition over Inheritance**: Prefer small, focused classes
- **Avoid Wrappers**: Refactor for clarity instead of wrapping existing code

### File Organization
- **Max File Size**: ~400 lines (split if larger, see data_table/ modular structure)
- **Module Structure**: `__init__.py` exports main classes only
- **Test Correspondence**: Each `src/X/Y.py` has `tests/unit/X/test_Y.py`

### Naming Conventions
- **Classes**: PascalCase (`DataTableStudy`, `FormulaEngine`)
- **Functions/Variables**: snake_case (`add_column`, `column_metadata`)
- **Constants**: ALL_CAPS (`DISPLAY_PRECISION`, `COLUMN_SYMBOLS`)
- **Private**: Single underscore (`_setup_ui`, `_validate_input`)
- **Qt Slots**: Use `@Slot()` decorator explicitly

## Testing Strategy

### Test Structure (300 tests across 3 layers)
```
tests/unit/
├── core/         # 87 tests - DataObject, FormulaEngine, Workspace, UndoManager, persistence
├── studies/      # 92 tests - DataTableStudy, PlotStudy, StatisticsStudy
└── ui/           # 61 tests - Preferences, notifications, plot export
```

### When to Write Tests
- **ALWAYS** write tests for new features/refactoring before implementation
- **Test-First**: Create `test_X.py` to guide development (helps debug)
- **Coverage Goal**: 95%+ for core/studies, 80%+ for UI

### Test Best Practices
- **Fixtures**: Use pytest fixtures in `conftest.py` (e.g., `sample_study`)
- **Isolation**: Each test resets state (no shared mutable data)
- **Naming**: `test_<function>_<scenario>_<expected>` (e.g., `test_add_column_invalid_name_raises_error`)
- **Assertions**: Use pytest assertions (`assert x == y`, not `self.assertEqual`)

## Key Implementation Details

### Display Precision
- **DISPLAY_PRECISION = 3**: Shown in cells (DisplayRole)
- **Full Precision**: Stored internally, returned in EditRole (33 significant digits)

### Column Types (5 types in DataTableStudy)
```python
ColumnType.DATA           # ✎ Editable by user
ColumnType.CALCULATED     # ƒ Formula-based (e.g., {A} + {B})
ColumnType.DERIVATIVE     # d/dx Numerical differentiation
ColumnType.RANGE          # ⋯ Generated ranges (start, stop, step)
ColumnType.UNCERTAINTY    # δ Propagated errors
```

### Formula Syntax
- **Variables**: `{column_name}` for columns, constants by name
- **Operations**: Standard math (`+`, `-`, `*`, `/`, `**`)
- **Functions**: NumPy functions (`np.sin`, `np.exp`), workspace custom functions
- **Units**: Automatic tracking via pint (`{distance} / {time}` preserves units)

### Performance Optimizations (3x speedup achieved)
- **Lazy Evaluation**: Dirty flag tracking, only recalc changed columns
- **Caching**: Compiled formulas + workspace constants (version tracking)
- **Batch Operations**: `add_columns_batch()` for multi-column adds
- **Parallelization**: ThreadPoolExecutor for independent columns

### Undo/Redo System
- **Supported Operations**: remove_column, rename_column, add_column
- **Stack Size**: 50 actions (configurable)
- **Shortcuts**: Ctrl+Z (undo), Ctrl+Y (redo)
- **Tooltips**: Show action descriptions ("Undo: Remove column 'x'")

## File I/O & Persistence

### Workspace Save/Load (Atomic writes)
```python
workspace.save(filepath)  # JSON with temp file + backup
workspace.load(filepath)  # Full roundtrip with numpy/pandas conversion
```
- **Format**: JSON (human-readable)
- **Safety**: Temp file → rename, backup on error
- **Coverage**: All studies (data table, plot, statistics), constants

## Common Tasks

### Add New Column Type
1. Add to `ColumnType` enum in `data_table_study.py`
2. Update `add_column()` logic
3. Add symbol to `COLUMN_SYMBOLS` in `constants.py`
4. Create dialog in `column_dialogs.py` (inherit from `BaseColumnDialog`)
5. Wire up in `DataTableWidget.column_edit.py`
6. Write 5+ tests in `tests/unit/studies/test_data_table_study.py`

### Add New Study Type
1. Create `src/studies/new_study.py` inheriting from `Study`
2. Implement `to_dict()` / `from_dict()` for persistence
3. Create widget in `src/ui/widgets/new_widget.py`
4. Add menu item in `main_window.py` (`_setup_menu()`)
5. Write 10+ tests in `tests/unit/studies/test_new_study.py`

### Refactor Large File
1. Identify logical components (e.g., model, view, controller, shortcuts)
2. Create subfolder (e.g., `data_table/`)
3. Split into ~150-line files (e.g., `model.py`, `widget.py`, `shortcuts.py`)
4. Update `__init__.py` to export main classes
5. Run tests to ensure no regressions

## Project Management

### Documentation Files
- **TODO.md**: Short-term priorities, current sprint, test status (UPDATE THIS)
- **PROJECT.md**: Architecture, features, long-term roadmap (reference only)
- **CONTRIBUTING.md**: Contributor guidelines (reference only)

### Development Workflow
1. Check TODO.md for current priorities
2. Create feature branch (`git checkout -b feature/X`)
3. Write tests first (test-driven development)
4. Implement feature (use Context7 for library-specific code)
5. Run tests (`uv run pytest tests/unit/ -v`)
6. Update TODO.md with progress
7. Commit with clear messages
8. PR with description + linked issues

### Never Do This
- ❌ Track development in copilot-instructions.md (use TODO.md)
- ❌ Create markdown summaries unless explicitly requested
- ❌ Use pip/conda (use uv only)
- ❌ Import PySide6 in core/ layer
- ❌ Create 1000+ line files (split into modules)
- ❌ Skip tests for new features
- ❌ Use verbose summaries (be concise)

## Project Philosophy

1. **Clarity First**: Readable code > clever code
2. **Modularity**: Small, focused classes/functions
3. **Testability**: Core layer has no Qt dependencies → easy to test
4. **Performance**: Optimize after profiling (don't premature optimize)
5. **User Experience**: Responsive UI, helpful error messages, keyboard shortcuts
6. **Maintainability**: Consistent patterns, clear separation of concerns