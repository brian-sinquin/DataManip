# TODO.md

## Recent Achievements (November 2025) ✅

### Architecture Refactoring
- [x] **Snake_case Migration** - Renamed all PascalCase packages to snake_case (DataTable→data_table, etc.)
- [x] **Domain Model Extraction** - Separated pure logic from Qt:
  - DataStore (310 lines) - Pure Pandas/NumPy storage
  - FormulaEngine (354 lines) - Formula evaluation and dependencies
  - ColumnRegistry (446 lines) - Metadata management
- [x] **Constants Package** - Centralized ColumnType, DataType, symbols, and units
- [x] **Models Package** - Qt-independent domain logic (1,110 lines extracted)
- [x] **Circular Import Fix** - Resolved models↔widgets circular dependency

### Testing & CI
- [x] **Test Coverage** - 407 tests passing (351 DataTable + 56 models)
- [x] **GitHub Actions CI** - Automated testing on push/PR
  - Multi-OS: Ubuntu, Windows, macOS
  - Multi-Python: 3.11, 3.12
  - Qt headless support with Xvfb
- [x] **Test Badge** - CI status badge in README

### Bug Fixes
- [x] **Interpolation Columns** - Fixed eval_column support, NaN preservation, method-specific validation
- [x] **Formula Validation** - Now recognizes variables in addition to columns
- [x] **Dialog AttributeError** - Fixed signal connection timing in derivative/interpolation dialogs
- [x] **Import Errors** - Fixed all snake_case import paths

- [ ] Variables are not recognized when propagating uncertainty (unify formula calculation)
- [ ] The creation / edition of uncertainty columns is not clear.
- [ ] Recalculation is not fully automatic

### DataTable Implementation
- [x] **Complete Feature Parity** - All features from AdvancedDataTableWidget migrated
- [x] **6 Column Types** - DATA, CALCULATED, DERIVATIVE, RANGE, INTERPOLATION, UNCERTAINTY
- [x] **Physics Examples** - 4 comprehensive examples working
- [x] **Full Application** - Data, Plotting, and Statistics tabs functional

## Current Issues

### Known Bugs
- [ ] Better unit calculation and printing (some printing issues remain)
- [ ] Derivative columns n-1 values (empty last row instead of first)


### Translation
- [ ] Update translations for snake_case module names (low priority)
- [ ] Complete translation coverage for DataTable dialogs

## Planned Features

### Examples & Documentation
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
