"""Toast notification system for user feedback."""

from PySide6.QtWidgets import QLabel, QGraphicsOpacityEffect
from PySide6.QtCore import QTimer, QPropertyAnimation, QEasingCurve, Qt, QPoint
from PySide6.QtGui import QFont
from typing import Optional


class ToastNotification(QLabel):
    """Toast notification widget.
    
    Displays temporary messages with fade-in/fade-out animations.
    """
    
    def __init__(self, message: str, parent=None, duration: int = 3000):
        """Initialize toast notification.
        
        Args:
            message: Message to display
            parent: Parent widget
            duration: Display duration in milliseconds
        """
        super().__init__(message, parent)
        
        self.duration = duration
        
        # Setup appearance
        self.setStyleSheet("""
            QLabel {
                background-color: rgba(50, 50, 50, 220);
                color: white;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 13px;
            }
        """)
        
        font = QFont()
        font.setPointSize(11)
        self.setFont(font)
        
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(True)
        self.setMaximumWidth(400)
        
        # Setup opacity effect
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)
        
        # Setup animations
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(200)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.InQuad)
        
        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(200)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setEasingCurve(QEasingCurve.OutQuad)
        self.fade_out.finished.connect(self.deleteLater)
        
        # Timer to start fade out
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.fade_out.start)
        
        self.adjustSize()
    
    def show_notification(self):
        """Show notification with animations."""
        if self.parent():
            # Position at top-right corner of parent
            parent_rect = self.parent().rect()
            x = parent_rect.width() - self.width() - 20
            y = 60  # Below menu bar
            self.move(x, y)
        
        self.show()
        self.raise_()
        self.fade_in.start()
        self.timer.start(self.duration)


class NotificationManager:
    """Manager for toast notifications.
    
    Handles displaying and stacking multiple notifications.
    """
    
    def __init__(self, parent):
        """Initialize notification manager.
        
        Args:
            parent: Parent widget where notifications will be displayed
        """
        self.parent = parent
        self.active_notifications = []
    
    def show_info(self, message: str, duration: int = 3000):
        """Show informational notification.
        
        Args:
            message: Message to display
            duration: Display duration in milliseconds
        """
        self._show_notification(message, duration, "info")
    
    def show_success(self, message: str, duration: int = 3000):
        """Show success notification.
        
        Args:
            message: Message to display
            duration: Display duration in milliseconds
        """
        self._show_notification(message, duration, "success")
    
    def show_warning(self, message: str, duration: int = 4000):
        """Show warning notification.
        
        Args:
            message: Message to display
            duration: Display duration in milliseconds
        """
        self._show_notification(message, duration, "warning")
    
    def show_error(self, message: str, duration: int = 5000):
        """Show error notification.
        
        Args:
            message: Message to display
            duration: Display duration in milliseconds
        """
        self._show_notification(message, duration, "error")
    
    def _show_notification(self, message: str, duration: int, notification_type: str):
        """Create and show notification.
        
        Args:
            message: Message to display
            duration: Display duration in milliseconds
            notification_type: Type of notification (info, success, warning, error)
        """
        toast = ToastNotification(message, self.parent, duration)
        
        # Customize appearance based on type
        if notification_type == "success":
            toast.setStyleSheet("""
                QLabel {
                    background-color: rgba(40, 120, 40, 220);
                    color: white;
                    border-radius: 8px;
                    padding: 12px 20px;
                    font-size: 13px;
                }
            """)
        elif notification_type == "warning":
            toast.setStyleSheet("""
                QLabel {
                    background-color: rgba(200, 140, 20, 220);
                    color: white;
                    border-radius: 8px;
                    padding: 12px 20px;
                    font-size: 13px;
                }
            """)
        elif notification_type == "error":
            toast.setStyleSheet("""
                QLabel {
                    background-color: rgba(180, 40, 40, 220);
                    color: white;
                    border-radius: 8px;
                    padding: 12px 20px;
                    font-size: 13px;
                }
            """)
        
        # Stack notifications if multiple are active
        self._reposition_notifications(toast)
        
        self.active_notifications.append(toast)
        toast.fade_out.finished.connect(
            lambda: self._remove_notification(toast)
        )
        
        toast.show_notification()
    
    def _reposition_notifications(self, new_toast: ToastNotification):
        """Reposition existing notifications to make room for new one.
        
        Args:
            new_toast: New notification to be shown
        """
        if not self.active_notifications:
            return
        
        # Move existing notifications down (stacking downward from top-right)
        spacing = 10
        offset = new_toast.height() + spacing
        
        for notification in self.active_notifications:
            current_pos = notification.pos()
            notification.move(current_pos.x(), current_pos.y() + offset)
    
    def _remove_notification(self, toast: ToastNotification):
        """Remove notification from active list.
        
        Args:
            toast: Notification to remove
        """
        if toast in self.active_notifications:
            self.active_notifications.remove(toast)


class ProgressNotification(QLabel):
    """Progress notification with updating message.
    
    Displays long-running operation progress.
    """
    
    def __init__(self, initial_message: str, parent=None):
        """Initialize progress notification.
        
        Args:
            initial_message: Initial message to display
            parent: Parent widget
        """
        super().__init__(initial_message, parent)
        
        # Setup appearance
        self.setStyleSheet("""
            QLabel {
                background-color: rgba(50, 80, 140, 220);
                color: white;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 13px;
            }
        """)
        
        font = QFont()
        font.setPointSize(11)
        self.setFont(font)
        
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(True)
        self.setMaximumWidth(400)
        
        # Setup opacity effect
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)
        
        # Setup fade in
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(200)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.InQuad)
        
        self.adjustSize()
    
    def show_progress(self):
        """Show progress notification."""
        if self.parent():
            # Position at bottom center of parent
            parent_rect = self.parent().rect()
            x = (parent_rect.width() - self.width()) // 2
            y = parent_rect.height() - self.height() - 50
            self.move(x, y)
        
        self.show()
        self.raise_()
        self.fade_in.start()
    
    def update_message(self, message: str):
        """Update progress message.
        
        Args:
            message: New message to display
        """
        self.setText(message)
        self.adjustSize()
        
        # Reposition if needed
        if self.parent():
            parent_rect = self.parent().rect()
            x = (parent_rect.width() - self.width()) // 2
            self.move(x, self.y())
    
    def finish(self, final_message: Optional[str] = None, success: bool = True):
        """Finish progress and fade out.
        
        Args:
            final_message: Optional final message to display
            success: Whether operation was successful
        """
        if final_message:
            self.setText(final_message)
            self.adjustSize()
        
        # Change color based on success
        if success:
            self.setStyleSheet("""
                QLabel {
                    background-color: rgba(40, 120, 40, 220);
                    color: white;
                    border-radius: 8px;
                    padding: 12px 20px;
                    font-size: 13px;
                }
            """)
        else:
            self.setStyleSheet("""
                QLabel {
                    background-color: rgba(180, 40, 40, 220);
                    color: white;
                    border-radius: 8px;
                    padding: 12px 20px;
                    font-size: 13px;
                }
            """)
        
        # Fade out after delay
        fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        fade_out.setDuration(200)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.OutQuad)
        fade_out.finished.connect(self.deleteLater)
        
        QTimer.singleShot(2000, fade_out.start)
