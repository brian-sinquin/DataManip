# DataManip v0.2.0 Release Notes

**Release Date**: November 24, 2025  
**Status**: Stable

## Overview

Complete rewrite with modern architecture, 300+ tests (99%+ passing), and production-ready data manipulation for experimental sciences.

## Key Features

### Data Management
- **5 Column Types**: Data (editable), Calculated (formulas), Derivative (d/dx), Range (sequences), Uncertainty (δ propagation)
- **Formula Engine**: NumPy functions, workspace constants, units (pint), automatic dependency tracking
- **Performance**: 3x speedup via lazy evaluation and caching

### Visualization
- **Plots**: Multiple series, error bars, customizable styling, export (PNG/SVG/PDF)
- **Statistics**: Histogram + box plot with descriptive stats

### Workspace
- **Constants**: Numeric, calculated, and function types with global scope
- **Save/Load**: JSON format with atomic writes
- **Import/Export**: CSV, Excel (multi-sheet)

### UX
- **Undo/Redo**: Column operations (50-step history), Ctrl+Z/Y shortcuts
- **Preferences**: Auto-save, theme, precision, performance tuning
- **Notifications**: Non-intrusive toasts (info/warning/error/success)
- **CLI**: Load workspaces directly: `uv run datamanip file.dmw`

### Examples
9 physics examples demonstrating all features:
- **Tutorials** (01-06): One feature each (data entry → custom functions)
- **Complete** (07-09): Calorimetry, photoelectric effect, spring-mass SHM

## Technical

- **Stack**: Python 3.12+, PySide6, pandas, NumPy, matplotlib, sympy, pint
- **Architecture**: 3-layer (Core/Studies/UI) with Qt-independent core
- **Tests**: 300 unit tests across all layers
- **Package Manager**: uv (NOT pip/conda)

## Installation

```bash
git clone https://github.com/brian-sinquin/DataManip.git
cd DataManip
uv sync
uv run datamanip
```

## Known Issues

- `test_notification_stacking`: Flaky positioning (non-critical)

## What's Next

### v0.3.0 - Core Stability
- Auto-save with intervals
- Extended undo (data modifications, constants)
- Interpolation columns

### v0.4.0 - UI/UX
- Modern interface redesign
- Dockable panels
- Localization (French/Spanish/German)

See [ROADMAP.md](ROADMAP.md) for details.

## License

MIT License - See [LICENSE](LICENSE)
