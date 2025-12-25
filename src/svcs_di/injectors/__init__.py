"""
Specialized injector implementations for svcs-di.

This module exports KeywordInjector and KeywordAsyncInjector which provide
three-tier precedence for dependency injection with kwargs override support.

KeywordInjector provides three-tier precedence:
1. kwargs passed to injector (highest priority)
2. container.get(T) for Injectable[T] fields
3. default values from field definitions (lowest priority)

Note: Helper functions remain in svcs_di.auto to keep DefaultInjector standalone.
KeywordInjector imports helpers from auto.py.
"""

from .keyword import KeywordAsyncInjector, KeywordInjector

__all__ = ["KeywordInjector", "KeywordAsyncInjector"]
