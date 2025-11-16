"""
Safe formula evaluation engine for AdvancedDataTableWidget.

This module provides a safe way to evaluate mathematical expressions
without using eval(), protecting against code injection attacks.
It also supports automatic unit calculation using the Pint library.
"""

import ast
import operator
import math
from typing import Dict, Union, Optional, Tuple, Any
import pint

# Import unit formatting utilities
from utils.units import format_pint_unit

# Initialize Pint unit registry
ureg = pint.UnitRegistry()


class SafeFormulaEvaluator:
    """Safe mathematical expression evaluator without eval().
    
    This class provides a secure way to evaluate mathematical formulas
    by parsing them into an Abstract Syntax Tree (AST) and evaluating
    only allowed operations and functions.
    
    Supported operators: +, -, *, /, ** (power), unary - and +
    Supported functions: abs, round, min, max, sum, len, sqrt, sin, cos, 
                        tan, log, log10, exp, pi, e
    
    Example:
        >>> evaluator = SafeFormulaEvaluator()
        >>> result = evaluator.evaluate("2 * x + 3", {"x": 5})
        >>> print(result)  # 13
    """

    # Supported operators mapped to their Python implementations
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    # Supported mathematical functions and constants
    FUNCTIONS = {
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
        'sum': sum,
        'len': len,
        'sqrt': math.sqrt,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'log': math.log,
        'log10': math.log10,
        'exp': math.exp,
        'pi': math.pi,
        'e': math.e,
    }

    @classmethod
    def evaluate(cls, expression: str, variables: Dict[str, Union[int, float]]) -> Union[int, float]:
        """
        Safely evaluate a mathematical expression with variables.

        Args:
            expression: Mathematical expression string (e.g., "2 * x + 3")
            variables: Dict of variable names to their numeric values

        Returns:
            The numeric result of the evaluation

        Raises:
            ValueError: If the expression is invalid or contains unsupported operations
        
        Example:
            >>> SafeFormulaEvaluator.evaluate("x ** 2 + y ** 2", {"x": 3, "y": 4})
            25.0
        """
        try:
            # Parse the expression into an Abstract Syntax Tree
            tree = ast.parse(expression, mode='eval')

            # Evaluate the AST safely
            return cls._eval_node(tree.body, variables)

        except (SyntaxError, TypeError, ZeroDivisionError) as e:
            raise ValueError(f"Invalid formula: {str(e)}")

    @classmethod
    def evaluate_with_units(
        cls, 
        expression: str, 
        variables: Dict[str, Tuple[Union[int, float], Optional[str]]]
    ) -> Tuple[float, str]:
        """
        Safely evaluate a mathematical expression with unit-aware variables.
        
        This method uses Pint to handle unit conversions and automatically
        calculates the resulting unit from the formula.

        Args:
            expression: Mathematical expression string (e.g., "x * y")
            variables: Dict mapping variable names to (value, unit) tuples
                      where unit is a string like 'm', 'kg', 's', etc.
                      Unit can be None for dimensionless values.

        Returns:
            Tuple of (magnitude, unit_string) where unit_string is the 
            calculated resulting unit (e.g., 'm/s', 'kg*m/s^2')

        Raises:
            ValueError: If the expression is invalid or contains unsupported operations
            
        Example:
            >>> SafeFormulaEvaluator.evaluate_with_units(
            ...     "distance / time", 
            ...     {"distance": (100, "m"), "time": (10, "s")}
            ... )
            (10.0, 'meter / second')
        """
        try:
            # Convert variables to Pint quantities
            pint_variables: Dict[str, Any] = {}
            for name, (value, unit) in variables.items():
                if unit and unit.strip():
                    # Parse unit string and create quantity
                    pint_variables[name] = ureg.Quantity(value, unit)
                else:
                    # Dimensionless quantity
                    pint_variables[name] = ureg.Quantity(value, 'dimensionless')
            
            # Parse the expression
            tree = ast.parse(expression, mode='eval')
            
            # Evaluate with Pint quantities
            result = cls._eval_node_with_units(tree.body, pint_variables)
            
            # Extract magnitude and units
            if hasattr(result, 'magnitude') and hasattr(result, 'units'):
                # It's a Pint Quantity
                magnitude = float(result.magnitude)
                # Get unit representation
                if result.dimensionless:
                    unit_str = ''
                else:
                    # Use pretty UTF-8 formatting for units
                    unit_str = format_pint_unit(result.units, use_dot=True, use_superscript=True)
            else:
                # Plain number (shouldn't happen with our implementation)
                magnitude = float(result)
                unit_str = ''
            
            return (magnitude, unit_str)
            
        except pint.errors.DimensionalityError as e:
            raise ValueError(f"Unit mismatch in formula: {str(e)}")
        except pint.errors.UndefinedUnitError as e:
            raise ValueError(f"Unknown unit: {str(e)}")
        except (SyntaxError, ZeroDivisionError) as e:
            raise ValueError(f"Invalid formula: {str(e)}")
        except TypeError as e:
            # Check if it's a Pint-related TypeError
            if 'dimension' in str(e).lower():
                raise ValueError(f"Unit error in formula: {str(e)}")
            raise ValueError(f"Invalid formula: {str(e)}")

    @classmethod
    def _eval_node(cls, node: ast.AST, variables: Dict[str, Union[int, float]]) -> Union[int, float]:
        """Recursively evaluate AST nodes.
        
        Args:
            node: The AST node to evaluate
            variables: Dict of variable names to values
            
        Returns:
            The numeric result of evaluating the node
            
        Raises:
            ValueError: If the node contains unsupported operations
        """
        if isinstance(node, ast.Constant):
            # Numbers and constants
            if isinstance(node.value, (int, float)):
                return node.value
            else:
                raise ValueError(f"Unsupported constant: {node.value}")

        elif isinstance(node, ast.Name):
            # Variable names or function names
            if node.id in variables:
                return variables[node.id]
            elif node.id in cls.FUNCTIONS:
                return cls.FUNCTIONS[node.id]
            else:
                raise ValueError(f"Unknown variable or function: {node.id}")

        elif isinstance(node, ast.BinOp):
            # Binary operations (e.g., x + y, a * b)
            left = cls._eval_node(node.left, variables)
            right = cls._eval_node(node.right, variables)
            op = cls.OPERATORS.get(type(node.op))
            if op:
                return op(left, right)
            else:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")

        elif isinstance(node, ast.UnaryOp):
            # Unary operations (e.g., -x, +x)
            operand = cls._eval_node(node.operand, variables)
            op = cls.OPERATORS.get(type(node.op))
            if op:
                return op(operand)
            else:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")

        elif isinstance(node, ast.Call):
            # Function calls (e.g., sqrt(x), sin(y))
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in cls.FUNCTIONS:
                    func = cls.FUNCTIONS[func_name]
                    args = [cls._eval_node(arg, variables) for arg in node.args]
                    return func(*args)
                else:
                    raise ValueError(f"Unsupported function: {func_name}")
            else:
                raise ValueError("Complex function calls not supported")

        else:
            raise ValueError(f"Unsupported expression element: {type(node).__name__}")

    @classmethod
    def _eval_node_with_units(cls, node: ast.AST, variables: Dict[str, Any]) -> Any:
        """Recursively evaluate AST nodes with Pint unit support.
        
        Args:
            node: The AST node to evaluate
            variables: Dict of variable names to Pint Quantity objects
            
        Returns:
            A Pint Quantity with the calculated value and units
            
        Raises:
            ValueError: If the node contains unsupported operations
        """
        if isinstance(node, ast.Constant):
            # Numbers and constants - treat as dimensionless
            if isinstance(node.value, (int, float)):
                return ureg.Quantity(node.value, 'dimensionless')
            else:
                raise ValueError(f"Unsupported constant: {node.value}")

        elif isinstance(node, ast.Name):
            # Variable names or function names
            if node.id in variables:
                return variables[node.id]
            elif node.id in cls.FUNCTIONS:
                # Functions like pi, e are accessed as constants
                value = cls.FUNCTIONS[node.id]
                if isinstance(value, (int, float)):
                    return ureg.Quantity(value, 'dimensionless')
                # For actual functions, return them (will be used in ast.Call)
                return value
            else:
                raise ValueError(f"Unknown variable or function: {node.id}")

        elif isinstance(node, ast.BinOp):
            # Binary operations (e.g., x + y, a * b)
            left = cls._eval_node_with_units(node.left, variables)
            right = cls._eval_node_with_units(node.right, variables)
            
            # Pint handles unit arithmetic automatically
            op = cls.OPERATORS.get(type(node.op))
            if op:
                result = op(left, right)
                return result
            else:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")

        elif isinstance(node, ast.UnaryOp):
            # Unary operations (e.g., -x, +x)
            operand = cls._eval_node_with_units(node.operand, variables)
            op = cls.OPERATORS.get(type(node.op))
            if op:
                return op(operand)
            else:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")

        elif isinstance(node, ast.Call):
            # Function calls (e.g., sqrt(x), sin(y))
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in cls.FUNCTIONS:
                    func = cls.FUNCTIONS[func_name]
                    args = [cls._eval_node_with_units(arg, variables) for arg in node.args]
                    
                    # Extract magnitudes for functions that don't handle Quantities
                    # For trig functions, the argument should be dimensionless or in radians
                    if func_name in ['sin', 'cos', 'tan']:
                        # Convert to dimensionless (radians assumed)
                        numeric_args = []
                        for arg in args:
                            if hasattr(arg, 'dimensionless') and arg.dimensionless:
                                numeric_args.append(arg.magnitude)
                            elif hasattr(arg, 'to'):
                                # Try to convert to radians
                                try:
                                    numeric_args.append(arg.to('radian').magnitude)
                                except:
                                    numeric_args.append(arg.magnitude)
                            else:
                                numeric_args.append(arg)
                        result = func(*numeric_args)
                        return ureg.Quantity(result, 'dimensionless')
                    elif func_name in ['log', 'log10', 'exp']:
                        # Logarithms and exp require dimensionless input
                        numeric_args = [arg.magnitude if hasattr(arg, 'magnitude') else arg for arg in args]
                        result = func(*numeric_args)
                        return ureg.Quantity(result, 'dimensionless')
                    elif func_name in ['abs', 'round']:
                        # These preserve units
                        if len(args) == 1 and hasattr(args[0], 'magnitude'):
                            return ureg.Quantity(func(args[0].magnitude), args[0].units)
                        else:
                            result = func(*[arg.magnitude if hasattr(arg, 'magnitude') else arg for arg in args])
                            return ureg.Quantity(result, 'dimensionless')
                    elif func_name in ['sqrt']:
                        # Square root with units
                        if hasattr(args[0], 'magnitude'):
                            return args[0] ** 0.5
                        else:
                            return ureg.Quantity(math.sqrt(args[0]), 'dimensionless')
                    else:
                        # Other functions - try to apply directly
                        numeric_args = [arg.magnitude if hasattr(arg, 'magnitude') else arg for arg in args]
                        result = func(*numeric_args)
                        return ureg.Quantity(result, 'dimensionless')
                else:
                    raise ValueError(f"Unsupported function: {func_name}")
            else:
                raise ValueError("Complex function calls not supported")

        else:
            raise ValueError(f"Unsupported expression element: {type(node).__name__}")

