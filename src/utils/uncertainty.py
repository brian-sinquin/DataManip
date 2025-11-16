"""
Uncertainty propagation for mathematical formulas.

This module provides tools to convert mathematical expressions to SymPy
symbolic form and calculate combined uncertainties using discrete differential
forms (partial derivatives).

The uncertainty propagation follows the standard formula:
    δf = sqrt(Σ(∂f/∂xᵢ * δxᵢ)²)

where:
- δf is the combined uncertainty of the result
- ∂f/∂xᵢ are the partial derivatives with respect to each variable
- δxᵢ are the uncertainties of each input variable
"""

import ast
import sympy as sp
from typing import Dict, Union, Optional, Tuple, Any
import pint

# Import unit registry from formula_evaluator
from widgets.AdvancedDataTableWidget.formula_evaluator import ureg


class FormulaToSymPy:
    """Convert mathematical expressions to SymPy symbolic form.
    
    This class converts AST-based formulas (safe for evaluation) into
    SymPy symbolic expressions that can be differentiated and manipulated.
    """

    # Map AST operators to SymPy equivalents
    OPERATORS = {
        ast.Add: lambda a, b: a + b,
        ast.Sub: lambda a, b: a - b,
        ast.Mult: lambda a, b: a * b,
        ast.Div: lambda a, b: a / b,
        ast.Pow: lambda a, b: a ** b,
        ast.USub: lambda a: -a,
        ast.UAdd: lambda a: +a,
    }

    # Map function names to SymPy functions
    SYMPY_FUNCTIONS = {
        'abs': sp.Abs,
        'sqrt': sp.sqrt,
        'sin': sp.sin,
        'cos': sp.cos,
        'tan': sp.tan,
        'log': sp.log,
        'log10': lambda x: sp.log(x, 10),
        'exp': sp.exp,
        'pi': sp.pi,
        'e': sp.E,
    }

    @classmethod
    def convert(cls, expression: str, variable_names: list[str]) -> sp.Expr:
        """
        Convert a mathematical expression string to a SymPy symbolic expression.

        Args:
            expression: Mathematical expression string (e.g., "2 * x + 3 * y")
            variable_names: List of variable names in the expression

        Returns:
            SymPy expression object

        Raises:
            ValueError: If the expression is invalid or contains unsupported operations
        
        Example:
            >>> expr = FormulaToSymPy.convert("x**2 + y**2", ["x", "y"])
            >>> print(expr)
            x**2 + y**2
        """
        try:
            # Parse the expression into an Abstract Syntax Tree
            tree = ast.parse(expression, mode='eval')

            # Create SymPy symbols for all variables
            symbols = {name: sp.Symbol(name) for name in variable_names}

            # Convert the AST to SymPy expression
            return cls._ast_to_sympy(tree.body, symbols)

        except (SyntaxError, TypeError) as e:
            raise ValueError(f"Invalid formula: {str(e)}")

    @classmethod
    def _ast_to_sympy(cls, node: ast.AST, symbols: Dict[str, sp.Symbol]) -> sp.Expr:
        """Recursively convert AST nodes to SymPy expressions.
        
        Args:
            node: The AST node to convert
            symbols: Dict of variable names to SymPy symbols
            
        Returns:
            SymPy expression
            
        Raises:
            ValueError: If the node contains unsupported operations
        """
        if isinstance(node, ast.Constant):
            # Numbers and constants
            if isinstance(node.value, (int, float)):
                return sp.sympify(node.value)
            else:
                raise ValueError(f"Unsupported constant: {node.value}")

        elif isinstance(node, ast.Name):
            # Variable names or constants
            if node.id in symbols:
                return symbols[node.id]
            elif node.id in cls.SYMPY_FUNCTIONS:
                # Return constant values for pi and e
                value = cls.SYMPY_FUNCTIONS[node.id]
                if callable(value):
                    return value  # Will be used in function calls
                else:
                    return value  # pi or e
            else:
                raise ValueError(f"Unknown variable: {node.id}")

        elif isinstance(node, ast.BinOp):
            # Binary operations (e.g., x + y, a * b)
            left = cls._ast_to_sympy(node.left, symbols)
            right = cls._ast_to_sympy(node.right, symbols)
            op = cls.OPERATORS.get(type(node.op))
            if op:
                return op(left, right)
            else:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")

        elif isinstance(node, ast.UnaryOp):
            # Unary operations (e.g., -x, +x)
            operand = cls._ast_to_sympy(node.operand, symbols)
            op = cls.OPERATORS.get(type(node.op))
            if op:
                return op(operand)
            else:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")

        elif isinstance(node, ast.Call):
            # Function calls (e.g., sqrt(x), sin(y))
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in cls.SYMPY_FUNCTIONS:
                    func = cls.SYMPY_FUNCTIONS[func_name]
                    args = [cls._ast_to_sympy(arg, symbols) for arg in node.args]
                    
                    # Handle special cases
                    if func_name in ['min', 'max', 'sum', 'len', 'round']:
                        # These are not directly supported in symbolic differentiation
                        raise ValueError(f"Function '{func_name}' is not supported for uncertainty calculation")
                    
                    return func(*args)
                else:
                    raise ValueError(f"Unsupported function: {func_name}")
            else:
                raise ValueError("Complex function calls not supported")

        else:
            raise ValueError(f"Unsupported expression element: {type(node).__name__}")


class UncertaintyCalculator:
    """Calculate combined uncertainty using partial derivatives.
    
    This class implements uncertainty propagation using the formula:
        δf = sqrt(Σ(∂f/∂xᵢ * δxᵢ)²)
    """

    @classmethod
    def calculate_uncertainty(
        cls,
        expression: str,
        values: Dict[str, float],
        uncertainties: Dict[str, float]
    ) -> float:
        """
        Calculate the combined uncertainty of a formula.

        Args:
            expression: Mathematical expression string (e.g., "x * y")
            values: Dict of variable names to their values
            uncertainties: Dict of variable names to their uncertainties (standard deviations)

        Returns:
            Combined uncertainty (standard deviation) of the result

        Raises:
            ValueError: If the expression is invalid or variables are missing
        
        Example:
            >>> # Calculate uncertainty of area = length * width
            >>> UncertaintyCalculator.calculate_uncertainty(
            ...     "length * width",
            ...     {"length": 10.0, "width": 5.0},
            ...     {"length": 0.1, "width": 0.05}
            ... )
            0.7071...
        """
        try:
            # Get variable names
            variable_names = list(values.keys())
            
            # Convert to SymPy expression
            sympy_expr = FormulaToSymPy.convert(expression, variable_names)
            
            # Calculate partial derivatives and squared contributions
            variance_contributions = []
            
            for var_name in variable_names:
                if var_name not in uncertainties:
                    # If no uncertainty specified, assume zero
                    continue
                
                # Get the SymPy symbol for this variable
                var_symbol = sp.Symbol(var_name)
                
                # Calculate partial derivative ∂f/∂xᵢ
                partial_derivative = sp.diff(sympy_expr, var_symbol)
                
                # Evaluate the partial derivative at the given values
                subs_dict = {sp.Symbol(name): val for name, val in values.items()}
                derivative_value = float(partial_derivative.evalf(subs=subs_dict))
                
                # Calculate contribution to variance: (∂f/∂xᵢ * δxᵢ)²
                uncertainty_contribution = derivative_value * uncertainties[var_name]
                variance_contributions.append(uncertainty_contribution ** 2)
            
            # Combined uncertainty: sqrt(Σ(contributions²))
            combined_variance = sum(variance_contributions)
            combined_uncertainty = combined_variance ** 0.5
            
            return combined_uncertainty
            
        except Exception as e:
            raise ValueError(f"Error calculating uncertainty: {str(e)}")

    @classmethod
    def calculate_uncertainty_with_units(
        cls,
        expression: str,
        values: Dict[str, Tuple[float, Optional[str]]],
        uncertainties: Dict[str, Tuple[float, Optional[str]]]
    ) -> Tuple[float, str]:
        """
        Calculate the combined uncertainty with unit support.

        Args:
            expression: Mathematical expression string (e.g., "distance / time")
            values: Dict mapping variable names to (value, unit) tuples
            uncertainties: Dict mapping variable names to (uncertainty, unit) tuples

        Returns:
            Tuple of (combined_uncertainty_magnitude, uncertainty_unit_string)

        Raises:
            ValueError: If units are incompatible or expression is invalid
        
        Example:
            >>> # Calculate uncertainty of velocity = distance / time
            >>> UncertaintyCalculator.calculate_uncertainty_with_units(
            ...     "distance / time",
            ...     {"distance": (100, "m"), "time": (10, "s")},
            ...     {"distance": (1, "m"), "time": (0.1, "s")}
            ... )
            (0.14..., 'meter / second')
        """
        try:
            # Extract variable names and create Pint quantities
            variable_names = list(values.keys())
            
            # Convert to SymPy expression
            sympy_expr = FormulaToSymPy.convert(expression, variable_names)
            
            # Prepare values as plain numbers for SymPy
            plain_values = {name: val for name, (val, _) in values.items()}
            
            # Calculate variance contributions with units
            variance_contributions = []
            result_unit = None
            
            # First, determine the result unit by evaluating the formula with units
            from widgets.AdvancedDataTableWidget.formula_evaluator import SafeFormulaEvaluator
            _, result_unit_str = SafeFormulaEvaluator.evaluate_with_units(
                expression, 
                values
            )
            if result_unit_str:
                result_unit = ureg.parse_expression(result_unit_str)
            else:
                result_unit = ureg.dimensionless
            
            for var_name in variable_names:
                if var_name not in uncertainties:
                    continue
                
                # Get the SymPy symbol for this variable
                var_symbol = sp.Symbol(var_name)
                
                # Calculate partial derivative ∂f/∂xᵢ
                partial_derivative = sp.diff(sympy_expr, var_symbol)
                
                # Evaluate the partial derivative at the given values
                subs_dict = {sp.Symbol(name): val for name, val in plain_values.items()}
                derivative_value = float(partial_derivative.evalf(subs=subs_dict))
                
                # Create Pint quantities for the variable
                var_value, var_unit = values[var_name]
                var_uncertainty, unc_unit = uncertainties[var_name]
                
                # The uncertainty must have the same unit as the variable
                if var_unit and unc_unit:
                    unc_qty = ureg.Quantity(var_uncertainty, unc_unit)
                    # Convert uncertainty to same unit as variable
                    unc_qty = unc_qty.to(var_unit)
                elif var_unit:
                    unc_qty = ureg.Quantity(var_uncertainty, var_unit)
                else:
                    unc_qty = ureg.Quantity(var_uncertainty, 'dimensionless')
                
                # Calculate the partial derivative's units
                # ∂f/∂xᵢ has units of [result] / [variable]
                if var_unit:
                    var_unit_qty = ureg.Quantity(1.0, var_unit)
                else:
                    var_unit_qty = ureg.Quantity(1.0, 'dimensionless')
                
                # derivative_units = result_unit / var_unit
                derivative_qty = ureg.Quantity(derivative_value, result_unit / var_unit_qty.units)
                
                # ∂f/∂xᵢ * δxᵢ has units of [result]
                contribution_qty = derivative_qty * unc_qty
                
                # Ensure contribution is in result units (should already be, but verify)
                if not result_unit.dimensionless:
                    contribution_qty = contribution_qty.to(result_unit)
                
                variance_contributions.append(contribution_qty.magnitude ** 2)
            
            # Combined uncertainty: sqrt(Σ(contributions²))
            combined_variance = sum(variance_contributions)
            combined_uncertainty = combined_variance ** 0.5
            
            # Format the result unit
            if result_unit and not result_unit.dimensionless:
                from utils.units import format_pint_unit
                unit_str = format_pint_unit(result_unit, use_dot=True, use_superscript=True)
            else:
                unit_str = ''
            
            return (combined_uncertainty, unit_str)
            
        except Exception as e:
            raise ValueError(f"Error calculating uncertainty with units: {str(e)}")

    @classmethod
    def get_partial_derivatives(
        cls,
        expression: str,
        variable_names: list[str]
    ) -> Dict[str, sp.Expr]:
        """
        Get symbolic partial derivatives of the expression with respect to each variable.

        Args:
            expression: Mathematical expression string
            variable_names: List of variable names

        Returns:
            Dict mapping variable names to their partial derivative expressions
        
        Example:
            >>> derivs = UncertaintyCalculator.get_partial_derivatives(
            ...     "x**2 + y**2",
            ...     ["x", "y"]
            ... )
            >>> print(derivs["x"])
            2*x
            >>> print(derivs["y"])
            2*y
        """
        # Convert to SymPy expression
        sympy_expr = FormulaToSymPy.convert(expression, variable_names)
        
        # Calculate partial derivatives
        derivatives = {}
        for var_name in variable_names:
            var_symbol = sp.Symbol(var_name)
            derivatives[var_name] = sp.diff(sympy_expr, var_symbol)
        
        return derivatives

    @classmethod
    def get_uncertainty_formula(
        cls,
        expression: str,
        variable_names: list[str]
    ) -> str:
        """
        Get a human-readable formula for the uncertainty calculation.

        Args:
            expression: Mathematical expression string
            variable_names: List of variable names

        Returns:
            String representation of the uncertainty formula
        
        Example:
            >>> formula = UncertaintyCalculator.get_uncertainty_formula(
            ...     "x * y",
            ...     ["x", "y"]
            ... )
            >>> print(formula)
            δf = sqrt((y*δx)² + (x*δy)²)
        """
        # Get partial derivatives
        derivatives = cls.get_partial_derivatives(expression, variable_names)
        
        # Build uncertainty formula terms
        terms = []
        for var_name in variable_names:
            deriv = derivatives[var_name]
            # Simplify the derivative
            deriv_simplified = sp.simplify(deriv)
            terms.append(f"({deriv_simplified}*δ{var_name})²")
        
        # Combine into formula
        formula = "δf = sqrt(" + " + ".join(terms) + ")"
        
        return formula
