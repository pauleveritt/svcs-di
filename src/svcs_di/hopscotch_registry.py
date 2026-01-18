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
    Resource and location resolution is delegated to the HopscotchInjector via its
    _get_resource() and _get_location() methods.

    Attributes:
        registry: The svcs.Registry instance (inherited from svcs.Container).
        injector: The synchronous injector class to use for inject().
            Defaults to HopscotchInjector.
        async_injector: The asynchronous injector class to use for ainject().
            Defaults to HopscotchAsyncInjector.

    Note:
        Unlike InjectorContainer, HopscotchContainer does not store a resource
        attribute. Resource resolution is handled dynamically by the injector.

    Example:
        >>> registry = HopscotchRegistry()
        >>> registry.register_implementation(Greeting, DefaultGreeting)
        >>> registry.register_implementation(Greeting, AdminGreeting, location=PurePath("/admin"))
        >>> container = HopscotchContainer(registry)
        >>> # Standard svcs.Container behavior
        >>> locator = container.get(ServiceLocator)
        >>> # With injection via HopscotchInjector
        >>> service = container.inject(WelcomeService)
    """

    injector: type[HopscotchInjector] | None = attrs.field(
        default=HopscotchInjector,
        kw_only=True,
    )
    async_injector: type[HopscotchAsyncInjector] | None = attrs.field(
        default=HopscotchAsyncInjector,
        kw_only=True,
    )

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
                When provided, the injector looks up this type from the container
                to determine which implementation to use.
            **kwargs: Keyword arguments to override injected dependencies.

        Returns:
            The resolved service instance.

        Raises:
            ValueError: If no injector is configured.

        Examples:
            Basic injection (uses locator-based resolution):
                >>> service = container.inject(WelcomeService)  # doctest: +SKIP

            With resource-based resolution:
                >>> service = container.inject(WelcomeService, resource=EmployeeContext)  # doctest: +SKIP

            With kwargs override:
                >>> service = container.inject(WelcomeService, greeting=mock_greeting)  # doctest: +SKIP

        See Also:
            HopscotchInjector: For details on locator-based resolution and precedence.
        """
        return self._do_inject(svc_type, {"resource": resource}, **kwargs)

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
                When provided, the injector looks up this type from the container
                to determine which implementation to use.
            **kwargs: Keyword arguments to override injected dependencies.

        Returns:
            The resolved service instance.

        Raises:
            ValueError: If no async_injector is configured.

        Examples:
            Basic async injection:
                >>> service = await container.ainject(WelcomeService)  # doctest: +SKIP

            With resource-based resolution:
                >>> service = await container.ainject(WelcomeService, resource=EmployeeContext)  # doctest: +SKIP

            With kwargs override:
                >>> service = await container.ainject(WelcomeService, greeting=mock_greeting)  # doctest: +SKIP

        See Also:
            HopscotchAsyncInjector: For details on async locator-based resolution.
        """
        return await self._do_ainject(svc_type, {"resource": resource}, **kwargs)
