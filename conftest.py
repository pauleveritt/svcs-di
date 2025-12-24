"""Root pytest configuration with Sybil doctest integration.

Handles:
- src/*.py: Python docstrings with DocTestParser
- README.md: Markdown with PythonCodeBlockParser

Note: docs/*.md files are handled by docs/conftest.py
"""

from sybil import Sybil
from sybil.parsers.myst import PythonCodeBlockParser
from sybil.parsers.rest import DocTestParser

# Configure Sybil for src/ Python files
# Note: auto.py excluded because its doctests are narrative multi-line examples
# that don't work with Sybil's line-by-line execution model
_sybil_src = Sybil(
    parsers=[DocTestParser()],
    patterns=["*.py"],
    path="src",
    excludes=["**/auto.py"],
    fixtures=[],
)

# Configure Sybil for README.md
_sybil_readme = Sybil(
    parsers=[PythonCodeBlockParser()],
    patterns=["README.md"],
    path=".",
)

# Combine hooks
_src_hook = _sybil_src.pytest()
_readme_hook = _sybil_readme.pytest()


def pytest_collect_file(file_path, parent):
    """Collect from src/ and README.md."""
    return _src_hook(file_path, parent) or _readme_hook(file_path, parent)
