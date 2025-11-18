"""UI package for DataManip - contains complete UI assemblies."""

# Delegates are imported separately to avoid circular imports
# Use: from ui.delegates import NumericDelegate, etc.

# Import all from sub-packages
from .MainWindow import *
from .AboutWindow import *  
from .PreferenceWindow import *
from .message_boxes import *
