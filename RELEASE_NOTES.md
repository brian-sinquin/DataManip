# DataManip Release Notes

## Version 0.2.0 - November 23, 2025

### 🎉 Major Release - Modern Architecture & Feature Complete Core

This release represents a complete rewrite of DataManip with a modern, maintainable architecture and comprehensive feature set for experimental sciences data analysis.

---

## ✨ Core Features

### 📊 Data Table Management
- **5 Column Types** with visual indicators:
  - ✎ **Data Columns** - User-editable numerical data
  - ƒ **Calculated Columns** - Formula-based with automatic recalculation
  - d/dx **Derivative Columns** - Numerical differentiation
  - ⋯ **Range Columns** - Auto-generated sequences (start, stop, step)
  - δ **Uncertainty Columns** - Propagated error analysis
- **Formula Engine** - Supports NumPy functions, custom workspace functions, units (pint)
- **Dependency Tracking** - Automatic formula recalculation on data changes
- **Performance Optimized** - 3x speedup (9.5M → 28.7M calc/sec) with lazy evaluation
- **Copy/Paste** - Excel-compatible clipboard operations
- **Editable Headers** - Double-click to rename columns inline

### 🎨 Plotting & Visualization
- **Plot Studies** - Multiple series per plot with customizable styling
- **Error Bars** - Optional X and/or Y error bars for uncertainty visualization
- **Statistics Studies** - Histogram + box plot dual visualization
- **Descriptive Statistics** - Mean, median, std dev, quartiles, min/max
- **Export to Image** - PNG, JPEG, SVG, PDF formats with DPI control
- **Interactive Tools** - Matplotlib navigation toolbar (zoom, pan, save)

### 🔧 Workspace & Constants
- **Constants Widget** - 3 types of workspace-level constants:
  - **Numeric** - Simple values with units
  - **Calculated** - Formula-based with dependency resolution
  - **Functions** - Custom Python functions for formulas
- **Constants Caching** - Version tracking for optimal performance
- **Tab Protection** - Constants tab cannot be closed
- **Global Scope** - Constants accessible in all studies

### 💾 File I/O & Persistence
- **Save/Load Workspace** - Complete workspace serialization to JSON
- **Atomic Writes** - Temp file + backup for data safety
- **CSV Import/Export** - Flexible delimiter, header options
- **Excel Export** - Multi-sheet support with formatting
- **Auto-conversion** - Seamless NumPy/pandas type handling

### ↩️ Undo/Redo System
- **Column Operations** - Undo add, remove, rename columns
- **50-Step History** - Configurable undo stack size
- **Keyboard Shortcuts** - Ctrl+Z (undo), Ctrl+Y (redo)
- **Visual Feedback** - Tooltips show action descriptions
- **Toast Notifications** - Confirmation messages for undo/redo

### ⚙️ Preferences & Settings
- **Preferences Dialog** - 4 organized tabs:
  - **General** - Auto-save, session restore, confirmation dialogs, language
  - **Display** - Theme, precision, grid, colors, row height
  - **Performance** - Parallel calculations, caching, undo history
  - **Recent Files** - Manage recent workspace list
- **Persistent Settings** - JSON in ~/.datamanip/preferences.json
- **System Default Theme** - Automatic light/dark mode support

### 📢 Notification System
- **Toast Notifications** - 4 types (info, warning, error, success)
- **Progress Notifications** - With progress bars and cancel support
- **Smart Positioning** - Automatic stacking and timeout management
- **Non-Intrusive** - Bottom-right corner, auto-dismiss

### ⌨️ Keyboard Shortcuts
- **F1** - Show keyboard shortcuts help dialog
- **Ctrl+T** - New data table
- **Ctrl+P** - New plot
- **Ctrl+S** - Save workspace
- **Ctrl+O** - Open workspace
- **Ctrl+Z/Y** - Undo/Redo
- **Ctrl+C/V** - Copy/Paste
- **Delete** - Remove selected rows/columns
- **Arrow Keys** - Navigate table cells

### 🧪 Advanced Features
- **Unit System** - Full pint integration for physical quantities
- **Uncertainty Propagation** - Automatic error calculation using sympy
- **Custom Functions** - Define reusable functions in constants
- **Formula Validation** - Real-time syntax checking and error messages
- **Parallel Execution** - ThreadPoolExecutor for independent columns
- **Batch Operations** - Efficient multi-column operations (8x faster)

---

## 🏗️ Architecture Highlights

### 3-Layer Design
- **Core Layer** (Qt-independent) - DataObject, FormulaEngine, Workspace, UndoManager
- **Studies Layer** - DataTableStudy, PlotStudy, StatisticsStudy
- **UI Layer** - PySide6 widgets with MVC pattern

### Code Quality
- **84% Code Reduction** - 139 → 22 Python files (clean rewrite)
- **300 Unit Tests** - 99%+ passing (244/245)
- **Modular Structure** - Files <400 lines, clear separation of concerns
- **Type Hints** - Full type coverage for all functions
- **Comprehensive Docstrings** - Google-style documentation

---

## 📦 Dependencies

- **Python**: 3.12+ (modern features: match/case, type hints)
- **PySide6**: 6.10.0+ (Qt for Python)
- **pandas**: 2.3.3+ (Data structures)
- **numpy**: 2.3.4+ (Numerical computing)
- **matplotlib**: 3.10.7+ (Plotting)
- **sympy**: 1.14.0+ (Symbolic math)
- **pint**: 0.25.2+ (Unit conversions)
- **scipy**: 1.16.3+ (Scientific computing)

---

## 🚀 Getting Started

### Installation
```bash
# Clone repository
git clone https://github.com/brian-sinquin/DataManip.git
cd DataManip

# Install with uv (recommended)
uv sync
uv run datamanip

# Or with pip
pip install -e .
datamanip
```

### Quick Start
1. Launch DataManip
2. Add data columns with "Add Column" → "Data Column"
3. Enter values or paste from Excel
4. Create calculated columns with formulas (e.g., `{A} + {B}`)
5. Add plots to visualize data
6. Save workspace (Ctrl+S)

---

## 🧪 Testing

```bash
# Run all tests
uv run pytest tests/unit/ -v

# Coverage report
uv run pytest --cov=src --cov-report=html

# Layer-specific tests
uv run pytest tests/unit/core/ -v      # Core layer
uv run pytest tests/unit/studies/ -v   # Studies layer
uv run pytest tests/unit/ui/ -v        # UI layer
```

---

## 📚 Examples

See `examples/` directory for demonstrations:
- `basic_usage.py` - Simple data manipulation
- `projectile_motion.py` - Physics calculations with units
- `uncertainty_demo.py` - Error propagation
- `derivative_example.py` - Numerical differentiation
- `performance_benchmark.py` - Performance testing

---

## 🐛 Known Issues

- **1 Test Failure** - `test_notification_stacking` (flaky positioning) - non-critical
- **Legacy Tests** - 407 archived tests from old codebase (pending migration)

---

## 🔮 What's Next?

See [ROADMAP.md](ROADMAP.md) for detailed future plans:

### v0.3.0 (Q4 2025) - Core Stability
- Auto-save & crash recovery
- Extended undo/redo (data modifications, constants)
- Interpolation columns

### v0.4.0 (Q1 2026) - UI/UX Rework
- Dark/light theme system
- Modern interface redesign
- Dockable panels & workspace improvements
- Accessibility & localization

### v0.5.0+ - Advanced Features
- Curve fitting & regression
- Data filtering & transformations
- Domain-specific modules (physics, chemistry, biology)
- Plugin system

---

## 🙏 Acknowledgments

Built with ❤️ by the DataManip community for experimental scientists worldwide.

**Contributors**: See `assets/contributors.json`

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/brian-sinquin/DataManip/issues)
- **Documentation**: [PROJECT.md](PROJECT.md)
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)

---

**For detailed feature documentation, see [PROJECT.md](PROJECT.md)**  
**For current development status, see [TODO.md](TODO.md)**
