"""
svcs-di: Minimal automatic dependency injection helper for svcs.

This package provides a thin layer on top of svcs for automatic dependency
resolution based on type hints, with explicit opt-in via the Inject[T] marker.

Key exports:
- auto: Factory function generator for automatic dependency injection
- auto_async: Async factory function generator for async dependencies
- Inject: Type marker for parameters that should be injected from container
- Injector: Protocol defining the injector interface
- AsyncInjector: Protocol defining the async injector interface
- DefaultInjector: Default synchronous injector implementation
- DefaultAsyncInjector: Default asynchronous injector implementation
- InjectionTarget: Type alias for class or callable targets (type[T] | Callable[..., T])
- AsyncInjectionTarget: Type alias for async targets (type[T] | Callable[..., Awaitable[T]])
"""

from svcs_di.auto import (
    AsyncInjectionTarget,
    AsyncInjector,
    DefaultAsyncInjector,
    DefaultInjector,
    Inject,
    InjectionTarget,
    Injector,
    auto,
    auto_async,
)

__all__ = [
    "auto",
    "auto_async",
    "Inject",
    "Injector",
    "AsyncInjector",
    "DefaultInjector",
    "DefaultAsyncInjector",
    "InjectionTarget",
    "AsyncInjectionTarget",
]
