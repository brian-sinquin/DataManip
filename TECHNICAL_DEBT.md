# Technical Debt & TODO Tracking

This document tracks technical debt, TODOs, and future improvements for the DataManip project.

## Active TODOs

### High Priority

#### 1. CSV Metadata Parsing
**Location**: `src/studies/data_table_study.py:1005`
**Status**: Planned
**Description**: Parse metadata from CSV comments when `has_metadata=True`

**Current Behavior**: Metadata comments in exported CSV files are not parsed on import

**Proposed Solution**:
```python
# Parse lines starting with "# Column Metadata:"
# Extract type, unit, formula, etc. from comment format
# Reconstruct column_metadata dictionary
```

**Impact**: Medium - Would enable full round-trip of study data
**Estimated Effort**: 2-3 hours

---

#### 2. Excel Data Section Detection
**Location**: `src/studies/data_table_study.py:1130`
**Status**: Planned
**Description**: Implement smarter parsing to find data section in Excel files

**Current Behavior**: Assumes data starts at specific row
**Proposed Solution**:
```python
# Search for "Data:" marker or first numeric row
# Auto-detect header vs metadata sections
# Handle variable metadata lengths
```

**Impact**: Low - Most imports work with current assumptions
**Estimated Effort**: 1-2 hours

---

### Medium Priority

#### 3. Theme System Integration
**Location**: `src/ui/main_window.py:1116`
**Status**: Deferred
**Description**: Implement theme switching when theme system is added

**Dependencies**: Requires theme system framework to be implemented first

**Proposed Features**:
- Light/Dark theme toggle
- Custom color schemes
- Persistent theme preference
- System theme detection

**Impact**: Low - UI enhancement, not critical functionality
**Estimated Effort**: 4-6 hours (after theme system exists)

---

## Resolved TODOs

### ✅ Uncertainty Propagation (Completed Nov 23, 2025)
- Extracted to `src/utils/uncertainty_propagation.py`
- Fixed workspace constant handling
- Added proper error handling

### ✅ Logging Framework (Completed Nov 23, 2025)
- Created `src/utils/logging_config.py`
- Replaced print statements with proper logging
- Added module-specific loggers

### ✅ Dialog Base Classes (Completed Nov 23, 2025)
- Created `src/ui/widgets/shared/base_dialog.py`
- Reduced code duplication across dialogs

---

## Technical Debt

### Code Organization

#### 1. Dialog Consolidation (In Progress)
**Priority**: Medium
**Description**: Refactor existing dialogs to use BaseDialog

**Files to Update**:
- `src/ui/widgets/column_dialogs.py` (845 lines)
- `src/ui/widgets/column_dialogs_extended.py` (424 lines)

**Expected Reduction**: 400-500 lines

---

#### 2. Data Table Study Modularization
**Priority**: Low
**Description**: Split `data_table_study.py` into logical modules

**Proposed Structure**:
```
src/studies/data_table/
├── __init__.py
├── base_study.py          # Core study class
├── column_operations.py   # Add/remove/rename columns
├── calculation_engine.py  # Formula evaluation
├── io_operations.py       # Import/export
└── derivatives.py         # Numerical differentiation
```

**Benefits**:
- Easier to navigate and understand
- Better separation of concerns
- Simplified testing

**Estimated Effort**: 6-8 hours

---

### Testing Gaps

#### 1. Uncertainty Propagation Tests
**Priority**: High
**Status**: Needed

**Test Cases**:
- Basic propagation with 2 variables
- Workspace constants in formulas
- Missing uncertainties (should use 0)
- Error handling for invalid formulas

---

#### 2. Dialog Base Class Tests
**Priority**: Medium
**Status**: Needed

**Test Cases**:
- Form building
- Validation framework
- Button handling
- Error messages

---

### Performance Optimization Opportunities

#### 1. Parallel Column Calculation
**Current**: Sequential evaluation of independent columns
**Proposed**: Use ThreadPoolExecutor for independent columns
**Impact**: Could reduce calculation time by 2-4x for large tables
**Risk**: Low - already implemented but needs more testing

---

#### 2. Formula Compilation Caching
**Status**: ✅ Implemented
**Impact**: Reduced formula evaluation overhead

---

## Future Enhancements

### Nice to Have

1. **Undo/Redo for Formula Changes**
   - Track formula modifications
   - Allow rollback of calculations
   - Priority: Low

2. **Auto-save Functionality**
   - Periodic workspace save
   - Crash recovery
   - Priority: Medium

3. **Formula Debugger**
   - Step-through evaluation
   - Intermediate value display
   - Priority: Low

4. **Custom Function Library**
   - User-defined function repository
   - Import/export functions
   - Priority: Low

---

## Maintenance Notes

### Deprecation Warnings

None currently.

### Breaking Changes Planned

None for v0.2.x series.

---

## How to Update This Document

When adding a TODO:
1. Add entry under appropriate priority section
2. Include location, description, and estimated effort
3. Add "Status" field (Planned/In Progress/Blocked)

When resolving a TODO:
1. Move to "Resolved TODOs" section
2. Add completion date
3. Link to relevant commit/PR if applicable

When identifying technical debt:
1. Add to "Technical Debt" section
2. Explain impact and proposed solution
3. Estimate effort required

---

**Last Updated**: November 23, 2025
**Next Review**: December 1, 2025
