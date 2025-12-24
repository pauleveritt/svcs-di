# Product Mission

## Pitch

svcs-di is a dependency injection extension for Python's `svcs` library that helps Python developers build maintainable,
type-safe applications by providing modern, protocol-based dependency injection with context-aware service resolution.

## Users

### Primary Customers

- **Python Application Developers**: Teams building web applications, CLIs, or services that need sophisticated
  dependency management
- **svcs Library Users**: Existing users of the `svcs` library looking to enhance their dependency management patterns
- **Enterprise Python Teams**: Organizations requiring structured, testable, and maintainable dependency injection for
  large-scale applications
- **Framework Migrators**: Developers transitioning from other DI frameworks (like Hopscotch) who need familiar patterns
  in a modern implementation

### User Personas

**Senior Python Developer** (30-45 years)

- **Role:** Lead developer or architect on a Python web application
- **Context:** Building multi-tenant SaaS platforms or location-aware applications that need different service
  implementations based on context
- **Pain Points:** Struggling with manual dependency wiring, lack of type safety, difficulty testing with mocked
  dependencies, complex conditional service resolution
- **Goals:** Clean, testable code with minimal boilerplate; type-safe dependency injection; flexible service resolution
  based on request context

**Python Library Maintainer** (25-40 years)

- **Role:** Open source contributor or library author
- **Context:** Building reusable Python packages that need flexible dependency injection without heavy framework
  dependencies
- **Pain Points:** Existing DI solutions are too heavy or framework-specific; need modern Python type hint support; want
  minimal dependencies
- **Goals:** Lightweight, standards-based DI using protocols; compatibility with free-threaded Python; easy integration
  with existing `svcs` usage

## The Problem

### Manual Dependency Wiring is Error-Prone and Verbose

Python applications often resort to manual dependency passing through function signatures or global state management,
leading to tightly coupled code, difficult testing, and maintenance headaches. Without type-safe dependency injection,
refactoring becomes risky and IDE support is limited.

**Our Solution:** svcs-di leverages Python 3.12+ type hints and protocols to provide automatic dependency resolution
with full IDE support and type checking.

### Context-Aware Service Resolution is Complex

Modern applications need different service implementations based on request context (customer vs employee, geographic
location, tenant ID, etc.). Implementing this manually requires complex conditional logic scattered throughout the
codebase.

**Our Solution:** Built-in support for context-specific and location-based service registration with precedence-based
resolution, allowing clean separation of concerns and declarative service configuration.

### Testing with Dependencies is Cumbersome

Setting up test fixtures with properly mocked or stubbed dependencies requires significant boilerplate, and it's easy to
create brittle tests that break during refactoring.

**Our Solution:** Container-based dependency injection makes testing trivial - simply register test implementations in a
test container and your entire application uses them automatically.

## Differentiators

### Protocol-Based Type Safety

Unlike traditional Python DI frameworks that rely on string names or class types, we use Python protocols for
interface-based programming. This provides compile-time type checking, excellent IDE support with autocomplete, and
clear contracts between components.

### Free-Threaded Python Support

Built from the ground up to work with Python's new free-threaded mode (PEP 703), ensuring your applications are ready
for the next generation of Python performance improvements.

### Context-Aware Resolution with Precedence

Unlike simple DI containers that provide one-to-one service mappings, we support multiple registrations for the same
interface with intelligent resolution based on request context, location, or custom criteria. The precedence system
ensures predictable behavior when multiple registrations could match.

### Minimal Core with Optional Advanced Features

The core `svcs_di` package is intentionally minimal - just type-safe dependency injection. Advanced features (multiple
registrations, operators, scanning) are optional modules, so you only pay for what you use.

### Built on svcs, Not a Replacement

We extend the battle-tested `svcs` library rather than creating yet another DI framework. If you're already using
`svcs`, you can adopt svcs-di incrementally without rewriting your application.

## Design Principles from Upstream Discussion

Based on [GitHub Discussion #94](https://github.com/hynek/svcs/discussions/94) with svcs maintainer Hynek Schlawack:

### Core Upstream-Acceptable Feature

The most likely feature to be accepted into svcs itself would be a minimal helper method for automatic dependency
resolution:

- **Example API:** `registry.register_factory(Wrapper, svcs.auto(Wrapper))`
- **Scope:** Single module, no imports beyond Python stdlib and svcs
- **Philosophy:** Optional helper that maintains svcs' non-magical approach
- **Key constraint:** Provides convenience without forcing complexity

### svcs-di Extended Features

Everything beyond the minimal `svcs.auto()` helper should remain in svcs-di as optional extensions:

- Context-aware resolution (location, tenant, user type)
- Multiple registrations with precedence
- Scanning/auto-discovery
- Field operators and custom construction patterns

### Implementation Constraints for Upstream Compatibility

1. **Keep an escape hatch:** Users should always be able to write custom factory methods
2. **Handle sync/async:** Support both synchronous and asynchronous dependency resolution
3. **Support defaults:** Work with functions/classes that have default arguments
4. **Minimal magic:** Type hints guide resolution but don't hide what's happening
5. **Frozen implementation:** Core utilities should be stable and internal

## Key Features

### Core Features

- **Type-Safe Injection:** Use Python 3.12+ type hints and protocols to declare dependencies. The container
  automatically resolves and injects them with full type checking support.
- **Protocol Support:** Define service interfaces using Python protocols for clean, interface-based programming with
  compile-time verification.
- **Registry and Container Pattern:** Separate configuration-time registration from request-time resolution using `svcs`
  Registry and Container abstractions.
- **Custom Construction:** Support for `__svcs__` method on dataclasses and classes for specialized construction logic,
  giving you control when needed.

### Context-Aware Features

- **Multiple Service Registrations:** Register different implementations of the same interface and resolve them based on
  runtime context.
- **Location-Based Resolution:** Register services specific to URL paths or logical locations, automatically selected
  based on the current request location.
- **Context-Specific Services:** Different service implementations for different user types (customer vs employee,
  tenant-specific, role-based, etc.).
- **Precedence System:** Clear, predictable rules for which service wins when multiple registrations could match the
  current context.

### Advanced Features

- **Auto-Discovery Scanning:** Minimal venusian-like scanning to automatically discover and register services without
  manual wiring.
- **Field Operators:** Special dataclass field support for advanced dependency features and configuration.
- **Test-Driven Examples:** Complete working examples with tests demonstrating real-world usage patterns.
- **Comprehensive Documentation:** Each example includes detailed documentation explaining the pattern, use cases, and
  best practices.
