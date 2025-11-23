# Missing Features from Legacy Version

**Analysis Date**: November 23, 2025  
**Current Branch**: release-v0.2.0  
**Legacy Source**: `src_legacy/`

## Overview

This document catalogs features present in the legacy version (`src_legacy/`) that have not yet been implemented in the current version (`src/`).

---

## 1. Language/Translation System ⭐ HIGH PRIORITY

### Status: ❌ Not Implemented

### Legacy Implementation
- **Location**: `src_legacy/utils/lang.py`
- **Translation Files**: `assets/lang/en_US.json`, `assets/lang/fr_FR.json`

### Features
- ✅ Thread-safe language manager
- ✅ JSON-based translation files
- ✅ Dot notation for translations (e.g., `tr("menu.file")`)
- ✅ Fallback to English if language not found
- ✅ Runtime language switching
- ✅ Available languages: English (en_US) and French (fr_FR)

### Current Translation Coverage
- **UI Elements**: Menus, dialogs, buttons, tooltips
- **Status Messages**: All status bar messages
- **About Dialog**: Complete translation
- **Preferences**: Language selection dialog

### Implementation Details

**LanguageManager Class**:
```python
class LanguageManager:
    def __init__(self, lang_code: str = "en_US")
    def load_language(self, lang_code: str) -> bool
    def get(self, key: str, default: str = "") -> str
    def get_available_languages(self) -> list
```

**Global Functions**:
```python
def init_language(lang_code: str = "en_US") -> LanguageManager
def get_lang_manager() -> LanguageManager
def tr(key: str, default: str = "") -> str  # Translation shortcut
```

### Usage Example
```python
from utils.lang import tr, init_language

# Initialize at startup
init_language("fr_FR")

# Use in code
file_menu = QMenu(tr("menu.file"))
save_action = QAction(tr("file.save"), self)
save_action.setToolTip(tr("file.save_tip"))
```

### Integration Requirements
1. Port `lang.py` to `src/utils/`
2. Update all hardcoded strings to use `tr()`
3. Add language selector to preferences dialog
4. Store language preference in config
5. Consider adding more languages (German, Spanish, etc.)

---

## 2. Interpolation Columns ⭐ MEDIUM PRIORITY

### Status: ❌ Not Implemented

### Legacy Implementation
- **Location**: `src_legacy/widgets/data_table/column_dialogs.py` (lines 1317-1593)
- **Model Support**: `src_legacy/models/data_table_model.py`

### Features
- ✅ Create interpolated columns from existing data
- ✅ Multiple interpolation methods:
  - Linear interpolation
  - Polynomial interpolation
  - Spline interpolation (cubic, quadratic)
  - Nearest neighbor
- ✅ Specify source X and Y columns
- ✅ Define new X values (can be different spacing)
- ✅ Extrapolation options (constant, linear, None)
- ✅ Visual preview of interpolation
- ✅ Formula display showing method and parameters

### Dialog Features
```python
class AddInterpolationColumnDialog(QDialog):
    """
    - Select source X and Y columns
    - Choose interpolation method
    - Configure extrapolation
    - Define target X values
    - Preview results
    """
```

### Use Cases
- Resampling data at different intervals
- Filling gaps in measurements
- Smoothing noisy data
- Preparing data for comparison with different x-axes

### Integration Requirements
1. Add interpolation methods to formula engine or separate module
2. Create `AddInterpolationColumnDialog`
3. Add toolbar/menu actions
4. Update column type enum
5. Add tests for interpolation methods

---

## 3. Enhanced Statistics Widget

### Status: ⚠️ Partially Implemented

### Missing Features from Legacy
- **Location**: `src_legacy/widgets/statistics_widget/`

#### Missing Components:
1. **Advanced Statistical Measures**
   - Skewness and Kurtosis calculations
   - Confidence intervals
   - Percentiles (25th, 75th)
   - Mode calculation

2. **Distribution Analysis**
   - Histogram with configurable bins
   - Normal distribution overlay
   - Q-Q plots
   - Distribution fitting

3. **Correlation Analysis**
   - Correlation matrix
   - Scatter plot matrix
   - Covariance calculations

4. **Time Series Analysis**
   - Trend lines
   - Moving averages
   - Seasonal decomposition

### Current Implementation
- Basic statistics (mean, median, std, min, max)
- Single column analysis
- No visualization

---

## 4. Plot Configuration Dialogs

### Status: ⚠️ Partially Implemented

### Legacy Implementation
- **Location**: `src_legacy/widgets/plot_widget/plot_dialogs.py`

### Missing Dialogs:

#### 4.1 AddSeriesDialog (Lines 31-507)
**Features**:
- ✅ Select data source (data table or study)
- ✅ Choose X and Y columns
- ✅ Configure series appearance:
  - Line style (solid, dashed, dotted, none)
  - Line width and color
  - Marker style, size, color
  - Fill area under curve
- ✅ Error bar configuration
- ✅ Series label and legend
- ✅ Live preview

#### 4.2 AxisConfigDialog (Lines 508-651)
**Features**:
- ✅ Axis label and unit
- ✅ Scale type (linear, log)
- ✅ Range (auto or manual)
- ✅ Grid configuration (major/minor)
- ✅ Tick configuration
- ✅ Invert axis option

#### 4.3 PlotConfigDialog (Lines 652+)
**Features**:
- ✅ Plot title and labels
- ✅ Legend configuration (position, style, font)
- ✅ Figure size and DPI
- ✅ Background color
- ✅ Export format defaults
- ✅ Multiple axes support

### Current Implementation
- Basic plot creation
- Limited customization
- No advanced configuration dialogs

---

## 5. Advanced Plot Features

### Status: ⚠️ Partially Implemented

### Missing Features from Legacy
- **Location**: `src_legacy/widgets/plot_widget/`

#### 5.1 Plot Export (plot_view.py)
```python
def export_image(self, filepath: str, dpi: Optional[int] = None)
```
- Export to PNG, PDF, SVG, EPS
- Configurable DPI
- Multiple format support
- Batch export capability

#### 5.2 Interactive Tools
- Zoom box
- Pan tool
- Data cursor (show coordinates)
- Pick events (click on data points)
- Annotation tools

#### 5.3 Multiple Subplots
- Grid layout configuration
- Shared axes
- Subplot synchronization

---

## 6. Validated Dialog Base Classes

### Status: ⚠️ Partially Implemented (New base classes created but not used everywhere)

### Legacy Implementation
- **Location**: `src_legacy/utils/base_dialogs.py`

### Features
```python
class ValidatedDialog(QDialog):
    """
    - Input validation framework
    - OK button auto-enable/disable
    - Visual feedback (red borders)
    - Validation messages
    """

class NameValidatedDialog(ValidatedDialog):
    """
    - Specialized for name inputs
    - Check for duplicates
    - Identifier validation (letters, numbers, underscore)
    - Reserved word checking
    """
```

### Current Status
- Created new `BaseDialog` and `BaseColumnDialog` in recent optimization
- Not yet adopted by all dialogs
- Legacy has more specialized validation types

---

## 7. Preferences/Configuration System

### Status: ⚠️ Partially Implemented

### Legacy Implementation
- **Location**: `src_legacy/utils/config.py`

### Missing Features:

#### 7.1 Comprehensive Config Management
```python
class Config:
    def get(self, key: str, default: Any) -> Any
    def set(self, key: str, value: Any) -> bool
    def get_language(self) -> str
    def set_language(self, lang_code: str) -> bool
    def reset_to_defaults() -> bool
```

#### 7.2 Config Categories
- **Appearance**: Theme, font size, colors
- **Language**: Current language selection
- **Data**: Default precision, date format
- **Plot**: Default DPI, colors, styles
- **Performance**: Cache size, thread count
- **Recent Files**: File history management

#### 7.3 Config Persistence
- JSON-based config file
- User-specific location
- Auto-save on change
- Import/export settings

---

## 8. Enhanced Error Dialogs

### Status: ❌ Not Implemented

### Legacy Implementation
- **Location**: `src_legacy/ui/notifications.py`

### Features
```python
class DetailedErrorDialog(QDialog):
    """
    - Error message display
    - Stack trace viewer
    - Copy to clipboard
    - Report bug button
    - Technical details expansion
    """
```

### Use Cases
- Display exceptions with context
- Help users report bugs
- Show technical details for developers
- Friendly error messages for users

---

## 9. About Dialog Enhancements

### Status: ⚠️ Basic Implementation Exists

### Legacy Features
- **Location**: `src_legacy/ui/about_window/about_window.py`

### Missing Features:
- Contributors list (loaded from `assets/contributors.json`)
- Version information display
- License viewer
- Links to GitHub, website
- System information
- Dependencies list

---

## 10. Workspace Management

### Status: ⚠️ Different Architecture

### Legacy Implementation
- **Location**: `src_legacy/ui/main_window/workspace.py`

### Features:
- Tab-based workspace switching
- Multiple studies in tabs
- Drag-and-drop between studies
- Tab context menus
- Tab reordering

### Current Implementation
- Study list in sidebar
- Single study view
- Different UX paradigm

---

## Priority Ranking

### 🔴 Critical (Should implement soon)
1. **Language/Translation System** - Essential for internationalization
2. **Enhanced Error Dialogs** - Better user experience
3. **Plot Export** - Core functionality

### 🟡 Important (Medium priority)
4. **Interpolation Columns** - Useful data manipulation feature
5. **Plot Configuration Dialogs** - Better plot customization
6. **Statistics Widget Enhancements** - More analysis capabilities

### 🟢 Nice to Have (Low priority)
7. **Validated Dialog Migration** - Already have new base classes
8. **About Dialog Enhancements** - Cosmetic improvements
9. **Advanced Config System** - Current system works
10. **Workspace Tabs** - Different UX approach chosen

---

## Implementation Roadmap

### Phase 1: Core Features (Sprint 1-2)
- [ ] Port language/translation system
- [ ] Add plot export functionality
- [ ] Create enhanced error dialogs

### Phase 2: Data Features (Sprint 3-4)
- [ ] Implement interpolation columns
- [ ] Enhance statistics widget
- [ ] Add correlation analysis

### Phase 3: UI Enhancements (Sprint 5-6)
- [ ] Create plot configuration dialogs
- [ ] Migrate all dialogs to new base classes
- [ ] Enhance about dialog

### Phase 4: Configuration (Sprint 7)
- [ ] Enhance config system
- [ ] Add preferences categories
- [ ] Implement settings import/export

---

## Notes

### Translation Files Ready
The JSON translation files already exist in `assets/lang/`:
- `en_US.json` - Complete English translation
- `fr_FR.json` - Complete French translation

These can be used immediately once the language system is ported.

### Code Reusability
Much of the legacy code can be ported with minimal changes:
- Dialog classes are well-structured
- Configuration system is modular
- Language manager is thread-safe and tested

### Testing Requirements
When implementing these features, ensure:
- Unit tests for core functionality
- Integration tests for dialogs
- Manual testing for UI/UX
- Translation completeness checks

---

## Conclusion

The legacy version contains several valuable features that enhance usability and functionality. Priority should be given to:

1. **Language system** - Quick to implement, high value
2. **Plot export** - Essential functionality
3. **Error dialogs** - Better user experience

Other features can be implemented incrementally based on user demand and development capacity.
