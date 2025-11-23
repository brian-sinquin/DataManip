"""Data type definitions."""

from enum import Enum


class DataType(Enum):
    """Data types for column storage.
    
    These map to Pandas/NumPy dtypes for efficient storage and computation.
    """
    
    FLOAT = "float64"       # Floating point numbers (default for calculations)
    INTEGER = "int64"       # Integer numbers (counts, IDs, etc.)
    STRING = "object"       # Text data
    CATEGORY = "category"   # Categorical data (efficient for repeated values)
    BOOLEAN = "bool"        # True/False values
