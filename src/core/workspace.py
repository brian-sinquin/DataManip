"""
Workspace container for studies.

A workspace is a top-level organizational unit containing multiple
studies of various types.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from .study import Study


class Workspace:
    """Workspace containing multiple studies.
    
    A workspace organizes related studies. Examples:
    - Numerical Analysis Workspace: DataTable, Plots, Statistics
    - Image Analysis Workspace: Image viewer, filters, measurements
    
    Attributes:
        name: Workspace name
        workspace_type: Type identifier (e.g., "numerical", "image")
        studies: Dictionary of studies in this workspace
        metadata: Workspace settings
    """
    
    def __init__(self, name: str, workspace_type: str):
        """Initialize workspace.
        
        Args:
            name: Workspace name
            workspace_type: Type identifier
        """
        self.name = name
        self.workspace_type = workspace_type
        self.studies: Dict[str, Study] = {}
        self.metadata: Dict[str, Any] = {}
        
        # Workspace-level constants, variables, and functions
        # Format: {name: {"type": "constant|calculated|function", "value": ..., "unit": ..., "formula": ...}}
        self.constants: Dict[str, Dict[str, Any]] = {}
    
    def add_study(self, study: Study):
        """Add study to workspace.
        
        Args:
            study: Study to add
        """
        self.studies[study.name] = study
    
    def remove_study(self, name: str):
        """Remove study from workspace.
        
        Args:
            name: Study name
        """
        if name in self.studies:
            del self.studies[name]
    
    def get_study(self, name: str) -> Optional[Study]:
        """Get study by name.
        
        Args:
            name: Study name
            
        Returns:
            Study or None
        """
        return self.studies.get(name)
    
    def add_constant(self, name: str, value: float, unit: Optional[str] = None):
        """Add numeric constant.
        
        Args:
            name: Constant name
            value: Numeric value
            unit: Optional unit
        """
        self.constants[name] = {
            "type": "constant",
            "value": value,
            "unit": unit
        }
    
    def add_calculated_variable(self, name: str, formula: str, unit: Optional[str] = None):
        """Add calculated variable (formula-based).
        
        Args:
            name: Variable name
            formula: Formula expression (can reference other constants/variables)
            unit: Optional unit
        """
        self.constants[name] = {
            "type": "calculated",
            "formula": formula,
            "unit": unit,
            "value": None  # Will be calculated on demand
        }
    
    def add_function(self, name: str, formula: str, parameters: List[str], unit: Optional[str] = None):
        """Add custom function.
        
        Args:
            name: Function name
            formula: Formula expression using parameter names
            parameters: List of parameter names
            unit: Optional unit for return value
        """
        self.constants[name] = {
            "type": "function",
            "formula": formula,
            "parameters": parameters,
            "unit": unit
        }
    
    def remove_constant(self, name: str):
        """Remove constant/variable/function.
        
        Args:
            name: Name to remove
        """
        if name in self.constants:
            del self.constants[name]
    
    def get_constant_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get constant information.
        
        Args:
            name: Constant name
            
        Returns:
            Dictionary with type, value, unit, formula, etc.
        """
        return self.constants.get(name)
    
    def list_studies(self) -> List[str]:
        """Get list of study names.
        
        Returns:
            List of study names
        """
        return list(self.studies.keys())
    
    def to_dict(self) -> Dict[str, Any]:
        """Export workspace to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "name": self.name,
            "workspace_type": self.workspace_type,
            "studies": {
                name: {
                    "type": study.get_type(),
                    "data": study.to_dict()
                } for name, study in self.studies.items()
            },
            "constants": self.constants,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Workspace:
        """Create workspace from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            Workspace instance
        """
        workspace = cls(
            name=data["name"],
            workspace_type=data["workspace_type"]
        )
        workspace.metadata = data.get("metadata", {})
        workspace.constants = data.get("constants", {})
        
        # Restore studies with type registry
        from studies.data_table_study import DataTableStudy
        from studies.plot_study import PlotStudy
        
        study_types = {
            "data_table": DataTableStudy,
            "plot": PlotStudy
        }
        
        for name, study_data in data.get("studies", {}).items():
            study_type = study_data.get("type", "data_table")
            study_class = study_types.get(study_type)
            
            if study_class:
                study = study_class.from_dict(study_data["data"], workspace=workspace)
                workspace.add_study(study)
        
        return workspace
    
    def __repr__(self) -> str:
        return f"Workspace(name='{self.name}', type='{self.workspace_type}', studies={len(self.studies)})"
