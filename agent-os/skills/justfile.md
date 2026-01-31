---
description:
  Guide for writing Justfiles for CI/CD automation. Use this when creating
  or maintaining Justfiles for project automation.
---

# Justfile Standard

[Just](https://github.com/casey/just) is a task runner for complex automation. Use it for CI/CD pipelines and project automation.

## Example Justfile

```just
# Requires: just, uv, Python 3.14.2t (free-threaded build)
# All tasks use uv to ensure isolated, reproducible runs.

# Default recipe shows help - displays all available commands when running 'just' with no args
default:
    @just --list

# Print environment info - shows Python and uv versions for troubleshooting
info:
    @echo "Python: $(python --version)"
    @uv --version

# Install project and dev dependencies - syncs all dependency groups from pyproject.toml
install:
    uv sync --all-groups

# Alias for install (better discoverability) - same as 'install' but more intuitive name
setup: install

# Run tests (sequential) - runs regular pytest tests one at a time, accepts any pytest args
test *ARGS:
    uv run pytest {{ ARGS }}

# Run tests (parallel) - uses pytest-xdist to run tests across multiple CPU cores for speed
test-parallel *ARGS:
    uv run pytest -n auto {{ ARGS }}

# Run tests with free-threading safety checks - tests for Python 3.14t GIL-free threading issues
# Runs tests 10 times across 8 threads to catch race conditions and deadlocks
test-freethreaded:
    uv run pytest -p freethreaded -p no:doctest --threads=8 --iterations=10 --require-gil-disabled tests

# Lint code (check for issues) - runs ruff linter to find code quality issues, doesn't modify files
lint *ARGS:
    uv run ruff check {{ ARGS }} .

# Format code (auto-format) - applies ruff formatter to auto-fix code style issues
fmt *ARGS:
    uv run ruff format {{ ARGS }} .

# Check formatting without modifying files (for CI) - verifies code formatting without changes
# Used in CI to fail if code isn't properly formatted
fmt-check *ARGS:
    uv run ruff format --check {{ ARGS }} .

# Lint and auto-fix - automatically fixes linting issues that can be safely corrected
lint-fix:
    uv run ruff check --fix .

# Type checking - runs ty type checker with examples/ in PYTHONPATH for import resolution
typecheck *ARGS:
    PYTHONPATH=examples uv run ty check {{ ARGS }}

# Build docs - generates HTML documentation using Sphinx
docs:
    uv run sphinx-build -b html docs docs/_build/html

# Build docs with auto-reload for development - watches for changes and rebuilds automatically
# Opens local server at http://127.0.0.1:8000
docs-live:
    uv run sphinx-autobuild docs docs/_build/html

# Clean docs build - removes all generated documentation files
docs-clean:
    rm -rf docs/_build

# Build docs and open in browser - builds documentation then opens index.html
docs-open:
    just docs && open docs/_build/html/index.html

# Build sdist/wheel - creates Python distribution packages for publishing to PyPI
build:
    uv build

# Clean build and cache artifacts - removes all generated files and caches
# Includes pytest, ruff, type checker caches, and build artifacts
clean:
    rm -rf .pytest_cache .ruff_cache .pyright .mypy_cache build dist
    find docs/_build -mindepth 1 -maxdepth 1 -not -name ".gitkeep" -exec rm -rf {} + || true

# Run all quality checks with fail-fast behavior - full CI pipeline
# Stops at first failure: install -> lint -> format check -> type check -> tests
ci-checks:
    just install && just lint && just fmt-check && just typecheck && just test

# Run all checks + free-threading safety tests - extends ci-checks with GIL-free tests
# Use this for comprehensive testing before releases
ci-checks-ft:
    just ci-checks && just test-freethreaded

# Enable pre-push hook to run ci-checks before pushing - installs git hook
# Automatically runs full quality checks before every git push
# Blocks push if any check fails, preventing broken code from being pushed
enable-pre-push:
    @echo "Installing pre-push hook..."
    @echo '#!/bin/sh' > .git/hooks/pre-push
    @echo '' >> .git/hooks/pre-push
    @echo '# Run quality checks before push' >> .git/hooks/pre-push
    @echo 'echo "Running quality checks before push..."' >> .git/hooks/pre-push
    @echo 'if ! just ci-checks; then' >> .git/hooks/pre-push
    @echo '    echo "Pre-push check failed! Push aborted."' >> .git/hooks/pre-push
    @echo '    exit 1' >> .git/hooks/pre-push
    @echo 'fi' >> .git/hooks/pre-push
    @chmod +x .git/hooks/pre-push
    @echo "Pre-push hook installed! Use 'just disable-pre-push' to disable."

# Disable pre-push hook - removes executable permissions from git hook
# Push will work normally without running checks
disable-pre-push:
    @chmod -x .git/hooks/pre-push 2>/dev/null || true
    @echo "Pre-push hook disabled. Use 'just enable-pre-push' to re-enable."

# Run slow tests (marked with @pytest.mark.slow) - tests that take longer to execute
# Separated from normal tests to speed up regular test runs
test-slow *ARGS:
    uv run pytest -m slow {{ ARGS }}

# Run doctest examples via Sybil integration with pytest - tests code in Python docstrings
test-doctest *ARGS:
    uv run pytest src/ {{ ARGS }}

# Run doctest examples in docs/ and README.md - tests documentation code examples
test-docs *ARGS:
    uv run pytest docs/ README.md {{ ARGS }}

# Run all doctests (src + docs + README) - comprehensive doctest suite
test-all-doctests *ARGS:
    uv run pytest src/ docs/ README.md {{ ARGS }}
```

## Key Recipes

| Recipe | Purpose |
|--------|---------|
| `just` | Show all available commands |
| `just install` | Install all dependencies |
| `just test` | Run test suite |
| `just lint` | Check for linting issues |
| `just fmt` | Auto-format code |
| `just typecheck` | Run type checker |
| `just ci-checks` | Full CI pipeline |
| `just docs` | Build documentation |

## Anti-Patterns

- **Missing default recipe**: Not having a `default` recipe that shows available commands
- **Undocumented recipes**: Recipes without comments explaining their purpose
- **Hardcoded paths**: Using absolute paths instead of relative or variable paths
- **Missing dependencies**: Not declaring recipe dependencies with `:` syntax
- **Duplicate logic**: Copying commands instead of calling other recipes
- **No fail-fast**: CI recipes that continue after failures instead of stopping early
- **Silent failures**: Using `|| true` to hide errors that should be visible
- **Missing ARGS**: Not accepting arguments for recipes that wrap tools like pytest

## Related Skills

- [workflow](workflow/workflow.md) - Development lifecycle standards
- [uv](uv.md) - Package management with uv
- [ruff](ruff.md) - Linting and formatting
- [ty](ty.md) - Type checking
- [testing](testing/testing.md) - Test running
