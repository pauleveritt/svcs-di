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
- KeywordInjector: Injector with kwargs override support (three-tier precedence)
- KeywordAsyncInjector: Async injector with kwargs override support
- InjectorContainer: Container with integrated injector support for kwargs
- HopscotchRegistry: Registry with pre-wired ServiceLocator integration
- HopscotchContainer: Container with HopscotchInjector defaults
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
from svcs_di.hopscotch_registry import HopscotchContainer, HopscotchRegistry
from svcs_di.injector_container import InjectorContainer
from svcs_di.injectors.keyword import KeywordAsyncInjector, KeywordInjector

__all__ = [
    "auto",
    "auto_async",
    "Inject",
    "Injector",
    "AsyncInjector",
    "DefaultInjector",
    "DefaultAsyncInjector",
    "KeywordInjector",
    "KeywordAsyncInjector",
    "InjectorContainer",
    "HopscotchRegistry",
    "HopscotchContainer",
    "InjectionTarget",
    "AsyncInjectionTarget",
]
