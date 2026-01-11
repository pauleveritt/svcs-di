---
title: Sphinx Integration Test Standards
description: Standards for writing Sphinx integration tests using sphinx.testing.fixtures with test roots, HTML verification, and event hook patterns
version: 2.0.0
tags: [sphinx, testing, pytest, integration-tests, sphinx.testing.fixtures, test-roots, tdom, aria-testing]
applies_to: [tests/test_integration.py, tests/roots/*, tests/conftest.py]
references:
  - https://www.sphinx-doc.org/en/master/development/tutorials/testing.html
  - src/svcs_sphinx/fixtures.py
last_updated: 2025-12-28
---

# Sphinx Integration Test Standards

Use Sphinx's built-in testing fixtures (`sphinx.testing.fixtures`) for integration tests. This skill guides you when asked to "write a Sphinx test" or work with Sphinx integration testing.

**Important**: Uses Sphinx's built-in `sphinx.testing.fixtures`, NOT the third-party `pytest-sphinx` package.

## Setup

### conftest.py Configuration

```python
# Load both Sphinx's testing fixtures and project fixtures
pytest_plugins = ["sphinx.testing.fixtures", "svcs_sphinx.fixtures"]
```

The project provides reusable fixtures in `src/svcs_sphinx/fixtures.py` including:
- `rootdir()` - Returns path to `tests/roots/` directory (function-scoped)
- `page(request, app)` - Loads built HTML page content as string
- `html_page(page)` - Parses HTML using tdom for aria-testing queries
- `sphinx_warnings(warning)` - Dictionary with warning text and lines

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
# testroot="basic-no-extension" → test_basic_no_extension()
@pytest.mark.sphinx("html", testroot="basic-no-extension")
def test_basic_no_extension(page, html_page):
    """Test without the extension."""
    ...

# testroot="basic-with-extension" → test_basic_with_extension()
@pytest.mark.sphinx("html", testroot="basic-with-extension")
def test_basic_with_extension(app):
    """Test with the extension."""
    ...

# For additional tests on same testroot, add descriptive suffix
# testroot="basic-with-extension" → test_basic_with_extension_workflow()
@pytest.mark.sphinx("html", testroot="basic-with-extension")
def test_basic_with_extension_workflow(page, html_page):
    """Test workflow with the extension."""
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

From `svcs_sphinx.fixtures`:
- `page` - HTML content as string (requires `@pytest.mark.parametrize` with `indirect=True`)
- `html_page` - Parsed tdom Element for aria-testing queries
- `sphinx_warnings` - Dict with `"text"` (full warnings) and `"lines"` (list of warning lines)

## Testing Patterns

### Testing Without page Fixture (Direct app Access)

When you need to inspect Sphinx state during build (e.g., `app.env.temp_data`):

```python
@pytest.mark.sphinx("html", testroot="basic-with-extension")
def test_extension_registers_services(app):
    """Test that extension properly registers services."""
    captured_state = {}
    
    def capture_page_context(app, pagename, templatename, context, doctree):
        """Hook into page rendering to capture state."""
        # Verify state during build before cleanup
        assert "svcs_sphinx" in app.env.temp_data
        captured_state["verified"] = True
    
    # Connect custom handler
    app.connect("html-page-context", capture_page_context)
    
    # Manually build
    app.build()
    
    # Verify handler ran
    assert captured_state["verified"]
    
    # Check state after build completes
    assert "svcs_sphinx" not in app.env.temp_data  # Cleanup happened
```

### Testing With page Fixture (HTML Verification)

When you need to verify HTML output:

```python
@pytest.mark.sphinx("html", testroot="basic-no-extension")
@pytest.mark.parametrize(
    "page",
    ["index.html"],
    indirect=True,
)
def test_html_output(page: str, html_page: Element, sphinx_warnings: dict):
    """Test HTML content and structure."""
    # Raw HTML assertions
    assert "expected content" in page
    
    # Semantic queries with aria-testing
    heading = get_by_tag_name(html_page, "h1")
    assert heading is not None
    assert "Project Title" in get_text_content(heading)
    
    # Filter benign warnings if needed
    actual_warnings = [
        line for line in sphinx_warnings["lines"]
        if "already registered" not in line
    ]
    assert not actual_warnings
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
    
    # Query navigation
    nav = get_by_role(html_page, "navigation")
```

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

## Testing Extension Functionality

### Manual Event Handler Testing

Test event handlers directly without full Sphinx build:

```python
from sphinx.application import Sphinx
from your_extension import on_builder_inited, on_build_finished

def test_event_handler(tmp_path):
    """Test event handler directly."""
    app = Sphinx(
        srcdir=tmp_path / "source",
        confdir=None,
        outdir=tmp_path / "build",
        doctreedir=tmp_path / "doctrees",
        buildername="html",
    )
    
    # Call handler
    on_builder_inited(app)
    
    # Verify behavior
    assert "your_data" in app.env.temp_data
```

### Full Build Integration Testing

Test complete build lifecycle with test roots:

```python
@pytest.mark.sphinx("html", testroot="with-extension")
def test_full_build(app):
    """Test complete build with extension."""
    app.build()
    
    # Verify extension worked
    assert app.statuscode == 0
    output_file = Path(app.outdir) / "index.html"
    assert output_file.exists()
```

## Best Practices

✅ **DO**:
- Match test function names to testroot names
- Use `@pytest.mark.sphinx` decorator for integration tests
- Use `page` fixture with `indirect=True` for HTML content testing
- Use `app` fixture directly when you need to inspect Sphinx internal state
- Use aria-testing for semantic HTML queries
- Filter "already registered" warnings (test pollution from running multiple tests)
- Test event handlers independently when possible
- Use descriptive docstrings explaining what's being tested

❌ **DON'T**:
- Use pytest-sphinx (third-party package) - use `sphinx.testing.fixtures` instead
- Forget `indirect=True` when using `page` fixture with parametrize
- Mix up test names and testroot names
- Test HTML structure with raw string matching when aria-testing is available
- Assume `app.env.temp_data` persists after `app.build()` completes

## Common Pitfalls

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

### Fixture Scope Issues

The `rootdir` fixture should be **function-scoped**, not session-scoped, to prevent app reuse:

```python
# CORRECT: Function scope (default)
@pytest.fixture
def rootdir():
    return Path(__file__).parent / "roots"

# WRONG: Session scope causes app reuse
@pytest.fixture(scope="session")  # ❌ Don't do this
def rootdir():
    return Path(__file__).parent / "roots"
```

### Page Fixture Timing

The `page` fixture triggers `app.build()`, which clears temp_data. If you need to inspect temp_data, use `app` fixture directly and connect to events:

```python
# Use app fixture + event hook, not page fixture
@pytest.mark.sphinx("html", testroot="test")
def test_temp_data(app):  # ✓ Use app, not page
    def capture(app, *args):
        # Inspect temp_data during build
        data = app.env.temp_data["your_key"]
    
    app.connect("html-page-context", capture)
    app.build()
```

## Further Reading

- [Sphinx Testing Documentation](https://www.sphinx-doc.org/en/master/development/tutorials/testing.html)
- Project's `src/svcs_sphinx/fixtures.py` for fixture implementations
- Project's `tests/test_integration.py` for comprehensive examples
