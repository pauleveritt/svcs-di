"""
Type stub file for auto.py that makes Injectable[T] transparent to type checkers.

This .pyi file provides type checking overrides that tell type checkers Injectable[T]
should be treated as T, while the runtime .py file maintains the actual marker class.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, NamedTuple, Protocol

import svcs

# Type aliases
type SvcsFactory[T] = Callable[..., T]
type AsyncSvcsFactory[T] = Callable[..., Awaitable[T]]

# Injector Protocols
class Injector(Protocol):
    def __call__[T](self, target: type[T], **kwargs: Any) -> T: ...

class AsyncInjector(Protocol):
    async def __call__[T](self, target: type[T], **kwargs: Any) -> T: ...

# For type checkers: Injectable[T] is just T
# This makes type checkers understand that Injectable[Greeting] has all Greeting attributes
type Injectable[T] = T

class FieldInfo(NamedTuple):
    name: str
    type_hint: Any
    is_injectable: bool
    inner_type: type | None
    is_protocol: bool
    has_default: bool
    default_value: Any

def is_injectable(type_hint: Any) -> bool: ...
def extract_inner_type(type_hint: Any) -> type | None: ...
def is_protocol_type(cls: type | Any) -> bool: ...
def _create_field_info(
    name: str,
    type_hint: Any,
    has_default: bool,
    default_value: Any,
) -> FieldInfo: ...
def get_field_infos(target: type | Callable) -> list[FieldInfo]: ...
@dataclass(frozen=True)
class DefaultInjector:
    container: svcs.Container
    def __call__[T](self, target: type[T], **kwargs: Any) -> T: ...

@dataclass(frozen=True)
class DefaultAsyncInjector:
    container: svcs.Container
    async def __call__[T](self, target: type[T], **kwargs: Any) -> T: ...

def auto[T](
    target: type[T],
    *,
    injector_class: type[Injector] | None = None,
) -> SvcsFactory[T]: ...
def auto_async[T](
    target: type[T],
    *,
    injector_class: type[AsyncInjector] | None = None,
) -> AsyncSvcsFactory[T]: ...
def get_injector(container: svcs.Container) -> Injector: ...
def get_async_injector(container: svcs.Container) -> AsyncInjector: ...
