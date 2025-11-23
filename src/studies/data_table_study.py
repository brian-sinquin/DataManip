"""
DataTable study for numerical data manipulation.

Provides tabular data editing with formula columns, units,
and uncertainty tracking.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
import sympy as sp

from core.study import Study
from core.data_object import DataObject
from core.formula_engine import FormulaEngine
from utils.uncertainty import FormulaToSymPy


class ColumnType:
    """Column type enumeration."""
    DATA = "data"
    CALCULATED = "calculated"
    DERIVATIVE = "derivative"  # Numerical differentiation
    RANGE = "range"  # Generated ranges
    UNCERTAINTY = "uncertainty"  # Propagated uncertainties
    INTERPOLATION = "interpolation"  # Future


class DataTableStudy(Study):
    """Study for numerical data tables.
    
    Features:
    - Multiple column types (data, calculated, derived, etc.)
    - Formula evaluation with dependency tracking
    - Unit tracking and conversion
    - Uncertainty propagation
    - Variables/constants
    
    Attributes:
        table: Main DataObject containing the table
        column_metadata: Metadata for each column (type, formula, unit)
        variables: Global variables/constants
        formula_engine: Formula evaluator
    """
    
    def __init__(self, name: str, workspace=None):
        """Initialize DataTable study.
        
        Args:
            name: Study name
            workspace: Reference to parent workspace for variables access
        """
        super().__init__(name)
        
        # Reference to workspace for variables/constants
        self.workspace = workspace
        
        # Create main table DataObject
        self.table = DataObject.empty(name="main_table")
        self.add_data_object(self.table)
        
        # Column metadata: {col_name: {type, formula, unit, uncertainty}}
        self.column_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Formula engine
        self.formula_engine = FormulaEngine()
    
    def get_type(self) -> str:
        """Get study type identifier."""
        return "data_table"
    
    # ========================================================================
    # Column Management
    # ========================================================================
    
    def add_column(
        self,
        name: str,
        column_type: str = ColumnType.DATA,
        formula: Optional[str] = None,
        unit: Optional[str] = None,
        initial_data: Optional[pd.Series] = None,
        # Derivative-specific
        derivative_of: Optional[str] = None,
        with_respect_to: Optional[str] = None,
        order: int = 1,
        # Range-specific
        range_type: Optional[str] = None,  # "linspace", "arange", "logspace"
        range_start: Optional[float] = None,
        range_stop: Optional[float] = None,
        range_count: Optional[int] = None,
        range_step: Optional[float] = None,
        # Uncertainty-specific
        propagate_uncertainty: bool = False,
        uncertainty_reference: Optional[str] = None
    ):
        """Add column to table.
        
        Args:
            name: Column name
            column_type: Column type (DATA, CALCULATED, DERIVATIVE, RANGE, UNCERTAINTY)
            formula: Formula string (for calculated columns)
            unit: Physical unit
            initial_data: Initial column values
            derivative_of: Source column for derivative (DERIVATIVE type)
            with_respect_to: Independent variable column (DERIVATIVE type)
            order: Derivative order (1=first, 2=second, etc.)
            range_type: Range generation method (RANGE type)
            range_start: Start value (RANGE type)
            range_stop: Stop value (RANGE type)
            range_count: Number of points (linspace, logspace)
            range_step: Step size (arange)
            propagate_uncertainty: Auto-calculate uncertainty (CALCULATED type)
            uncertainty_reference: Parent column name (UNCERTAINTY type)
        """
        # Add column to DataObject
        if initial_data is not None:
            self.table.set_column(name, initial_data)
        else:
            self.table.add_column(name)
        
        # Store metadata
        self.column_metadata[name] = {
            "type": column_type,
            "formula": formula,
            "unit": unit,
            "uncertainty": None,
            "derivative_of": derivative_of,
            "with_respect_to": with_respect_to,
            "order": order,
            "range_type": range_type,
            "range_start": range_start,
            "range_stop": range_stop,
            "range_count": range_count,
            "range_step": range_step,
            "propagate_uncertainty": propagate_uncertainty,
            "uncertainty_reference": uncertainty_reference
        }
        
        # Handle by type
        if column_type == ColumnType.CALCULATED and formula:
            self.formula_engine.register_formula(name, formula)
            if len(self.table.data) > 0:
                self._recalculate_column(name)
            
            # Auto-create uncertainty column if requested
            if propagate_uncertainty:
                uncert_name = f"{name}_u"
                if uncert_name not in self.column_metadata:
                    uncert_values = self._calculate_propagated_uncertainty(name)
                    self.add_column(
                        uncert_name,
                        column_type=ColumnType.UNCERTAINTY,
                        unit=unit,  # Same unit as parent
                        initial_data=uncert_values,
                        uncertainty_reference=name
                    )
        
        elif column_type == ColumnType.DERIVATIVE:
            if len(self.table.data) > 0:
                self._calculate_derivative(name)
        elif column_type == ColumnType.RANGE:
            self._generate_range(name)
    
    def remove_column(self, name: str):
        """Remove column from table.
        
        Args:
            name: Column name
        """
        self.table.remove_column(name)
        if name in self.column_metadata:
            del self.column_metadata[name]
    
    def rename_column(self, old_name: str, new_name: str):
        """Rename a column.
        
        Args:
            old_name: Current column name
            new_name: New column name
        """
        # Rename in DataFrame
        self.table.data.rename(columns={old_name: new_name}, inplace=True)
        
        # Update metadata
        if old_name in self.column_metadata:
            self.column_metadata[new_name] = self.column_metadata.pop(old_name)
        
        # Update formulas that reference this column
        for col_name, metadata in list(self.column_metadata.items()):
            if col_name == new_name:
                # Skip the renamed column itself
                continue
            
            formula = metadata.get("formula")
            if formula and f"{{{old_name}}}" in formula:
                # Replace {old_name} with {new_name} in formulas
                new_formula = formula.replace(f"{{{old_name}}}", f"{{{new_name}}}")
                metadata["formula"] = new_formula
                # Re-register with formula engine if it's a calculated column
                if metadata.get("type") in (ColumnType.CALCULATED, ColumnType.DATA):
                    self.formula_engine.register_formula(col_name, new_formula)
        
        # Re-register renamed column's formula with formula engine (if it has one)
        renamed_metadata = self.column_metadata.get(new_name, {})
        formula = renamed_metadata.get("formula")
        if formula:
            self.formula_engine.register_formula(new_name, formula)
        
        # Recalculate dependent columns
        self.recalculate_all()
    
    def get_column_type(self, name: str) -> str:
        """Get column type.
        
        Args:
            name: Column name
            
        Returns:
            Column type string
        """
        return self.column_metadata.get(name, {}).get("type", ColumnType.DATA)
    
    def get_column_formula(self, name: str) -> Optional[str]:
        """Get column formula.
        
        Args:
            name: Column name
            
        Returns:
            Formula string or None
        """
        return self.column_metadata.get(name, {}).get("formula")
    
    def get_column_unit(self, name: str) -> Optional[str]:
        """Get column unit.
        
        Args:
            name: Column name
            
        Returns:
            Unit string or None
        """
        return self.column_metadata.get(name, {}).get("unit")
    
    # ========================================================================
    # Formula Evaluation
    # ========================================================================
    
    def _generate_range(self, name: str):
        """Generate range data for a column.
        
        Args:
            name: Range column name
        """
        meta = self.column_metadata[name]
        range_type = meta.get("range_type")
        start = meta.get("range_start")
        stop = meta.get("range_stop")
        count = meta.get("range_count")
        step = meta.get("range_step")
        
        if not range_type:
            return
        
        # Generate data based on type
        data = None
        if range_type == "linspace":
            if start is not None and stop is not None and count is not None:
                data = np.linspace(start, stop, count)
        elif range_type == "arange":
            if start is not None and stop is not None:
                if step is None:
                    step = 1.0
                data = np.arange(start, stop, step)
        elif range_type == "logspace":
            if start is not None and stop is not None and count is not None:
                data = np.logspace(start, stop, count)
        
        if data is None:
            return
        
        # Store result - handle different lengths
        if len(self.table.data) == 0:
            # First column - initialize DataFrame
            self.table.data = pd.DataFrame({name: data})
        else:
            # Extend or truncate table to match new column length
            current_len = len(self.table.data)
            new_len = len(data)
            
            if new_len > current_len:
                # Extend table
                self.table.data = pd.concat([
                    self.table.data,
                    pd.DataFrame(index=range(current_len, new_len))
                ], ignore_index=True)
            
            # Now add the column (will fill NaN if shorter than table)
            if new_len < len(self.table.data):
                # Pad with NaN
                padded_data = np.full(len(self.table.data), np.nan)
                padded_data[:new_len] = data
                self.table.data[name] = padded_data
            else:
                self.table.data[name] = data
    
    def _calculate_derivative(self, name: str):
        """Calculate numerical derivative for a column.
        
        Args:
            name: Derivative column name
        """
        meta = self.column_metadata[name]
        y_col = meta.get("derivative_of")
        x_col = meta.get("with_respect_to")
        order = meta.get("order", 1)
        
        if not y_col or not x_col:
            return
        
        # Get data
        y = self.table.get_column(y_col).values
        x = self.table.get_column(x_col).values
        
        # Calculate derivative using numpy gradient
        deriv = np.gradient(y, x)
        
        # Higher order derivatives
        for _ in range(1, order):
            deriv = np.gradient(deriv, x)
        
        # Store result
        self.table.set_column(name, pd.Series(deriv))
    
    def _calculate_propagated_uncertainty(self, name: str) -> pd.Series:
        """Calculate propagated uncertainty for a calculated column.
        
        Uses symbolic differentiation to compute: δf = √(Σ(∂f/∂xᵢ · δxᵢ)²)
        
        Args:
            name: Calculated column name
            
        Returns:
            Series of propagated uncertainties
        """
        meta = self.column_metadata.get(name)
        if not meta or meta.get("type") != ColumnType.CALCULATED:
            # Return NaN series if not a calculated column
            return pd.Series([np.nan] * len(self.table.data))
        
        formula = meta.get("formula")
        if not formula:
            return pd.Series([np.nan] * len(self.table.data))
        
        # Extract dependencies from formula
        dependencies = self.formula_engine.extract_dependencies(formula)
        
        # Collect values and uncertainties for each dependency
        values = {}
        uncertainties = {}
        
        for dep in dependencies:
            if dep not in self.table.columns:
                continue
            
            # Add the value series
            values[dep] = self.table.get_column(dep)
            
            # Check if uncertainty column exists
            uncert_col_name = f"{dep}_u"
            if uncert_col_name in self.table.columns:
                uncertainties[dep] = self.table.get_column(uncert_col_name)
        
        # If no uncertainties available, return zeros
        if not uncertainties:
            return pd.Series([0.0] * len(self.table.data))
        
        # Prepare formula for SymPy (remove curly braces)
        formula_for_sympy = formula
        for dep in dependencies:
            formula_for_sympy = formula_for_sympy.replace(f"{{{dep}}}", dep)
        
        try:
            # Convert to SymPy expression
            sympy_expr = FormulaToSymPy.convert(formula_for_sympy, list(dependencies))
            
            # Calculate partial derivatives
            partial_derivs = {}
            for var_name in dependencies:
                var_symbol = sp.Symbol(var_name)
                partial_derivs[var_name] = sp.diff(sympy_expr, var_symbol)
            
            # Calculate uncertainty for each row
            result_uncertainties = []
            
            for i in range(len(self.table.data)):
                # Get values for this row
                row_values = {var: values[var].iloc[i] for var in dependencies}
                row_uncerts = {var: uncertainties.get(var, pd.Series([0.0] * len(self.table.data))).iloc[i]
                              for var in dependencies}
                
                # If any input value is NaN, result uncertainty is NaN
                if any(pd.isna(row_values[var]) for var in dependencies):
                    result_uncertainties.append(np.nan)
                    continue
                
                # Calculate variance contributions
                variance = 0.0
                
                for var_name in dependencies:
                    # Skip if no uncertainty for this variable
                    if var_name not in uncertainties:
                        continue
                    
                    # Get value and uncertainty for this variable
                    var_uncert = row_uncerts[var_name]
                    
                    # Skip if uncertainty is NaN
                    if pd.isna(var_uncert):
                        continue
                    
                    # Evaluate partial derivative at this point
                    try:
                        # Substitute all variable values
                        subs_dict = {sp.Symbol(var): val for var, val in row_values.items()
                                    if not pd.isna(val)}
                        deriv_value = float(partial_derivs[var_name].evalf(subs=subs_dict))
                        
                        # Add contribution to variance: (∂f/∂xᵢ * δxᵢ)²
                        contribution = deriv_value * var_uncert
                        variance += contribution ** 2
                        
                    except Exception:
                        # If evaluation fails, mark as NaN
                        variance = np.nan
                        break
                
                # Combined uncertainty = sqrt(variance)
                if pd.isna(variance):
                    result_uncertainties.append(np.nan)
                else:
                    result_uncertainties.append(np.sqrt(variance))
            
            return pd.Series(result_uncertainties)
        except Exception as e:
            # If calculation fails, return NaN
            print(f"Warning: Uncertainty calculation failed for {name}: {e}")
            return pd.Series([np.nan] * len(self.table.data))
    
    def _recalculate_column(self, name: str):
        """Recalculate a formula column.
        
        Args:
            name: Column name
        """
        formula = self.get_column_formula(name)
        if not formula:
            return
        
        # Build evaluation context
        context = {}
        
        # Add all data columns (convert Series to numpy arrays for cleaner evaluation)
        for col_name in self.table.columns:
            col_data = self.table.get_column(col_name)
            # Convert to numpy array, replacing None with nan
            if isinstance(col_data, pd.Series):
                arr = col_data.values
                # Convert None to nan for proper numeric operations
                arr = np.where(pd.isna(arr), np.nan, arr).astype(float)
                context[col_name] = arr
            else:
                context[col_name] = col_data
        
        # Add constants and functions from workspace
        if self.workspace:
            # First pass: collect all constant definitions
            const_defs = {}
            for const_name, const_data in self.workspace.constants.items():
                const_type = const_data.get("type")
                const_defs[const_name] = (const_type, const_data)
            
            # Helper to recursively evaluate calculated constants
            def evaluate_constant(name, visited=None):
                if visited is None:
                    visited = set()
                
                # Check for circular dependency
                if name in visited:
                    raise ValueError(f"Circular dependency detected in calculated constant: {name}")
                
                # Return cached value if already computed
                if name in context:
                    return context[name]
                
                if name not in const_defs:
                    return None
                
                const_type, const_data = const_defs[name]
                
                if const_type == "constant":
                    # Numeric constant
                    context[name] = const_data["value"]
                    return context[name]
                
                elif const_type == "calculated":
                    # Calculated constant - need to evaluate its formula
                    calc_formula = const_data["formula"]
                    
                    # Add to visited to detect circular refs
                    visited = visited.copy()  # Use a copy for this branch
                    visited.add(name)
                    
                    # Build context for evaluation - include other constants
                    calc_context = {}
                    
                    # Add numpy functions
                    calc_context['np'] = np
                    calc_context['pd'] = pd
                    calc_context.update({
                        'sqrt': np.sqrt,
                        'sin': np.sin,
                        'cos': np.cos,
                        'tan': np.tan,
                        'exp': np.exp,
                        'log': np.log,
                        'log10': np.log10,
                        'abs': np.abs,
                        'pi': np.pi,
                        'e': np.e,
                        'arcsin': np.arcsin,
                        'arccos': np.arccos,
                        'arctan': np.arctan,
                    })
                    
                    # Add only the constants that are dependencies (already evaluated)
                    # OR recursively evaluate constants on-demand
                    for other_name in const_defs:
                        if other_name != name and other_name not in visited:
                            # Only evaluate if not in visited (avoids circular ref)
                            val = evaluate_constant(other_name, visited)
                            if val is not None:
                                calc_context[other_name] = val
                    
                    # Evaluate the calculated constant
                    try:
                        result = eval(calc_formula, {"__builtins__": {}}, calc_context)
                        context[name] = result
                        return result
                    except Exception as e:
                        print(f"Warning: Failed to evaluate calculated constant {name}: {e}")
                        return None
                
                elif const_type == "function":
                    # Custom function - convert to callable
                    func_formula = const_data["formula"]
                    func_params = const_data["parameters"]
                    
                    # Create a Python function that evaluates the formula
                    def make_function(formula_str, params):
                        def custom_func(*args):
                            # Build context for function evaluation
                            func_context = dict(zip(params, args))
                            # Add numpy functions
                            func_context['np'] = np
                            func_context['pd'] = pd
                            func_context.update({
                                'sqrt': np.sqrt,
                                'sin': np.sin,
                                'cos': np.cos,
                                'tan': np.tan,
                                'exp': np.exp,
                                'log': np.log,
                                'log10': np.log10,
                                'abs': np.abs,
                                'pi': np.pi,
                                'e': np.e,
                                'arcsin': np.arcsin,
                                'arccos': np.arccos,
                                'arctan': np.arctan,
                            })
                            # Replace {param} with param in formula
                            eval_formula = formula_str
                            for param in params:
                                eval_formula = eval_formula.replace(f"{{{param}}}", param)
                            # Evaluate
                            return eval(eval_formula, {"__builtins__": {}}, func_context)
                        return custom_func
                    
                    context[name] = make_function(func_formula, func_params)
                    return context[name]
                
                return None
            
            # Evaluate all constants
            for const_name in const_defs:
                evaluate_constant(const_name)
        
        # Evaluate formula
        try:
            result = self.formula_engine.evaluate(formula, context)
        except Exception as e:
            # If evaluation fails, fill with NaN
            print(f"Warning: Failed to calculate {name}: {e}")
            result = np.full(len(self.table.data), np.nan)
        
        # Store result (convert back to Series if needed)
        if not isinstance(result, pd.Series):
            result = pd.Series(result)
        
        self.table.set_column(name, result)
    
    def recalculate_all(self):
        """Recalculate all formula and derivative columns in dependency order."""
        # Recalculate calculated columns
        calc_columns = [
            name for name, meta in self.column_metadata.items()
            if meta.get("type") == ColumnType.CALCULATED
        ]
        for col_name in calc_columns:
            self._recalculate_column(col_name)
            
            # Update uncertainty column if it exists
            if self.column_metadata[col_name].get("propagate_uncertainty"):
                uncert_name = f"{col_name}_u"
                if uncert_name in self.column_metadata:
                    uncert_values = self._calculate_propagated_uncertainty(col_name)
                    self.table.set_column(uncert_name, uncert_values)
        
        # Recalculate derivative columns
        deriv_columns = [
            name for name, meta in self.column_metadata.items()
            if meta.get("type") == ColumnType.DERIVATIVE
        ]
        for col_name in deriv_columns:
            self._calculate_derivative(col_name)
    
    def on_data_changed(self, column_name: str):
        """Handle data change in a column.
        
        Args:
            column_name: Changed column name
        """
        # Get affected columns
        affected = self.formula_engine.get_calculation_order([column_name])
        
        # Recalculate affected columns
        for col_name in affected:
            self._recalculate_column(col_name)
            
            # Update uncertainty column if it exists
            if self.column_metadata.get(col_name, {}).get("propagate_uncertainty"):
                uncert_name = f"{col_name}_u"
                if uncert_name in self.column_metadata:
                    uncert_values = self._calculate_propagated_uncertainty(col_name)
                    self.table.set_column(uncert_name, uncert_values)
    
    # Variables are managed at workspace level via workspace.constants
    # Access via self.workspace.constants (type="constant")
    
    # ========================================================================
    # Row Operations
    # ========================================================================
    
    def add_rows(self, count: int):
        """Add rows to table.
        
        Args:
            count: Number of rows to add
        """
        current_rows = len(self.table.data)
        new_rows = pd.DataFrame(
            index=range(current_rows, current_rows + count),
            columns=self.table.columns
        )
        self.table.data = pd.concat([self.table.data, new_rows], ignore_index=True)
        
        # Recalculate formula columns
        self.recalculate_all()
    
    def remove_rows(self, indices: List[int]):
        """Remove rows from table.
        
        Args:
            indices: List of row indices to remove
        """
        self.table.data = self.table.data.drop(index=indices).reset_index(drop=True)
        
        # Recalculate formula columns
        self.recalculate_all()
    
    # ========================================================================
    # Serialization
    # ========================================================================
    
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            "column_metadata": self.column_metadata,
            # Variables are stored at workspace level, not study level
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], workspace=None) -> DataTableStudy:
        """Create from dictionary."""
        study = cls(name=data["name"], workspace=workspace)
        
        # Restore table data
        if "data_objects" in data and "main_table" in data["data_objects"]:
            table_data = data["data_objects"]["main_table"]
            study.table = DataObject.from_dict(
                name=table_data["name"],
                data_dict=table_data["data"],
                **table_data.get("metadata", {})
            )
        
        # Restore metadata
        study.column_metadata = data.get("column_metadata", {})
        
        # Variables are managed at workspace level (not restored here)
        
        # Rebuild formula engine
        for col_name, meta in study.column_metadata.items():
            if meta.get("type") == ColumnType.CALCULATED and meta.get("formula"):
                study.formula_engine.register_formula(col_name, meta["formula"])
        
        return study
    
    def export_to_csv(self, filepath: str, include_metadata: bool = True) -> None:
        """Export table to CSV format.
        
        Args:
            filepath: Path to save CSV file
            include_metadata: If True, includes metadata as comment header
            
        Example:
            >>> study.export_to_csv("data.csv")
            >>> study.export_to_csv("data.csv", include_metadata=False)  # Data only
        """
        import csv
        
        df = self.table.data
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            if include_metadata:
                # Write metadata header as comments
                f.write("# DataManip CSV Export\n")
                f.write(f"# Study: {self.name}\n")
                f.write(f"# Version: 0.2.0\n")
                f.write("#\n")
                f.write("# Column Metadata:\n")
                for col_name in self.table.columns:
                    meta = self.column_metadata.get(col_name, {})
                    col_type = meta.get("type", ColumnType.DATA)
                    f.write(f"#   {col_name}: type={col_type}")
                    
                    if meta.get("unit"):
                        f.write(f", unit={meta['unit']}")
                    if meta.get("formula"):
                        # Escape formula for CSV
                        formula = meta['formula'].replace(',', ';')
                        f.write(f", formula={formula}")
                    if col_type == ColumnType.DERIVATIVE:
                        f.write(f", derivative_of={meta.get('derivative_of', '')}")
                        f.write(f", with_respect_to={meta.get('with_respect_to', '')}")
                    if col_type == ColumnType.RANGE:
                        f.write(f", range_type={meta.get('range_type', '')}")
                    f.write("\n")
                f.write("#\n")
            
            # Write data using pandas
            df.to_csv(f, index=False)
    
    def import_from_csv(
        self, 
        filepath: str, 
        has_metadata: bool = True,
        delimiter: str = ",",
        encoding: str = "utf-8",
        decimal: str = ".",
        skip_rows: int = 0,
        header: int = 0
    ) -> None:
        """Import table from CSV format with advanced configuration.
        
        Args:
            filepath: Path to CSV file
            has_metadata: Whether file contains metadata comments
            delimiter: Column delimiter (default: ",")
            encoding: File encoding (default: "utf-8")
            decimal: Decimal separator for numbers (default: ".")
            skip_rows: Number of rows to skip at beginning
            header: Row number to use as column names (None for no header)
            
        Note:
            This replaces current table data. Complex metadata (formulas, derivatives)
            may need manual recreation after import.
            
        Example:
            >>> study.import_from_csv("data.csv")
            >>> study.import_from_csv("euro.csv", delimiter=";", decimal=",")
            >>> study.import_from_csv("simple.csv", has_metadata=False, header=None)
        """
        # Read CSV with advanced parameters
        df = pd.read_csv(
            filepath, 
            delimiter=delimiter,
            encoding=encoding,
            decimal=decimal,
            skiprows=skip_rows if skip_rows > 0 else None,
            header=header,
            comment='#' if has_metadata else None
        )
        
        # If no header, generate column names
        if header is None:
            df.columns = [f"Column_{i}" for i in range(len(df.columns))]
        
        # Clear existing table
        self.table = DataObject.from_dataframe("table", df)
        self.column_metadata.clear()
        self.formula_engine = FormulaEngine()
        
        # Create basic metadata for all columns
        for col_name in df.columns:
            self.column_metadata[col_name] = {
                "type": ColumnType.DATA,
                "unit": None
            }
        
        # TODO: Parse metadata from comments if has_metadata=True
        # For now, all columns imported as DATA type
    
    def export_to_excel(self, filepath: str, sheet_name: str = "Data") -> None:
        """Export table to Excel format.
        
        Args:
            filepath: Path to save Excel file (.xlsx)
            sheet_name: Name of the sheet to create
            
        Requires:
            openpyxl package (pip install openpyxl)
            
        Example:
            >>> study.export_to_excel("data.xlsx")
            >>> study.export_to_excel("data.xlsx", sheet_name="Experiment1")
        """
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill
        except ImportError:
            raise ImportError(
                "openpyxl is required for Excel export. "
                "Install with: pip install openpyxl"
            )
        
        df = self.table.data
        
        # Create workbook and sheet
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = sheet_name
        
        # Write metadata section
        ws['A1'] = 'DataManip Export'
        ws['A1'].font = Font(bold=True, size=14)
        ws['A2'] = f'Study: {self.name}'
        ws['A3'] = 'Version: 0.2.0'
        
        # Write column metadata
        row = 5
        ws[f'A{row}'] = 'Column Metadata:'
        ws[f'A{row}'].font = Font(bold=True)
        row += 1
        
        ws[f'A{row}'] = 'Column'
        ws[f'B{row}'] = 'Type'
        ws[f'C{row}'] = 'Unit'
        ws[f'D{row}'] = 'Formula/Info'
        for cell in [ws[f'A{row}'], ws[f'B{row}'], ws[f'C{row}'], ws[f'D{row}']]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color='DDDDDD', fill_type='solid')
        row += 1
        
        for col_name in self.table.columns:
            meta = self.column_metadata.get(col_name, {})
            ws[f'A{row}'] = col_name
            ws[f'B{row}'] = meta.get('type', ColumnType.DATA)
            ws[f'C{row}'] = meta.get('unit', '')
            
            # Formula or other info
            if meta.get('formula'):
                ws[f'D{row}'] = meta['formula']
            elif meta.get('type') == ColumnType.DERIVATIVE:
                ws[f'D{row}'] = f"d({meta.get('derivative_of', '')})/d({meta.get('with_respect_to', '')})"
            elif meta.get('type') == ColumnType.RANGE:
                ws[f'D{row}'] = meta.get('range_type', '')
            row += 1
        
        # Add spacing
        row += 2
        
        # Write data section
        ws[f'A{row}'] = 'Data:'
        ws[f'A{row}'].font = Font(bold=True)
        row += 1
        
        # Write column headers
        for col_idx, col_name in enumerate(df.columns, start=1):
            cell = ws.cell(row, col_idx, col_name)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color='EEEEEE', fill_type='solid')
        row += 1
        
        # Write data rows
        for _, data_row in df.iterrows():
            for col_idx, value in enumerate(data_row, start=1):
                ws.cell(row, col_idx, value)
            row += 1
        
        # Auto-adjust column widths
        for col in ws.columns:
            max_length = 0
            col_letter = col[0].column_letter
            for cell in col:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            ws.column_dimensions[col_letter].width = min(max_length + 2, 50)
        
        # Save workbook
        wb.save(filepath)
    
    def import_from_excel(self, filepath: str, sheet_name: str = "Data") -> None:
        """Import table from Excel format.
        
        Args:
            filepath: Path to Excel file (.xlsx)
            sheet_name: Name of the sheet to read
            
        Note:
            Imports the data section only. Metadata needs manual recreation.
            
        Example:
            >>> study.import_from_excel("data.xlsx")
            >>> study.import_from_excel("data.xlsx", sheet_name="Experiment1")
        """
        # Use pandas to read Excel
        df = pd.read_excel(filepath, sheet_name=sheet_name, skiprows=None)
        
        # Find where data section starts (look for "Data:" marker)
        # For now, simple approach - assume data starts after empty rows
        # TODO: Smarter parsing to find data section
        
        # Clear existing table
        self.table = DataObject.from_dataframe("table", df)
        self.column_metadata.clear()
        self.formula_engine = FormulaEngine()
        
        # Create basic metadata
        for col_name in df.columns:
            self.column_metadata[col_name] = {
                "type": ColumnType.DATA,
                "unit": None
            }

