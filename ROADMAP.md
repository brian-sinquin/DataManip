# DataManip Roadmap

## Vision

Production-ready data analysis tool for experimental sciences with speed, flexibility, and zero-code usability.

## Milestones

### v0.3.0 - Core Stability

**File I/O**

- Auto-save (5/15/30 min intervals)
- Unsaved changes warning
- Format versioning

**Undo/Redo**

- Data modifications (cell edits, rows)
- Constants operations
- Study-level undo
- Non-linear history support

**New Features**

- Interpolation columns (linear, spline, polynomial)
- Performance profiling
- Memory leak detection

### v0.4.0 - UI/UX

**Interface**

- Modern redesign (icons, typography, spacing)
- Dockable panels (VS Code-style)
- Split view for study comparison
- Workspace navigator tree
- Global search

**Experience**

- Drag-and-drop (files, columns)
- Contextual tooltips
- Customizable toolbar
- Onboarding tour
- <2s startup time

**Accessibility**

- Localization (French, Spanish, German)
- Font scaling
- Colorblind-friendly themes

### v0.5.0 - Advanced Analysis

**Curve Fitting**

- Linear/polynomial regression with CI
- Custom function fitting
- Residuals plot + R² stats
- Export fit parameters

**Data Processing**

- Filter by condition
- Multi-level sorting
- Outlier removal (IQR, Z-score)
- Moving average/median
- FFT analysis

**Plotting**

- Subplot support
- Logarithmic axes
- Publication templates
- Interactive annotations
- Vector export (SVG, PDF)

**Units**

- Custom definitions
- Interactive conversion dialog
- Compatibility checking
- Dimensionality warnings

### v0.6.0 - Enhanced I/O

**Import/Export**

- HDF5, MATLAB .mat, SQL databases
- LaTeX tables
- Batch import
- Import preview with mapping

**Performance**

- Lazy loading (>100K rows)
- Virtual scrolling
- Background calculation threads
- Incremental saves
- Memory-mapped files

## Contributing

Feature requests: GitHub issues with `[ROADMAP]` tag
Pull requests: Tackle roadmap items directly
