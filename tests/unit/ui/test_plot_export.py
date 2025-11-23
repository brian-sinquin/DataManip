"""
Test plot export functionality.
"""

import pytest
from pathlib import Path
import tempfile

from core.workspace import Workspace
from studies.data_table_study import DataTableStudy, ColumnType
from studies.plot_study import PlotStudy


def test_plot_export_requires_series():
    """Test that plot export validates series presence."""
    workspace = Workspace("Test Workspace", "general")
    study = PlotStudy("Test Plot", workspace=workspace)
    
    # No series yet - should have empty series list
    assert len(study.series) == 0


def test_plot_export_with_data():
    """Test plot export with actual data."""
    workspace = Workspace("Test Workspace", "general")
    
    # Create data table
    data_study = DataTableStudy("Data", workspace=workspace)
    data_study.add_column("x", ColumnType.RANGE, 
                          range_type="linspace", 
                          range_start=0, 
                          range_stop=10, 
                          range_count=11)
    data_study.add_column("y", ColumnType.CALCULATED, formula="{x}**2")
    
    # Create plot
    plot_study = PlotStudy("Test Plot", workspace=workspace)
    plot_study.add_series("Data", "x", "y", label="x²")
    
    # Verify series added
    assert len(plot_study.series) == 1
    assert plot_study.series[0]["label"] == "x²"
    
    # Export to temp file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    
    try:
        from matplotlib.figure import Figure
        fig = Figure()
        plot_study.update_plot(fig)
        fig.savefig(str(tmp_path), dpi=100, bbox_inches='tight')
        
        # Verify file created
        assert tmp_path.exists()
        assert tmp_path.stat().st_size > 0
    finally:
        # Cleanup
        if tmp_path.exists():
            tmp_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
