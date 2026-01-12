"""Root pytest configuration with Sybil doctest integration.

Handles:
- src/*.py: Python docstrings with DocTestParser
- README.md: Markdown with PythonCodeBlockParser

Note: docs/*.md files are handled by docs/conftest.py
"""

from pathlib import PurePath

import svcs

from sybil import Sybil
from sybil.parsers.myst import PythonCodeBlockParser
from sybil.parsers.rest import DocTestParser


def _doctest_setup(namespace: dict) -> None:
    """Setup function that provides mock types for src/ doctests.

    The doctests in src/ files use example types like Greeting, Database, etc.
    to illustrate API usage. This setup function provides these types so the
    doctests can execute.
    """
    # Service types (protocols/interfaces)
    class Greeting:
        """Example service type for greeting functionality."""

        def __init__(self, message: str = "Hello") -> None:
            self.message = message

    class Database:
        """Example database service."""

        def __init__(self, host: str = "localhost") -> None:
            self.host = host

    class MyService:
        """Generic example service."""

        pass

    class Config:
        """Example configuration service."""

        pass

    class WelcomeService:
        """Example service that depends on Greeting."""

        def __init__(self, greeting: Greeting | None = None) -> None:
            self.greeting = greeting

    # Greeting implementations
    class DefaultGreeting(Greeting):
        """Default greeting implementation."""

        pass

    class AdminGreeting(Greeting):
        """Admin-specific greeting."""

        pass

    class EmployeeGreeting(Greeting):
        """Employee-specific greeting."""

        pass

    class PublicGreeting(Greeting):
        """Public greeting."""

        pass

    class EnhancedGreeting(Greeting):
        """Enhanced greeting with extra features."""

        pass

    class VIPGreeting(Greeting):
        """VIP greeting."""

        pass

    # Context/Resource types for multi-implementation resolution
    class EmployeeContext:
        """Context indicating employee access."""

        pass

    class CustomerContext:
        """Context indicating customer access."""

        pass

    class AuthenticatedContext:
        """Context indicating authenticated access."""

        pass

    class VIPContext:
        """Context indicating VIP access."""

        pass

    # Populate the namespace with all types
    namespace.update(
        {
            # Service types
            "Greeting": Greeting,
            "Database": Database,
            "MyService": MyService,
            "Config": Config,
            "WelcomeService": WelcomeService,
            # Implementations
            "DefaultGreeting": DefaultGreeting,
            "AdminGreeting": AdminGreeting,
            "EmployeeGreeting": EmployeeGreeting,
            "PublicGreeting": PublicGreeting,
            "EnhancedGreeting": EnhancedGreeting,
            "VIPGreeting": VIPGreeting,
            # Context types
            "EmployeeContext": EmployeeContext,
            "CustomerContext": CustomerContext,
            "AuthenticatedContext": AuthenticatedContext,
            "VIPContext": VIPContext,
            # Common imports
            "PurePath": PurePath,
            "svcs": svcs,
        }
    )


# Configure Sybil for src/ Python files
# Note: auto.py excluded because its doctests are narrative multi-line examples
# that don't work with Sybil's line-by-line execution model
_sybil_src = Sybil(
    parsers=[DocTestParser()],
    patterns=["**/*.py"],
    path="src",
    excludes=["**/auto.py"],
    setup=_doctest_setup,
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
