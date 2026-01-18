"""
Mixin providing shared inject/ainject methods for container classes.

This module contains InjectorMixin which provides the core implementation
for inject() and ainject() methods used by InjectorContainer and HopscotchContainer.
"""

from typing import Any

from svcs_di.auto import AsyncInjector, Injector


class InjectorMixin:
    """
    Mixin providing inject/ainject methods for containers.

    This mixin provides _do_inject and _do_ainject methods that implement
    the core injection logic. Subclasses should define their own inject()
    and ainject() methods that delegate to these with appropriate injector_kwargs.

    Attributes:
        injector: The synchronous injector class to use.
        async_injector: The asynchronous injector class to use.
    """

    injector: type[Injector] | None
    async_injector: type[AsyncInjector] | None

    def _do_inject[T](
        self,
        svc_type: type[T],
        injector_kwargs: dict[str, Any],
        **kwargs: Any,
    ) -> T:
        """
        Core sync injection implementation.

        Args:
            svc_type: The service type to resolve.
            injector_kwargs: Kwargs to pass to injector constructor (e.g., resource).
            **kwargs: Kwargs to pass through to the target callable.

        Returns:
            The resolved service instance.

        Raises:
            ValueError: If no injector is configured.
        """
        if self.injector is None:
            raise ValueError("Cannot inject without an injector configured")
        return self.injector(container=self, **injector_kwargs)(svc_type, **kwargs)

    async def _do_ainject[T](
        self,
        svc_type: type[T],
        injector_kwargs: dict[str, Any],
        **kwargs: Any,
    ) -> T:
        """
        Core async injection implementation.

        Args:
            svc_type: The service type to resolve.
            injector_kwargs: Kwargs to pass to injector constructor (e.g., resource).
            **kwargs: Kwargs to pass through to the target callable.

        Returns:
            The resolved service instance.

        Raises:
            ValueError: If no async injector is configured.
        """
        if self.async_injector is None:
            raise ValueError("Cannot inject without an async injector configured")
        return await self.async_injector(container=self, **injector_kwargs)(
            svc_type, **kwargs
        )
