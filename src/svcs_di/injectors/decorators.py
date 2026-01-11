"""
Decorator-based service registration for svcs-di.

Provides @injectable decorator for marking classes and functions for auto-discovery
during package scanning. The decorator stores metadata on targets without performing
registration, which is deferred to the scan() function.

Usage::

    @injectable
    @dataclass
    class Database:
        host: str = "localhost"

    @injectable(for_=Greeting, resource=CustomerContext)
    @dataclass
    class CustomerGreeting(Greeting):
        salutation: str = "Hello"

    @injectable(location=PurePath("/admin"))
    class AdminService:
        name: str = "Admin"

    @injectable
    def create_greeting() -> Greeting:
        return Greeting("Hello from factory")

    @injectable(for_=Greeting, resource=CustomerContext)
    def create_customer_greeting() -> Greeting:
        return Greeting("Welcome, customer!")

See examples/scanning/ for complete examples.
"""

import inspect
from collections.abc import Callable
from pathlib import PurePath
from typing import Any, TypedDict, overload


class InjectableMetadata(TypedDict):
    """Metadata stored on classes and functions by the @injectable decorator."""

    for_: type | None
    resource: type | None
    location: PurePath | None


# Attribute name used to store injectable metadata on decorated classes/functions
INJECTABLE_METADATA_ATTR = "__injectable_metadata__"

# Type alias for targets that can be decorated with @injectable
type InjectableTarget = type | Callable[..., Any]

# Type alias for a decorator that wraps an injectable target
type InjectableDecorator = Callable[[InjectableTarget], InjectableTarget]


def _mark_injectable[T: InjectableTarget](
    target: T,
    for_: type | None = None,
    resource: type | None = None,
    location: PurePath | None = None,
) -> T:
    """
    Store metadata on target class or function for scan() to discover later.

    For classes, the metadata is stored directly on the class.
    For functions, the metadata is stored via setattr on the function object.

    Args:
        target: The class or function to mark as injectable
        for_: The service type this implementation provides (optional)
        resource: The resource context for locator-based registration (optional)
        location: The location path for locator-based registration (optional)

    Returns:
        The original target with metadata attached
    """
    if not (inspect.isclass(target) or callable(target)):
        msg = (
            "The @injectable decorator can only be applied to classes or functions. "
            f"{target} is neither a class nor a callable."
        )
        raise TypeError(msg)

    metadata: InjectableMetadata = {
        "for_": for_,
        "resource": resource,
        "location": location,
    }
    setattr(target, INJECTABLE_METADATA_ATTR, metadata)
    return target


class _InjectDecorator:
    """Supports both @injectable and @injectable(for_=X, resource=Y, location=Z) syntax."""

    @overload
    def __call__[T: InjectableTarget](self, target: T) -> T: ...

    @overload
    def __call__(
        self,
        *,
        for_: type | None = None,
        resource: type | None = None,
        location: PurePath | None = None,
    ) -> InjectableDecorator: ...

    def __call__[T: InjectableTarget](
        self,
        target: T | None = None,
        *,
        for_: type | None = None,
        resource: type | None = None,
        location: PurePath | None = None,
    ) -> T | Callable[[T], T]:
        # Bare decorator: @injectable
        if target is not None:
            return _mark_injectable(target, for_=None, resource=None, location=None)

        # Called decorator: @injectable() or @injectable(for_=X, resource=Y, location=Z)
        def decorator(cls: T) -> T:
            return _mark_injectable(
                cls, for_=for_, resource=resource, location=location
            )

        return decorator


injectable = _InjectDecorator()
