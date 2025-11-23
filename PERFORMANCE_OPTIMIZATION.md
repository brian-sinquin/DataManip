# Formula Engine Performance Optimizations

## Overview
The FormulaEngine has been optimized for blazing-fast calculations with multiple caching strategies and minimized overhead.

## Key Optimizations

### 1. Workspace Constants Caching
**Problem**: Workspace constants (numeric, calculated, functions) were re-evaluated from scratch for every column calculation.

**Solution**: 
- Cache evaluated workspace constants using workspace ID and version
- Only invalidate cache when workspace constants change
- Reuse cached constants across all column calculations

**Impact**: Eliminates O(n) multi-pass evaluation on every column, replacing with O(1) cache lookup.

### 2. Formula Compilation Caching  
**Problem**: Formula strings were parsed and transformed for every evaluation (extracting dependencies, replacing `{var}` syntax).

**Solution**:
- Pre-compile formulas into executable form
- Cache compiled formulas in `_compiled_formulas` dict
- Reuse compiled form for repeated evaluations

**Impact**: Eliminates repeated string operations and regex parsing.

### 3. Math Context Reuse
**Problem**: Math functions dictionary was copied on every context build.

**Solution**:
- Build math context once in `__init__`
- Reuse same dict via `update()` instead of copying
- Math functions are immutable, safe to share

**Impact**: Reduces memory allocation and dict copy overhead.

### 4. Optimized Context Building
**Problem**: Context was built inefficiently with multiple dict copies.

**Solution**:
- Build context in optimal order: base → math → cached constants
- Minimize dict copies by updating in-place where safe
- Fast-path for numeric constants (no circular dependency check needed)

**Impact**: Reduces context building from O(n²) to O(n) for n constants.

## Performance Results

### Benchmarks
From `examples/performance_benchmark.py`:

```
Benchmark 1: Workspace Constants (50 columns)
  Time: 0.041s
  Average: 0.82ms per column
  ✓ Workspace constants cached and reused

Benchmark 2: Formula Compilation (100 columns)
  Time: 0.127s
  Average: 1.27ms per column
  ✓ Formulas compiled once and cached

Benchmark 3: Large Dataset (10,000 points × 20 columns)
  Time: 0.021s
  Average: 1.05ms per column
  Throughput: 9.5M calculations/second
  ✓ Vectorized numpy operations
```

### Comprehensive Demo
`examples/comprehensive_demo.py` (17 columns, 61 points, complex calculations):
- Execution time: ~1.1 seconds
- Includes CSV/Excel export
- No warnings with optimized evaluation

## Cache Invalidation

### Workspace Version Tracking
The `Workspace` class maintains a version counter (`_version`) that increments whenever constants are modified:
- `add_constant()`: +1
- `add_calculated_variable()`: +1  
- `add_function()`: +1
- `remove_constant()`: +1

### Automatic Cache Invalidation
When `DataTableStudy._recalculate_column()` is called:
1. Gets current workspace version
2. Compares with cached version
3. If version changed: re-evaluate and update cache
4. If version same: reuse cached constants

### Manual Invalidation
For advanced use cases:
```python
engine.invalidate_workspace_cache()  # Clear all
engine.invalidate_workspace_cache(workspace_id)  # Clear specific
```

## Implementation Details

### FormulaEngine Caches
```python
self._workspace_cache: Dict[int, Dict[str, Any]]  # {workspace_id: constants}
self._workspace_cache_version: Dict[int, int]     # {workspace_id: version}
self._compiled_formulas: Dict[str, tuple]          # {formula: (eval_formula, deps)}
```

### Key Methods
- `build_context_with_workspace()`: Main entry point with caching
- `_evaluate_workspace_constants()`: Multi-pass evaluation (cached)
- `evaluate()`: Formula evaluation with compilation cache
- `invalidate_workspace_cache()`: Manual cache clearing

## Testing
All 149 unit tests pass, confirming:
- Correctness maintained
- Backward compatibility
- No regressions
- Cache invalidation works correctly

## Future Enhancements
Possible further optimizations:
1. **Compiled Python code**: Use `compile()` to create code objects
2. **Numba JIT**: Compile hot paths with numba for near-C speed
3. **Parallel evaluation**: Evaluate independent columns in parallel
4. **Lazy evaluation**: Only evaluate columns when accessed
5. **Incremental updates**: Only recalculate changed rows
