"""Message boxes and dialogs for DataManip application."""

from PySide6.QtWidgets import QMessageBox

from utils.lang import get_lang_manager


def about(parent):
    """Show about dialog."""
    lang = get_lang_manager()
    # Format description with proper line breaks
    description = lang.get('about.description').replace('\\n', '<br>')
    QMessageBox.about(
        parent,
        lang.get("about.title"),
        f"<h2>{lang.get('app.name')}</h2>"
        f"<p><b>{lang.get('about.version')} 0.1.0</b></p>"
        f"<p>{description}</p>",
    )


def show_info(parent, title, message):
    """Show an information message box."""
    QMessageBox.information(parent, title, message)


def show_warning(parent, title, message):
    """Show a warning message box."""
    QMessageBox.warning(parent, title, message)


def show_error(parent, title, message):
    """Show an error message box."""
    QMessageBox.critical(parent, title, message)


def show_question(parent, title, message):
    """
    Show a question message box with Yes/No buttons.
    Returns True if Yes is clicked, False otherwise.
    """
    reply = QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return reply == QMessageBox.StandardButton.Yes


def confirm_save(parent):
    """Show a save confirmation dialog."""
    reply = QMessageBox.question(
        parent,
        "Save Changes?",
        "Do you want to save your changes before closing?",
        QMessageBox.StandardButton.Save
        | QMessageBox.StandardButton.Discard
        | QMessageBox.StandardButton.Cancel,
        QMessageBox.StandardButton.Save,
    )
    return reply


def confirm_overwrite(parent, filename):
    """Show a file overwrite confirmation dialog."""
    return show_question(
        parent, "Overwrite File?", f"The file '{filename}' already exists. Overwrite?"
    )


def show_not_implemented(parent):
    """Show a 'not implemented yet' message."""
    show_info(parent, "Not Implemented", "This feature is not yet implemented.")


def show_file_saved(parent, filename):
    """Show a file saved success message."""
    show_info(parent, "File Saved", f"File '{filename}' has been saved successfully.")


def show_file_loaded(parent, filename):
    """Show a file loaded success message."""
    show_info(parent, "File Loaded", f"File '{filename}' has been loaded successfully.")