"""
Service Locator - Multiple implementation registrations with resource-based selection.

This module provides two key capabilities:

1. **ServiceLocator**: A thread-safe, immutable locator for managing multiple service
   implementations with resource-based selection. This allows different implementations
   to be selected based on business entity types like Customer, Employee, or Product.

2. **Package Scanning**: Decorator-based auto-discovery of services via the @injectable
   decorator and scan() function. This eliminates manual registration code by automatically
   discovering and registering decorated classes.

The ServiceLocator uses svcs.Registry as the underlying storage and provides a locator
service that tracks multiple implementations with three-tier precedence:
- Exact resource match (highest)
- Subclass resource match (medium)
- Default/no resource (lowest)

The scanning functionality provides a venusian-inspired decorator pattern that:
- Marks services with @injectable decorator at class definition time
- Discovers and registers them at application startup via scan()
- Supports resource-based registrations with @injectable(resource=...)
- Works seamlessly with Injectable[T] dependency injection

Also includes HopscotchInjector which extends KeywordInjector to support automatic
locator-based resolution for Injectable[T] fields with multiple implementations.

Examples:
    Basic usage with ServiceLocator:
        >>> locator = ServiceLocator()
        >>> locator = locator.register(Greeting, DefaultGreeting)
        >>> locator = locator.register(Greeting, EmployeeGreeting, resource=EmployeeContext)
        >>> registry.register_value(ServiceLocator, locator)

    Basic usage with scanning:
        >>> @injectable
        ... @dataclass
        ... class Database:
        ...     host: str = "localhost"
        ...
        >>> registry = svcs.Registry()
        >>> scan(registry, "myapp.services")

    Resource-based scanning:
        >>> @injectable(resource=CustomerContext)
        ... @dataclass
        ... class CustomerGreeting(Greeting):
        ...     salutation: str = "Hello"
        ...
        >>> scan(registry, "myapp.services")

For complete examples, see:
- examples/multiple_implementations.py (ServiceLocator usage)
- examples/scanning/basic_scanning.py (simple scanning workflow)
- examples/scanning/context_aware_scanning.py (resource-based resolution)
"""

from __future__ import annotations

import importlib
import logging
import pkgutil
from dataclasses import dataclass, field
from types import ModuleType
from typing import Any, Optional

import svcs

from svcs_di.auto import FieldInfo, Injector, get_field_infos

log = logging.getLogger("svcs_di")


@dataclass(frozen=True)
class FactoryRegistration:
    """A single implementation registration with service type and optional resource.

    The resource represents a business entity type (e.g., Customer, Employee, Product)
    that determines which implementation to use.
    """

    service_type: type
    implementation: type
    resource: Optional[type] = None

    def matches(self, resource: Optional[type]) -> int:
        """
        Calculate match score for this registration against a resource type.

        Args:
            resource: The resource type to match against (e.g., Customer, Employee)

        Returns:
            2 = exact resource match (highest)
            1 = subclass resource match (medium)
            0 = no resource match (lowest/default)
            -1 = no match
        """
        match (self.resource, resource):
            case (None, None):
                return 0  # Default match
            case (r, req) if r is req:
                return 2  # Exact match
            case (None, _):
                return 0  # Default fallback
            case (r, req) if req is not None and r is not None and issubclass(req, r):
                return 1  # Subclass match
            case _:
                return -1  # No match


@dataclass(frozen=True)
class ServiceLocator:
    """
    Thread-safe, immutable locator for multiple service implementations with resource-based selection.

    This is the ONE locator for the entire application. Implementations are stored in LIFO
    order (most recent first). Selection uses three-tier precedence: exact > subclass > default.

    Resource-based matching allows different implementations to be selected based on business
    entity types like Customer, Employee, or Product.

    Thread-safe: All data is immutable (frozen dataclass with tuple).

    Caching: Results are cached for performance. Cache is keyed by (service_type, resource_type)
    tuple and stores the resolved implementation class or None.

    Example:
        # Create with registrations
        locator = ServiceLocator.with_registrations(
            (Greeting, DefaultGreeting, None),
            (Greeting, EmployeeGreeting, EmployeeContext),
            (Database, PostgresDB, None),
        )

        # Or build up immutably
        locator = ServiceLocator()
        locator = locator.register(Greeting, DefaultGreeting)
        locator = locator.register(Greeting, EmployeeGreeting, resource=EmployeeContext)
    """

    registrations: tuple[FactoryRegistration, ...] = field(default_factory=tuple)
    _cache: dict[tuple[type, Optional[type]], Optional[type]] = field(
        default_factory=dict
    )

    @staticmethod
    def with_registrations(
        *registrations: tuple[type, type, Optional[type]],
    ) -> "ServiceLocator":
        """
        Create ServiceLocator with registrations.

        Args:
            registrations: Variable number of (service_type, implementation, resource) tuples

        Returns:
            New ServiceLocator instance

        Example:
            locator = ServiceLocator.with_registrations(
                (Greeting, DefaultGreeting, None),
                (Greeting, EmployeeGreeting, EmployeeContext),
            )
        """
        factory_regs = tuple(
            FactoryRegistration(service_type, impl, ctx)
            for service_type, impl, ctx in registrations
        )
        return ServiceLocator(registrations=factory_regs)

    def register(
        self, service_type: type, implementation: type, resource: Optional[type] = None
    ) -> "ServiceLocator":
        """
        Return new ServiceLocator with additional registration (immutable, thread-safe).

        LIFO ordering: new registrations are inserted at the front.
        Cache invalidation: new instance has empty cache since registrations changed.

        Args:
            service_type: The service type to register for
            implementation: The implementation class
            resource: Optional resource type for resource-specific resolution

        Returns:
            New ServiceLocator with the registration prepended and cleared cache
        """
        new_reg = FactoryRegistration(service_type, implementation, resource)
        # Prepend for LIFO (most recent first)
        new_registrations = (new_reg,) + self.registrations
        # Return new instance with empty cache (cache invalidation)
        return ServiceLocator(registrations=new_registrations)

    def get_implementation(
        self, service_type: type, resource: Optional[type] = None
    ) -> Optional[type]:
        """
        Find best matching implementation class for a service type using three-tier precedence.

        The resource parameter specifies a business entity type (like Customer or Employee)
        to select the appropriate implementation.

        Results are cached for performance. The cache key is (service_type, resource_type).

        Args:
            service_type: The service type to find an implementation for
            resource: Optional resource type for resource-based matching

        Returns:
            The implementation class from the first registration with highest score.

        Thread-safe: Only reads immutable data (cache is mutated but that's thread-safe for dicts).
        """
        cache_key = (service_type, resource)

        # Check cache first
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Cache miss - perform lookup
        best_score = -1
        best_impl = None

        for reg in self.registrations:
            if reg.service_type is not service_type:
                continue  # Skip registrations for other service types

            score = reg.matches(resource)
            if score > best_score:
                best_score = score
                best_impl = reg.implementation
                if score == 2:  # Exact match, can't do better
                    break

        # Store in cache before returning
        # Note: Mutating frozen dataclass's dict field is safe here because:
        # 1. Dict operations are thread-safe for simple get/set
        # 2. We never replace the dict object itself
        # 3. Worst case: multiple threads compute same result (idempotent)
        self._cache[cache_key] = best_impl

        return best_impl


def get_from_locator[T](
    container: svcs.Container,
    service_type: type[T],
    resource: Optional[type] = None,
) -> T:
    """
    Get a service from the locator with automatic construction.

    The ServiceLocator is registered as a service in the registry.

    Usage:
        # Setup (once per application)
        registry = svcs.Registry()
        locator = ServiceLocator()
        locator = locator.register(Greeting, DefaultGreeting)
        locator = locator.register(Greeting, EmployeeGreeting, resource=EmployeeContext)
        locator = locator.register(Database, PostgresDB)
        locator = locator.register(Database, TestDB, resource=TestContext)
        registry.register_value(ServiceLocator, locator)

        # Or use the static constructor:
        locator = ServiceLocator.with_registrations(
            (Greeting, DefaultGreeting, None),
            (Greeting, EmployeeGreeting, EmployeeContext),
            (Database, PostgresDB, None),
            (Database, TestDB, TestContext),
        )
        registry.register_value(ServiceLocator, locator)

        # Get service (per request)
        container = svcs.Container(registry)
        greeting = get_from_locator(container, Greeting, resource=EmployeeContext)
        db = get_from_locator(container, Database, resource=TestContext)
    """
    locator = container.get(ServiceLocator)

    implementation = locator.get_implementation(service_type, resource)

    if implementation is None:
        raise LookupError(
            f"No implementation found for {service_type.__name__} with resource {resource}"
        )

    # Construct the instance from the implementation class
    # Type ignore needed: implementation is type[T], calling it returns T,
    # but type checkers can't infer constructor signatures generically
    return implementation()  # type: ignore[return-value]


@dataclass(frozen=True)
class HopscotchInjector:
    """
    Injector that extends KeywordInjector with locator-based multi-implementation resolution.

    Implements three-tier precedence for value resolution:
    1. kwargs passed to injector (highest priority - overrides everything)
    2. ServiceLocator for Injectable[T] types with multiple implementations, falling back to container.get(T)
    3. default values from field definitions (lowest priority)

    When resolving Injectable[T] fields, it first tries ServiceLocator.get_implementation()
    with resource obtained from container. If no locator or no matching implementation is found,
    falls back to standard container.get(T) or container.get_abstract(T) behavior.
    """

    container: svcs.Container
    resource: Optional[type] = (
        None  # Optional: type to get from container for resource (e.g., RequestContext)
    )

    def _validate_kwargs(
        self, target: type, field_infos: list[FieldInfo], kwargs: dict[str, Any]
    ) -> None:
        """Validate that all kwargs match actual field names."""
        valid_field_names = {f.name for f in field_infos}
        for kwarg_name in kwargs:
            if kwarg_name not in valid_field_names:
                raise ValueError(
                    f"Unknown parameter '{kwarg_name}' for {target.__name__}. "
                    f"Valid parameters: {', '.join(sorted(valid_field_names))}"
                )

    def _get_resource(self) -> Optional[type]:
        """Get the resource type from container if resource is configured."""
        if self.resource is None:
            return None

        try:
            resource_instance = self.container.get(self.resource)
            return type(resource_instance)
        except svcs.exceptions.ServiceNotFoundError:
            return None

    def _resolve_field_value_sync(
        self, field_info: FieldInfo, kwargs: dict[str, Any]
    ) -> tuple[bool, Any]:
        """
        Resolve a single field's value using three-tier precedence with locator support.

        Returns:
            tuple[bool, Any]: (has_value, value) where has_value indicates if a value was resolved
        """
        field_name = field_info.name

        # Tier 1: kwargs (highest priority)
        if field_name in kwargs:
            return (True, kwargs[field_name])

        # Tier 2: Injectable from container (with locator support)
        if field_info.is_injectable:
            inner_type = field_info.inner_type
            if inner_type is None:
                raise TypeError(f"Injectable field '{field_name}' has no inner type")

            # Try locator first for types with multiple implementations
            try:
                locator = self.container.get(ServiceLocator)
                resource_type = self._get_resource()

                implementation = locator.get_implementation(inner_type, resource_type)
                if implementation is not None:
                    # Construct instance using the injector recursively (for nested injection)
                    return (True, implementation())
            except svcs.exceptions.ServiceNotFoundError:
                pass  # No locator registered, fall through to normal resolution

            # Fall back to standard container resolution
            try:
                if field_info.is_protocol:
                    value = self.container.get_abstract(inner_type)
                else:
                    value = self.container.get(inner_type)
                return True, value
            except svcs.exceptions.ServiceNotFoundError:
                # Not in container either, fall through to defaults
                pass

        # Tier 3: default value
        if field_info.has_default:
            default_val = field_info.default_value
            # Handle default_factory (callable) or regular default
            if callable(default_val):
                return True, default_val()
            else:
                return True, default_val

        # No value found at any tier
        return (False, None)

    def __call__[T](self, target: type[T], **kwargs: Any) -> T:
        """
        Inject dependencies and construct target instance.

        Args:
            target: The class or callable to construct
            **kwargs: Keyword arguments that override any resolved dependencies

        Returns:
            An instance of target with dependencies injected

        Raises:
            ValueError: If unknown kwargs are provided
            TypeError: If an Injectable field has no inner type
        """
        field_infos = get_field_infos(target)
        self._validate_kwargs(target, field_infos, kwargs)

        resolved_kwargs: dict[str, Any] = {}
        for field_info in field_infos:
            has_value, value = self._resolve_field_value_sync(field_info, kwargs)
            if has_value:
                resolved_kwargs[field_info.name] = value

        return target(**resolved_kwargs)


@dataclass(frozen=True)
class HopscotchAsyncInjector:
    """
    Async version of HopscotchInjector.

    Like HopscotchInjector but uses async container methods (aget, aget_abstract)
    for resolving Injectable[T] dependencies.

    Implements the same three-tier precedence as HopscotchInjector:
    1. kwargs passed to injector (highest priority)
    2. ServiceLocator for Injectable[T] types, falling back to container.aget(T)
    3. default values from field definitions (lowest priority)
    """

    container: svcs.Container
    resource: Optional[type] = None

    def _validate_kwargs(
        self, target: type, field_infos: list[FieldInfo], kwargs: dict[str, Any]
    ) -> None:
        """Validate that all kwargs match actual field names."""
        valid_field_names = {f.name for f in field_infos}
        for kwarg_name in kwargs:
            if kwarg_name not in valid_field_names:
                raise ValueError(
                    f"Unknown parameter '{kwarg_name}' for {target.__name__}. "
                    f"Valid parameters: {', '.join(sorted(valid_field_names))}"
                )

    async def _get_resource(self) -> Optional[type]:
        """Get the resource type from container if resource is configured."""
        if self.resource is None:
            return None

        try:
            resource_instance = await self.container.aget(self.resource)
            return type(resource_instance)
        except svcs.exceptions.ServiceNotFoundError:
            return None

    async def _resolve_field_value_async(
        self, field_info: FieldInfo, kwargs: dict[str, Any]
    ) -> tuple[bool, Any]:
        """
        Async version of field value resolution with three-tier precedence and locator support.

        Returns:
            tuple[bool, Any]: (has_value, value) where has_value indicates if a value was resolved
        """
        field_name = field_info.name

        # Tier 1: kwargs (highest priority)
        if field_name in kwargs:
            return (True, kwargs[field_name])

        # Tier 2: Injectable from container (async, with locator support)
        if field_info.is_injectable:
            inner_type = field_info.inner_type
            if inner_type is None:
                raise TypeError(f"Injectable field '{field_name}' has no inner type")

            # Try locator first for types with multiple implementations
            try:
                locator = await self.container.aget(ServiceLocator)
                resource_type = await self._get_resource()

                implementation = locator.get_implementation(inner_type, resource_type)
                if implementation is not None:
                    # Construct instance using the injector recursively (for nested injection)
                    return (True, implementation())
            except svcs.exceptions.ServiceNotFoundError:
                pass  # No locator registered, fall through to normal resolution

            # Fall back to standard async container resolution
            try:
                if field_info.is_protocol:
                    value = await self.container.aget_abstract(inner_type)
                else:
                    value = await self.container.aget(inner_type)
                return True, value
            except svcs.exceptions.ServiceNotFoundError:
                # Not in container either, fall through to defaults
                pass

        # Tier 3: default value
        if field_info.has_default:
            default_val = field_info.default_value
            # Handle default_factory (callable) or regular default
            if callable(default_val):
                return True, default_val()
            else:
                return True, default_val

        # No value found at any tier
        return (False, None)

    async def __call__[T](self, target: type[T], **kwargs: Any) -> T:
        """
        Async inject dependencies and construct target instance.

        Args:
            target: The class or callable to construct
            **kwargs: Keyword arguments that override any resolved dependencies

        Returns:
            An instance of target with dependencies injected

        Raises:
            ValueError: If unknown kwargs are provided
            TypeError: If an Injectable field has no inner type
        """
        field_infos = get_field_infos(target)
        self._validate_kwargs(target, field_infos, kwargs)

        resolved_kwargs: dict[str, Any] = {}
        for field_info in field_infos:
            has_value, value = await self._resolve_field_value_async(field_info, kwargs)
            if has_value:
                resolved_kwargs[field_info.name] = value

        return target(**resolved_kwargs)


# ============================================================================
# Package Scanning Implementation
# ============================================================================


def _create_injector_factory(target_class: type, injector_type: type[Injector]) -> Any:
    """Create a factory function for a decorated class."""

    def factory(svcs_container: svcs.Container) -> Any:
        try:
            injector = svcs_container.get(injector_type)
        except svcs.exceptions.ServiceNotFoundError:
            injector = injector_type(container=svcs_container)
        return injector(target_class)

    return factory


def _get_or_create_locator(registry: svcs.Registry) -> ServiceLocator:
    """Get existing ServiceLocator from registry or create new one."""
    try:
        temp_container = svcs.Container(registry)
        return temp_container.get(ServiceLocator)
    except svcs.exceptions.ServiceNotFoundError:
        return ServiceLocator()


def _register_decorated_items(
    registry: svcs.Registry,
    decorated_items: list[tuple[type, dict[str, Any]]],
    injector_type: type[Injector],
) -> None:
    """Register all decorated items to registry and/or locator."""
    locator = _get_or_create_locator(registry)
    locator_modified = False

    for decorated_class, metadata in decorated_items:
        resource = metadata.get("resource")

        if resource is not None:
            locator = locator.register(
                decorated_class, decorated_class, resource=resource
            )
            locator_modified = True
        else:
            factory = _create_injector_factory(decorated_class, injector_type)
            registry.register_factory(decorated_class, factory)

    if locator_modified:
        registry.register_value(ServiceLocator, locator)


def _caller_module(level: int = 2) -> ModuleType | None:
    """
    Return the module of the caller at a specific frame level.

    Uses sys._getframe to inspect the call stack and find the module
    that called the current function.

    Args:
        level: Frame level to inspect (2 = caller's caller by default)

    Returns:
        The ModuleType of the caller, or None if in special contexts like doctests
    """
    import sys

    try:
        frame = sys._getframe(level)
        module_globals = frame.f_globals
        module_name = module_globals.get("__name__") or "__main__"

        # Special case: doctest/Sybil execution
        if module_name == "__test__":
            return None

        return sys.modules.get(module_name)
    except (AttributeError, ValueError, KeyError):
        return None


def _caller_package(level: int = 2) -> ModuleType | None:
    """
    Return the package of the caller at a specific frame level.

    This is useful for automatically detecting the calling package when
    scan() is called without arguments, enabling convenient usage like:
        scan(registry)  # Automatically scans the caller's package

    Args:
        level: Frame level to inspect (2 = caller's caller by default)

    Returns:
        The package ModuleType of the caller, or None if detection fails
    """
    module = _caller_module(level + 1)
    if module is None:
        return None

    # Check if this module is itself a package (has __init__.py)
    module_file = getattr(module, "__file__", "")
    if "__init__.py" in module_file or "__init__$py" in module_file:
        return module

    # Not a package, go up one level to get the containing package
    module_name = module.__name__
    if "." in module_name:
        package_name = module_name.rsplit(".", 1)[0]
        import sys

        return sys.modules.get(package_name)

    return module


def _scan_locals(frame_locals: dict[str, Any]) -> list[tuple[type, dict[str, Any]]]:
    """
    Scan local variables in a scope for @injectable decorated classes.

    This enables testing patterns where decorated classes are defined
    within a test function and then scanned without importing.

    Args:
        frame_locals: Dictionary of local variables (typically from locals())

    Returns:
        List of tuples: (decorated_class, metadata)
    """
    decorated_items: list[tuple[type, dict[str, Any]]] = []

    for name, obj in frame_locals.items():
        if isinstance(obj, type) and hasattr(obj, "__injectable_metadata__"):
            metadata = obj.__injectable_metadata__
            decorated_items.append((obj, metadata))

    return decorated_items


def scan(
    registry: svcs.Registry,
    *packages: str | ModuleType | None,
    injector_type: type[Injector] | None = None,
    locals_dict: dict[str, Any] | None = None,
) -> svcs.Registry:
    """
    Scan packages/modules for @injectable decorated classes and register them.

    Discovers and registers services marked with @injectable decorator. Classes with
    resource metadata are registered to ServiceLocator for resource-based resolution.
    Classes without resource metadata are registered directly to Registry.

    Args:
        registry: svcs.Registry to register services into
        *packages: Package/module references to scan:
                   - String names: "myapp.services" (auto-imported)
                   - ModuleType objects: myapp.services
                   - None/empty: Auto-detects caller's package
                   - Multiple: scan(registry, "app.models", "app.views")
        injector_type: Injector type for service construction (defaults to DefaultInjector)
        locals_dict: Dictionary of local variables to scan (useful for testing)

    Returns:
        The registry instance for method chaining.

    Examples:
        scan(registry)                           # Auto-detect caller's package
        scan(registry, "myapp.services")         # Specific package
        scan(registry, locals_dict=locals())     # Test pattern

    See examples/scanning/ for complete examples.
    """
    if injector_type is None:
        from svcs_di.auto import DefaultInjector

        injector_type = DefaultInjector

    # Handle locals_dict scanning for testing (local scope scanning)
    if locals_dict is not None:
        decorated_items = _scan_locals(locals_dict)
        _register_decorated_items(registry, decorated_items, injector_type)
        return registry

    # ========================================================================
    # Handle package/module scanning
    # ========================================================================

    # If no packages specified, auto-detect caller's package
    if not packages or (len(packages) == 1 and packages[0] is None):
        caller_pkg = _caller_package(level=2)
        if caller_pkg is not None:
            packages = (caller_pkg,)
        else:
            log.warning(
                "Could not auto-detect caller's package. No scanning performed."
            )
            return registry

    # Collect all modules to scan
    modules_to_scan: list[ModuleType] = []

    for pkg in packages:
        if pkg is None:
            # Skip None values (might occur in mixed usage)
            continue
        elif isinstance(pkg, str):
            # String package name - import it
            try:
                module = importlib.import_module(pkg)
                modules_to_scan.append(module)
            except ImportError as e:
                log.warning(f"Failed to import package '{pkg}': {e}")
                continue
        elif isinstance(pkg, ModuleType):
            # Already a module - use directly (no sys.modules hack needed!)
            modules_to_scan.append(pkg)
        else:
            log.warning(
                f"Invalid package type: {type(pkg)}. Must be str, ModuleType, or None"
            )
            continue

    # Walk through packages and discover submodules
    discovered_modules: list[ModuleType] = []

    for module in modules_to_scan:
        discovered_modules.append(module)

        # Check if this is a package (has __path__)
        if hasattr(module, "__path__"):
            # Use pkgutil.walk_packages to discover submodules
            try:
                for importer, modname, ispkg in pkgutil.walk_packages(
                    path=module.__path__,  # type: ignore[attr-defined]
                    prefix=module.__name__ + ".",
                    onerror=lambda name: None,
                ):
                    try:
                        submodule = importlib.import_module(modname)
                        discovered_modules.append(submodule)
                    except ImportError as e:
                        log.warning(f"Failed to import submodule '{modname}': {e}")
                        continue
            except Exception as e:
                log.warning(f"Error walking package '{module.__name__}': {e}")

    # Collect decorated items from all discovered modules
    decorated_items: list[tuple[type, dict[str, Any]]] = []

    for module in discovered_modules:
        for attr_name in dir(module):
            try:
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and hasattr(attr, "__injectable_metadata__"):
                    metadata = attr.__injectable_metadata__
                    decorated_items.append((attr, metadata))
            except (AttributeError, ImportError):
                continue

    # Register all decorated items
    _register_decorated_items(registry, decorated_items, injector_type)
    return registry
