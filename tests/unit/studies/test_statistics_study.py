"""
Unit tests for StatisticsStudy class.
"""

import pytest
import numpy as np
from studies.statistics_study import StatisticsStudy
from studies.data_table_study import DataTableStudy, ColumnType
from core.workspace import Workspace


class TestStatisticsStudyCreation:
    """Test StatisticsStudy creation and basic properties."""
    
    def test_create_study(self):
        """Test creating a statistics study."""
        study = StatisticsStudy("Test Statistics")
        
        assert study.name == "Test Statistics"
        assert study.get_type() == "statistics"
        assert study.source_study is None
        assert len(study.analyzed_columns) == 0
        assert len(study.results) == 0
    
    def test_create_with_source(self):
        """Test creating a statistics study with source."""
        study = StatisticsStudy("Test Statistics", source_study="Data Table 1")
        
        assert study.source_study == "Data Table 1"


class TestSourceManagement:
    """Test source data management."""
    
    def test_set_source_study(self):
        """Test setting source study."""
        study = StatisticsStudy("Stats")
        study.set_source_study("Data Table 1")
        
        assert study.source_study == "Data Table 1"
    
    def test_get_source_data_without_workspace(self):
        """Test getting source data without workspace returns None."""
        study = StatisticsStudy("Stats", source_study="Data Table 1")
        
        data = study.get_source_data("x")
        assert data is None
    
    def test_get_available_columns_without_workspace(self):
        """Test getting available columns without workspace."""
        study = StatisticsStudy("Stats", source_study="Data Table 1")
        
        columns = study.get_available_columns()
        assert columns == []


class TestStatisticalAnalysis:
    """Test statistical analysis functionality."""
    
    @pytest.fixture
    def workspace_with_data(self):
        """Create workspace with data table for testing."""
        workspace = Workspace("Test Workspace", "general")
        
        # Create data table study
        data_study = DataTableStudy("Data Table 1", workspace=workspace)
        workspace.add_study(data_study)
        
        # Add numerical data column
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        data_study.add_column("values", unit="m", initial_data=data)
        
        return workspace
    
    def test_get_source_data(self, workspace_with_data):
        """Test getting source data from workspace."""
        stats_study = StatisticsStudy("Stats", source_study="Data Table 1", workspace=workspace_with_data)
        
        data = stats_study.get_source_data("values")
        
        assert data is not None
        assert len(data) == 10
        np.testing.assert_array_equal(data, np.arange(1.0, 11.0))
    
    def test_get_available_columns(self, workspace_with_data):
        """Test getting available columns."""
        stats_study = StatisticsStudy("Stats", source_study="Data Table 1", workspace=workspace_with_data)
        
        columns = stats_study.get_available_columns()
        
        assert "values" in columns
    
    def test_analyze_column_basic(self, workspace_with_data):
        """Test basic column analysis."""
        stats_study = StatisticsStudy("Stats", source_study="Data Table 1", workspace=workspace_with_data)
        
        results = stats_study.analyze_column("values")
        
        # Check basic statistics
        assert results['count'] == 10
        assert results['mean'] == pytest.approx(5.5)
        assert results['median'] == pytest.approx(5.5)
        assert results['min'] == 1.0
        assert results['max'] == 10.0
        assert results['range'] == 9.0
        
        # Check column was added to analyzed list
        assert "values" in stats_study.analyzed_columns
        assert "values" in stats_study.results
    
    def test_analyze_column_variance_std(self, workspace_with_data):
        """Test variance and standard deviation calculations."""
        stats_study = StatisticsStudy("Stats", source_study="Data Table 1", workspace=workspace_with_data)
        
        results = stats_study.analyze_column("values")
        
        # For 1-10, std should be ~3.03
        assert results['std'] == pytest.approx(3.0276503, rel=1e-5)
        assert results['variance'] == pytest.approx(9.1666667, rel=1e-5)
    
    def test_analyze_column_quartiles(self, workspace_with_data):
        """Test quartile calculations."""
        stats_study = StatisticsStudy("Stats", source_study="Data Table 1", workspace=workspace_with_data)
        
        results = stats_study.analyze_column("values")
        
        assert results['q25'] == pytest.approx(3.25)
        assert results['q50'] == pytest.approx(5.5)
        assert results['q75'] == pytest.approx(7.75)
        assert results['iqr'] == pytest.approx(4.5)
    
    def test_skewness_symmetric_data(self, workspace_with_data):
        """Test skewness for symmetric data."""
        stats_study = StatisticsStudy("Stats", source_study="Data Table 1", workspace=workspace_with_data)
        
        results = stats_study.analyze_column("values")
        
        # Uniform distribution should have near-zero skewness
        assert abs(results['skewness']) < 0.1
    
    def test_kurtosis_uniform_data(self, workspace_with_data):
        """Test kurtosis for uniform-like data."""
        stats_study = StatisticsStudy("Stats", source_study="Data Table 1", workspace=workspace_with_data)
        
        results = stats_study.analyze_column("values")
        
        # Uniform distribution has negative excess kurtosis
        assert results['kurtosis'] < 0
    
    def test_analyze_with_nan_values(self):
        """Test analysis with NaN values."""
        workspace = Workspace("Test", "general")
        data_study = DataTableStudy("Data", workspace=workspace)
        workspace.add_study(data_study)
        
        # Add data with NaN
        data = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        data_study.add_column("x", initial_data=data)
        
        stats_study = StatisticsStudy("Stats", source_study="Data", workspace=workspace)
        results = stats_study.analyze_column("x")
        
        # Should ignore NaN
        assert results['count'] == 4
        assert results['mean'] == pytest.approx(3.0)
    
    def test_analyze_with_inf_values(self):
        """Test analysis with infinity values."""
        workspace = Workspace("Test", "general")
        data_study = DataTableStudy("Data", workspace=workspace)
        workspace.add_study(data_study)
        
        # Add data with inf
        data = np.array([1.0, 2.0, np.inf, 4.0, 5.0])
        data_study.add_column("x", initial_data=data)
        
        stats_study = StatisticsStudy("Stats", source_study="Data", workspace=workspace)
        results = stats_study.analyze_column("x")
        
        # Should ignore inf
        assert results['count'] == 4
        assert results['mean'] == pytest.approx(3.0)
    
    def test_analyze_empty_column(self):
        """Test analyzing empty column."""
        workspace = Workspace("Test", "general")
        data_study = DataTableStudy("Data", workspace=workspace)
        workspace.add_study(data_study)
        
        # Add empty column
        data_study.add_column("x")
        
        stats_study = StatisticsStudy("Stats", source_study="Data", workspace=workspace)
        results = stats_study.analyze_column("x")
        
        # Should return empty dict
        assert results == {}
    
    def test_get_results(self, workspace_with_data):
        """Test getting stored results."""
        stats_study = StatisticsStudy("Stats", source_study="Data Table 1", workspace=workspace_with_data)
        
        stats_study.analyze_column("values")
        results = stats_study.get_results("values")
        
        assert results is not None
        assert results['count'] == 10
    
    def test_get_results_not_analyzed(self, workspace_with_data):
        """Test getting results for non-analyzed column."""
        stats_study = StatisticsStudy("Stats", source_study="Data Table 1", workspace=workspace_with_data)
        
        results = stats_study.get_results("values")
        
        assert results is None
    
    def test_clear_results(self, workspace_with_data):
        """Test clearing results."""
        stats_study = StatisticsStudy("Stats", source_study="Data Table 1", workspace=workspace_with_data)
        
        stats_study.analyze_column("values")
        assert len(stats_study.results) > 0
        
        stats_study.clear_results()
        
        assert len(stats_study.results) == 0
        assert len(stats_study.analyzed_columns) == 0


class TestEdgeCases:
    """Test edge cases for statistics calculations."""
    
    def test_skewness_insufficient_data(self):
        """Test skewness with less than 3 data points."""
        workspace = Workspace("Test", "general")
        data_study = DataTableStudy("Data", workspace=workspace)
        workspace.add_study(data_study)
        
        data = np.array([1.0, 2.0])
        data_study.add_column("x", initial_data=data)
        
        stats_study = StatisticsStudy("Stats", source_study="Data", workspace=workspace)
        results = stats_study.analyze_column("x")
        
        assert results['skewness'] == 0.0
    
    def test_kurtosis_insufficient_data(self):
        """Test kurtosis with less than 4 data points."""
        workspace = Workspace("Test", "general")
        data_study = DataTableStudy("Data", workspace=workspace)
        workspace.add_study(data_study)
        
        data = np.array([1.0, 2.0, 3.0])
        data_study.add_column("x", initial_data=data)
        
        stats_study = StatisticsStudy("Stats", source_study="Data", workspace=workspace)
        results = stats_study.analyze_column("x")
        
        assert results['kurtosis'] == 0.0
    
    def test_constant_data(self):
        """Test analysis with constant data."""
        workspace = Workspace("Test", "general")
        data_study = DataTableStudy("Data", workspace=workspace)
        workspace.add_study(data_study)
        
        data = np.array([5.0, 5.0, 5.0, 5.0, 5.0])
        data_study.add_column("x", initial_data=data)
        
        stats_study = StatisticsStudy("Stats", source_study="Data", workspace=workspace)
        results = stats_study.analyze_column("x")
        
        assert results['mean'] == 5.0
        assert results['std'] == 0.0
        assert results['variance'] == 0.0
        assert results['range'] == 0.0
        assert results['skewness'] == 0.0
        assert results['kurtosis'] == 0.0


class TestSerialization:
    """Test serialization and deserialization."""
    
    def test_to_dict_empty(self):
        """Test serialization of empty study."""
        study = StatisticsStudy("Stats", source_study="Data Table 1")
        
        data = study.to_dict()
        
        assert data['name'] == "Stats"
        assert data['type'] == "statistics"
        assert data['metadata']['source_study'] == "Data Table 1"
        assert data['metadata']['analyzed_columns'] == []
        assert data['metadata']['results'] == {}
    
    def test_to_dict_with_results(self):
        """Test serialization with results."""
        workspace = Workspace("Test", "general")
        data_study = DataTableStudy("Data", workspace=workspace)
        workspace.add_study(data_study)
        
        data = np.array([1.0, 2.0, 3.0])
        data_study.add_column("x", initial_data=data)
        
        stats_study = StatisticsStudy("Stats", source_study="Data", workspace=workspace)
        stats_study.analyze_column("x")
        
        data_dict = stats_study.to_dict()
        
        assert data_dict['metadata']['analyzed_columns'] == ["x"]
        assert "x" in data_dict['metadata']['results']
        assert data_dict['metadata']['results']['x']['count'] == 3
    
    def test_from_dict(self):
        """Test deserialization."""
        data = {
            'name': "Stats",
            'type': "statistics",
            'metadata': {
                'source_study': "Data Table 1",
                'analyzed_columns': ["x", "y"],
                'results': {
                    'x': {'count': 10, 'mean': 5.0}
                }
            }
        }
        
        study = StatisticsStudy.from_dict(data)
        
        assert study.name == "Stats"
        assert study.source_study == "Data Table 1"
        assert study.analyzed_columns == ["x", "y"]
        assert "x" in study.results
        assert study.results['x']['count'] == 10
    
    def test_roundtrip_serialization(self):
        """Test round-trip serialization."""
        workspace = Workspace("Test", "general")
        data_study = DataTableStudy("Data", workspace=workspace)
        workspace.add_study(data_study)
        
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        data_study.add_column("values", initial_data=data)
        
        stats_study = StatisticsStudy("Stats", source_study="Data", workspace=workspace)
        stats_study.analyze_column("values")
        
        # Serialize
        data_dict = stats_study.to_dict()
        
        # Deserialize
        restored_study = StatisticsStudy.from_dict(data_dict, workspace=workspace)
        
        assert restored_study.name == stats_study.name
        assert restored_study.source_study == stats_study.source_study
        assert restored_study.analyzed_columns == stats_study.analyzed_columns
        assert "values" in restored_study.results
        assert restored_study.results['values']['count'] == 5
