#!/usr/bin/env python
"""Fix escaped quotes in data_table_widget.py"""

file_path = r"c:\Users\brian\Documents\GitHub\DataManip\src\ui\widgets\data_table_widget.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace escaped quotes
content = content.replace(r'\"', '"')
content = content.replace(r"\'", "'")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed escaped quotes")
