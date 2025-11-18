# DataManip
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

**δf = √(Σ(∂f/∂xᵢ · δxᵢ)²)**

Where:
- δf = combined uncertainty of result
- ∂f/∂xᵢ = partial derivatives (calculated symbolically using SymPy)
- δxᵢ = uncertainties of input variables

### Example Usage

```python
from widgets import DataTableModel
import pandas as pd

# Create model
model = DataTableModel()

# Add data with uncertainties
model.add_data_column("x", data=pd.Series([1.0, 2.0, 3.0]))
model.add_data_column("x_u", data=pd.Series([0.1, 0.1, 0.15]))

# Create calculated column with uncertainty propagation
model.add_calculated_column(
    "y",
    formula="{x}**2",
    propagate_uncertainty=True  # Automatically creates y_u column
)
```

## Project Structure

```
DataManip/
├── src/
│   ├── config/           # Application configuration
│   ├── constants/        # Column types, data types, symbols, units
│   ├── models/           # Domain logic (future extraction)
│   ├── ui/               # UI components
│   │   ├── main_window/
│   │   ├── about_window/
│   │   └── preference_window/
│   ├── utils/            # Utility functions, formula parser, uncertainty
│   └── widgets/          # Reusable widgets
│       ├── data_table/   # Main data table widget
│       ├── plot_widget/  # Plotting widget
│       └── statistics_widget/
├── tests/
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── fixtures/         # Test fixtures
└── examples/             # Usage examples

# Uncertainties update automatically when data changes!
```

See `tests/widgets/DataTableV2/demo_uncertainty.py` for a complete interactive demo.