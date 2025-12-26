# Testing Standards

*ALWAYS* run pytest via `just test` (or `uv run pytest`). Don't run `python` or `pytest` directly.

## Test Structure

- Place tests in `tests/` directory
- Use descriptive function names: `test_<functionality>_<scenario>`
- Organize test module names to match the module being tested
- Test both the happy path and edge cases
- Use `tests/conftest.py` and fixtures as appropriate (but only when useful)
- When you create fixtures, write tests for those fixtures

## Coverage

- Don't write too many tests
- Try hard to consolidate tests
- But try to keep coverage at 100% as part of final verification
- Prefer unit tests but where needed write

Use this in `pyproject.toml` for pytest options:

```ini
[tool.pytest.ini_options]
testpaths = ["tests", "src", "docs"]
python_files = ["test_*.py"]
addopts = "-p no:doctest -p no:freethreaded -m \"not slow\""
pythonpath = ["examples"]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
]
# Free-threading safety: timeout tests to detect hangs/deadlocks
timeout = 60
faulthandler_timeout = 120
```