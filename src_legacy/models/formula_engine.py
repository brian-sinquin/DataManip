"""
Formula evaluation and dependency tracking engine.

This module provides Qt-independent formula evaluation with automatic
dependency tracking and topological sorting for recalculation order.
"""

from typing import Dict, Set, List, Tuple, Optional, Any
import pandas as pd
from utils.formula_parser import FormulaParser, FormulaError
from utils.exceptions import ColumnNotFoundError


class FormulaEngine:
    """Formula evaluation engine with dependency tracking.
    
    Manages formula dependencies as a directed acyclic graph (DAG) and
    determines optimal recalculation order using topological sorting.
    
    Attributes:
        _dependencies: Maps each column to the columns it depends on
        _dependents: Maps each column to the columns that depend on it
        _formula_parser: Parser for evaluating formulas
    """
    
    def __init__(self):
        """Initialize formula engine."""
        self._dependencies: Dict[str, Set[str]] = {}  # {col: {depends_on}}
        self._dependents: Dict[str, Set[str]] = {}    # {col: {dependent_cols}}
        self._formula_parser = FormulaParser()
    
    # ========================================================================
    # Dependency Registration
    # ========================================================================
    
    def register_formula(self, column_name: str, formula: str) -> List[str]:
        """Register a formula and its dependencies.
        
        Args:
            column_name: Name of the column with the formula
            formula: Formula string using {column_name} syntax
            
        Returns:
            List of column names this formula depends on
            
        Raises:
            FormulaError: If formula is invalid
        """
        # Extract dependencies from formula
        dependencies = self._formula_parser.extract_dependencies(formula)
        
        # Clear old dependencies
        if column_name in self._dependencies:
            old_deps = self._dependencies[column_name]
            for old_dep in old_deps:
                if old_dep in self._dependents:
                    self._dependents[old_dep].discard(column_name)
        
        # Register new dependencies
        self._dependencies[column_name] = set(dependencies)
        
        for dep in dependencies:
            if dep not in self._dependents:
                self._dependents[dep] = set()
            self._dependents[dep].add(column_name)
        
        return dependencies
    
    def unregister_column(self, column_name: str) -> None:
        """Remove all dependency information for a column.
        
        Args:
            column_name: Name of column to unregister
        """
        # Remove from dependencies
        if column_name in self._dependencies:
            del self._dependencies[column_name]
        
        # Remove from dependents
        if column_name in self._dependents:
            del self._dependents[column_name]
        
        # Remove from other columns' dependencies
        for col_deps in self._dependencies.values():
            col_deps.discard(column_name)
        
        # Remove from other columns' dependents
        for col_deps in self._dependents.values():
            col_deps.discard(column_name)
    
    def get_dependencies(self, column_name: str) -> Set[str]:
        """Get columns that this column depends on.
        
        Args:
            column_name: Column name
            
        Returns:
            Set of column names this column depends on
        """
        return self._dependencies.get(column_name, set()).copy()
    
    def get_dependents(self, column_name: str) -> Set[str]:
        """Get columns that depend on this column.
        
        Args:
            column_name: Column name
            
        Returns:
            Set of column names that depend on this column
        """
        return self._dependents.get(column_name, set()).copy()
    
    def has_dependents(self, column_name: str) -> bool:
        """Check if any columns depend on this column.
        
        Args:
            column_name: Column name
            
        Returns:
            True if any columns depend on this one
        """
        return column_name in self._dependents and len(self._dependents[column_name]) > 0
    
    # ========================================================================
    # Recalculation Order
    # ========================================================================
    
    def get_recalculation_order(self, changed_columns: List[str]) -> List[str]:
        """Get columns to recalculate in dependency order.
        
        Uses breadth-first search to find all affected columns, then
        topologically sorts them to ensure correct calculation order.
        
        Args:
            changed_columns: Names of columns that changed
            
        Returns:
            List of column names in calculation order (dependent columns
            appear after the columns they depend on)
            
        Raises:
            FormulaError: If circular dependency detected
        """
        # Find all columns affected by changes (BFS)
        to_recalc = set()
        queue = list(changed_columns)
        visited = set()
        
        while queue:
            col = queue.pop(0)
            if col in visited:
                continue
            visited.add(col)
            
            # Add dependents to recalculation set
            if col in self._dependents:
                for dependent in self._dependents[col]:
                    if dependent not in to_recalc:
                        to_recalc.add(dependent)
                        queue.append(dependent)
        
        # Topological sort to get calculation order
        sorted_cols = []
        remaining = to_recalc.copy()
        
        max_iterations = len(remaining) + 1
        iteration = 0
        
        while remaining:
            iteration += 1
            if iteration > max_iterations:
                # Circular dependency detected
                raise FormulaError(
                    f"Circular dependency detected involving: {', '.join(sorted(remaining))}"
                )
            
            # Find columns with no unresolved dependencies
            ready = []
            for col in remaining:
                deps = self._dependencies.get(col, set())
                # Only check dependencies within the recalculation set
                unresolved_deps = deps & remaining
                if not unresolved_deps:
                    ready.append(col)
            
            if not ready:
                # Circular dependency detected
                raise FormulaError(
                    f"Circular dependency detected involving: {', '.join(sorted(remaining))}"
                )
            
            # Add ready columns in sorted order for determinism
            ready.sort()
            sorted_cols.extend(ready)
            remaining -= set(ready)
        
        return sorted_cols
    
    # ========================================================================
    # Formula Evaluation
    # ========================================================================
    
    def evaluate_formula(
        self,
        formula: str,
        data: Dict[str, pd.Series],
        variables: Optional[Dict[str, Tuple[float, Optional[str]]]] = None,
        row_count: int = 0
    ) -> pd.Series:
        """Evaluate a formula using available data.
        
        Args:
            formula: Formula string using {column_name} syntax
            data: Dictionary mapping column names to their data
            variables: Optional global variables/constants
            row_count: Expected number of rows in result
            
        Returns:
            Pandas Series with formula results
            
        Raises:
            FormulaError: If formula evaluation fails
            ColumnNotFoundError: If formula references missing columns
        """
        # Extract dependencies
        dependencies = self._formula_parser.extract_dependencies(formula)
        
        # Check all dependencies are available
        missing = [dep for dep in dependencies if dep not in data]
        if missing:
            raise ColumnNotFoundError(
                f"Formula references undefined columns: {', '.join(missing)}"
            )
        
        # Prepare context for evaluation
        context = {}
        
        # Add column data
        for dep in dependencies:
            context[dep] = data[dep]
        
        # Add variables
        if variables:
            for var_name, (var_value, var_unit) in variables.items():
                context[var_name] = var_value
        
        # Evaluate formula
        try:
            result = self._formula_parser.evaluate(formula, context)
            
            # Ensure result is a Series
            if not isinstance(result, pd.Series):
                if isinstance(result, (int, float)):
                    result = pd.Series([result] * row_count)
                else:
                    result = pd.Series(result)
            
            return result
            
        except Exception as e:
            raise FormulaError(f"Formula evaluation failed: {str(e)}")
    
    def extract_dependencies(self, formula: str) -> List[str]:
        """Extract column dependencies from a formula.
        
        Args:
            formula: Formula string using {column_name} syntax
            
        Returns:
            List of column names referenced in the formula
        """
        return self._formula_parser.extract_dependencies(formula)
    
    # ========================================================================
    # Validation
    # ========================================================================
    
    def validate_formula(
        self,
        formula: str,
        available_columns: List[str],
        target_column: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """Validate a formula before registration.
        
        Args:
            formula: Formula string to validate
            available_columns: List of available column names
            target_column: Optional name of column this formula will be assigned to
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Extract dependencies
            deps = self._formula_parser.extract_dependencies(formula)
            
            # Check all dependencies exist
            missing = [dep for dep in deps if dep not in available_columns]
            if missing:
                return False, f"Formula references undefined columns: {', '.join(missing)}"
            
            # Check for self-reference
            if target_column and target_column in deps:
                return False, f"Formula cannot reference itself: {target_column}"
            
            # Check for circular dependencies (if target_column provided)
            if target_column:
                # Save current state
                old_deps = self._dependencies.get(target_column, set()).copy()
                old_dependents_for_target = self._dependents.get(target_column, set()).copy()
                
                # Temporarily register formula
                self._dependencies[target_column] = set(deps)
                
                # Update dependents
                for dep in deps:
                    if dep not in self._dependents:
                        self._dependents[dep] = set()
                    self._dependents[dep].add(target_column)
                
                try:
                    # Try to get recalculation order - this will detect cycles
                    self.get_recalculation_order([target_column])
                except FormulaError as e:
                    # Restore old state
                    if old_deps:
                        self._dependencies[target_column] = old_deps
                    elif target_column in self._dependencies:
                        del self._dependencies[target_column]
                    
                    if old_dependents_for_target:
                        self._dependents[target_column] = old_dependents_for_target
                    elif target_column in self._dependents:
                        del self._dependents[target_column]
                    
                    # Remove from dependents
                    for dep in deps:
                        if dep in self._dependents:
                            self._dependents[dep].discard(target_column)
                            if not self._dependents[dep]:
                                del self._dependents[dep]
                    
                    return False, str(e)
                
                # Restore old state (validation passed)
                if old_deps:
                    self._dependencies[target_column] = old_deps
                elif target_column in self._dependencies:
                    del self._dependencies[target_column]
                
                if old_dependents_for_target:
                    self._dependents[target_column] = old_dependents_for_target
                elif target_column in self._dependents:
                    del self._dependents[target_column]
                
                # Remove from dependents
                for dep in deps:
                    if dep in self._dependents:
                        self._dependents[dep].discard(target_column)
                        if not self._dependents[dep]:
                            del self._dependents[dep]
            
            return True, None
            
        except Exception as e:
            return False, f"Formula validation error: {str(e)}"
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def clear(self) -> None:
        """Clear all dependency information."""
        self._dependencies.clear()
        self._dependents.clear()
    
    def get_all_formulas(self) -> Dict[str, Set[str]]:
        """Get all registered formulas and their dependencies.
        
        Returns:
            Dictionary mapping column names to their dependencies
        """
        return {col: deps.copy() for col, deps in self._dependencies.items()}
    
    def to_dict(self) -> Dict[str, Any]:
        """Export formula engine state to dictionary.
        
        Returns:
            Dictionary with dependencies and dependents
        """
        return {
            'dependencies': {col: list(deps) for col, deps in self._dependencies.items()},
            'dependents': {col: list(deps) for col, deps in self._dependents.items()}
        }
