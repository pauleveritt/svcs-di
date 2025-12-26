"""
svcs-di: Minimal automatic dependency injection helper for svcs.

This package provides a thin layer on top of svcs for automatic dependency
resolution based on type hints, with explicit opt-in via the Injectable[T] marker.

Key exports:
- auto: Factory function generator for automatic dependency injection
- auto_async: Async factory function generator for async dependencies
- Injectable: Type marker for parameters that should be injected from container
- Injector: Protocol defining the injector interface
- AsyncInjector: Protocol defining the async injector interface
- DefaultInjector: Default synchronous injector implementation
- DefaultAsyncInjector: Default asynchronous injector implementation
- KeywordInjector: Injector with kwargs override support (three-tier precedence)
- KeywordAsyncInjector: Async injector with kwargs override support
"""

from svcs_di.auto import (
    AsyncInjector,
    DefaultAsyncInjector,
    DefaultInjector,
    Injectable,
    Injector,
    TypeHintResolutionError,
    auto,
    auto_async,
)
from svcs_di.injectors import KeywordAsyncInjector, KeywordInjector

__all__ = [
    "auto",
    "auto_async",
    "Injectable",
    "Injector",
    "AsyncInjector",
    "DefaultInjector",
    "DefaultAsyncInjector",
    "KeywordInjector",
    "KeywordAsyncInjector",
    "TypeHintResolutionError",
]
