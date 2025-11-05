"""Menu bar for DataManip application."""

from PySide6.QtWidgets import QMenuBar
from PySide6.QtGui import QAction, QKeySequence

import ui.message_boxes as mb
from ui.AboutWindow import show_about_dialog
from ui.PreferenceWindow import show_preference_window
from utils.lang import tr

class MenuBar:
    """Menu bar handler for the main window."""
    
    def __init__(self, main_window):
        """Initialize the menu bar with reference to main window."""
        self.main_window = main_window
        self.lang = main_window.lang
        self.menubar = main_window.menuBar()
        
    def create_menu_bar(self):
        """Create the complete application menu bar."""
        try:
            # File Menu
            file_menu = self.menubar.addMenu(tr("menu.file"))
            self._create_file_menu(file_menu)

            # Edit Menu
            edit_menu = self.menubar.addMenu(tr("menu.edit"))
            self._create_edit_menu(edit_menu)

            # Help Menu
            help_menu = self.menubar.addMenu(tr("menu.help"))
            self._create_help_menu(help_menu)

            # Create status bar
            self.main_window.statusBar().showMessage(tr("status.ready"))
            
        except Exception:
            # Continue with minimal UI if menu creation fails
            pass
    
    def _create_file_menu(self, file_menu):
        """Create file menu actions."""
        # New action
        new_action = QAction(tr("file.new"), self.main_window)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.setStatusTip(tr("file.new_tip"))
        new_action.triggered.connect(self.main_window.new_file)
        file_menu.addAction(new_action)

        # Open action
        open_action = QAction(tr("file.open"), self.main_window)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.setStatusTip(tr("file.open_tip"))
        open_action.triggered.connect(self.main_window.open_file)
        file_menu.addAction(open_action)

        # Save action
        save_action = QAction(tr("file.save"), self.main_window)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.setStatusTip(tr("file.save_tip"))
        save_action.triggered.connect(self.main_window.save_file)
        file_menu.addAction(save_action)

        # Save As action
        save_as_action = QAction(tr("file.save_as"), self.main_window)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.setStatusTip(tr("file.save_as_tip"))
        save_as_action.triggered.connect(self.main_window.save_as_file)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction(tr("file.exit"), self.main_window)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setStatusTip(tr("file.exit_tip"))
        exit_action.triggered.connect(self.main_window.close)
        file_menu.addAction(exit_action)
    
    def _create_edit_menu(self, edit_menu):
        """Create edit menu actions."""
        # Undo action
        undo_action = QAction(tr("edit.undo"), self.main_window)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.setStatusTip(tr("edit.undo_tip"))
        undo_action.triggered.connect(self.main_window.undo)
        edit_menu.addAction(undo_action)

        # Redo action
        redo_action = QAction(tr("edit.redo"), self.main_window)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.setStatusTip(tr("edit.redo_tip"))
        redo_action.triggered.connect(self.main_window.redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        # Cut action
        cut_action = QAction(tr("edit.cut"), self.main_window)
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        cut_action.setStatusTip(tr("edit.cut_tip"))
        cut_action.triggered.connect(self.main_window.cut)
        edit_menu.addAction(cut_action)

        # Copy action
        copy_action = QAction(tr("edit.copy"), self.main_window)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.setStatusTip(tr("edit.copy_tip"))
        copy_action.triggered.connect(self.main_window.copy)
        edit_menu.addAction(copy_action)

        # Paste action
        paste_action = QAction(tr("edit.paste"), self.main_window)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.setStatusTip(tr("edit.paste_tip"))
        paste_action.triggered.connect(self.main_window.paste)
        edit_menu.addAction(paste_action)

        edit_menu.addSeparator()

        # Preferences action
        preferences_action = QAction(tr("edit.preferences"), self.main_window)
        preferences_action.setShortcut(QKeySequence.StandardKey.Preferences)
        preferences_action.setStatusTip(tr("edit.preferences_tip"))
        preferences_action.triggered.connect(self.main_window.show_preferences)
        edit_menu.addAction(preferences_action)
    
    
    def _create_help_menu(self, help_menu):
        """Create help menu actions."""
        # Documentation action
        documentation_action = QAction(tr("help.documentation"), self.main_window)
        documentation_action.setShortcut(QKeySequence.StandardKey.HelpContents)
        documentation_action.setStatusTip(tr("help.documentation_tip"))
        documentation_action.triggered.connect(self.main_window.documentation)
        help_menu.addAction(documentation_action)

        help_menu.addSeparator()

        # About action
        about_action = QAction(tr("help.about"), self.main_window)
        about_action.setStatusTip(tr("help.about_tip"))
        about_action.triggered.connect(lambda: show_about_dialog(self.main_window))
        help_menu.addAction(about_action)