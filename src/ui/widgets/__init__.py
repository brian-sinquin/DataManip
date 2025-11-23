"""UI widgets for studies."""

from .data_table import DataTableWidget
from .constants_widget import ConstantsWidget
from .variables_widget import VariablesWidget  # Legacy
from .statistics import StatisticsWidget

__all__ = ["DataTableWidget", "ConstantsWidget", "VariablesWidget", "StatisticsWidget"]
