"""Update all imports to use new snake_case package names."""
import re
from pathlib import Path

# Define replacements
replacements = [
    (r'from widgets\.DataTable', 'from widgets.data_table'),
    (r'from src\.widgets\.DataTable', 'from src.widgets.data_table'),
    (r'import widgets\.DataTable', 'import widgets.data_table'),
    (r'from \.DataTable', 'from .data_table'),
    
    (r'from widgets\.AdvancedDataTablePlotWidget', 'from widgets.plot_widget'),
    (r'widgets\.AdvancedDataTablePlotWidget', 'widgets.plot_widget'),
    
    (r'from widgets\.AdvancedDataTableStatisticsWidget', 'from widgets.statistics_widget'),
    (r'widgets\.AdvancedDataTableStatisticsWidget', 'widgets.statistics_widget'),
    
    (r'from ui\.MainWindow', 'from ui.main_window'),
    (r'ui\.MainWindow', 'ui.main_window'),
    
    (r'from ui\.AboutWindow', 'from ui.about_window'),
    (r'ui\.AboutWindow', 'ui.about_window'),
    
    (r'from ui\.PreferenceWindow', 'from ui.preference_window'),
    (r'ui\.PreferenceWindow', 'ui.preference_window'),
]

def update_file(file_path: Path):
    """Update imports in a single file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        changed = False
        for pattern, replacement in replacements:
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                content = new_content
                changed = True
                print(f"  - Applied: {pattern} -> {replacement}")
        
        if changed:
            file_path.write_text(content, encoding='utf-8')
            print(f"[OK] Updated {file_path}")
            return True
        return False
    except Exception as e:
        print(f"[ERROR] updating {file_path}: {e}")
        return False

def main():
    """Update all Python files in src/ and tests/."""
    root = Path('.')
    updated_count = 0
    
    # Update all Python files
    for py_file in root.rglob('*.py'):
        # Skip __pycache__ and virtual environments
        if '__pycache__' in str(py_file) or '.venv' in str(py_file):
            continue
        
        if update_file(py_file):
            updated_count += 1
    
    # Also update markdown files
    for md_file in root.rglob('*.md'):
        if update_file(md_file):
            updated_count += 1
    
    print(f"\n[OK] Updated {updated_count} files")

if __name__ == '__main__':
    main()
