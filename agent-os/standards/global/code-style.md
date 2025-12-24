# Code Style

## Python idioms

- Prefer structural pattern matching `match`/`case` statements for complex conditionals
- Use `except*` for handling exception groups when appropriate
- Don't use `from __future__ import annotations` unless you have a string with a generic such as `BaseNode["Subject"]`
- Prefer `PurePath` and `Path` over `str` for file paths
- Try to avoid local imports, put them at module level unless it leads to circular imports