# DataManip

[![Tests](https://github.com/brian-sinquin/DataManip/actions/workflows/tests.yml/badge.svg)](https://github.com/brian-sinquin/DataManip/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/brian-sinquin/DataManip/graph/badge.svg?token=JFNKIFNNTS)](https://codecov.io/gh/brian-sinquin/DataManip)
[![PyPI version](https://img.shields.io/pypi/v/datamanip.svg)](https://pypi.org/project/datamanip/)
[![Python](https://img.shields.io/badge/python-3.12+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

A powerful, user-friendly data manipulation application for experimental sciences. Perform calculations with formulas, units, uncertainty propagation, derivatives, and visualization—all in one place.

**[📖 Release Notes](RELEASE_NOTES.md)** | **[🗺️ Roadmap](ROADMAP.md)** | **[🤝 Contributing](CONTRIBUTING.md)**

---

## ✨ Key Features

- **5 Column Types**: Data, Calculated, Derivative, Range, Uncertainty
- **Formula Engine**: NumPy functions, custom functions, unit-aware calculations (pint)
- **Automatic Uncertainty Propagation**: Symbolic differentiation with SymPy
- **High Performance**: 3x speedup with lazy evaluation, caching, and parallel execution
- **Plotting with Error Bars**: Multiple series, X/Y uncertainties, statistics (histogram/box plot)
- **Workspace Management**: Save/load complete workspaces with all studies
- **Undo/Redo**: 50-step history for column operations
- **Constants System**: Numeric, calculated, and function constants (workspace-level)

📋 **[View v0.2.0 Release Notes →](RELEASE_NOTES.md)**

---

## 📦 Installation

### Option 1: Install from PyPI (Recommended)

```bash
# Using pip
pip install datamanip

# Using uv (faster)
uv pip install datamanip

# Run directly with uvx (no installation)
uvx datamanip

# Launch the application
python -m datamanip
# or simply:
datamanip
```

### Option 2: Development Setup

```bash
# Clone the repository
git clone https://github.com/brian-sinquin/DataManip.git
cd DataManip

# Install dependencies and run with uv
uv sync
uv run datamanip
```

---

## 📚 Documentation

- **[RELEASE_NOTES.md](RELEASE_NOTES.md)** - Complete feature list and v0.2.0 details
- **[ROADMAP.md](ROADMAP.md)** - Development roadmap from v0.3.0 to v1.0.0
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute to DataManip

---

## 🧮 Uncertainty Propagation

DataManip automatically calculates propagated uncertainties using the standard error propagation formula:

$$\delta f = \sqrt{\sum_i \left(\frac{\partial f}{\partial x_i} \cdot \delta x_i\right)^2}$$

Where:

- $\delta f$ = combined uncertainty of result
- $\frac{\partial f}{\partial x_i}$ = partial derivatives (calculated symbolically using SymPy)
- $\delta x_i$ = uncertainties of input variables

---

## 🚀 Quick Examples

```bash
# See examples/ directory for 8 complete demonstrations
examples/
├── 01_basic_introduction.dmw        # Getting started
├── 02_constants_and_formulas.dmw    # Formula engine basics
├── 03_ranges_and_derivatives.dmw    # Numerical differentiation
├── 04_uncertainty_propagation.dmw   # Error analysis
├── 05_custom_functions.dmw          # User-defined functions
├── 06_calculated_constants.dmw      # Dynamic constants
├── 07_advanced_kinematics.dmw       # Physics with units
└── 08_photoelectric_effect.dmw      # Complete experiment

# Open an example
datamanip examples/01_basic_introduction.dmw
```

---

## 🧪 Testing

```bash
# Run all tests
uv run pytest tests/unit/ -v

# Generate coverage report
uv run pytest --cov=src --cov-report=html

# Test by layer
uv run pytest tests/unit/core/ -v
uv run pytest tests/unit/studies/ -v
uv run pytest tests/unit/ui/ -v
```

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

---

## 🙏 Acknowledgments

Built with ❤️ for experimental scientists worldwide.

**Contributors**: See [assets/contributors.json](assets/contributors.json)

---

Made with PySide6 • pandas • NumPy • matplotlib • sympy • pint
