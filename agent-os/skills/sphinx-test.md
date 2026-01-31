---
description:
  Sphinx integration test standards using sphinx.testing.fixtures. Use this
  when writing Sphinx integration tests or testing Sphinx extensions.
---

# Sphinx Integration Test Standards

Use Sphinx's built-in testing fixtures (`sphinx.testing.fixtures`) for integration tests.

**Important**: Uses Sphinx's built-in `sphinx.testing.fixtures`, NOT the third-party `pytest-sphinx` package.

## Setup

### conftest.py Configuration

```python
# Load both Sphinx's testing fixtures and project fixtures
pytest_plugins = ["sphinx.testing.fixtures", "svcs_sphinx.fixtures"]
```

### Test Roots Structure

- Test roots stored in `tests/roots/` directory
- Each test root is a minimal Sphinx project: `test-<name>/`
- Minimum required: `conf.py` and `index.rst`
- Examples: `test-basic-no-extension`, `test-basic-with-extension`

## Naming Convention

**CRITICAL**: Test function names MUST match their testroot names for maintainability.

### Pattern

- testroot directory: `tests/roots/test-<name>/`
- test function: `def test_<name>():`

### Examples

```python
# testroot="basic-no-extension" -> test_basic_no_extension()
@pytest.mark.sphinx("html", testroot="basic-no-extension")
def test_basic_no_extension(page, html_page):
    """Test without the extension."""
    ...

# testroot="basic-with-extension" -> test_basic_with_extension()
@pytest.mark.sphinx("html", testroot="basic-with-extension")
def test_basic_with_extension(app):
    """Test with the extension."""
    ...
```

## Test Structure

### Using @pytest.mark.sphinx Decorator

```python
@pytest.mark.sphinx("html", testroot="basic-no-extension")
@pytest.mark.parametrize(
    "page",
    ["index.html"],
    indirect=True,
)
def test_basic_no_extension(page: str, html_page: Element, sphinx_warnings: dict):
    """Test description."""
    # Verify page content
    assert "expected content" in page

    # Use aria-testing for semantic queries
    heading = get_by_tag_name(html_page, "h1")
    assert "Expected Title" in get_text_content(heading)

    # Check warnings
    assert not sphinx_warnings["lines"], "No warnings expected"
```

### Common Fixtures

From `sphinx.testing.fixtures`:
- `app` - Sphinx application instance
- `status` - Build status output (StringIO)
- `warning` - Build warning output (StringIO)
- `rootdir` - Path to test roots directory

## Test Root Structure

Minimum test root structure:

```
tests/roots/test-basic-no-extension/
├── conf.py          # Sphinx configuration
└── index.rst        # Main document
```

Example `conf.py`:

```python
# Minimal configuration
project = "Test Project"
extensions = []  # Or ["your_extension"]
html_theme = "basic"
```

Example `index.rst`:

```rst
Test Project
============

This is basic content for testing.
```

## HTML Testing with tdom and aria-testing

Use semantic queries instead of CSS selectors:

```python
from aria_testing import get_by_tag_name, get_by_role
from aria_testing.utils import get_text_content
from tdom import Element

def test_with_aria_testing(html_page: Element):
    # Query by tag name
    heading = get_by_tag_name(html_page, "h1")
    assert "Expected Title" in get_text_content(heading)

    # Query by ARIA role
    button = get_by_role(html_page, "button", name="Submit")
    assert button is not None
```

## Best Practices

**DO**:
- Match test function names to testroot names
- Use `@pytest.mark.sphinx` decorator for integration tests
- Use `page` fixture with `indirect=True` for HTML content testing
- Use `app` fixture directly when you need to inspect Sphinx internal state
- Use aria-testing for semantic HTML queries
- Filter "already registered" warnings (test pollution from running multiple tests)

**DON'T**:
- Use pytest-sphinx (third-party package) - use `sphinx.testing.fixtures` instead
- Forget `indirect=True` when using `page` fixture with parametrize
- Mix up test names and testroot names
- Test HTML structure with raw string matching when aria-testing is available
- Assume `app.env.temp_data` persists after `app.build()` completes

## Common Pitfalls

### Fixture Scope Issues

The `rootdir` fixture **MUST be function-scoped**, not session-scoped, to prevent app reuse:

```python
# CORRECT: Function scope (default)
@pytest.fixture
def rootdir():
    return Path(__file__).parent / "roots"

# WRONG: Session scope causes app reuse
@pytest.fixture(scope="session")  # Don't do this
def rootdir():
    return Path(__file__).parent / "roots"
```

### Page Fixture Timing

The `page` fixture triggers `app.build()`, which clears `temp_data`. If you need to inspect `temp_data`, use the `app` fixture directly and connect to events:

```python
# Use app fixture + event hook, not page fixture
@pytest.mark.sphinx("html", testroot="test")
def test_temp_data(app):  # Use app, not page
    def capture(app, *args):
        # Inspect temp_data during build
        data = app.env.temp_data["your_key"]

    app.connect("html-page-context", capture)
    app.build()
```

### Warning Pollution Between Tests

When tests run in sequence, Sphinx global registries can cause "already registered" warnings:

```python
# Filter out benign warnings
actual_warnings = [
    line for line in sphinx_warnings["lines"]
    if "already registered" not in line
]
assert not actual_warnings
```

## Further Reading

- [Sphinx Testing Documentation](https://www.sphinx-doc.org/en/master/development/tutorials/testing.html)
