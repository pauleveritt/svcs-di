"""
Decorator-based service registration for svcs-di.

Provides @injectable decorator for marking classes for auto-discovery during
package scanning. The decorator stores metadata on classes without performing
registration, which is deferred to the scan() function.

Usage::

    @injectable
    class Database:
        host: str = "localhost"

    @injectable(resource=CustomerContext)
    class CustomerGreeting(Greeting):
        salutation: str = "Hello"

See examples/scanning/ for complete examples.
"""

from typing import Optional, overload

__all__ = ["injectable"]


def _mark_injectable(target: type, resource: Optional[type] = None) -> type:
    """Store metadata on target class for scan() to discover later."""
    target.__injectable_metadata__ = {"resource": resource}  # type: ignore[attr-defined]
    return target


class _InjectableDecorator:
    """Supports both @injectable and @injectable(resource=X) syntax."""

    @overload
    def __call__(self, target: type) -> type: ...

    @overload
    def __call__(self, *, resource: Optional[type] = None) -> type: ...

    def __call__(
        self, target: type | None = None, *, resource: Optional[type] = None
    ) -> type:
        # Bare decorator: @injectable
        if target is not None:
            return _mark_injectable(target, resource=None)

        # Called decorator: @injectable() or @injectable(resource=X)
        def decorator(cls: type) -> type:
            return _mark_injectable(cls, resource=resource)

        return decorator  # type: ignore[return-value]


injectable = _InjectableDecorator()
