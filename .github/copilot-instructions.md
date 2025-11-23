# DataManip - Copilot Instructions

**Be concise. No verbose summaries. Track changes in todo list only.**

## Project

PySide6 data manipulation app for experimental sciences.

**Run**: `uv run datamanip`
**Test**: `uv run pytest tests/unit/widgets/data_table/`
**Console**: Use only powershell commands and close terminal with `exit` command.

## MCP use

- Use Context7 for all code generation.
- Use pylance for code checking.
- Use MCP for file formatting, replacements, listings and renamings.

# Good coding practices to follow

- Use Model-View-Controller (MVC) pattern for data table widget.
- Follow PEP 8 style guidelines.
- Write clear, concise docstrings for classes and methods.
- Use type hints for function signatures.
- Avoid wrappers arround already existing code and prefere a new architecture if that brings more clarity, faster execution or better maintainability.
- Ensure proper signal-slot connections for UI interactions.
- Use Python 3.10+ features.
- When developing new structures or refactoring, create a specific unit test file to cover the new code and help to debug it.

# Never keep track of the development here 

- Use a SINGLE todo list in the project management tool instead.
- Use a SINGLE project structure file instead.
- Be concise and to the point in this file.
- Those two files should always be up to date and reflect the current state of the project.

# Project philosophy
- Prioritize code clarity and maintainability.
- Optimize for performance when possible without sacrificing readability.
- Ensure modularity and separation of concerns.
- Focus on user experience and responsiveness in the UI.