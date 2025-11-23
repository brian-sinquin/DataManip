"""Unit tests for notification manager."""

import pytest
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QTimer

from ui.notification_manager import (
    ToastNotification, NotificationManager, ProgressNotification
)


@pytest.fixture
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def main_window(qapp):
    """Create main window for notification parent."""
    window = QMainWindow()
    window.resize(800, 600)
    window.show()
    yield window
    window.close()


class TestToastNotification:
    """Tests for ToastNotification."""
    
    def test_initialization(self, qapp, main_window):
        """Test toast notification initialization."""
        toast = ToastNotification("Test message", main_window)
        
        assert toast.text() == "Test message"
        assert toast.parent() == main_window
        assert toast.duration == 3000
    
    def test_custom_duration(self, qapp, main_window):
        """Test custom duration."""
        toast = ToastNotification("Test", main_window, duration=5000)
        
        assert toast.duration == 5000
    
    def test_opacity_effect(self, qapp, main_window):
        """Test opacity effect is applied."""
        toast = ToastNotification("Test", main_window)
        
        assert toast.opacity_effect is not None
        assert toast.opacity_effect.opacity() == 0.0
    
    def test_animations_exist(self, qapp, main_window):
        """Test fade animations exist."""
        toast = ToastNotification("Test", main_window)
        
        assert toast.fade_in is not None
        assert toast.fade_out is not None
        assert toast.timer is not None
    
    def test_show_notification(self, qapp, main_window):
        """Test showing notification."""
        toast = ToastNotification("Test", main_window)
        toast.show_notification()
        
        assert toast.isVisible()
    
    def test_positioning(self, qapp, main_window):
        """Test notification is positioned correctly."""
        toast = ToastNotification("Test", main_window)
        toast.show_notification()
        
        # Should be at top-right corner
        parent_rect = main_window.rect()
        expected_x = parent_rect.width() - toast.width() - 20
        expected_y = 60  # Below menu bar
        
        assert abs(toast.x() - expected_x) < 10  # Allow small margin
        assert abs(toast.y() - expected_y) < 10


class TestNotificationManager:
    """Tests for NotificationManager."""
    
    def test_initialization(self, qapp, main_window):
        """Test notification manager initialization."""
        manager = NotificationManager(main_window)
        
        assert manager.parent == main_window
        assert manager.active_notifications == []
    
    def test_show_info(self, qapp, main_window):
        """Test showing info notification."""
        manager = NotificationManager(main_window)
        manager.show_info("Info message")
        
        assert len(manager.active_notifications) == 1
    
    def test_show_success(self, qapp, main_window):
        """Test showing success notification."""
        manager = NotificationManager(main_window)
        manager.show_success("Success message")
        
        assert len(manager.active_notifications) == 1
    
    def test_show_warning(self, qapp, main_window):
        """Test showing warning notification."""
        manager = NotificationManager(main_window)
        manager.show_warning("Warning message")
        
        assert len(manager.active_notifications) == 1
    
    def test_show_error(self, qapp, main_window):
        """Test showing error notification."""
        manager = NotificationManager(main_window)
        manager.show_error("Error message")
        
        assert len(manager.active_notifications) == 1
    
    def test_multiple_notifications(self, qapp, main_window):
        """Test multiple notifications stack correctly."""
        manager = NotificationManager(main_window)
        
        manager.show_info("Message 1")
        manager.show_info("Message 2")
        manager.show_info("Message 3")
        
        assert len(manager.active_notifications) == 3
    
    def test_notification_types(self, qapp, main_window):
        """Test different notification types."""
        manager = NotificationManager(main_window)
        
        manager.show_info("Info")
        manager.show_success("Success")
        manager.show_warning("Warning")
        manager.show_error("Error")
        
        assert len(manager.active_notifications) == 4
    
    def test_custom_duration_info(self, qapp, main_window):
        """Test custom duration for info."""
        manager = NotificationManager(main_window)
        manager.show_info("Test", duration=10000)
        
        toast = manager.active_notifications[0]
        assert toast.duration == 10000
    
    def test_custom_duration_warning(self, qapp, main_window):
        """Test custom duration for warning."""
        manager = NotificationManager(main_window)
        manager.show_warning("Test", duration=8000)
        
        toast = manager.active_notifications[0]
        assert toast.duration == 8000
    
    def test_custom_duration_error(self, qapp, main_window):
        """Test custom duration for error."""
        manager = NotificationManager(main_window)
        manager.show_error("Test", duration=12000)
        
        toast = manager.active_notifications[0]
        assert toast.duration == 12000


class TestProgressNotification:
    """Tests for ProgressNotification."""
    
    def test_initialization(self, qapp, main_window):
        """Test progress notification initialization."""
        progress = ProgressNotification("Processing...", main_window)
        
        assert progress.text() == "Processing..."
        assert progress.parent() == main_window
    
    def test_show_progress(self, qapp, main_window):
        """Test showing progress notification."""
        progress = ProgressNotification("Loading...", main_window)
        progress.show_progress()
        
        assert progress.isVisible()
    
    def test_update_message(self, qapp, main_window):
        """Test updating progress message."""
        progress = ProgressNotification("Step 1", main_window)
        progress.show_progress()
        
        progress.update_message("Step 2")
        assert progress.text() == "Step 2"
        
        progress.update_message("Step 3")
        assert progress.text() == "Step 3"
    
    def test_finish_success(self, qapp, main_window):
        """Test finishing with success."""
        progress = ProgressNotification("Working...", main_window)
        progress.show_progress()
        
        progress.finish("Done!", success=True)
        assert progress.text() == "Done!"
    
    def test_finish_failure(self, qapp, main_window):
        """Test finishing with failure."""
        progress = ProgressNotification("Working...", main_window)
        progress.show_progress()
        
        progress.finish("Failed!", success=False)
        assert progress.text() == "Failed!"
    
    def test_finish_without_message(self, qapp, main_window):
        """Test finishing without final message."""
        progress = ProgressNotification("Working...", main_window)
        progress.show_progress()
        
        progress.finish()
        assert progress.text() == "Working..."
    
    def test_opacity_effect(self, qapp, main_window):
        """Test opacity effect is applied."""
        progress = ProgressNotification("Test", main_window)
        
        assert progress.opacity_effect is not None
        assert progress.opacity_effect.opacity() == 0.0
    
    def test_fade_in_animation(self, qapp, main_window):
        """Test fade in animation exists."""
        progress = ProgressNotification("Test", main_window)
        
        assert progress.fade_in is not None
    
    def test_positioning(self, qapp, main_window):
        """Test progress notification is positioned correctly."""
        progress = ProgressNotification("Test", main_window)
        progress.show_progress()
        
        # Should be near bottom center
        parent_rect = main_window.rect()
        expected_x = (parent_rect.width() - progress.width()) // 2
        
        assert abs(progress.x() - expected_x) < 10


class TestNotificationIntegration:
    """Integration tests for notification system."""
    
    def test_manager_with_multiple_types(self, qapp, main_window):
        """Test manager handles multiple notification types."""
        manager = NotificationManager(main_window)
        
        manager.show_info("Info")
        manager.show_success("Success")
        manager.show_warning("Warning")
        
        assert len(manager.active_notifications) == 3
        
        # All should be visible
        for notification in manager.active_notifications:
            assert notification.isVisible()
    
    def test_notification_stacking(self, qapp, main_window):
        """Test notifications stack properly."""
        manager = NotificationManager(main_window)
        
        manager.show_info("First")
        first_pos_initial = manager.active_notifications[0].y()
        
        manager.show_info("Second")
        first_pos_after = manager.active_notifications[0].y()
        second_pos = manager.active_notifications[1].y()
        
        # First notification gets moved down when second appears (higher y)
        # Second appears at the top position (60)
        assert second_pos == 60  # Second is at top
        assert first_pos_after > first_pos_initial  # First was moved down
    
    def test_progress_with_manager(self, qapp, main_window):
        """Test progress notification alongside toast notifications."""
        manager = NotificationManager(main_window)
        
        # Show some toasts
        manager.show_info("Info 1")
        manager.show_info("Info 2")
        
        # Show progress
        progress = ProgressNotification("Loading...", main_window)
        progress.show_progress()
        
        assert len(manager.active_notifications) == 2
        assert progress.isVisible()
    
    def test_notification_styles(self, qapp, main_window):
        """Test different notification types have different styles."""
        manager = NotificationManager(main_window)
        
        manager.show_info("Info")
        manager.show_success("Success")
        manager.show_warning("Warning")
        manager.show_error("Error")
        
        # Each should have its own style
        notifications = manager.active_notifications
        
        # Check all have stylesheet
        for notif in notifications:
            assert notif.styleSheet() != ""
