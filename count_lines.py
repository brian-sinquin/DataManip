import pathlib

files = list(pathlib.Path('src').rglob('*.py'))
print(f"Found {len(files)} Python files")

total = sum(len(f.read_text(encoding='utf-8').splitlines()) for f in files)
print(f'\nTotal files: {len(files)}')
print(f'Total lines: {total}')
print(f'Avg lines/file: {total//len(files) if files else 0}')

print('\n10 Largest files:')
files_sorted = sorted([(f, len(f.read_text(encoding='utf-8').splitlines())) for f in files], 
                      key=lambda x: x[1], reverse=True)[:10]
for f, lines in files_sorted:
    print(f'{lines:5} {f.relative_to("src")}')
