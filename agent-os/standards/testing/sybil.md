# Sybil Doctest Integration for Multi-Location Testing

## Context

This skill documents how to integrate Sybil with pytest to run doctests across multiple locations in a Python project: source code docstrings, root-level README.md, and documentation markdown files. Based on the tdom-path project implementation.

## Problem

Projects need to test code examples in three different locations:
1. **Source code docstrings** (`src/**/*.py`) - API documentation with examples
2. **README.md** - Quick-start examples for users
3. **Documentation files** (`docs/**/*.md`) - Comprehensive guides and tutorials

Each location has different requirements:
- Source code needs minimal imports (just what the module provides)
- README and docs need comprehensive test environment with all public APIs
- Different parsers needed: `DocTestParser` for Python docstrings, `PythonCodeBlockParser` for markdown

## Solution

Use Sybil with multiple configurations and custom `pytest_collect_file` hook to handle different file types and locations separately.

### Architecture

```
project/
├── conftest.py              # Root config: src/*.py + README.md
├── docs/
│   ├── conftest.py          # Docs config: docs/**/*.md
│   └── *.md
├── src/
│   └── package/
│       └── *.py             # Python docstrings
└── README.md                # Root markdown
```

### Step 1: Add Sybil Dependency

**File**: `pyproject.toml`

```toml
[dependency-groups]
dev = [
    "sybil[pytest]>=8.0.0",
    # ... other dependencies
]
```

Then install:
```bash
uv sync
```

### Step 2: Root Configuration

**File**: `conftest.py` (project root)

This handles **both** source code Python files and README.md:

```python
"""Root pytest configuration with Sybil doctest integration.

Handles:
- src/*.py: Python docstrings with DocTestParser
- README.md: Markdown with PythonCodeBlockParser

Note: docs/*.md files are handled by docs/conftest.py
"""

from sybil import Sybil
from sybil.parsers.myst import PythonCodeBlockParser
from sybil.parsers.rest import DocTestParser

# Import all APIs needed for README examples
from pathlib import PurePosixPath
from typing import Protocol
from importlib.resources.abc import Traversable
from your_package import public_api_function, PublicClass
# ... more imports as needed


# Mock classes if needed for testing
class MockComponent:
    """Mock for testing without real component."""
    __module__ = "examples.components.mock"


# Configure Sybil for src/ Python files (minimal globals)
_sybil_src = Sybil(
    parsers=[DocTestParser()],
    patterns=["*.py"],
    path="src",
    setup=lambda ns: ns.update({"MockComponent": MockComponent}),
)

# Configure Sybil for README.md (comprehensive globals)
_sybil_readme = Sybil(
    parsers=[PythonCodeBlockParser()],
    patterns=["README.md"],
    path=".",
    setup=lambda ns: ns.update(
        {
            "MockComponent": MockComponent,
            "public_api_function": public_api_function,
            "PublicClass": PublicClass,
            "PurePosixPath": PurePosixPath,
            "Protocol": Protocol,
            "Traversable": Traversable,
            # Add all public APIs used in README
        }
    ),
)

# Combine hooks
_src_hook = _sybil_src.pytest()
_readme_hook = _sybil_readme.pytest()


def pytest_collect_file(file_path, parent):
    """Collect from src/ and README.md."""
    return _src_hook(file_path, parent) or _readme_hook(file_path, parent)
```

**Key patterns:**
- **Two separate Sybil instances** for different file types
- **Different parsers**: `DocTestParser` for `.py`, `PythonCodeBlockParser` for `.md`
- **Different globals**: minimal for source code, comprehensive for README
- **Custom `pytest_collect_file`**: combines both hooks with OR logic

### Step 3: Documentation Configuration

**File**: `docs/conftest.py`

This handles all markdown files in the docs directory:

```python
"""Pytest configuration for docs/ markdown doctests.

This conftest handles docs/**/*.md only (README.md is in root conftest.py)
Uses PythonCodeBlockParser to parse ```python blocks containing doctest syntax.
"""

from pathlib import PurePosixPath
from typing import Protocol
from importlib.resources.abc import Traversable

from sybil import Sybil
from sybil.parsers.myst import PythonCodeBlockParser
from your_package import public_api_function, PublicClass


# Mock classes for documentation examples
class MockComponent:
    __module__ = "examples.components.mock"


# Configure Sybil for docs/ markdown files
pytest_collect_file = Sybil(
    parsers=[PythonCodeBlockParser()],
    patterns=["*.md"],
    path=".",
    setup=lambda ns: ns.update(
        {
            "MockComponent": MockComponent,
            "public_api_function": public_api_function,
            "PublicClass": PublicClass,
            "PurePosixPath": PurePosixPath,
            "Protocol": Protocol,
            "Traversable": Traversable,
            # Same globals as README for consistency
        }
    ),
).pytest()
```

**Key patterns:**
- **Single Sybil instance** - docs only have markdown
- **Relative path** (`path="."`) - relative to docs/ directory
- **Comprehensive globals** - same as README for consistency

### Step 4: Pytest Configuration

**File**: `pyproject.toml`

```toml
[tool.pytest.ini_options]
testpaths = ["tests", "src", "docs"]
python_files = ["test_*.py"]
addopts = "-p no:doctest"  # Disable built-in doctest, use Sybil
pythonpath = ["examples"]  # If you have example code to import
```

**Key patterns:**
- **`testpaths`** includes `src` and `docs` for Sybil collection
- **`-p no:doctest`** disables pytest's built-in doctest plugin
- **`pythonpath`** adds directories needed for test imports

### Step 5: Justfile Recipes

**File**: `Justfile`

```just
# Run doctest examples via Sybil integration with pytest
test-doctest *ARGS:
    uv run pytest src/ {{ ARGS }}

# Run doctest examples in docs/ and README.md
test-docs *ARGS:
    uv run pytest docs/ README.md {{ ARGS }}

# Run all doctests (src + docs + README)
test-all-doctests *ARGS:
    uv run pytest src/ docs/ README.md {{ ARGS }}
```

**Usage:**
```bash
just test-doctest          # Test source code docstrings
just test-docs             # Test README and docs
just test-all-doctests     # Test everything
just test-docs -v          # Verbose output
```

## Writing Doctests

### In Source Code (src/**/*.py)

Use standard Python doctest syntax:

```python
def make_path(component: Any, path: str) -> Path:
    """Resolve component resource path.

    Args:
        component: Component class or instance
        path: Relative path to resource

    Returns:
        Resolved Path to resource

    Examples:
        >>> from mypackage import make_path
        >>> path = make_path(MockComponent, "static/styles.css")
        >>> str(path)  # doctest: +SKIP
        '/path/to/component/static/styles.css'
    """
    # implementation
```

### In Markdown Files (README.md, docs/**/*.md)

Use Python code blocks with doctest syntax:

````markdown
## Quick Start

```python
>>> from mypackage import make_path
>>> path = make_path(MockComponent, "static/styles.css")
>>> isinstance(path, Path)
True
```
````

**Note:** The `>>>` prompt tells Sybil's `PythonCodeBlockParser` to treat the code block as a doctest.

## Mock Classes Pattern

When examples reference application classes that may not exist or are hard to instantiate:

```python
# In conftest.py
class MockComponent:
    """Mock component for doctest examples."""
    __module__ = "examples.components.heading"  # Point to example location
```

The `__module__` attribute is crucial - it tells `importlib.resources` where to look for relative assets.

## Python 3.14 Known Issue

**WARNING**: Python 3.14 (both free-threaded and standard) has a recursion bug in `doctest.py` line 1507 (`__patched_linecache_getlines`). Tests pass until first failure, then pytest crashes with `RecursionError`.

Add this warning to your root `conftest.py`:

```python
"""
WARNING: Python 3.14 (both free-threaded and non-free-threaded) has a recursion
bug in doctest's __patched_linecache_getlines (line 1507). The bug triggers when
pytest+Sybil tries to format error messages for failed doctests. Tests will pass
until a failure occurs, then pytest will crash with RecursionError.

Workaround if needed: Use `python -m doctest src/package/*.py` directly.
"""
```

**Workaround** (if you hit the bug):
```bash
# Use Python's built-in doctest module
python -m doctest src/package/*.py -v
```

## Verification

### Check Installation
```bash
# Verify Sybil is installed
uv run python -c "import sybil; print(sybil.__version__)"

# Check pytest finds Sybil tests
uv run pytest src/ docs/ README.md --collect-only
```

### Run Tests
```bash
just test-all-doctests           # All doctests
just test-doctest -v             # Source code with verbose
just test-docs -k "Quick Start"  # Filter by pattern
```

## Key Benefits

1. **Multiple file types**: Python docstrings + Markdown in one setup
2. **Pytest integration**: Full access to fixtures, plugins, and reporting
3. **Custom globals**: Mock objects and APIs injected into doctest namespace
4. **Fail-fast validation**: Asset/import errors caught immediately
5. **Separate concerns**: Different configs for different locations
6. **Living documentation**: Examples are tested, stay up-to-date

## Common Patterns from tdom-path

### Pattern 1: Separate Globals by Location

```python
# Minimal for source code (just mocks)
_sybil_src = Sybil(
    parsers=[DocTestParser()],
    path="src",
    setup=lambda ns: ns.update({"MockComponent": MockComponent}),
)

# Comprehensive for docs (all public APIs)
_sybil_readme = Sybil(
    parsers=[PythonCodeBlockParser()],
    path=".",
    setup=lambda ns: ns.update({
        "MockComponent": MockComponent,
        "make_traversable": make_traversable,
        "make_path_nodes": make_path_nodes,
        # ... all public APIs
    }),
)
```

### Pattern 2: Custom pytest_collect_file Hook

```python
def pytest_collect_file(file_path, parent):
    """Collect from multiple Sybil configurations."""
    return _src_hook(file_path, parent) or _readme_hook(file_path, parent)
```

This allows combining multiple Sybil configurations in a single conftest.

### Pattern 3: Justfile Test Organization

```just
test-doctest *ARGS:        # Just source code
    uv run pytest src/ {{ ARGS }}

test-docs *ARGS:           # Just documentation
    uv run pytest docs/ README.md {{ ARGS }}

test-all-doctests *ARGS:   # Everything
    uv run pytest src/ docs/ README.md {{ ARGS }}
```

Separate recipes for different workflows.

## Troubleshooting

### Doctests Not Found
- Check `testpaths` in `pyproject.toml` includes `src` and `docs`
- Verify `patterns` in Sybil config matches your files
- Run `pytest --collect-only` to see what's being collected

### Import Errors in Doctests
- Add missing imports to `setup` lambda globals
- Check `pythonpath` in `pyproject.toml`
- Verify mock class `__module__` attributes

### RecursionError on Test Failure
- Python 3.14 bug - use built-in doctest workaround
- Add warning to conftest.py
- Consider using Python 3.13 until fixed

## Related Documentation

- Sybil docs: https://sybil.readthedocs.io/
- Pytest doctest: https://docs.pytest.org/en/stable/how-to/doctest.html
- Python doctest: https://docs.python.org/3/library/doctest.html
