# TODO.md

## Bugs

- [x] Better unit calculation and printing (acceleration is a bug example) - FIXED: Added unit_simplification.py module + fixed format_unit_pretty() to handle superscript exponents in denominators
- [x] Derivative columns should have n-1 values (last row undefined) - FIXED: Updated _recalculate_derivative_column() to leave last row empty, updated plot widget for paired data extraction
- [x] Avalanche update when range column density changes - FIXED: Made _recalculate_dependent_columns() recursive for multi-level dependency propagation
- [x] Formulas using derivatives should propagate empty cells - FIXED: _evaluate_formula_with_units() returns None when any referenced column is empty, creating empty cells instead of zeros

## Open Issues

- [ ] Better new raw injection when editing last raw item ??
- [x] Remove toolbar - DONE: Replaced with tabbed interface
- [ ] Fix translation for new DataTableWidget (ignore)

## Features

- [ ] Raw deletion context menu
- [ ] Copy Paste, smart Data column injection
- [ ] CSV import / export
- [x] Start basic plotting widget - DONE: AdvancedDataTablePlotWidget created with X/Y column selection
- [x] Statistics widget - DONE: AdvancedDataTableStatisticsWidget with descriptive stats, histogram, and box plot

## Short term
- [ ] Add unit tests
- [ ] Add CI testing
- [ ] Potential full rewrite of the widget instead of wrapping arround original one

## Long term
- [ ] Zig build for windows using Cython
