# Release Note v0.2.0

## Features

### Enhanced Plot Widget Architecture
- **Model-View Separation**: Implemented `PlotModel` and `PlotView` following DataTable design patterns
- **Multi-Series Support**: Plot multiple data series with independent styling on the same axes
- **Series Management**: Add, edit, remove, show/hide, and reorder plot series via intuitive dialogs
- **Advanced Styling**: Comprehensive customization of colors, markers, line styles, transparency, and z-order
- **Error Bar Support**: Automatic uncertainty propagation from DataTable uncertainty columns
- **Plot Configuration**: Full control over axes (scale, range, labels, units), legend, grid, and figure properties
- **Auto-Configuration**: Automatically detect and configure axes labels and units from DataTable columns when adding first series
- **Export Functionality**: Export plots as PNG, PDF, or SVG with configurable DPI
- **Interactive Toolbar**: Quick actions for series management, axis configuration, and export operations

### New Plot Widget Components
- `PlotModel`: Pure data model for series and configuration management
- `PlotView`: Matplotlib canvas integration with automatic rendering
- `PlotWidget`: All-in-one widget with built-in model (like DataTableWidget)
- `SeriesMetadata`: Rich metadata for plot series (columns, style, errors)
- `PlotConfig`: Comprehensive plot configuration (axes, legend, grid, figure)
- `PlotToolbar`: Full-featured toolbar with dropdowns and quick actions
- `AddSeriesDialog`: Multi-tab dialog for series configuration
- `AxisConfigDialog`: Dedicated axis configuration dialog
- `PlotConfigDialog`: General plot appearance settings

### Plot Styles Supported
- Line plots with customizable line styles (solid, dashed, dotted, dash-dot)
- Scatter plots with 8 marker styles (circle, square, triangle, diamond, plus, cross, star)
- Combined line+scatter plots
- Bar plots with automatic width calculation
- Step plots for discrete data
- Error bar plots with cap customization

### Axis Features
- Linear, logarithmic, symmetric log, and logit scales
- Auto-range or manual min/max settings
- Axis inversion support
- Grid line customization (major, minor, both, none)
- Unit-aware labels with automatic formatting

## Bug fixes

## Enhancements

### Testing
- **Plot Widget Tests**: Added comprehensive unit test suite with 82 tests
  - `test_series_metadata.py`: Tests for SeriesMetadata, PlotStyle, MarkerStyle, LineStyle enums (35+ tests)
  - `test_plot_config.py`: Tests for PlotConfig, AxisConfig, LegendConfig, and related enums (30+ tests)
  - `test_plot_model.py`: Tests for PlotModel business logic (33+ tests)
    - Series management (add, remove, update, rename)
    - Data extraction and validation
    - Configuration management
    - Auto-configuration from DataTable
    - Serialization/deserialization
    - DataTable event handling (column renames, deletions)
  - All tests passing, following DataTable test patterns