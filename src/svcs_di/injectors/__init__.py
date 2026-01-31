"""
Custom injectors, containers, and related utilities for svcs-di.

Injectors:
- KeywordInjector, KeywordAsyncInjector: Three-tier precedence with kwargs override
- HopscotchInjector, HopscotchAsyncInjector: Multi-implementation resolution

Containers:
- InjectorContainer: Container with inject() method supporting kwargs
- HopscotchRegistry, HopscotchContainer: Pre-wired locator integration

Utilities:
- ServiceLocator, Location: Multi-implementation registration and resolution
- injectable, scan: Auto-discovery of services
"""

from svcs_di.hopscotch_registry import HopscotchContainer, HopscotchRegistry
from svcs_di.injector_container import InjectorContainer
from svcs_di.injectors.decorators import injectable
from svcs_di.injectors.hopscotch import HopscotchAsyncInjector, HopscotchInjector
from svcs_di.injectors.keyword import KeywordAsyncInjector, KeywordInjector
from svcs_di.injectors.locator import Location, ServiceLocator
from svcs_di.injectors.scanning import scan

__all__ = [
    # Injectors
    "KeywordInjector",
    "KeywordAsyncInjector",
    "HopscotchInjector",
    "HopscotchAsyncInjector",
    # Containers
    "InjectorContainer",
    "HopscotchRegistry",
    "HopscotchContainer",
    # Utilities
    "ServiceLocator",
    "Location",
    "injectable",
    "scan",
]
