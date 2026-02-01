"""
HopscotchRegistry and HopscotchContainer: Pre-wired integration with ServiceLocator.

This module provides HopscotchRegistry and HopscotchContainer, which extend svcs.Registry
and svcs.Container to provide automatic ServiceLocator management for multi-implementation
service resolution with resource and location-based selection.

The HopscotchRegistry maintains an internal ServiceLocator that is automatically
updated when implementations are registered via register_implementation(). The
locator is also registered as a value service so it can be resolved from containers.

HopscotchContainer extends svcs.Container with inject() and ainject() methods that
use HopscotchInjector for dependency resolution with resource/location-based
multi-implementation support.

Example:
    >>> from pathlib import PurePath
    >>> registry = HopscotchRegistry()
    >>> # Register implementations with resource/location context
    >>> registry.register_implementation(Greeting, DefaultGreeting)
    >>> registry.register_implementation(Greeting, AdminGreeting, location=PurePath("/admin"))
    >>> registry.register_implementation(Greeting, EmployeeGreeting, resource=EmployeeContext)
    >>> # Standard svcs.Registry methods still work
    >>> registry.register_value(Database, Database(host="localhost"))
    >>> # Use HopscotchContainer for injection with locator-based resolution
    >>> container = HopscotchContainer(registry)
    >>> service = container.inject(WelcomeService)  # Resolves via locator
"""

from collections.abc import Callable
from pathlib import PurePath
from typing import Any

import attrs
import svcs

from svcs_di._container_mixin import InjectorMixin
from svcs_di.injectors.hopscotch import HopscotchAsyncInjector, HopscotchInjector
from svcs_di.injectors.locator import Implementation, ServiceLocator


@attrs.define
class HopscotchRegistry(svcs.Registry):
    """
    A registry that extends svcs.Registry with integrated ServiceLocator management.

    HopscotchRegistry automatically manages an internal ServiceLocator for
    multi-implementation service resolution with resource and location-based
    selection. When implementations are registered via register_implementation(),
    the internal locator is updated and re-registered as a value service.

    Attributes:
        _locator: The internal ServiceLocator instance (automatically created).
            Access via the `locator` property for read-only access.

    The registry inherits all standard svcs.Registry methods (register_factory,
    register_value, etc.) unchanged.

    Example:
        >>> from pathlib import PurePath
        >>> registry = HopscotchRegistry()
        >>> # Register multi-implementation service with context
        >>> registry.register_implementation(Greeting, DefaultGreeting)
        >>> registry.register_implementation(Greeting, AdminGreeting, location=PurePath("/admin"))
        >>> # Access the locator
        >>> locator = registry.locator
        >>> impl = locator.get_implementation(Greeting, location=PurePath("/admin"))
        >>> # Standard registry methods still work
        >>> registry.register_value(Config, Config())
    """

    _locator: ServiceLocator = attrs.field(factory=ServiceLocator, init=False)
    _container_setup_funcs: list[Callable[[Any], None]] = attrs.field(
        factory=list, init=False
    )
    _metadata: dict[str, Any] = attrs.field(factory=dict, init=False)

    @property
    def locator(self) -> ServiceLocator:
        """
        Read-only access to the internal ServiceLocator.

        Returns:
            The internal ServiceLocator instance containing all registered
            implementations.

        Example:
            >>> registry = HopscotchRegistry()
            >>> registry.register_implementation(Greeting, DefaultGreeting)
            >>> locator = registry.locator
            >>> impl = locator.get_implementation(Greeting)
        """
        return self._locator

    @property
    def container_setup_funcs(self) -> list[Callable[[Any], None]]:
        """
        Read-only access to container setup functions.

        These functions are discovered by scan() when a module defines a
        `svcs_container` function. They are called for each new HopscotchContainer
        instance during __attrs_post_init__.

        Returns:
            List of callable setup functions that take a container as argument.
        """
        return self._container_setup_funcs

    def metadata[T](self, key: str, default_factory: Callable[[], T]) -> T:
        """
        Get metadata by key, creating with default_factory if missing.

        This method provides a generic extension point for storing arbitrary
        metadata on the registry. Each caller defines their own key namespace
        and default factory for the data structure they need.

        Args:
            key: Unique key for the metadata (e.g., "tdom.middleware_types")
            default_factory: Callable that returns a new instance if key not found
                (e.g., list, dict, set)

        Returns:
            The metadata value for the key, creating it if not present.

        Example:
            >>> registry = HopscotchRegistry()
            >>> # Get or create a list for middleware types
            >>> middleware_types = registry.metadata("myapp.middleware", list)
            >>> middleware_types.append(LoggingMiddleware)
            >>> # Get or create a dict for component middleware
            >>> component_mw = registry.metadata("myapp.component_mw", dict)
            >>> component_mw[Button] = {"pre": [logging_mw]}
        """
        return self._metadata.setdefault(key, default_factory())

    def register_implementation(
        self,
        service_type: type,
        implementation: Implementation,
        *,
        resource: type | None = None,
        location: PurePath | None = None,
    ) -> None:
        """
        Register an implementation with optional resource and location context.

        This method registers the implementation to the internal ServiceLocator
        and then re-registers the updated locator as a value service so it can
        be resolved from containers.

        Args:
            service_type: The service type (interface/protocol) to register for.
            implementation: The implementation class or callable factory function.
                For classes, instances are created by calling the class.
                For functions, instances are created by calling the function.
            resource: Optional resource type for resource-based resolution.
                When specified, this implementation is only selected when the
                resource type matches.
            location: Optional location (PurePath) for location-based resolution.
                When specified, this implementation is only available at this
                location or its children (hierarchical matching).

        Example:
            >>> from pathlib import PurePath
            >>> registry = HopscotchRegistry()
            >>> # Default implementation (no context)
            >>> registry.register_implementation(Greeting, DefaultGreeting)
            >>> # Function factory
            >>> def create_greeting() -> Greeting:
            ...     return Greeting("Hello from factory")
            >>> registry.register_implementation(Greeting, create_greeting)
            >>> # Resource-specific implementation
            >>> registry.register_implementation(Greeting, EmployeeGreeting, resource=EmployeeContext)
            >>> # Location-specific implementation
            >>> registry.register_implementation(Greeting, AdminGreeting, location=PurePath("/admin"))
            >>> # Combined resource + location
            >>> registry.register_implementation(
            ...     Greeting, VIPGreeting,
            ...     resource=VIPContext,
            ...     location=PurePath("/premium")
            ... )

        Note:
            The internal locator uses an immutable update pattern - each call
            to register() returns a new ServiceLocator instance. This method
            handles the update internally and re-registers the locator as a
            value service automatically.
        """
        # Update the internal locator (immutable update pattern)
        self._locator = self._locator.register(
            service_type, implementation, resource=resource, location=location
        )

        # Re-register the updated locator as a value service
        self.register_value(ServiceLocator, self._locator)


@attrs.define
class HopscotchContainer(InjectorMixin, svcs.Container):
    """
    A container that extends svcs.Container with HopscotchInjector-based injection.

    HopscotchContainer adds inject() and ainject() methods that use HopscotchInjector
    for dependency resolution with ServiceLocator-based multi-implementation support.

    Attributes:
        registry: The svcs.Registry instance (inherited from svcs.Container).
        resource: Optional resource instance for resource-based resolution.
            When provided, the resource is automatically registered as a local value
            under both the Resource marker type and its concrete type, and its type
            is used for ServiceLocator matching.
        location: Optional location (PurePath) for location-based resolution.
            When provided, the location is automatically registered as a local value
            under the Location type.
        injector: The synchronous injector class to use for inject().
            Defaults to HopscotchInjector.
        async_injector: The asynchronous injector class to use for ainject().
            Defaults to HopscotchAsyncInjector.

    Example:
        >>> registry = HopscotchRegistry()
        >>> registry.register_implementation(Greeting, DefaultGreeting)
        >>> registry.register_implementation(Greeting, AdminGreeting, location=PurePath("/admin"))
        >>> registry.register_implementation(Greeting, EmployeeGreeting, resource=EmployeeContext)
        >>> # New API: pass resource and location to container
        >>> container = HopscotchContainer(registry, resource=EmployeeContext(), location=PurePath("/admin"))
        >>> service = container.inject(WelcomeService)  # Uses EmployeeContext for matching
        >>> # Services can inject Resource or Location
        >>> # resource: Inject[Resource]  # Gets EmployeeContext instance (generic)
        >>> # resource: Inject[EmployeeContext]  # Gets EmployeeContext instance (type-safe)
        >>> # location: Inject[Location]  # Gets PurePath("/admin")
    """

    resource: Any = attrs.field(default=None, kw_only=True)
    location: PurePath | None = attrs.field(default=None, kw_only=True)
    injector: type[HopscotchInjector] | None = attrs.field(
        default=HopscotchInjector,
        kw_only=True,
    )
    async_injector: type[HopscotchAsyncInjector] | None = attrs.field(
        default=HopscotchAsyncInjector,
        kw_only=True,
    )

    def __attrs_post_init__(self) -> None:
        """Auto-register location and invoke container setup functions."""
        from svcs_di.injectors.locator import Location

        if self.location is not None:
            self.register_local_value(Location, self.location)

        # Invoke container setup functions if registry is HopscotchRegistry
        if isinstance(self.registry, HopscotchRegistry):
            for setup_func in self.registry.container_setup_funcs:
                setup_func(self)

    def inject[T](
        self, svc_type: type[T], /, resource: type | None = None, **kwargs: Any
    ) -> T:
        """
        Resolve a service using HopscotchInjector with optional resource resolution.

        This method uses the configured injector to resolve dependencies with
        ServiceLocator-based multi-implementation support.

        Args:
            svc_type: The service type to resolve (positional-only).
            resource: Optional resource type for resource-based resolution.
                When provided, overrides the container's stored resource for
                ServiceLocator matching. If not provided and the container has
                a stored resource, its type is used automatically.
            **kwargs: Keyword arguments to override injected dependencies.

        Returns:
            The resolved service instance.

        Raises:
            ValueError: If no injector is configured.

        Examples:
            With container resource (automatic type derivation)::

                container = HopscotchContainer(registry, resource=EmployeeContext())
                service = container.inject(WelcomeService)  # Uses EmployeeContext

            With explicit resource override::

                service = container.inject(WelcomeService, resource=VIPContext)

            With kwargs override::

                service = container.inject(WelcomeService, greeting=mock_greeting)

        See Also:
            HopscotchInjector: For details on locator-based resolution and precedence.
        """
        effective_resource = resource
        if effective_resource is None and self.resource is not None:
            effective_resource = type(self.resource)
        return self._do_inject(
            svc_type,
            {"resource": effective_resource, "location": self.location},
            **kwargs,
        )

    async def ainject[T](
        self, svc_type: type[T], /, resource: type | None = None, **kwargs: Any
    ) -> T:
        """
        Asynchronously resolve a service using HopscotchAsyncInjector.

        This method uses the configured async_injector to resolve dependencies with
        ServiceLocator-based multi-implementation support.

        Args:
            svc_type: The service type to resolve (positional-only).
            resource: Optional resource type for resource-based resolution.
                When provided, overrides the container's stored resource for
                ServiceLocator matching. If not provided and the container has
                a stored resource, its type is used automatically.
            **kwargs: Keyword arguments to override injected dependencies.

        Returns:
            The resolved service instance.

        Raises:
            ValueError: If no async_injector is configured.

        Examples:
            With container resource (automatic type derivation)::

                container = HopscotchContainer(registry, resource=EmployeeContext())
                service = await container.ainject(WelcomeService)  # Uses EmployeeContext

            With explicit resource override::

                service = await container.ainject(WelcomeService, resource=VIPContext)

            With kwargs override::

                service = await container.ainject(WelcomeService, greeting=mock_greeting)

        See Also:
            HopscotchAsyncInjector: For details on async locator-based resolution.
        """
        effective_resource = resource
        if effective_resource is None and self.resource is not None:
            effective_resource = type(self.resource)
        return await self._do_ainject(
            svc_type,
            {"resource": effective_resource, "location": self.location},
            **kwargs,
        )
