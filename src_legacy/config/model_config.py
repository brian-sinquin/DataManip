"""DataTable model configuration."""

from dataclasses import dataclass
from constants.data_types import DataType


@dataclass
class ModelConfig:
    """Configuration for DataTableModel behavior.
    
    Attributes:
        default_precision: Default number of decimal places for display
        default_dtype: Default data type for new columns
        auto_recalculate: Whether to automatically recalculate formulas
        max_undo_steps: Maximum number of undo steps to keep (0 = disabled)
    """
    default_precision: int = 6
    default_dtype: DataType = DataType.FLOAT
    auto_recalculate: bool = True
    max_undo_steps: int = 0  # Disabled for now
