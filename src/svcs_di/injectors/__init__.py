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
- Resource: Type marker for resource injection (from svcs_di.auto)
- injectable, scan: Auto-discovery of services
"""

# Import Resource from auto (it's a type alias like Inject)
from svcs_di.auto import Resource

# Import injector modules first (these don't depend on hopscotch_registry)
from svcs_di.injector_container import InjectorContainer
from svcs_di.injectors.decorators import injectable
from svcs_di.injectors.hopscotch import HopscotchAsyncInjector, HopscotchInjector
from svcs_di.injectors.keyword import KeywordAsyncInjector, KeywordInjector
from svcs_di.injectors.locator import Location, ServiceLocator
from svcs_di.injectors.scanning import scan

# Import hopscotch_registry AFTER injectors.hopscotch to avoid circular import
# (hopscotch_registry imports from injectors.hopscotch)
from svcs_di.hopscotch_registry import HopscotchContainer, HopscotchRegistry

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
    "Resource",
    "injectable",
    "scan",
]
