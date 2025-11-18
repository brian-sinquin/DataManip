# TODO.md

## Migration to DataTable (Nov 2025)

### Completed ✅
- [x] **DataTable Implementation** - Complete Model/View architecture with Pandas backend
- [x] **Feature Parity** - All AdvancedDataTableWidget features migrated:
  - Global variables/constants system (VariablesDialog)
  - Manual uncertainty columns (AddUncertaintyColumnDialog)
  - Toolbar with column type dropdown
  - Auto-row creation on Enter key
  - Column insertion positioning control
- [x] **Full Migration** - Renamed DataTableV2 → DataTable, deleted AdvancedDataTableWidget
- [x] **Physics Examples** - 4 comprehensive examples reimplemented:
  - Projectile Motion (baseball trajectory)
  - Ideal Gas Law (PV=nRT)
  - Simple Harmonic Motion (mass-spring)
  - RC Circuit Charging (capacitor)
- [x] **Plot Widget** - Updated AdvancedDataTablePlotWidget for new API
- [x] **Statistics Widget** - Updated AdvancedDataTableStatisticsWidget for new API
- [x] **Application Running** - Full functionality across all 3 tabs (Data, Plotting, Statistics)

### Test Coverage
- 348+ tests in tests/widgets/DataTable/
- All major features tested (formulas, derivatives, uncertainty, file I/O)

## Bugs (Legacy - mostly resolved in DataTable)

- [ ] Better unit calculation and printing, still some printing issues
- [ ] Derivative columns n-1 values, empty last instead of first
- [x] Avalanche update on range changes - FIXED: Recursive dependency propagation
- [x] Formula derivative propagation - FIXED: Empty cell handling

## Open Issues

- [ ] Better new row injection UX
- [x] Remove old toolbar - DONE: New toolbar with dropdown
- [ ] Translation updates for DataTable (low priority)

## Features

### Implemented ✅
- [x] CSV/Excel import/export (DataTable file I/O)
- [x] Plotting widget with uncertainty support
- [x] Statistics widget (14+ measures, histograms, box plots)
- [x] Undo/Redo (Qt command pattern)
- [x] Global variables for formulas
- [x] Manual uncertainty columns
- [x] Column type dropdown toolbar

### Planned
- [ ] Additional examples:
  - Free fall with air resistance
  - Damped harmonic oscillator
  - Electric field from point charges
  - Chemical kinetics (reaction rates)
- [ ] Plot enhancements:
  - Multi-series plotting
  - Curve fitting overlay
  - Export plots as images
- [ ] Statistics enhancements:
  - Correlation analysis between columns
  - Regression analysis
  - Normality tests

## Short term
- [ ] Expand unit test coverage to 500+ tests
- [ ] Add CI/CD pipeline (GitHub Actions)
- [ ] Performance profiling for large datasets (10k+ rows)
- [ ] Documentation:
  - User guide with examples
  - API documentation
  - Formula syntax reference

## Long term
- [ ] Plugin system for custom column types
- [ ] Scripting interface (Python API for automation)
- [ ] Web version (PyScript/WASM)
- [ ] Zig build optimization for performance-critical paths
