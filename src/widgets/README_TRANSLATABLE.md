# Translatable Widget System

This system allows widgets to update their UI text when the language changes, while **preserving all data**.

## Simple Widgets (Labels, Buttons)

For simple text-only widgets, use the pre-made translatable classes:

```python
from widgets.translatable import TranslatableLabel, TranslatableButton

# Create a label that auto-translates
self.title_label = TranslatableLabel("welcome.title")
self.translatable_widgets.append(self.title_label)

# Create a button that auto-translates
self.ok_button = TranslatableButton("common.ok")
self.translatable_widgets.append(self.ok_button)
```

## Complex Widgets (Tables, Forms with Data)

For widgets that contain data (like tables, forms, etc.), use `TranslatableMixin`:

```python
from widgets.translatable import TranslatableMixin

class MyDataWidget(QWidget, TranslatableMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        TranslatableMixin.__init__(self)
        
        # Create UI elements
        self.title_label = QLabel()
        self.table = QTableWidget()
        
        # Register translatable elements
        self.register_translatable(self.title_label, "my_widget.title", "text")
        
        # Initial translation
        self.refresh_translations()
    
    def refresh_translations(self):
        """Override to update all translatable elements."""
        super().refresh_translations()  # Updates registered elements
        
        # Update table headers manually
        lang = get_lang_manager()
        headers = [lang.get("table.col1"), lang.get("table.col2")]
        self.table.setHorizontalHeaderLabels(headers)
    
    def add_data(self, data):
        """Add data - this will NOT be lost when language changes!"""
        # Your data logic here
        pass
```

## How It Works

1. **Widget Creation**: Use `TranslatableLabel` or inherit from `TranslatableMixin`
2. **Registration**: Add widgets to `self.translatable_widgets` list in MainWindow
3. **Language Change**: When user changes language, `refresh_ui()` calls `refresh_text()` on all registered widgets
4. **Data Preservation**: Only UI text is updated, all data (table contents, form values, etc.) is preserved!

## Example

See `widgets/data_table_example.py` for a complete working example of a table that:
- Has translatable title and column headers
- Preserves all table data when language changes
- Only updates the UI text

## Benefits

- ✅ Data is never lost when changing language
- ✅ Simple to use for basic widgets
- ✅ Flexible for complex widgets
- ✅ Scalable - add as many translatable widgets as needed
- ✅ No manual refresh code needed for each widget
