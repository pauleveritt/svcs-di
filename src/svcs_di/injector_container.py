"""
InjectorContainer: A container with integrated dependency injection support.

This module provides InjectorContainer, which extends svcs.Container to provide
dependency injection capabilities via inject() and ainject() methods that support
kwargs for service resolution.

The InjectorContainer serves as a drop-in replacement for svcs.Container with
additional inject() and ainject() methods that use KeywordInjector for
dependency resolution with kwargs support.

Example:
    >>> registry = svcs.Registry()
    >>> container = InjectorContainer(registry)
    >>> # Use like a normal svcs.Container
    >>> service = container.get(MyService)
    >>> # Or use inject() with kwargs override
    >>> service = container.inject(MyService, some_dep=override_value)
"""

from typing import Any

import attrs
import svcs

from svcs_di.auto import AsyncInjector, Injector
from svcs_di.injectors.keyword import KeywordAsyncInjector, KeywordInjector


@attrs.define
class InjectorContainer(svcs.Container):
    """
    A container that extends svcs.Container with dependency injection support.

    InjectorContainer adds inject() and ainject() methods that allow passing
    kwargs when resolving services, enabling override of injected dependencies
    at resolution time.

    Attributes:
        registry: The svcs.Registry instance (inherited from svcs.Container).
        injector: The synchronous injector class to use for inject().
            Defaults to KeywordInjector.
        async_injector: The asynchronous injector class to use for ainject().
            Defaults to KeywordAsyncInjector.

    Example:
        >>> registry = svcs.Registry()
        >>> container = InjectorContainer(registry)
        >>> # Standard svcs.Container behavior
        >>> service = container.get(MyService)
        >>> # With kwargs override via inject()
        >>> service = container.inject(MyService, dependency=mock_dep)
    """

    injector: type[Injector] | None = attrs.field(
        default=KeywordInjector,
        kw_only=True,
    )
    async_injector: type[AsyncInjector] | None = attrs.field(
        default=KeywordAsyncInjector,
        kw_only=True,
    )

    def inject[T](self, svc_type: type[T], /, **kwargs: Any) -> T:
        """
        Resolve a service using the injector with optional kwargs override.

        This method uses the configured injector to resolve dependencies with
        three-tier precedence: kwargs > container > defaults.

        Args:
            svc_type: The service type to resolve (positional-only).
            **kwargs: Keyword arguments to override injected dependencies.

        Returns:
            The resolved service instance.

        Raises:
            ValueError: If no injector is configured.

        Examples:
            Basic injection (uses container values and defaults):
                >>> service = container.inject(MyService)

            With kwargs override:
                >>> service = container.inject(MyService, dependency=mock_dep)

        See Also:
            KeywordInjector: For details on three-tier kwargs override behavior.
        """
        if self.injector is None:
            raise ValueError("Cannot inject without an injector configured")

        return self.injector(container=self)(svc_type, **kwargs)

    async def ainject[T](self, svc_type: type[T], /, **kwargs: Any) -> T:
        """
        Asynchronously resolve a service using the async injector with optional kwargs.

        This method uses the configured async_injector to resolve dependencies with
        three-tier precedence: kwargs > container > defaults.

        Args:
            svc_type: The service type to resolve (positional-only).
            **kwargs: Keyword arguments to override injected dependencies.

        Returns:
            The resolved service instance.

        Raises:
            ValueError: If no async_injector is configured.

        Examples:
            Basic async injection:
                >>> service = await container.ainject(MyService)

            With kwargs override:
                >>> service = await container.ainject(MyService, dependency=mock_dep)

        See Also:
            KeywordAsyncInjector: For details on async three-tier kwargs override behavior.
        """
        if self.async_injector is None:
            raise ValueError("Cannot inject without an injector configured")

        return await self.async_injector(container=self)(svc_type, **kwargs)
