"""Constants widget module for managing workspace-level values.

Modular structure:
- __init__.py: Public API
- widget.py: Main ConstantsWidget
- dialogs.py: Add/Edit dialogs
- model.py: Table model (if needed)
"""

from .widget import ConstantsWidget

__all__ = ["ConstantsWidget"]
