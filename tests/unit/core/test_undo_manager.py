"""Unit tests for undo/redo system."""

import pytest
import numpy as np

from core.undo_manager import UndoManager, UndoAction, ActionType, UndoContext
from studies.data_table_study import DataTableStudy, ColumnType
from core.workspace import Workspace


class TestUndoManager:
    """Tests for UndoManager."""
    
    def test_initialization(self):
        """Test undo manager initialization."""
        undo_mgr = UndoManager()
        
        assert undo_mgr.max_history == 50
        assert not undo_mgr.can_undo()
        assert not undo_mgr.can_redo()
        assert undo_mgr.is_enabled()
    
    def test_custom_max_history(self):
        """Test custom history limit."""
        undo_mgr = UndoManager(max_history=10)
        
        assert undo_mgr.max_history == 10
    
    def test_push_action(self):
        """Test pushing action to stack."""
        undo_mgr = UndoManager()
        
        action = UndoAction(
            action_type=ActionType.ADD_COLUMN,
            undo_func=lambda: None,
            redo_func=lambda: None,
            description="Test action"
        )
        
        undo_mgr.push(action)
        
        assert undo_mgr.can_undo()
        assert not undo_mgr.can_redo()
        assert undo_mgr.get_undo_count() == 1
    
    def test_undo_action(self):
        """Test undo action execution."""
        undo_mgr = UndoManager()
        
        value = [0]
        
        def undo():
            value[0] -= 1
        
        def redo():
            value[0] += 1
        
        action = UndoAction(
            action_type=ActionType.ADD_COLUMN,
            undo_func=undo,
            redo_func=redo,
            description="Test"
        )
        
        undo_mgr.push(action)
        value[0] += 1  # Simulate action
        
        assert value[0] == 1
        
        undo_mgr.undo()
        assert value[0] == 0
        assert undo_mgr.can_redo()
    
    def test_redo_action(self):
        """Test redo action execution."""
        undo_mgr = UndoManager()
        
        value = [0]
        
        def undo():
            value[0] -= 1
        
        def redo():
            value[0] += 1
        
        action = UndoAction(
            action_type=ActionType.ADD_COLUMN,
            undo_func=undo,
            redo_func=redo,
            description="Test"
        )
        
        undo_mgr.push(action)
        value[0] += 1
        
        undo_mgr.undo()
        assert value[0] == 0
        
        undo_mgr.redo()
        assert value[0] == 1
    
    def test_redo_clears_on_new_action(self):
        """Test redo stack clears when new action is pushed."""
        undo_mgr = UndoManager()
        
        action1 = UndoAction(
            action_type=ActionType.ADD_COLUMN,
            undo_func=lambda: None,
            redo_func=lambda: None,
            description="Action 1"
        )
        
        action2 = UndoAction(
            action_type=ActionType.ADD_COLUMN,
            undo_func=lambda: None,
            redo_func=lambda: None,
            description="Action 2"
        )
        
        undo_mgr.push(action1)
        undo_mgr.undo()
        
        assert undo_mgr.can_redo()
        
        undo_mgr.push(action2)
        assert not undo_mgr.can_redo()
    
    def test_max_history_limit(self):
        """Test history limit enforcement."""
        undo_mgr = UndoManager(max_history=3)
        
        for i in range(5):
            action = UndoAction(
                action_type=ActionType.ADD_COLUMN,
                undo_func=lambda: None,
                redo_func=lambda: None,
                description=f"Action {i}"
            )
            undo_mgr.push(action)
        
        assert undo_mgr.get_undo_count() == 3
    
    def test_get_undo_description(self):
        """Test getting undo description."""
        undo_mgr = UndoManager()
        
        action = UndoAction(
            action_type=ActionType.ADD_COLUMN,
            undo_func=lambda: None,
            redo_func=lambda: None,
            description="Add column 'x'"
        )
        
        undo_mgr.push(action)
        
        assert undo_mgr.get_undo_description() == "Add column 'x'"
    
    def test_get_redo_description(self):
        """Test getting redo description."""
        undo_mgr = UndoManager()
        
        action = UndoAction(
            action_type=ActionType.REMOVE_COLUMN,
            undo_func=lambda: None,
            redo_func=lambda: None,
            description="Remove column 'y'"
        )
        
        undo_mgr.push(action)
        undo_mgr.undo()
        
        assert undo_mgr.get_redo_description() == "Remove column 'y'"
    
    def test_clear_history(self):
        """Test clearing all history."""
        undo_mgr = UndoManager()
        
        action = UndoAction(
            action_type=ActionType.ADD_COLUMN,
            undo_func=lambda: None,
            redo_func=lambda: None,
            description="Test"
        )
        
        undo_mgr.push(action)
        undo_mgr.undo()
        
        assert undo_mgr.can_redo()
        
        undo_mgr.clear()
        
        assert not undo_mgr.can_undo()
        assert not undo_mgr.can_redo()
    
    def test_enable_disable(self):
        """Test enabling/disabling undo tracking."""
        undo_mgr = UndoManager()
        
        action = UndoAction(
            action_type=ActionType.ADD_COLUMN,
            undo_func=lambda: None,
            redo_func=lambda: None,
            description="Test"
        )
        
        undo_mgr.set_enabled(False)
        undo_mgr.push(action)
        
        assert not undo_mgr.can_undo()
        
        undo_mgr.set_enabled(True)
        undo_mgr.push(action)
        
        assert undo_mgr.can_undo()
    
    def test_get_history(self):
        """Test getting action history."""
        undo_mgr = UndoManager()
        
        for i in range(5):
            action = UndoAction(
                action_type=ActionType.ADD_COLUMN,
                undo_func=lambda: None,
                redo_func=lambda: None,
                description=f"Action {i}"
            )
            undo_mgr.push(action)
        
        history = undo_mgr.get_history(limit=3)
        
        assert len(history) == 3
        assert history[0] == "Action 4"  # Most recent first
        assert history[1] == "Action 3"
        assert history[2] == "Action 2"


class TestUndoContext:
    """Tests for UndoContext."""
    
    def test_disable_tracking(self):
        """Test disabling tracking in context."""
        undo_mgr = UndoManager()
        
        action = UndoAction(
            action_type=ActionType.ADD_COLUMN,
            undo_func=lambda: None,
            redo_func=lambda: None,
            description="Test"
        )
        
        with UndoContext(undo_mgr, enabled=False):
            undo_mgr.push(action)
        
        assert not undo_mgr.can_undo()
    
    def test_restore_previous_state(self):
        """Test restoring previous tracking state."""
        undo_mgr = UndoManager()
        undo_mgr.set_enabled(False)
        
        with UndoContext(undo_mgr, enabled=True):
            assert undo_mgr.is_enabled()
        
        assert not undo_mgr.is_enabled()


class TestDataTableStudyUndo:
    """Tests for undo/redo in DataTableStudy."""
    
    def test_remove_column_undo(self):
        """Test undo of column removal."""
        workspace = Workspace("test", "numerical")
        study = DataTableStudy("test", workspace)
        
        study.add_column("x", ColumnType.DATA)
        study.add_rows(5)
        study.table.set_column("x", np.array([1, 2, 3, 4, 5]))
        
        # Remove column
        study.remove_column("x")
        assert "x" not in study.table.data.columns
        
        # Undo
        study.undo_manager.undo()
        assert "x" in study.table.data.columns
        assert list(study.table.get_column("x")) == [1, 2, 3, 4, 5]
    
    def test_remove_column_redo(self):
        """Test redo of column removal."""
        workspace = Workspace("test", "numerical")
        study = DataTableStudy("test", workspace)
        
        study.add_column("y", ColumnType.DATA)
        study.add_rows(3)
        
        study.remove_column("y")
        study.undo_manager.undo()
        
        # Redo
        study.undo_manager.redo()
        assert "y" not in study.table.data.columns
    
    def test_rename_column_undo(self):
        """Test undo of column rename."""
        workspace = Workspace("test", "numerical")
        study = DataTableStudy("test", workspace)
        
        study.add_column("old_name", ColumnType.DATA)
        study.add_rows(3)
        
        # Rename
        study.rename_column("old_name", "new_name")
        assert "new_name" in study.table.data.columns
        assert "old_name" not in study.table.data.columns
        
        # Undo
        study.undo_manager.undo()
        assert "old_name" in study.table.data.columns
        assert "new_name" not in study.table.data.columns
    
    def test_rename_column_redo(self):
        """Test redo of column rename."""
        workspace = Workspace("test", "numerical")
        study = DataTableStudy("test", workspace)
        
        study.add_column("a", ColumnType.DATA)
        study.add_rows(2)
        
        study.rename_column("a", "b")
        study.undo_manager.undo()
        
        # Redo
        study.undo_manager.redo()
        assert "b" in study.table.data.columns
        assert "a" not in study.table.data.columns
    
    def test_undo_preserves_metadata(self):
        """Test undo preserves column metadata."""
        workspace = Workspace("test", "numerical")
        study = DataTableStudy("test", workspace)
        
        study.add_column("data_col", ColumnType.DATA, unit="m")
        study.add_rows(5)
        
        study.remove_column("data_col")
        study.undo_manager.undo()
        
        assert study.column_metadata["data_col"]["type"] == ColumnType.DATA
        assert study.column_metadata["data_col"]["unit"] == "m"
    
    def test_undo_manager_initialized(self):
        """Test undo manager is initialized in study."""
        workspace = Workspace("test", "numerical")
        study = DataTableStudy("test", workspace)
        
        assert hasattr(study, 'undo_manager')
        assert isinstance(study.undo_manager, UndoManager)
    
    def test_multiple_operations(self):
        """Test multiple undo/redo operations."""
        workspace = Workspace("test", "numerical")
        study = DataTableStudy("test", workspace)
        
        # Add columns
        study.add_column("col1", ColumnType.DATA)
        study.add_column("col2", ColumnType.DATA)
        study.add_column("col3", ColumnType.DATA)
        study.add_rows(3)
        
        # Remove col2
        study.remove_column("col2")
        
        # Rename col3
        study.rename_column("col3", "col3_renamed")
        
        # Undo rename
        study.undo_manager.undo()
        assert "col3" in study.table.data.columns
        
        # Undo remove
        study.undo_manager.undo()
        assert "col2" in study.table.data.columns
        
        # Redo remove
        study.undo_manager.redo()
        assert "col2" not in study.table.data.columns
        
        # Redo rename
        study.undo_manager.redo()
        assert "col3_renamed" in study.table.data.columns
