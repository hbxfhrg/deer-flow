# Temporary module to fix import error
# This module was created because something is trying to import deerflow.tools.skill_tool
# but the actual module is named skill_manage_tool

# Re-export from the correct module
from .skill_manage_tool import *

# Explicitly define the expected skill_tool attribute/class
from .skill_manage_tool import skill_manage_tool as skill_tool

__all__ = ["skill_tool"] + __all__ if '__all__' in dir() else ["skill_tool"]