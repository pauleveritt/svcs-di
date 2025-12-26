"""
Specialized injector implementations for svcs-di.

This module exports KeywordInjector and KeywordAsyncInjector which provide
three-tier precedence for dependency injection with kwargs override support.

KeywordInjector provides three-tier precedence:
1. kwargs passed to injector (highest priority)
2. container.get(T) for Injectable[T] fields
3. default values from field definitions (lowest priority)

This module also exports the @injectable decorator for marking classes and
classmethods for auto-discovery during package scanning.

Note: Helper functions remain in svcs_di.auto to keep DefaultInjector standalone.
KeywordInjector imports helpers from auto.py.
"""

from .decorators import injectable
from .keyword import KeywordAsyncInjector, KeywordInjector

__all__ = ["KeywordInjector", "KeywordAsyncInjector", "injectable"]
