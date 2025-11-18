"""UI package for DataManip - contains complete UI assemblies."""

# Delegates are imported separately to avoid circular imports
# Use: from ui.delegates import NumericDelegate, etc.

# Import all from sub-packages
from .main_window import *
from .about_window import *  
from .preference_window import *
from .notifications import *
