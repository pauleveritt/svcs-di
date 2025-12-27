# Tech Stack

## Language & Runtime

- **Language:** Python 3.14+ (requires modern type hints and protocol support)
- **Package Manager:** uv (primary), pip (fallback)
- **Python Features:** Type hints, protocols, dataclasses, PEP 703 free-threaded support

## Core Dependencies

- **svcs:** Foundation library providing Registry and Container abstractions for service management
- **typing:** Python's type system for protocols, generics, and type annotations

### Upstream Contribution Strategy

Based on [GitHub Discussion #94](https://github.com/hynek/svcs/discussions/94):

- **Phase 0 Module:** A single minimal module (`svcs.auto()` helper) designed for potential upstream contribution
    - No imports beyond Python stdlib and svcs
    - Provides automatic dependency resolution based on type hints
    - Maintains svcs' non-magical, optional helper philosophy
    - Should be frozen/internal implementation
- **svcs-di Extensions:** Everything beyond the minimal helper remains in svcs-di as optional extensions

## Testing & Quality

- **Test Framework:** pytest
    - pytest-cov for coverage reporting
    - pytest-xdist for parallel test execution
    - pytest-timeout for detecting hangs/deadlocks in free-threaded mode
    - pytest-run-parallel for free-threaded Python compatibility testing
- **Documentation Testing:** Sybil for testing code examples in documentation
- **Linting & Formatting:** Ruff (linting and formatting)
- **Type Checking:** Modern Python type hints with protocol support (ty for type utilities)

## Documentation

- **Documentation Generator:** Sphinx with MyST Parser for Markdown support
- **Theme:** Furo (clean, modern Sphinx theme)
- **Live Preview:** sphinx-autobuild for local development
- **Markdown Extensions:** linkify-it-py for automatic URL linking

## Development Tools

- **Build System:** uv_build (uv's build backend)
- **Coverage:** coverage.py with pytest-cov integration
- **Version Control:** Git with GitHub for repository hosting

## Project Structure

- **Source:** `/src/svcs_di/` - main package code
- **Tests:** `/tests/` - unit and integration tests
- **Examples:** `/examples/` - working example applications (included in pytest path)
- **Documentation:** `/docs/` - Sphinx documentation with examples
    - `/docs/examples/*.md` - documentation for each example
    - `/docs/guides/` - user guides and tutorials
    - `/docs/reference/` - API reference documentation

## Optional Modules (Future)

- **Scanning Module:** Venusian-inspired auto-discovery (when implemented)
- **Advanced Features Module:** Field operators and enhanced dependency features (when implemented)

## Development Standards

- **Free-Threading Safety:** All code must be compatible with Python's free-threaded mode (PEP 703)
- **Type Safety:** Full type hint coverage with protocol-based interfaces
- **Test Coverage:** Comprehensive test coverage including examples
- **Documentation:** Every example must have corresponding docs and tests

## CI/CD

- **Platform:** GitHub Actions (implied by project structure)
- **Test Matrix:** Multiple Python versions including free-threaded builds
- **Quality Checks:** Ruff linting, type checking, test coverage reporting

## Related Projects

- **svcs:** Core dependency located at `/Users/pauleveritt/PycharmProjects/svcs/`
- **hopscotch:** Predecessor DI framework at `/Users/pauleveritt/projects/pauleveritt/hopscotch`
- **venusian:** Scanning inspiration (pattern reference, not a dependency)
