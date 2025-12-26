# Specification: Optional Scanning Module

## Goal
Add venusian-inspired scanning for auto-discovery of services via decorators. Keep it minimal, focusing only on package/module scanning without venusian's complex features like categories or depth controls.

## User Stories
- As a developer, I want to mark services with `@injectable` decorator so they are auto-discovered without manual registration
- As a developer, I want to call a scan function to discover and register all decorated services in my application packages

## Specific Requirements

**@injectable decorator API**
- Named `@injectable` (lowercase) following Python decorator conventions
- Accepts optional `resource` parameter to register resource-specific implementations
- Can be applied to classes to mark them for auto-registration
- Stores metadata on decorated targets without performing registration at decoration time
- Defers all registration actions until scan phase is explicitly invoked

**Scanning entry point function**
- Standalone function `scan()` that does NOT extend Registry
- Accepts registry instance, package/module references to scan, and optional injector type
- Uses `importlib.metadata` for package discovery following Python 3.14+ standards
- Imports modules to execute decorator code and trigger metadata attachment
- Collects all `@injectable` decorated items and performs registrations on provided registry
- Returns registry for method chaining pattern
- Thread-safe: all registration happens during scan phase before containers are created

**Integration with locator.py**
- Registration logic goes in `locator.py` NOT in `auto.py`
- Decorated items are registered to ServiceLocator when resource is specified
- Decorated items without resource are registered directly to registry
- Uses existing ServiceLocator.register() for resource-based registrations
- Maintains LIFO ordering and caching behavior from existing locator implementation

**Resource parameter support**
- `@injectable(resource=CustomerContext)` registers implementation for specific resource type
- `@injectable()` or bare `@injectable` registers as default implementation
- Multiple decorators on same service type are supported (multiple implementations pattern)
- Resource matching follows existing three-tier precedence: exact match > subclass match > default

**Context integration**
- Decorators support context-aware services following existing HopscotchInjector patterns
- Resource types can be context classes like CustomerContext or EmployeeContext
- Context resolution happens at request time via HopscotchInjector, NOT during scanning
- Scan phase is context-agnostic, only records resource metadata

**Module structure placement**
- Implementation goes in `locator.py` as part of core module
- NOT a separate installable extra or optional dependency
- Import scanning requires only stdlib `importlib.metadata`
- Decorator functionality requires no additional dependencies

**Examples scope**
- Basic scanning example: simple classes with `@injectable`, scan and retrieve
- Context-aware scanning example: multiple implementations with resource parameter

## Visual Design
No visual assets provided.

## Existing Code to Leverage

**ServiceLocator from locator.py**
- Use existing `ServiceLocator.register()` for resource-based registrations
- Leverage `FactoryRegistration` dataclass for storing metadata
- Maintain immutable, thread-safe design patterns
- Reuse resource matching logic (exact > subclass > default precedence)
- Keep LIFO ordering and caching behavior

**HopscotchInjector from locator.py**
- Follow existing pattern for resource resolution at request time
- Use `_get_resource()` method pattern for obtaining resource type from container
- Maintain three-tier precedence model for value resolution
- Scanning does NOT invoke injector, only registers metadata for later use

**Registry and Container from svcs**
- Use `svcs.Registry.register_factory()` for non-resource registrations
- Use `svcs.Registry.register_value()` for ServiceLocator itself
- Follow existing factory function signature patterns from `auto.py`
- Maintain compatibility with existing injection workflows

**auto() factory pattern from auto.py**
- Decorated classes should work with existing `auto()` if needed
- Factory functions follow same signature: `(svcs_container: svcs.Container) -> T`
- Injectable[T] fields in decorated classes resolve via existing injector logic
- No changes needed to auto.py, decorator only adds registration convenience

**get_field_infos and FieldInfo from auto.py**
- Reuse existing field introspection for decorated classes
- Support both dataclasses and regular classes with `__init__` parameters
- Follow existing type hint resolution with Injectable[T] marker
- Use existing protocol detection logic via `_is_protocol` attribute

## Out of Scope
- Venusian features: depth parameter, ignore parameter, categories, action callbacks, onerror handling
- Extending or modifying Registry class with scan methods
- Creating separate installable extra or optional package structure
- Scan-time dependency injection or construction of services
- Automatic context detection during scanning (context is request-time only)
- Path-based or location-based registration (covered in roadmap item 8)
- Configuration file-based registration or external metadata
- Decorator support for functions (only classes)
- Classmethod decorator alternative for decoration configuration
- Multiple scan passes or incremental scanning
- Unregistration or decorator removal functionality
