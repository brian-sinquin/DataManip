"""Uncertainty propagation for mathematical formulas.

Provides tools to convert mathematical expressions to SymPy symbolic form
and calculate combined uncertainties using partial derivatives.

The uncertainty propagation follows the standard formula:
    δf = sqrt(Σ(∂f/∂xᵢ * δxᵢ)²)
"""

import ast
import sympy as sp
from typing import Dict


class FormulaToSymPy:
    """Convert mathematical expressions to SymPy symbolic form."""

    OPERATORS = {
        ast.Add: lambda a, b: a + b,
        ast.Sub: lambda a, b: a - b,
        ast.Mult: lambda a, b: a * b,
        ast.Div: lambda a, b: a / b,
        ast.Pow: lambda a, b: a ** b,
        ast.USub: lambda a: -a,
        ast.UAdd: lambda a: +a,
    }

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
    def convert(cls, expression: str, variable_names: list) -> sp.Expr:
        """Convert a mathematical expression to SymPy.
        
        Args:
            expression: Mathematical expression (e.g., "2 * x + 3 * y")
            variable_names: List of variable names
            
        Returns:
            SymPy expression
        """
        try:
            tree = ast.parse(expression, mode='eval')
            symbols = {name: sp.Symbol(name) for name in variable_names}
            return cls._ast_to_sympy(tree.body, symbols)
        except (SyntaxError, TypeError) as e:
            raise ValueError(f"Invalid formula: {str(e)}")

    @classmethod
    def _ast_to_sympy(cls, node: ast.AST, symbols: Dict[str, sp.Symbol]) -> sp.Expr:
        """Recursively convert AST nodes to SymPy."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return sp.sympify(node.value)
            else:
                raise ValueError(f"Unsupported constant: {node.value}")

        elif isinstance(node, ast.Name):
            if node.id in symbols:
                return symbols[node.id]
            elif node.id in cls.SYMPY_FUNCTIONS:
                value = cls.SYMPY_FUNCTIONS[node.id]
                return value if not callable(value) else value
            else:
                raise ValueError(f"Unknown variable: {node.id}")

        elif isinstance(node, ast.BinOp):
            left = cls._ast_to_sympy(node.left, symbols)
            right = cls._ast_to_sympy(node.right, symbols)
            op = cls.OPERATORS.get(type(node.op))
            if op:
                return op(left, right)
            else:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")

        elif isinstance(node, ast.UnaryOp):
            operand = cls._ast_to_sympy(node.operand, symbols)
            op = cls.OPERATORS.get(type(node.op))
            if op:
                return op(operand)
            else:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")

        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in cls.SYMPY_FUNCTIONS:
                    func = cls.SYMPY_FUNCTIONS[func_name]
                    args = [cls._ast_to_sympy(arg, symbols) for arg in node.args]
                    if func_name in ['min', 'max', 'sum', 'len', 'round']:
                        raise ValueError(f"Function '{func_name}' not supported for uncertainty")
                    return func(*args)
                else:
                    raise ValueError(f"Unsupported function: {func_name}")
            else:
                raise ValueError("Complex function calls not supported")

        else:
            raise ValueError(f"Unsupported expression: {type(node).__name__}")


class UncertaintyCalculator:
    """Calculate combined uncertainty using partial derivatives."""

    @classmethod
    def calculate_uncertainty(
        cls,
        expression: str,
        values: Dict[str, float],
        uncertainties: Dict[str, float]
    ) -> float:
        """Calculate combined uncertainty of a formula.
        
        Args:
            expression: Mathematical expression
            values: Variable values
            uncertainties: Variable uncertainties
            
        Returns:
            Combined uncertainty
        """
        try:
            variable_names = list(values.keys())
            sympy_expr = FormulaToSymPy.convert(expression, variable_names)
            
            variance_contributions = []
            for var_name in variable_names:
                if var_name not in uncertainties:
                    continue
                
                var_symbol = sp.Symbol(var_name)
                partial_derivative = sp.diff(sympy_expr, var_symbol)
                
                subs_dict = {sp.Symbol(name): val for name, val in values.items()}
                derivative_value = float(partial_derivative.evalf(subs=subs_dict))
                
                uncertainty_contribution = derivative_value * uncertainties[var_name]
                variance_contributions.append(uncertainty_contribution ** 2)
            
            combined_variance = sum(variance_contributions)
            return combined_variance ** 0.5
            
        except Exception as e:
            raise ValueError(f"Error calculating uncertainty: {str(e)}")

    @classmethod
    def get_partial_derivatives(
        cls,
        expression: str,
        variable_names: list
    ) -> Dict[str, sp.Expr]:
        """Get symbolic partial derivatives.
        
        Args:
            expression: Mathematical expression
            variable_names: List of variable names
            
        Returns:
            Dict mapping variable names to partial derivatives
        """
        sympy_expr = FormulaToSymPy.convert(expression, variable_names)
        derivatives = {}
        for var_name in variable_names:
            var_symbol = sp.Symbol(var_name)
            derivatives[var_name] = sp.diff(sympy_expr, var_symbol)
        return derivatives
