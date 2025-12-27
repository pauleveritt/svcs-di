"""
Decorator-based service registration for svcs-di.

Provides @injectable decorator for marking classes for auto-discovery during
package scanning. The decorator stores metadata on classes without performing
registration, which is deferred to the scan() function.

Usage::

    @injectable
    class Database:
        host: str = "localhost"

    @injectable(for_=Greeting, resource=CustomerContext)
    class CustomerGreeting(Greeting):
        salutation: str = "Hello"

    @injectable(location=PurePath("/admin"))
    class AdminService:
        name: str = "Admin"

See examples/scanning/ for complete examples.
"""

from pathlib import PurePath
from typing import Optional, overload

__all__ = ["injectable"]


def _mark_injectable(
    target: type,
    for_: Optional[type] = None,
    resource: Optional[type] = None,
    location: Optional[PurePath] = None,
) -> type:
    """Store metadata on target class for scan() to discover later."""
    target.__injectable_metadata__ = {  # type: ignore[attr-defined]
        "for_": for_,
        "resource": resource,
        "location": location,
    }
    return target


class _InjectDecorator:
    """Supports both @injectable and @injectable(for_=X, resource=Y, location=Z) syntax."""

    @overload
    def __call__(self, target: type) -> type: ...

    @overload
    def __call__(
        self,
        *,
        for_: Optional[type] = None,
        resource: Optional[type] = None,
        location: Optional[PurePath] = None,
    ) -> type: ...

    def __call__(
        self,
        target: type | None = None,
        *,
        for_: Optional[type] = None,
        resource: Optional[type] = None,
        location: Optional[PurePath] = None,
    ) -> type:
        # Bare decorator: @injectable
        if target is not None:
            return _mark_injectable(target, for_=None, resource=None, location=None)

        # Called decorator: @injectable() or @injectable(for_=X, resource=Y, location=Z)
        def decorator(cls: type) -> type:
            return _mark_injectable(
                cls, for_=for_, resource=resource, location=location
            )

        return decorator  # type: ignore[return-value]


injectable = _InjectDecorator()
