"""
Type stub file for keyword.py with overloaded __call__ signatures.

Uses @overload to enable proper generic type inference when calling
injector(SomeClass) - ty and other type checkers can infer the return type.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, overload

import svcs

@dataclass(frozen=True)
class KeywordInjector:
    """Dependency injector with kwargs override support."""

    container: svcs.Container

    @overload
    def __call__[T](self, target: type[T], **kwargs: Any) -> T: ...
    @overload
    def __call__[T](self, target: Callable[..., T], **kwargs: Any) -> T: ...

@dataclass(frozen=True)
class KeywordAsyncInjector:
    """Async dependency injector with kwargs override support."""

    container: svcs.Container

    @overload
    async def __call__[T](self, target: type[T], **kwargs: Any) -> T: ...
    @overload
    async def __call__[T](
        self, target: Callable[..., Awaitable[T]], **kwargs: Any
    ) -> T: ...
