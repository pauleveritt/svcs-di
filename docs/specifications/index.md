# Specifications

`svcs-di` was largely written in a spec-driven development workflow using Claude Code coding agent with
the [Agent OS](https://buildermethods.com/agent-os) system for SDD.

This section provides access to the product documentation and feature specifications that guide the development of
`svcs-di`. Here you can explore the project's mission, roadmap, technology choices, and the detailed specifications for
each implemented feature.

```{toctree}
:maxdepth: 2
:hidden:

product/mission
product/roadmap
product/tech-stack
features/basic-examples-and-documentation
features/core-type-safe-dependency-injection
features/context-specific-service-resolution
features/keyword-injector
features/multiple-service-registrations
features/free-threaded
features/location-based-service-resolution-and-precedence
features/optional-scanning-module
features/github-workflows
features/inject-container
features/specifications-into-sphinx
features/hopscotch-registry
features/injection-container
```

## Product

Core product documentation describing the vision, goals, and technical foundation of svcs-di.

### Mission

svcs-di is a dependency injection extension for Python's `svcs` library that helps Python developers build maintainable,
type-safe applications by providing modern, protocol-based dependency injection with context-aware service resolution.

[Read More](product/mission.md)

### Roadmap

Implement basic dependency injection using Python 3.12+ type hints,

[Read More](product/roadmap.md)

### Tech Stack

Core technology stack based on Python 3.14+ with modern type hints, protocol support, and free-threaded compatibility,
using uv for package management and building on the svcs library foundation.

[Read More](product/tech-stack.md)

## Features

Feature specifications documenting the evolution of svcs-di, presented in chronological order to show how the project
has developed over time.

### Basic Examples and Documentation

Create comprehensive documentation for all 5 existing examples in `/examples/`, including inline code snippets tested
with Sybil, structured by complexity, and expanded test coverage in a single test file.

[Read More](features/basic-examples-and-documentation.md)

### Minimal svcs.auto() Helper for Automatic Dependency Injection

Create a minimal, upstream-compatible `svcs.auto()` helper that enables automatic dependency resolution based on type
hints, allowing `registry.register_factory(Wrapper, svcs.auto(Wrapper))` to automatically resolve constructor

[Read More](features/core-type-safe-dependency-injection.md)

### Context-Specific Service Resolution

Refactor context-based service resolution by renaming "context" to "resource" throughout the codebase to better
represent business entity matching, and implement svcs-style caching for improved performance of resource-based lookups.

[Read More](features/context-specific-service-resolution.md)

### Keyword Injector

Extract kwargs handling from DefaultInjector into a specialized KeywordInjector, simplifying DefaultInjector to only
handle Injectable[T] resolution while creating reusable helper functions for future injector implementations.

[Read More](features/keyword-injector.md)

### Multiple Service Registrations

Enable registration of multiple implementations for the same protocol interface with metadata-driven resolution based on
a three-tier precedence algorithm, providing the foundation for context-aware and location-based service selection.

[Read More](features/multiple-service-registrations.md)

### Free-Threaded Python Compatibility

Verify and formally test that the existing svcs-di codebase works correctly with PEP 703's free-threaded Python (no-GIL
mode) through comprehensive concurrent access stress tests and CI/CD integration.

[Read More](features/free-threaded.md)

### Location-Based Service Resolution and Precedence

Add hierarchical location-based service resolution to enable URL-path or filesystem-like service selection, with
intelligent precedence scoring when multiple registrations match a request based on both context and location

[Read More](features/location-based-service-resolution-and-precedence.md)

### Optional Scanning Module

Add venusian-inspired scanning for auto-discovery of services via decorators. Keep it minimal, focusing only on
package/module scanning without venusian's complex features like categories or depth controls.

[Read More](features/optional-scanning-module.md)

### GitHub Workflows for CI/CD

Implement comprehensive GitHub Actions workflows for continuous integration testing with Python 3.14.2t (free-threaded),
documentation deployment to GitHub Pages, and reusable composite actions for dependency management using uv.

[Read More](features/github-workflows.md)

### Inject Container

Enable automatic injection of the `svcs.Container` instance itself when functions or dataclass fields are annotated with
`Inject[Container]`, allowing injected code to access the container for dynamic service resolution.

[Read More](features/inject-container.md)

### Specifications Into Sphinx

Integrate product documentation and feature specifications into Sphinx documentation system, creating a new "
Specifications" section that makes development history, feature specs, and product strategy accessible through published
documentation.

[Read More](features/specifications-into-sphinx.md)

### Hopscotch Registry

Create `HopscotchRegistry` and `HopscotchContainer` classes that provide pre-wired integration between svcs
registry/container and ServiceLocator for multi-implementation service resolution with minimal setup.

[Read More](features/hopscotch-registry.md)

### Injector Container

Implement an `InjectorContainer` class that extends `svcs.Container` to provide dependency injection capabilities by
integrating an injector into the container's `get()` and `aget()` methods, enabling kwargs support for service
resolution.

[Read More](features/injection-container.md)
