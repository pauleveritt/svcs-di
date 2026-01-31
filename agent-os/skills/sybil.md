---
description:
  Sybil doctest integration for testing code examples across source, README,
  and docs. Use this when setting up doctests or testing documentation examples.
---

# Sybil Doctest Integration

## Context

This skill documents how to integrate Sybil with pytest to run doctests across multiple locations in a Python project: source code docstrings, root-level README.md, and documentation markdown files.

## Problem

Projects need to test code examples in three different locations:
1. **Source code docstrings** (`src/**/*.py`) - API documentation with examples
2. **README.md** - Quick-start examples for users
3. **Documentation files** (`docs/**/*.md`) - Comprehensive guides and tutorials

Each location has different requirements:
- Source code needs minimal imports (just what the module provides)
- README and docs need comprehensive test environment with all public APIs
- Different parsers needed: `DocTestParser` for Python docstrings, `PythonCodeBlockParser` for markdown

## Architecture

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

## Step 1: Add Sybil Dependency

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

## Step 2: Root Configuration

**File**: `conftest.py` (project root)

This handles **both** source code Python files and README.md:

```python
"""Root pytest configuration with Sybil doctest integration.

Handles:
- src/*.py: Python docstrings with DocTestParser
- README.md: Markdown with PythonCodeBlockParser

Note: docs/*.md files are handled by docs/conftest.py

WARNING: Python 3.14 (both free-threaded and non-free-threaded) has a recursion
bug in doctest's __patched_linecache_getlines (line 1507). The bug triggers when
pytest+Sybil tries to format error messages for failed doctests. Tests will pass
until a failure occurs, then pytest will crash with RecursionError.

Workaround if needed: Use `python -m doctest src/package/*.py` directly.
"""

from sybil import Sybil
from sybil.parsers.myst import PythonCodeBlockParser
from sybil.parsers.rest import DocTestParser

# Import all APIs needed for README examples
from your_package import public_api_function, PublicClass

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

## Step 3: Documentation Configuration

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

## Step 4: Pytest Configuration

**File**: `pyproject.toml`

```toml
[tool.pytest.ini_options]
testpaths = ["tests", "src", "docs"]
python_files = ["test_*.py"]
addopts = "-p no:doctest"  # Disable built-in doctest, use Sybil
pythonpath = ["examples"]  # If you have example code to import
```

## Writing Doctests

### In Source Code (src/**/*.py)

Use standard Python doctest syntax:

```python
def make_path(component: Any, path: str) -> Path:
    """Resolve component resource path.

    Examples:
        >>> from mypackage import make_path
        >>> path = make_path(MockComponent, "static/styles.css")
        >>> str(path)  # doctest: +SKIP
        '/path/to/component/static/styles.css'
    """
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

## Doctest Directives

Common directives to control test behavior:

```python
>>> result = some_function()  # doctest: +SKIP
# Skips this example entirely

>>> print(result)  # doctest: +ELLIPSIS
Some output... more text

>>> messy_output()  # doctest: +NORMALIZE_WHITESPACE
Expected   output
```

## Best Practices

**DO**:
- Use clear, concise examples in docstrings
- Show realistic usage
- Test edge cases
- Focus doctests on user-facing functions

**DON'T**:
- Use relative imports beyond local modules
- Store mutable business state in examples
- Skip verification of failing tests

## Python 3.14 Known Issue

**WARNING**: Python 3.14 (both free-threaded and standard) has a recursion bug in `doctest.py` line 1507 (`__patched_linecache_getlines`). Tests pass until first failure, then pytest crashes with `RecursionError`.

**Workaround** (if you hit the bug):
```bash
# Use Python's built-in doctest module
python -m doctest src/package/*.py -v
```

## Related Documentation

- Sybil docs: https://sybil.readthedocs.io/
- Pytest doctest: https://docs.pytest.org/en/stable/how-to/doctest.html
- Python doctest: https://docs.python.org/3/library/doctest.html
