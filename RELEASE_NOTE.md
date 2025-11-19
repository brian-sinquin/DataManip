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
- **Secondary Y-Axis Support**: Plot series with different units on a secondary Y-axis (twinx), with independent configuration and legend
- **Unit Compatibility Validation**: Prevent plotting series with incompatible units on the same axis; suggest secondary axis when needed
- **Minimal Navigation Toolbar**: Only Home, Pan, and Zoom buttons shown for cleaner UI

## Bug fixes

- **Derivative Calculation**: Fixed bug where derivative columns lost two points (first and last); now only one empty value at the correct boundary for each method
- **Derivative Recalculation**: Ensured recalculation uses the correct method and preserves NaN placement
- **Interpolation Columns**: Fixed NaN preservation and method-specific validation
- **Dialog AttributeError**: Fixed signal connection timing in derivative/interpolation dialogs
- **Import Errors**: Fixed all snake_case import paths

## Enhancements

### Testing
- **Plot Widget Tests**: Added comprehensive unit test suite with 82 tests
- **Derivative Column Tests**: 30+ tests for all difference methods and edge cases
- **Full DataTable/Plot Integration**: All tests passing, including recalculation and dependency handling