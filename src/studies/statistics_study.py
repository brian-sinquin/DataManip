"""
Statistics study for analyzing data table columns.

Provides statistical analysis including descriptive statistics,
distributions, and visualizations.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd

from core.study import Study
from core.data_object import DataObject


class StatisticsStudy(Study):
    """Study for statistical analysis of data.
    
    Features:
    - Descriptive statistics (mean, median, std, min, max, quartiles)
    - Distribution analysis (skewness, kurtosis)
    - Linked to a DataTableStudy for data source
    - Multiple column analysis support
    
    Attributes:
        source_study: Name of the DataTableStudy to analyze
        analyzed_columns: List of column names being analyzed
        results: Dictionary of analysis results per column
    """
    
    def __init__(self, name: str, source_study: Optional[str] = None, workspace=None):
        """Initialize Statistics study.
        
        Args:
            name: Study name
            source_study: Name of DataTableStudy to analyze (optional)
            workspace: Reference to parent workspace
        """
        super().__init__(name)
        
        self.workspace = workspace
        self.source_study = source_study
        self.analyzed_columns: List[str] = []
        self.results: Dict[str, Dict[str, Any]] = {}
    
    def get_type(self) -> str:
        """Get study type identifier."""
        return "statistics"
    
    # ========================================================================
    # Data Source Management
    # ========================================================================
    
    def set_source_study(self, study_name: str):
        """Set the source DataTableStudy to analyze.
        
        Args:
            study_name: Name of DataTableStudy in workspace
        """
        self.source_study = study_name
    
    def get_source_data(self, column_name: str) -> Optional[np.ndarray]:
        """Get numerical data from source study column.
        
        Args:
            column_name: Name of column to extract
            
        Returns:
            Numpy array of cleaned numerical values, or None
        """
        if not self.workspace or not self.source_study:
            return None
        
        try:
            # Get source study
            study = self.workspace.get_study(self.source_study)
            if study is None or study.get_type() != "data_table":
                return None
            
            # Check if column exists
            if column_name not in study.table.data.columns:
                return None
            
            # Get column data as Series
            series = study.table.data[column_name]
            
            # Clean data: remove NaN and inf
            data = series.replace([np.inf, -np.inf], np.nan).dropna().to_numpy()
            
            return data if len(data) > 0 else None
            
        except Exception:
            return None
    
    def get_available_columns(self) -> List[str]:
        """Get list of numerical columns available for analysis.
        
        Returns:
            List of column names
        """
        if not self.workspace or not self.source_study:
            return []
        
        try:
            study = self.workspace.get_study(self.source_study)
            if study is None or study.get_type() != "data_table":
                return []
            
            # Get all columns and filter numerical ones
            columns = []
            for col_name in study.table.data.columns:
                try:
                    data = self.get_source_data(col_name)
                    if data is not None and len(data) > 0:
                        columns.append(col_name)
                except Exception:
                    continue
            
            return columns
            
        except Exception:
            return []
    
    # ========================================================================
    # Statistical Analysis
    # ========================================================================
    
    def analyze_column(self, column_name: str) -> Dict[str, Any]:
        """Perform statistical analysis on a column.
        
        Args:
            column_name: Name of column to analyze
            
        Returns:
            Dictionary of statistical measures
        """
        data = self.get_source_data(column_name)
        
        if data is None or len(data) == 0:
            return {}
        
        # Calculate statistics
        stats = {
            'column_name': column_name,
            'count': int(len(data)),
            'mean': float(np.mean(data)),
            'median': float(np.median(data)),
            'std': float(np.std(data, ddof=1)) if len(data) > 1 else 0.0,
            'variance': float(np.var(data, ddof=1)) if len(data) > 1 else 0.0,
            'min': float(np.min(data)),
            'max': float(np.max(data)),
            'range': float(np.max(data) - np.min(data)),
            'q25': float(np.percentile(data, 25)),
            'q50': float(np.percentile(data, 50)),
            'q75': float(np.percentile(data, 75)),
            'iqr': float(np.percentile(data, 75) - np.percentile(data, 25)),
            'skewness': float(self._calculate_skewness(data)),
            'kurtosis': float(self._calculate_kurtosis(data)),
        }
        
        # Store results
        self.results[column_name] = stats
        
        # Add to analyzed columns if not already present
        if column_name not in self.analyzed_columns:
            self.analyzed_columns.append(column_name)
        
        return stats
    
    def _calculate_skewness(self, data: np.ndarray) -> float:
        """Calculate skewness (measure of asymmetry).
        
        Args:
            data: Numpy array of values
            
        Returns:
            Skewness value
        """
        if len(data) < 3:
            return 0.0
        
        n = len(data)
        mean = np.mean(data)
        std = np.std(data, ddof=1)
        
        if std == 0:
            return 0.0
        
        m3 = np.sum((data - mean)**3) / n
        skew = m3 / (std**3)
        
        # Apply bias correction
        skew = skew * np.sqrt(n * (n - 1)) / (n - 2)
        
        return skew
    
    def _calculate_kurtosis(self, data: np.ndarray) -> float:
        """Calculate excess kurtosis (measure of tailedness).
        
        Excess kurtosis: subtract 3 so normal distribution has kurtosis of 0.
        
        Args:
            data: Numpy array of values
            
        Returns:
            Excess kurtosis value
        """
        if len(data) < 4:
            return 0.0
        
        n = len(data)
        mean = np.mean(data)
        std = np.std(data, ddof=1)
        
        if std == 0:
            return 0.0
        
        m4 = np.sum((data - mean)**4) / n
        kurt = m4 / (std**4)
        
        # Excess kurtosis (subtract 3 for normal distribution = 0)
        excess_kurt = kurt - 3.0
        
        # Apply bias correction
        excess_kurt = ((n - 1) * ((n + 1) * excess_kurt + 6)) / ((n - 2) * (n - 3))
        
        return excess_kurt
    
    def get_results(self, column_name: str) -> Optional[Dict[str, Any]]:
        """Get analysis results for a column.
        
        Args:
            column_name: Column name
            
        Returns:
            Dictionary of statistics, or None if not analyzed
        """
        return self.results.get(column_name)
    
    def clear_results(self):
        """Clear all analysis results."""
        self.results.clear()
        self.analyzed_columns.clear()
    
    # ========================================================================
    # Serialization
    # ========================================================================
    
    def to_dict(self) -> Dict[str, Any]:
        """Export study to dictionary format.
        
        Returns:
            Dictionary representation
        """
        base_dict = super().to_dict()
        
        base_dict["metadata"]["source_study"] = self.source_study
        base_dict["metadata"]["analyzed_columns"] = self.analyzed_columns
        base_dict["metadata"]["results"] = self.results
        
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], workspace=None) -> StatisticsStudy:
        """Create study from dictionary.
        
        Args:
            data: Dictionary representation
            workspace: Reference to workspace
            
        Returns:
            StatisticsStudy instance
        """
        metadata = data.get("metadata", {})
        
        study = cls(
            name=data["name"],
            source_study=metadata.get("source_study"),
            workspace=workspace
        )
        
        study.analyzed_columns = metadata.get("analyzed_columns", [])
        study.results = metadata.get("results", {})
        
        # Restore base metadata
        study.metadata = metadata
        
        return study
    
    def __repr__(self) -> str:
        return f"StatisticsStudy(name='{self.name}', source='{self.source_study}', analyzed={len(self.analyzed_columns)})"
