# Missing Features from Legacy Code

## Analysis Date: November 23, 2025

This document identifies features from the legacy codebase that should be adapted to the new architecture.

---

## 🔴 Critical Missing Features (High Priority)

### 1. CSV/Excel Import/Export
**Status**: ❌ Not Implemented  
**Legacy Location**: `src_legacy/widgets/data_table/model.py`

**Legacy Features**:
- `save_to_csv()` - Export with metadata comments
- `load_from_csv()` - Import with automatic type detection
- `save_to_excel()` - Export to .xlsx format
- `load_from_excel()` - Import from .xlsx with sheet selection

**Implementation Plan**:
- Add methods to `DataTableStudy` class
- Create import/export dialogs in UI
- Add menu items: File → Export → CSV/Excel
- Add menu items: File → Import → CSV/Excel
- Support metadata preservation where possible

**Priority**: HIGH - Essential for data interoperability

---

### 2. Statistics Widget
**Status**: ❌ Not Implemented  
**Legacy Location**: `src_legacy/widgets/statistics_widget/statistics_widget.py`

**Legacy Features**:
- Descriptive statistics (mean, median, std, min, max, quartiles)
- Histogram visualization
- Box plot visualization
- Column selection interface
- Matplotlib integration

**Implementation Plan**:
- Create `StatisticsStudy` class in `src/studies/`
- Create `StatisticsWidget` in `src/ui/widgets/`
- Add to study type menu: New → Statistics
- Integrate with existing DataTableStudy data
- Reuse matplotlib patterns from PlotWidget

**Priority**: HIGH - Important analytical feature

---

### 3. Plot Export to Image
**Status**: ❌ Not Implemented  
**Legacy Location**: `src_legacy/widgets/plot_widget/plot_view.py`

**Legacy Features**:
- `export_image()` - Save plot as PNG/PDF/SVG
- DPI configuration
- Export dialog with format selection

**Implementation Plan**:
- Add `export_image()` method to `PlotWidget`
- Add toolbar action: "Export Plot..."
- Support formats: PNG, PDF, SVG
- Add DPI/quality settings in dialog

**Priority**: HIGH - Users need to save visualizations

---

## 🟡 Important Missing Features (Medium Priority)

### 4. Examples Menu
**Status**: ⚠️ Partially Implemented  
**Current**: Manual examples in `examples/` directory  
**Legacy**: Integrated menu with one-click loading

**Legacy Features**:
- Examples menu in menu bar
- One-click load of predefined datasets
- Multiple example datasets (projectile, ideal gas, harmonic oscillator, RC circuit)

**Implementation Plan**:
- Add "Examples" menu to main window
- Create example loader that instantiates studies
- Port example data generators from legacy
- Add examples: Projectile Motion, Ideal Gas, Harmonic Oscillator, RC Circuit

**Priority**: MEDIUM - Helpful for new users

---

### 5. Preferences/Settings Window
**Status**: ❌ Not Implemented  
**Legacy Location**: `src_legacy/ui/preference_window/`

**Legacy Features**:
- General preferences tab
- Appearance settings
- Default units
- Language selection
- Persistent configuration

**Implementation Plan**:
- Create `PreferencesDialog` in `src/ui/`
- Add Edit → Preferences menu item
- Implement configuration storage (JSON)
- Settings: theme, default units, language, auto-save

**Priority**: MEDIUM - Quality of life improvement

---

### 6. Enhanced Notifications/Dialogs
**Status**: ⚠️ Partially Implemented  
**Current**: Basic dialog_utils  
**Legacy**: Rich notification system

**Legacy Features**:
- `confirm_save()` - Save confirmation
- `confirm_overwrite()` - File overwrite confirmation
- `show_file_saved()` - Success notification
- `show_file_loaded()` - Load confirmation
- `show_not_implemented()` - Feature placeholder

**Implementation Plan**:
- Enhance `dialog_utils.py` with missing functions
- Add status bar notifications
- Implement auto-hide timed messages
- Add icons to notifications

**Priority**: MEDIUM - Better UX feedback

---

## 🟢 Nice-to-Have Features (Low Priority)

### 7. Undo/Redo System
**Status**: ❌ Not Implemented  
**Legacy**: Command pattern implementation

**Legacy Features**:
- Full undo/redo for all operations
- Command history
- Keyboard shortcuts (Ctrl+Z/Ctrl+Y)

**Implementation Plan**:
- Implement command pattern in studies
- Add undo stack to workspace
- Connect to Edit menu
- Support multi-level undo

**Priority**: LOW - Complex to implement correctly

---

### 8. Interpolation Columns
**Status**: ❌ Not Implemented  
**Legacy**: Part of column types

**Legacy Features**:
- Linear interpolation
- Cubic spline interpolation
- Interpolation dialog

**Implementation Plan**:
- Add INTERPOLATION column type
- Create AddInterpolationColumnDialog
- Use scipy for interpolation methods
- Add to column type menu

**Priority**: LOW - Specialized feature

---

### 9. Multi-language Support
**Status**: ❌ Not Implemented  
**Legacy**: Full i18n system

**Legacy Features**:
- Language manager
- Translation files (en_US, fr_FR)
- Dynamic language switching

**Implementation Plan**:
- Port language manager from legacy
- Update all UI strings to use tr()
- Create translation files
- Add language preference

**Priority**: LOW - Nice for international users

---

## ✅ Already Implemented (Verify)

### Workspace Save/Load
- ✅ Save workspace to JSON (.dmw format)
- ✅ Load workspace from JSON
- ✅ Serialization of studies and constants
- **Status**: Implemented in current main_window.py

### Plot Widget
- ✅ Add/remove series
- ✅ Matplotlib integration
- ✅ Plot refresh
- ❌ Export to image (missing)
- **Status**: Mostly implemented, needs export

### Constants System
- ✅ 3 types (numeric, calculated, functions)
- ✅ ConstantsWidget
- ✅ Workspace-level sharing
- **Status**: Fully implemented and enhanced

### Column Types
- ✅ DATA columns
- ✅ CALCULATED columns
- ✅ DERIVATIVE columns
- ✅ RANGE columns
- ✅ UNCERTAINTY columns (new!)
- **Status**: Fully implemented

---

## Implementation Priority Order

### Phase 1 (Immediate - This Week)
1. **CSV/Excel Export** - Essential for data sharing
2. **Plot Export** - Save visualizations
3. **Examples Menu** - Improve onboarding

### Phase 2 (Short-term - Next Week)
4. **Statistics Widget** - Key analytical feature
5. **Enhanced Notifications** - Better UX
6. **Preferences Window** - Configuration management

### Phase 3 (Medium-term - This Month)
7. **CSV/Excel Import** - Complete I/O cycle
8. **Interpolation Columns** - Advanced feature
9. **Undo/Redo** - Power user feature

### Phase 4 (Long-term - Future)
10. **Multi-language Support** - Internationalization
11. **Advanced Plot Features** - More chart types
12. **Plugin System** - Extensibility

---

## Estimated Effort

| Feature | Complexity | Lines of Code | Time Estimate |
|---------|-----------|---------------|---------------|
| CSV Export | Low | ~100 | 2-3 hours |
| Excel Export | Medium | ~150 | 3-4 hours |
| CSV Import | Medium | ~150 | 3-4 hours |
| Excel Import | Medium | ~200 | 4-5 hours |
| Plot Export | Low | ~80 | 2 hours |
| Examples Menu | Low | ~100 | 2-3 hours |
| Statistics Widget | High | ~400 | 8-10 hours |
| Preferences | Medium | ~300 | 5-6 hours |
| Interpolation | Medium | ~200 | 4-5 hours |
| Undo/Redo | High | ~500 | 12-15 hours |

**Total Effort (Phase 1)**: ~6-8 hours  
**Total Effort (Phase 1-2)**: ~25-30 hours  
**Total Effort (Complete)**: ~50-60 hours

---

## Notes

- All legacy code is preserved in `src_legacy/` for reference
- Focus on Phase 1 features first for complete rebase
- New architecture is cleaner - adaptations should be simpler than legacy
- Some features may be enhanced during porting (better than legacy)

---

## Next Steps

1. Review this document with team/user
2. Prioritize based on user needs
3. Start with Phase 1 implementation
4. Update TODO.md with specific tasks
5. Create feature branches for each major feature
