"""Main window UI for DataManip application."""

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence

from . import message_boxes as mb
from .language_dialog import LanguageDialog
from utils.lang import get_lang_manager
from widgets.translatable import TranslatableLabel

class MainWindow(QMainWindow):
    """
    Main application window for DataManip.
    
    Language System:
    ----------------
    This window uses a translatable widget system that preserves data when language changes.
    
    For simple labels/buttons:
        - Use TranslatableLabel("json.key") or TranslatableButton("json.key")
        - Add them to self.translatable_widgets list
        - They will auto-refresh when language changes
    
    For complex widgets with data (tables, forms, etc.):
        - Inherit from TranslatableMixin
        - Register translatable elements with register_translatable()
        - Override refresh_translations() to update headers/labels
        - The actual data in the widget is PRESERVED across language changes
    
    See widgets/data_table_example.py for a complete example.
    """

    def __init__(self):
        super().__init__()
        
        # Get language manager
        self.lang = get_lang_manager()
        
        # Registry of translatable widgets
        # Add any TranslatableLabel, TranslatableButton, or custom translatable widgets here
        self.translatable_widgets = []
        
        self.setWindowTitle(self.lang.get("app.title"))
        self.setMinimumSize(1000, 700)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Add welcome label using TranslatableLabel
        self.welcome_label = TranslatableLabel("welcome.title")
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        layout.addWidget(self.welcome_label)
        self.translatable_widgets.append(self.welcome_label)

        # Add description label using TranslatableLabel
        self.description_label = TranslatableLabel("welcome.description")
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.description_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.description_label)
        self.translatable_widgets.append(self.description_label)

        # Add stretch to center content
        layout.addStretch()

        # Create menu bar
        self._create_menu_bar()

    def _create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu(self.lang.get("menu.file"))

        # New action
        new_action = QAction(self.lang.get("file.new"), self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.setStatusTip(self.lang.get("file.new_tip"))
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        # Open action
        open_action = QAction(self.lang.get("file.open"), self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.setStatusTip(self.lang.get("file.open_tip"))
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        # Save action
        save_action = QAction(self.lang.get("file.save"), self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.setStatusTip(self.lang.get("file.save_tip"))
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        # Save As action
        save_as_action = QAction(self.lang.get("file.save_as"), self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.setStatusTip(self.lang.get("file.save_as_tip"))
        save_as_action.triggered.connect(self.save_as_file)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction(self.lang.get("file.exit"), self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setStatusTip(self.lang.get("file.exit_tip"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit Menu
        edit_menu = menubar.addMenu(self.lang.get("menu.edit"))

        # Undo action
        undo_action = QAction(self.lang.get("edit.undo"), self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.setStatusTip(self.lang.get("edit.undo_tip"))
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)

        # Redo action
        redo_action = QAction(self.lang.get("edit.redo"), self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.setStatusTip(self.lang.get("edit.redo_tip"))
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        # Cut action
        cut_action = QAction(self.lang.get("edit.cut"), self)
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        cut_action.setStatusTip(self.lang.get("edit.cut_tip"))
        cut_action.triggered.connect(self.cut)
        edit_menu.addAction(cut_action)

        # Copy action
        copy_action = QAction(self.lang.get("edit.copy"), self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.setStatusTip(self.lang.get("edit.copy_tip"))
        copy_action.triggered.connect(self.copy)
        edit_menu.addAction(copy_action)

        # Paste action
        paste_action = QAction(self.lang.get("edit.paste"), self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.setStatusTip(self.lang.get("edit.paste_tip"))
        paste_action.triggered.connect(self.paste)
        edit_menu.addAction(paste_action)

        edit_menu.addSeparator()

        # Language action
        language_action = QAction(self.lang.get("language.select_language", "Language..."), self)
        language_action.setStatusTip(self.lang.get("language.dialog_title", "Change application language"))
        language_action.triggered.connect(self.change_language)
        edit_menu.addAction(language_action)

        # Preferences action
        preferences_action = QAction(self.lang.get("edit.preferences"), self)
        preferences_action.setShortcut(QKeySequence.StandardKey.Preferences)
        preferences_action.setStatusTip(self.lang.get("edit.preferences_tip"))
        preferences_action.triggered.connect(self.preferences)
        edit_menu.addAction(preferences_action)

        # View Menu
        view_menu = menubar.addMenu(self.lang.get("menu.view"))

        # Zoom In action
        zoom_in_action = QAction(self.lang.get("view.zoom_in"), self)
        zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in_action.setStatusTip(self.lang.get("view.zoom_in_tip"))
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)

        # Zoom Out action
        zoom_out_action = QAction(self.lang.get("view.zoom_out"), self)
        zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out_action.setStatusTip(self.lang.get("view.zoom_out_tip"))
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)

        # Reset Zoom action
        reset_zoom_action = QAction(self.lang.get("view.reset_zoom"), self)
        reset_zoom_action.setShortcut("Ctrl+0")
        reset_zoom_action.setStatusTip(self.lang.get("view.reset_zoom_tip"))
        reset_zoom_action.triggered.connect(self.reset_zoom)
        view_menu.addAction(reset_zoom_action)

        # Tools Menu
        tools_menu = menubar.addMenu(self.lang.get("menu.tools"))

        # Data Analysis action
        data_analysis_action = QAction(self.lang.get("tools.data_analysis"), self)
        data_analysis_action.setStatusTip(self.lang.get("tools.data_analysis_tip"))
        data_analysis_action.triggered.connect(self.data_analysis)
        tools_menu.addAction(data_analysis_action)

        # Visualization action
        visualization_action = QAction(self.lang.get("tools.visualization"), self)
        visualization_action.setStatusTip(self.lang.get("tools.visualization_tip"))
        visualization_action.triggered.connect(self.visualization)
        tools_menu.addAction(visualization_action)

        # Help Menu
        help_menu = menubar.addMenu(self.lang.get("menu.help"))

        # Documentation action
        documentation_action = QAction(self.lang.get("help.documentation"), self)
        documentation_action.setShortcut(QKeySequence.StandardKey.HelpContents)
        documentation_action.setStatusTip(self.lang.get("help.documentation_tip"))
        documentation_action.triggered.connect(self.documentation)
        help_menu.addAction(documentation_action)

        help_menu.addSeparator()

        # About action
        about_action = QAction(self.lang.get("help.about"), self)
        about_action.setStatusTip(self.lang.get("help.about_tip"))
        about_action.triggered.connect(lambda: mb.about(self))
        help_menu.addAction(about_action)

        # Create status bar
        self.statusBar().showMessage(self.lang.get("status.ready"))

    # File Menu Actions
    def new_file(self):
        """Create a new file."""
        self.statusBar().showMessage(self.lang.get("status.new_file"), 2000)

    def open_file(self):
        """Open an existing file."""
        self.statusBar().showMessage(self.lang.get("status.open_file"), 2000)

    def save_file(self):
        """Save the current file."""
        self.statusBar().showMessage(self.lang.get("status.file_saved"), 2000)

    def save_as_file(self):
        """Save the file with a new name."""
        self.statusBar().showMessage(self.lang.get("status.save_as"), 2000)

    # Edit Menu Actions
    def undo(self):
        """Undo the last action."""
        self.statusBar().showMessage(self.lang.get("status.undo"), 2000)

    def redo(self):
        """Redo the last undone action."""
        self.statusBar().showMessage(self.lang.get("status.redo"), 2000)

    def cut(self):
        """Cut the selection."""
        self.statusBar().showMessage(self.lang.get("status.cut"), 2000)

    def copy(self):
        """Copy the selection."""
        self.statusBar().showMessage(self.lang.get("status.copy"), 2000)

    def paste(self):
        """Paste from clipboard."""
        self.statusBar().showMessage(self.lang.get("status.paste"), 2000)

    def change_language(self):
        """Open language selection dialog."""
        dialog = LanguageDialog(self)
        if dialog.exec():
            # Language was changed, refresh the UI
            self.refresh_ui()
            self.statusBar().showMessage(
                self.lang.get("status.preferences", "Language changed"), 
                3000
            )
    
    def refresh_ui(self):
        """Refresh all UI elements with current language."""
        # Update window title
        self.setWindowTitle(self.lang.get("app.title"))
        
        # Clear and recreate menu bar (menus need to be recreated)
        self.menuBar().clear()
        self._create_menu_bar()
        
        # Refresh all translatable widgets (this preserves their data!)
        for widget in self.translatable_widgets:
            if hasattr(widget, 'refresh_text'):
                widget.refresh_text()
        
        # Update status bar
        self.statusBar().showMessage(self.lang.get("status.ready"))

    def preferences(self):
        """Open preferences dialog."""
        self.statusBar().showMessage(self.lang.get("status.preferences"), 2000)

    # View Menu Actions
    def zoom_in(self):
        """Zoom in."""
        self.statusBar().showMessage(self.lang.get("status.zoom_in"), 2000)

    def zoom_out(self):
        """Zoom out."""
        self.statusBar().showMessage(self.lang.get("status.zoom_out"), 2000)

    def reset_zoom(self):
        """Reset zoom to default."""
        self.statusBar().showMessage(self.lang.get("status.reset_zoom"), 2000)

    # Tools Menu Actions
    def data_analysis(self):
        """Open data analysis tools."""
        self.statusBar().showMessage(self.lang.get("status.data_analysis"), 2000)

    def visualization(self):
        """Open visualization tools."""
        self.statusBar().showMessage(self.lang.get("status.visualization"), 2000)

    # Help Menu Actions
    def documentation(self):
        """View documentation."""
        self.statusBar().showMessage(self.lang.get("status.documentation"), 2000)

