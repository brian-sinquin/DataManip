# DataManip - Project Status

**Version**: 0.2.0 (Active Development)  
**Last Updated**: November 23, 2025

For complete project documentation, architecture, and testing details, see [PROJECT.md](PROJECT.md).

---

## Recent Achievements (November 2025) ✅

### Fresh Rebase - New Architecture
- [x] **Core Architecture** - Qt-independent DataObject + FormulaEngine
- [x] **Studies Pattern** - DataTableStudy with 4 column types (DATA, CALCULATED, DERIVATIVE, RANGE)
- [x] **Workspace-level Constants** - 3 types (numeric, calculated, functions)
- [x] **85/85 Unit Tests Passing (100%)** - Core (51) + Studies (34)
- [x] **UI Redesign** - Single workspace with study tabs + dedicated Constants tab
- [x] **Constants Migration** - Consolidated workspace.variables → workspace.constants
- [x] **Visual Column Differentiation** - Header symbols for each column type
- [x] **Type Safety** - All PySide6 type errors suppressed
- [x] **Legacy Tests Archived** - Moved to tests/_legacy/ (407 old tests)

### Code Quality Improvements (Nov 23, 2025)
- [x] **Utility Modules** - Created dialog_utils.py and model_utils.py
- [x] **Reduced Duplication** - Centralized 29 QMessageBox patterns
- [x] **Enhanced Constants System** - 3 types (constants, calculated, functions)
- [x] **New UI** - ConstantsWidget with AddConstantDialog
- [x] **Comprehensive Tests** - Added test_workspace.py (28 tests) and test_data_table_study.py (34 tests)
- [x] **Project Documentation** - Unified REBASE docs into PROJECT.md

### Working Features
- [x] **5 Column Types** - DATA, CALCULATED, DERIVATIVE, RANGE, UNCERTAINTY fully implemented
- [x] **Uncertainty Propagation** - Symbolic differentiation using SymPy (δf = √(Σ(∂f/∂xᵢ · δxᵢ)²))
- [x] **Formula Engine** - Dependency tracking, scalar broadcasting, unit-aware
- [x] **Constants System** - 3 types with workspace-level sharing
- [x] **5 Working Examples** - Demonstrating all features

---

## Current Issues

### Known Bugs 🔴
- [x] Recalculation works automatically (on_data_changed called by UI) ✅
- [x] Derivative columns work correctly (np.gradient returns full length) ✅
- [x] Uncertainty propagation implemented ✅

### Testing Status ✅
- [x] Core tests complete (51/51 passing) ✅
- [x] Studies tests complete (46/46 passing) ✅
- [x] 100% pass rate achieved (97/97) ✅
- [x] Uncertainty propagation tested (12 tests) ✅
- [ ] UI widget tests (future)
- [ ] Integration tests (future)

### Architecture Cleanup 🟢
- [x] Core layer fully tested ✅
- [x] Documentation unified into PROJECT.md ✅
- [ ] Migrate or delete 407 legacy tests
- [ ] Complete PySide6 type stub installation

---

## Short-Term Priorities

### Phase 1: Testing (COMPLETE ✅)
- [x] Add workspace tests (28 tests) ✅
- [x] Add DataTableStudy tests (20 tests) ✅
- [x] 85/85 tests passing (100% pass rate) ✅
- [x] Constants migration (workspace.variables → workspace.constants) ✅
- [ ] Add UI widget tests (future integration level)
- [ ] Add end-to-end workflow tests (future)

### Phase 2: File I/O & Missing Legacy Features (IN PROGRESS 🟡)
- [x] Save/load workspaces (JSON format)
- [ ] **Export to CSV** - High priority, ~3 hours
- [ ] **Export to Excel** - High priority, ~4 hours  
- [ ] **Import from CSV** - High priority, ~4 hours
- [ ] **Import from Excel** - High priority, ~5 hours
- [ ] Auto-save and recovery
- [ ] **Plot export to image** (PNG/PDF/SVG) - High priority, ~2 hours
- [ ] **Examples menu** - One-click dataset loading, ~3 hours

See [MISSING_FEATURES.md](MISSING_FEATURES.md) for complete analysis.

### Phase 3: Bug Fixes (COMPLETE ✅)
- [x] Automatic recalculation verified working ✅
- [x] Derivative columns verified working ✅
- [ ] Uncertainty propagation (future feature - not yet implemented)

### Phase 4: Advanced Features from Legacy
- [ ] **Statistics Widget** - Descriptive stats + visualizations, ~10 hours
- [ ] **Preferences Window** - Settings dialog, ~6 hours
- [ ] Interpolation columns (~5 hours)
- [ ] Pint integration (unit-aware calculations)
- [ ] Undo/redo system (~15 hours)
- [ ] Enhanced notifications system
- [ ] Multi-language support (i18n)

See [MISSING_FEATURES.md](MISSING_FEATURES.md) for detailed implementation plan.

---

## Development Roadmap

See [PROJECT.md](PROJECT.md) for complete roadmap including:
- Visualization study (plotting)
- Statistics study
- Plugin system
- Multi-table support
- Distribution and packaging

---

## Quick Commands

```bash
# Development
uv run datamanip              # Launch app
uv run pytest tests/unit/ -v  # Run all tests
uv run python examples/*.py   # Run examples

# Testing
uv run pytest tests/unit/core/ -v       # Core tests only
uv run pytest --cov=src --cov-report=html  # Coverage report
```

---

**For detailed architecture, features, and technical documentation, see [PROJECT.md](PROJECT.md)**

### Fresh Rebase - New Architecture
- [x] **Core Architecture** - Qt-independent DataObject + FormulaEngine
- [x] **Studies Pattern** - DataTableStudy with 4 column types (DATA, CALCULATED, DERIVATIVE, RANGE)
- [x] **Workspace-level Variables** - Shared constants across all studies
- [x] **40 Unit Tests Passing** - Core (25) + Studies (15)
- [x] **UI Redesign** - Single workspace with study tabs + dedicated Variables tab
- [x] **Visual Column Differentiation** - Header symbols for each column type:
  - ✎ DATA columns (editable)
  - ƒ CALCULATED columns (formulas)
  - d/dx DERIVATIVE columns
  - ⋯ RANGE columns
- [x] **Type Safety** - All PySide6 type errors suppressed with # type: ignore
- [x] **Legacy Tests Archived** - Moved to tests/_legacy/ (407 old tests)

### Code Quality Improvements (Nov 23, 2025)
- [x] **Utility Modules** - Created dialog_utils.py and model_utils.py
- [x] **Reduced Duplication** - Centralized 29 QMessageBox patterns
- [x] **Refactored Files**:
  - data_table_widget.py - Split _add_column into 4 focused methods
  - variables_widget.py - Using dialog utilities
  - column_dialogs.py - Using dialog utilities, fixed derivative dialog combo boxes
- [x] **Bug Fix** - Derivative column dialog now sets default selections
- [x] **Enhanced Constants System** - Supports 3 types:
  - Numeric constants (e.g., g = 9.81 m/s^2)
  - Calculated variables (formula-based, e.g., v = sqrt(2*g*h))
  - Custom functions (parameterized, e.g., f(x,y) = x^2 + y^2)
- [x] **New UI** - ConstantsWidget replaces VariablesWidget with AddConstantDialog

### Working Features
- [x] **4 Column Types** - DATA, CALCULATED, DERIVATIVE, RANGE fully implemented
- [x] **Formula Engine** - Dependency tracking, scalar broadcasting, unit-aware
- [x] **Variables System** - Workspace-level with sync to all studies
- [x] **4 Working Examples** - Demonstrating all features

## Current Issues

### Known Bugs
- [ ] Variables are not recognized when propagating uncertainty (unify formula calculation)
- [ ] The creation/edition of uncertainty columns is not clear
- [ ] Recalculation is not fully automatic (manual refresh needed sometimes)
- [ ] Better unit calculation and printing (some printing issues remain)
- [ ] Derivative columns n-1 values (empty last row instead of first)

### Architecture Cleanup Needed
- [x] Remove old code (src/models/, src/widgets/data_table/) - DONE
- [x] Create utility modules for dialog patterns - DONE (dialog_utils.py, model_utils.py)
- [x] Update examples to new architecture - DONE (basic_usage.py, projectile_motion.py)
- [ ] Migrate or delete legacy tests (407 tests in tests/_legacy/)
- [ ] Complete PySide6 type stub installation or custom stubs


### Translation
- [ ] Update translations for snake_case module names (low priority)
- [ ] Complete translation coverage for DataTable dialogs

## Planned Features

### Phase 1: Critical Missing Features (HIGH Priority - 6-8 hours) ⚠️
- [x] **CSV/Excel Export/Import** (~3-5 hours) - COMPLETED
  - [x] Backend methods in DataTableStudy (export_to_csv, import_from_csv, export_to_excel, import_from_excel)
  - [x] File menu items (Export → CSV/Excel, Import → CSV/Excel)
  - [x] Metadata preservation in exports
  - [x] Keyboard shortcuts (Ctrl+E for CSV export, Ctrl+I for CSV import)
- [x] **Plot Export to Image** (~2 hours) - COMPLETED
  - [x] Export dialog with format selection (PNG, SVG, PDF, JPG)
  - [x] DPI configuration (72-600)
  - [x] Toolbar button with Ctrl+Shift+E shortcut
  - [x] File browser integration
- [x] **Examples Menu** (~3 hours) - COMPLETED
  - [x] Examples menu between View and Help
  - [x] 4 example datasets: Projectile Motion, Free Fall, Harmonic Oscillator, Derivatives Demo
  - [x] One-click loading with auto-switch to new tab
  - [x] Comprehensive physics examples using all column types

### Phase 2: Important Features (MEDIUM Priority - 19-22 hours)
- [ ] **Statistics Widget** (~10 hours)
- [ ] Additional physics examples:
  - Free fall with air resistance
  - Damped harmonic oscillator
  - Electric field from point charges
  - Chemical kinetics (reaction rates)
- [ ] User guide with step-by-step tutorials
- [ ] Formula syntax reference
- [ ] API documentation for domain models

### Plotting Enhancements
- [ ] Multi-series plotting with legend
- [ ] Curve fitting overlay (linear, polynomial, exponential)
- [ ] Export plots as PNG/SVG
- [ ] Zoom/pan controls
- [ ] Plot styling options

### Statistics Enhancements
- [ ] Correlation matrix between columns
- [ ] Linear/polynomial regression analysis
- [ ] Normality tests (Shapiro-Wilk, Anderson-Darling)
- [ ] ANOVA for comparing groups
- [ ] Export statistics reports

### Code Quality
- [ ] Expand unit test coverage to 500+ tests
- [ ] Integration tests for full workflows
- [ ] Performance profiling for large datasets (10k+ rows)
- [ ] Type hint coverage analysis
- [ ] Documentation coverage

## Long-Term Vision

### Architecture
- [ ] Plugin system for custom column types
- [ ] Event-driven architecture for better extensibility
- [ ] Async operations for large datasets
- [ ] Memory-efficient streaming for huge files

### Automation & Scripting
- [ ] Python API for automation (headless mode)
- [ ] Batch processing scripts
- [ ] Command-line interface
- [ ] Jupyter notebook integration

### Advanced Features
- [ ] Multi-table support (relationships between tables)
- [ ] Database connectivity (SQLite, PostgreSQL)
- [ ] Real-time data streaming
- [ ] Collaborative editing (multi-user)

### Distribution
- [ ] Portable executable builds (PyInstaller/Nuitka)
- [ ] Web version (PyScript/WASM)
- [ ] Package distribution (pip, conda)
- [ ] Docker containerization

### Performance
- [ ] Zig build optimization for critical paths
- [ ] Numba JIT compilation for formulas
- [ ] GPU acceleration for large computations
- [ ] Lazy evaluation for calculated columns

## Short-Term Priorities

1. **Fix remaining bugs** (unit printing, derivative row indexing)
2. **Add 2-3 more physics examples** (demonstrate capabilities)
3. **Write user guide** (getting started, tutorials)
4. **Performance testing** (10k+ rows, complex formulas)
5. **Windows/macOS CI validation** (ensure cross-platform stability)
