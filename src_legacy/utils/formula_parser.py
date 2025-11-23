"""
Formula parser for safe evaluation of mathematical expressions.

This module provides safe AST-based formula parsing and evaluation for
calculated columns. Formulas use {column_name} syntax for variable references.

Features:
- Safe AST parsing (no eval/exec)
- Vectorized operations using NumPy/Pandas
- Dependency extraction
- Unit-aware calculations (Pint integration)

Example:
    >>> parser = FormulaParser()
    >>> result = parser.parse("{x} * 2 + sin({y})")
    >>> deps = parser.extract_dependencies("{x} * 2 + sin({y})")  # ['x', 'y']
"""

import ast
import re
from typing import Any, List, Set, Dict, Optional, Union
import numpy as np
import pandas as pd


class FormulaError(Exception):
    """Base exception for formula-related errors."""
    pass


class FormulaSyntaxError(FormulaError):
    """Raised when formula has invalid syntax."""
    pass


class FormulaEvaluationError(FormulaError):
    """Raised when formula evaluation fails."""
    pass


class FormulaParser:
    """Parse and evaluate formulas safely using AST.
    
    Supported operators:
        +, -, *, /, ** (power), // (floor division), % (modulo)
        <, >, <=, >=, ==, != (comparisons)
    
    Supported functions:
        Mathematical: sin, cos, tan, asin, acos, atan, sinh, cosh, tanh
        Exponential: exp, log, log10, log2
        Rounding: abs, sqrt, ceil, floor, round
        Constants: pi, e
        Aggregation: sum, mean, std, min, max (for arrays)
    
    Variable syntax:
        Use {column_name} to reference columns
        Example: "{mass} * {velocity}**2 / 2"
    """
    
    # Allowed operators
    ALLOWED_OPS = {
        ast.Add: np.add,
        ast.Sub: np.subtract,
        ast.Mult: np.multiply,
        ast.Div: np.divide,
        ast.Pow: np.power,
        ast.FloorDiv: np.floor_divide,
        ast.Mod: np.mod,
        ast.USub: np.negative,
        ast.UAdd: lambda x: x,
    }
    
    # Allowed comparison operators
    ALLOWED_COMPARE_OPS = {
        ast.Lt: np.less,
        ast.LtE: np.less_equal,
        ast.Gt: np.greater,
        ast.GtE: np.greater_equal,
        ast.Eq: np.equal,
        ast.NotEq: np.not_equal,
    }
    
    # Allowed functions (all vectorized)
    ALLOWED_FUNCTIONS = {
        # Trigonometric
        'sin': np.sin,
        'cos': np.cos,
        'tan': np.tan,
        'asin': np.arcsin,
        'acos': np.arccos,
        'atan': np.arctan,
        'sinh': np.sinh,
        'cosh': np.cosh,
        'tanh': np.tanh,
        # Exponential and logarithmic
        'exp': np.exp,
        'log': np.log,
        'log10': np.log10,
        'log2': np.log2,
        # Rounding and absolute
        'abs': np.abs,
        'sqrt': np.sqrt,
        'ceil': np.ceil,
        'floor': np.floor,
        'round': np.round,
        # Aggregations (work on arrays)
        'sum': np.sum,
        'mean': np.mean,
        'std': np.std,
        'min': np.min,
        'max': np.max,
    }
    
    # Constants
    ALLOWED_CONSTANTS = {
        'pi': np.pi,
        'e': np.e,
    }
    
    def __init__(self):
        """Initialize the formula parser."""
        self._variable_pattern = re.compile(r'\{(\w+)\}')
    
    def extract_dependencies(self, formula: str) -> List[str]:
        """Extract list of column names referenced in formula.
        
        Args:
            formula: Formula string with {column_name} syntax
            
        Returns:
            Sorted list of unique column names
            
        Example:
            >>> parser.extract_dependencies("{x} * 2 + sin({y})")
            ['x', 'y']
        """
        matches = self._variable_pattern.findall(formula)
        return sorted(set(matches))
    
    def prepare_formula(self, formula: str) -> str:
        """Convert {column_name} syntax to valid Python identifiers.
        
        Args:
            formula: Formula with {column_name} syntax
            
        Returns:
            Formula with column names as plain identifiers
            
        Example:
            >>> parser.prepare_formula("{x} * 2")
            'x * 2'
        """
        return self._variable_pattern.sub(r'\1', formula)
    
    def validate_syntax(self, formula: str) -> tuple[bool, Optional[str]]:
        """Validate formula syntax without evaluating.
        
        Args:
            formula: Formula string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            prepared = self.prepare_formula(formula)
            tree = ast.parse(prepared, mode='eval')
            self._validate_ast(tree.body)
            return True, None
        except SyntaxError as e:
            return False, f"Syntax error: {e}"
        except FormulaSyntaxError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Validation error: {e}"
    
    def _validate_ast(self, node: ast.AST) -> None:
        """Recursively validate AST nodes for safety.
        
        Args:
            node: AST node to validate
            
        Raises:
            FormulaSyntaxError: If node contains disallowed operations
        """
        # Allowed node types
        if isinstance(node, ast.Constant):
            # Constants are safe (numbers, strings)
            return
        
        elif isinstance(node, ast.Name):
            # Variable names - check if it's a constant
            if node.id not in self.ALLOWED_CONSTANTS and node.id not in self.ALLOWED_FUNCTIONS:
                # Assume it's a column reference (will be validated at runtime)
                pass
            return
        
        elif isinstance(node, ast.BinOp):
            # Binary operations
            if type(node.op) not in self.ALLOWED_OPS:
                raise FormulaSyntaxError(f"Operation {node.op.__class__.__name__} not allowed")
            self._validate_ast(node.left)
            self._validate_ast(node.right)
            return
        
        elif isinstance(node, ast.UnaryOp):
            # Unary operations
            if type(node.op) not in self.ALLOWED_OPS:
                raise FormulaSyntaxError(f"Operation {node.op.__class__.__name__} not allowed")
            self._validate_ast(node.operand)
            return
        
        elif isinstance(node, ast.Compare):
            # Comparison operations
            self._validate_ast(node.left)
            for op in node.ops:
                if type(op) not in self.ALLOWED_COMPARE_OPS:
                    raise FormulaSyntaxError(f"Comparison {op.__class__.__name__} not allowed")
            for comparator in node.comparators:
                self._validate_ast(comparator)
            return
        
        elif isinstance(node, ast.Call):
            # Function calls
            if not isinstance(node.func, ast.Name):
                raise FormulaSyntaxError("Only simple function calls allowed")
            
            func_name = node.func.id
            if func_name not in self.ALLOWED_FUNCTIONS:
                raise FormulaSyntaxError(f"Function '{func_name}' not allowed")
            
            # Validate arguments
            for arg in node.args:
                self._validate_ast(arg)
            
            if node.keywords:
                raise FormulaSyntaxError("Keyword arguments not supported")
            
            return
        
        else:
            raise FormulaSyntaxError(f"AST node type {node.__class__.__name__} not allowed")
    
    def evaluate(self, formula: str, variables: Dict[str, Union[float, np.ndarray, pd.Series]]) -> Union[float, np.ndarray, pd.Series]:
        """Evaluate formula with given variable values.
        
        This method performs vectorized evaluation - if variables are arrays/Series,
        the result will be an array/Series of the same length.
        
        Args:
            formula: Formula string
            variables: Dictionary mapping column names to values
                      Values can be scalars, NumPy arrays, or Pandas Series
            
        Returns:
            Result of evaluation (scalar, array, or Series depending on inputs)
            
        Raises:
            FormulaEvaluationError: If evaluation fails
            
        Example:
            >>> import pandas as pd
            >>> parser = FormulaParser()
            >>> x = pd.Series([1, 2, 3])
            >>> y = pd.Series([4, 5, 6])
            >>> result = parser.evaluate("{x} * 2 + {y}", {'x': x, 'y': y})
            >>> # Result: Series([6, 9, 12])
        """
        try:
            # Prepare formula
            prepared = self.prepare_formula(formula)
            
            # Parse to AST
            tree = ast.parse(prepared, mode='eval')
            
            # Validate
            self._validate_ast(tree.body)
            
            # Create evaluation context
            context = {}
            context.update(self.ALLOWED_FUNCTIONS)
            context.update(self.ALLOWED_CONSTANTS)
            context.update(variables)
            
            # Evaluate
            result = self._eval_node(tree.body, context)
            
            return result
            
        except FormulaError:
            raise
        except KeyError as e:
            raise FormulaEvaluationError(f"Undefined variable: {e}")
        except Exception as e:
            raise FormulaEvaluationError(f"Evaluation error: {e}")
    
    def _eval_node(self, node: ast.AST, context: Dict[str, Any]) -> Any:
        """Recursively evaluate AST node.
        
        Args:
            node: AST node to evaluate
            context: Evaluation context with variables and functions
            
        Returns:
            Evaluation result
        """
        if isinstance(node, ast.Constant):
            return node.value
        
        elif isinstance(node, ast.Name):
            return context[node.id]
        
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left, context)
            right = self._eval_node(node.right, context)
            op_func = self.ALLOWED_OPS[type(node.op)]
            return op_func(left, right)
        
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand, context)
            op_func = self.ALLOWED_OPS[type(node.op)]
            return op_func(operand)
        
        elif isinstance(node, ast.Compare):
            left = self._eval_node(node.left, context)
            result = left
            
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_node(comparator, context)
                op_func = self.ALLOWED_COMPARE_OPS[type(op)]
                result = op_func(result, right)
                if not isinstance(result, (np.ndarray, pd.Series)):
                    if not result:
                        return result
            
            return result
        
        elif isinstance(node, ast.Call):
            func_name = node.func.id
            func = context[func_name]
            args = [self._eval_node(arg, context) for arg in node.args]
            return func(*args)
        
        else:
            raise FormulaEvaluationError(f"Cannot evaluate node type {node.__class__.__name__}")
