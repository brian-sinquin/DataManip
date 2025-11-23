# DataManip

[![Tests](https://github.com/brian-sinquin/DataManip/actions/workflows/tests.yml/badge.svg)](https://github.com/brian-sinquin/DataManip/actions/workflows/tests.yml)
[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](RELEASE_NOTES.md)
[![Python](https://img.shields.io/badge/python-3.12+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

An open-source data manipulation software for experimental sciences

**[📖 Release Notes](RELEASE_NOTES.md)** | **[🗺️ Roadmap](ROADMAP.md)** | **[🤝 Contributing](CONTRIBUTING.md)**

---

## ✨ Key Features

- **5 Column Types**: Data, Calculated, Derivative, Range, Uncertainty
- **Formula Engine**: NumPy functions, custom functions, unit-aware calculations
- **Plotting with Error Bars**: Multiple series, X/Y uncertainties, statistics (histogram/box plot), image export
- **Workspace Management**: Save/load complete workspaces, atomic file operations
- **Undo/Redo**: 50-step history for column operations
- **Constants System**: Numeric, calculated, and function constants
- **Preferences**: Customizable settings with theme support
- **Performance**: 3x faster with lazy evaluation and parallel execution
- **308 Tests**: 99%+ passing unit test coverage (8 new error bar tests)

📋 **[View Complete Feature List →](RELEASE_NOTES.md)**

---

## Getting Started

### Prerequisites
- [uv](https://docs.astral.sh/uv/) package manager

### Clone and Run

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
- **[TODO.md](TODO.md)** - Current sprint priorities and task tracking
- **[CONFIG_MIGRATION.md](CONFIG_MIGRATION.md)** - Configuration changes guide
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

```python
# See examples/ directory for complete demonstrations
examples/
├── basic_usage.py              # Simple data manipulation
├── projectile_motion.py        # Physics with units
├── uncertainty_demo.py         # Error propagation
├── derivative_example.py       # Numerical differentiation
├── error_bars_example.py       # Plotting with uncertainties ⭐ NEW
└── performance_benchmark.py    # Performance testing
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

**Made with PySide6 • pandas • NumPy • matplotlib • sympy • pint**