# Testing Standards

*ALWAYS* run pytest via the `uv` skill using the `Skill` tool: `Skill(skill="astral:uv", args="run pytest")`.

**Don't:**
- Run `uv run pytest` via Bash
- Run `python` or `pytest` directly
- Use `just test` command

## Test Structure

- **Write tests as functions, NOT classes** - Do not use `class TestFoo:` style. Write standalone `def test_foo():` functions.
- Place tests in `tests/` directory
- Use descriptive function names: `test_<functionality>_<scenario>`
- Organize test module names to match the module being tested
- Test both the happy path and edge cases
- Use `tests/conftest.py` and fixtures as appropriate (but only when useful)
- When you create fixtures, write tests for those fixtures

**Example - Correct:**
```python
def test_user_can_login_with_valid_credentials() -> None:
    """Test successful login."""
    ...

def test_user_cannot_login_with_invalid_password() -> None:
    """Test login failure with wrong password."""
    ...
```

**Example - WRONG (do not do this):**
```python
class TestUserLogin:
    def test_valid_credentials(self) -> None:
        ...
    def test_invalid_password(self) -> None:
        ...
```

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