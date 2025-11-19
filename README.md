# DataManip

[![Tests](https://github.com/brian-sinquin/DataManip/actions/workflows/tests.yml/badge.svg)](https://github.com/brian-sinquin/DataManip/actions/workflows/tests.yml)

An open-source data manipulation software for experimental sciences

## Features

- **Data Columns**: Create and manage numerical, categorical, and text data
- **Calculated Columns**: Define formulas using other columns (e.g., `{A} + {B}`)
- **Uncertainty Propagation**: Automatic error propagation using symbolic differentiation
- **Derivative Columns**: Calculate discrete differences (numerical derivatives)
- **Units Support**: Assign and convert units using Pint
- **File I/O**: Save and load data tables in JSON format
- **Copy/Paste**: Excel-compatible clipboard operations
- **Undo/Redo**: Full command history with multi-level undo

## Getting Started

### Prerequisites
- [uv](https://docs.astral.sh/uv/) package manager

### Clone and Run

```bash
# Clone the repository
git clone https://github.com/yourusername/DataManip.git
cd DataManip

# Install dependencies and run with uv
uv sync
uv run datamanip
```

## Uncertainty Propagation

DataManip automatically calculates propagated uncertainties using the standard error propagation formula:

$$\delta f = \sqrt{\sum_i \left(\frac{\partial f}{\partial x_i} \cdot \delta x_i\right)^2}$$

Where:
- $\delta f$ = combined uncertainty of result
- $\frac{\partial f}{\partial x_i}$ = partial derivatives (calculated symbolically using SymPy)
- $\delta x_i$ = uncertainties of input variables