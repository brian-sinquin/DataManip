"""Message boxes and dialogs for DataManip application."""

import logging
from typing import Optional, List, Tuple
from PySide6.QtWidgets import (
    QMessageBox, QInputDialog, QProgressDialog, QErrorMessage,
    QDialogButtonBox, QDialog, QVBoxLayout, QLabel, QTextEdit
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QIcon

from utils.lang import get_lang_manager, tr

# Set up logging
logger = logging.getLogger(__name__)


class DetailedErrorDialog(QDialog):
    """Custom dialog for showing detailed error information."""
    
    def __init__(self, parent=None, title="Error", message="", details=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(400, 300)
        self.setMaximumSize(800, 600)
        
        layout = QVBoxLayout()
        
        # Main message
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)
        
        # Details (collapsible)
        if details:
            details_label = QLabel("Details:")
            details_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            layout.addWidget(details_label)
            
            details_text = QTextEdit()
            details_text.setPlainText(details)
            details_text.setReadOnly(True)
            details_text.setMaximumHeight(200)
            layout.addWidget(details_text)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
        
        self.setLayout(layout)


def about(parent):
    """Show about dialog."""
    try:
        lang = get_lang_manager()
        # Format description with proper line breaks
        description = tr('about.description').replace('\\n', '<br>')
        QMessageBox.about(
            parent,
            tr("about.title"),
            f"<h2>{tr('app.name')}</h2>"
            f"<p><b>{tr('about.version')} 0.1.0</b></p>"
            f"<p>{description}</p>",
        )
        logger.info("About dialog shown successfully")
    except Exception as e:
        logger.error(f"Error showing about dialog: {e}")
        show_error(parent, "Error", f"Failed to show about dialog: {str(e)}")


def show_info(parent, title: str, message: str, details: Optional[str] = None):
    """
    Show an information message box.
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Main message
        details: Optional detailed information
    """
    try:
        if details:
            dialog = DetailedErrorDialog(parent, title, message, details)
            dialog.exec()
        else:
            QMessageBox.information(parent, title, message)
        logger.debug(f"Info dialog shown: {title}")
    except Exception as e:
        logger.error(f"Error showing info dialog: {e}")


def show_warning(parent, title: str, message: str, details: Optional[str] = None):
    """
    Show a warning message box.
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Main message
        details: Optional detailed information
    """
    try:
        if details:
            dialog = DetailedErrorDialog(parent, title, message, details)
            dialog.exec()
        else:
            QMessageBox.warning(parent, title, message)
        logger.warning(f"Warning dialog shown: {title} - {message}")
    except Exception as e:
        logger.error(f"Error showing warning dialog: {e}")


def show_error(parent, title: str, message: str, details: Optional[str] = None):
    """
    Show an error message box.
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Main message
        details: Optional detailed information
    """
    try:
        if details:
            dialog = DetailedErrorDialog(parent, title, message, details)
            dialog.exec()
        else:
            QMessageBox.critical(parent, title, message)
        logger.error(f"Error dialog shown: {title} - {message}")
    except Exception as e:
        logger.critical(f"Critical error showing error dialog: {e}")


def show_question(parent, title: str, message: str, 
                 default_yes: bool = False) -> bool:
    """
    Show a question message box with Yes/No buttons.
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Main message
        default_yes: Whether Yes should be the default button
        
    Returns:
        True if Yes is clicked, False otherwise
    """
    try:
        default_button = (QMessageBox.StandardButton.Yes if default_yes 
                         else QMessageBox.StandardButton.No)
        
        reply = QMessageBox.question(
            parent,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            default_button,
        )
        result = reply == QMessageBox.StandardButton.Yes
        logger.debug(f"Question dialog result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error showing question dialog: {e}")
        return False


def show_custom_question(parent, title: str, message: str, 
                        buttons: List[str], default_button: int = 0) -> int:
    """
    Show a custom question dialog with custom buttons.
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Main message
        buttons: List of button texts
        default_button: Index of default button
        
    Returns:
        Index of clicked button, -1 if dialog was closed
    """
    try:
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Question)
        
        # Add custom buttons
        custom_buttons = []
        for i, button_text in enumerate(buttons):
            btn = msg_box.addButton(button_text, QMessageBox.ButtonRole.ActionRole)
            custom_buttons.append(btn)
            if i == default_button:
                msg_box.setDefaultButton(btn)
        
        result = msg_box.exec()
        
        # Find which button was clicked
        clicked_button = msg_box.clickedButton()
        if clicked_button in custom_buttons:
            return custom_buttons.index(clicked_button)
        return -1
    except Exception as e:
        logger.error(f"Error showing custom question dialog: {e}")
        return -1


def get_text_input(parent, title: str, label: str, 
                  default_text: str = "") -> Tuple[str, bool]:
    """
    Show an input dialog for text input.
    
    Args:
        parent: Parent widget
        title: Dialog title
        label: Input label
        default_text: Default text in input field
        
    Returns:
        Tuple of (entered_text, ok_pressed)
    """
    try:
        text, ok = QInputDialog.getText(parent, title, label, text=default_text)
        logger.debug(f"Text input dialog result: ok={ok}")
        return text, ok
    except Exception as e:
        logger.error(f"Error showing text input dialog: {e}")
        return "", False


def get_item_input(parent, title: str, label: str, 
                  items: List[str], current: int = 0) -> Tuple[str, bool]:
    """
    Show an input dialog for item selection.
    
    Args:
        parent: Parent widget
        title: Dialog title
        label: Selection label
        items: List of items to choose from
        current: Index of current/default item
        
    Returns:
        Tuple of (selected_item, ok_pressed)
    """
    try:
        item, ok = QInputDialog.getItem(parent, title, label, items, current)
        logger.debug(f"Item input dialog result: ok={ok}")
        return item, ok
    except Exception as e:
        logger.error(f"Error showing item input dialog: {e}")
        return "", False


def show_progress_dialog(parent, title: str, label: str, 
                        maximum: int = 100) -> Optional[QProgressDialog]:
    """
    Create and show a progress dialog.
    
    Args:
        parent: Parent widget
        title: Dialog title
        label: Progress label
        maximum: Maximum progress value
        
    Returns:
        QProgressDialog instance or None if creation failed
    """
    try:
        progress = QProgressDialog(label, "Cancel", 0, maximum, parent)
        progress.setWindowTitle(title)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()
        logger.debug(f"Progress dialog created: {title}")
        return progress
    except Exception as e:
        logger.error(f"Error creating progress dialog: {e}")
        return None


def confirm_save(parent):
    """Show a save confirmation dialog."""
    try:
        lang = get_lang_manager()
        reply = QMessageBox.question(
            parent,
            tr("dialogs.save_changes"),
            tr("dialogs.save_changes_message"),
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        logger.debug(f"Save confirmation result: {reply}")
        return reply
    except Exception as e:
        logger.error(f"Error showing save confirmation: {e}")
        return QMessageBox.StandardButton.Cancel


def confirm_overwrite(parent, filename: str) -> bool:
    """Show a file overwrite confirmation dialog."""
    try:
        lang = get_lang_manager()
        return show_question(
            parent, 
            tr("dialogs.overwrite_file"), 
            tr("dialogs.overwrite_message")
        )
    except Exception as e:
        logger.error(f"Error showing overwrite confirmation: {e}")
        return False


def confirm_delete(parent, item_name: str) -> bool:
    """Show a delete confirmation dialog."""
    try:
        lang = get_lang_manager()
        return show_question(
            parent,
            tr("dialogs.confirm_delete"),
            tr("dialogs.delete_message")
        )
    except Exception as e:
        logger.error(f"Error showing delete confirmation: {e}")
        return False


def show_not_implemented(parent):
    """Show a 'not implemented yet' message."""
    try:
        lang = get_lang_manager()
        show_info(
            parent, 
            tr("dialogs.not_implemented"), 
            tr("dialogs.not_implemented_message")
        )
    except Exception as e:
        logger.error(f"Error showing not implemented dialog: {e}")


def show_file_saved(parent, filename: str):
    """Show a file saved success message."""
    try:
        lang = get_lang_manager()
        show_info(
            parent, 
            tr("dialogs.file_saved"), 
            tr("dialogs.file_saved_message")
        )
    except Exception as e:
        logger.error(f"Error showing file saved dialog: {e}")


def show_file_loaded(parent, filename: str):
    """Show a file loaded success message."""
    try:
        lang = get_lang_manager()
        show_info(
            parent, 
            tr("dialogs.file_loaded"), 
            tr("dialogs.file_loaded_message")
        )
    except Exception as e:
        logger.error(f"Error showing file loaded dialog: {e}")


def show_auto_hide_message(parent, title: str, message: str, timeout_ms: int = 3000):
    """
    Show a message that automatically hides after a timeout.
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Message to show
        timeout_ms: Timeout in milliseconds
    """
    try:
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.setDefaultButton(QMessageBox.StandardButton.Ok)
        
        # Auto-close after timeout
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(msg_box.accept)
        timer.start(timeout_ms)
        
        msg_box.exec()
        timer.stop()
        
        logger.debug(f"Auto-hide message shown: {title}")
    except Exception as e:
        logger.error(f"Error showing auto-hide message: {e}")


def show_detailed_error(parent, title: str, message: str, 
                       details: str, icon_path: Optional[str] = None):
    """
    Show a detailed error dialog with expandable details.
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Main error message
        details: Detailed error information
        icon_path: Optional path to custom icon
    """
    try:
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setDetailedText(details)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        
        if icon_path:
            icon = QIcon(icon_path)
            if not icon.isNull():
                msg_box.setWindowIcon(icon)
        
        msg_box.exec()
        logger.error(f"Detailed error dialog shown: {title}")
    except Exception as e:
        logger.critical(f"Critical error showing detailed error dialog: {e}")


# Convenience functions for common dialog patterns
def ask_yes_no(parent, title: str, message: str) -> bool:
    """Simple yes/no question."""
    return show_question(parent, title, message)


def ask_ok_cancel(parent, title: str, message: str) -> bool:
    """Show OK/Cancel dialog."""
    try:
        reply = QMessageBox.question(
            parent, title, message,
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Ok
        )
        return reply == QMessageBox.StandardButton.Ok
    except Exception as e:
        logger.error(f"Error showing OK/Cancel dialog: {e}")
        return False


def notify_success(parent, message: str):
    """Show a success notification."""
    try:
        lang = get_lang_manager()
        show_info(parent, tr("dialogs.success"), message)
    except Exception as e:
        logger.error(f"Error showing success notification: {e}")


def notify_error(parent, message: str, details: Optional[str] = None):
    """Show an error notification."""
    try:
        lang = get_lang_manager()
        show_error(parent, tr("dialogs.error"), message, details)
    except Exception as e:
        logger.critical(f"Critical error showing error notification: {e}")