"""
Package scanning functionality for automatic service discovery and registration.

This module provides decorator-based auto-discovery of services via the @injectable
decorator and scan() function. This eliminates manual registration code by automatically
discovering and registering decorated classes.

Usage:
    from svcs_di.injectors.decorators import injectable
    from svcs_di.injectors.scanning import scan

    @injectable
    @dataclass
    class Database:
        host: str = "localhost"

    registry = svcs.Registry()
    scan(registry, "myapp.services")

See examples/scanning/ for complete examples.
"""

import importlib
import logging
import pkgutil
from types import ModuleType
from typing import Any

import svcs

from svcs_di import DefaultInjector
from svcs_di.auto import Injector
from svcs_di.injectors.locator import ServiceLocator

log = logging.getLogger("svcs_di")


def _create_injector_factory(target_class: type) -> Any:
    """Create a factory function for a decorated class."""

    def factory(svcs_container: svcs.Container) -> Any:
        try:
            injector = svcs_container.get(Injector)
        except svcs.exceptions.ServiceNotFoundError:
            injector = DefaultInjector(container=svcs_container)
        return injector(target_class)

    return factory


def _get_or_create_locator(registry: svcs.Registry) -> ServiceLocator:
    """Get existing ServiceLocator from registry or create new one."""
    try:
        temp_container = svcs.Container(registry)
        return temp_container.get(ServiceLocator)
    except svcs.exceptions.ServiceNotFoundError:
        return ServiceLocator()


def _register_decorated_items(
    registry: svcs.Registry,
    decorated_items: list[tuple[type, dict[str, Any]]],
) -> None:
    """Register all decorated items to registry and/or locator."""
    locator = _get_or_create_locator(registry)
    locator_modified = False

    for decorated_class, metadata in decorated_items:
        resource = metadata.get("resource")
        location = metadata.get("location")
        service_type = (
            metadata.get("for_") or decorated_class
        )  # Default to self if None

        # Use ServiceLocator for:
        # 1. Resource-based registrations (resource != None)
        # 2. Location-based registrations (location != None)
        # 3. Multi-implementation scenarios (for_ != None, service_type != decorated_class)
        if (
            resource is not None
            or location is not None
            or service_type != decorated_class
        ):
            locator = locator.register(
                service_type, decorated_class, resource=resource, location=location
            )
            locator_modified = True
        else:
            # Direct registry registration (no resource, no location, no service type override)
            factory = _create_injector_factory(decorated_class)
            registry.register_factory(decorated_class, factory)

    if locator_modified:
        registry.register_value(ServiceLocator, locator)


def _caller_module(level: int = 2) -> ModuleType | None:
    """
    Return the module of the caller at a specific frame level.

    Uses sys._getframe to inspect the call stack and find the module
    that called the current function.

    Args:
        level: Frame level to inspect (2 = caller's caller by default)

    Returns:
        The ModuleType of the caller, or None if in special contexts like doctests
    """
    import sys

    try:
        frame = sys._getframe(level)
        module_globals = frame.f_globals
        module_name = module_globals.get("__name__") or "__main__"

        # Special case: doctest/Sybil execution
        if module_name == "__test__":
            return None

        return sys.modules.get(module_name)
    except (AttributeError, ValueError, KeyError):
        return None


def _caller_package(level: int = 2) -> ModuleType | None:
    """
    Return the package of the caller at a specific frame level.

    This is useful for automatically detecting the calling package when
    scan() is called without arguments, enabling convenient usage like:
        scan(registry)  # Automatically scans the caller's package

    Args:
        level: Frame level to inspect (2 = caller's caller by default)

    Returns:
        The package ModuleType of the caller, or None if detection fails
    """
    module = _caller_module(level + 1)
    if module is None:
        return None

    # Check if this module is itself a package (has __init__.py)
    module_file = getattr(module, "__file__", "")
    if "__init__.py" in module_file or "__init__$py" in module_file:
        return module

    # Not a package, go up one level to get the containing package
    module_name = module.__name__
    if "." in module_name:
        package_name = module_name.rsplit(".", 1)[0]
        import sys

        return sys.modules.get(package_name)

    return module


def _scan_locals(frame_locals: dict[str, Any]) -> list[tuple[type, dict[str, Any]]]:
    """Scan local variables for @injectable decorated classes."""
    return [
        (obj, obj.__injectable_metadata__)
        for obj in frame_locals.values()
        if isinstance(obj, type) and hasattr(obj, "__injectable_metadata__")
    ]


def _import_package(pkg: str) -> ModuleType | None:
    """Import a package by string name, logging warnings on failure."""
    try:
        return importlib.import_module(pkg)
    except ImportError as e:
        log.warning(f"Failed to import package '{pkg}': {e}")
        return None


def _collect_modules_to_scan(
    packages: tuple[str | ModuleType | None, ...],
) -> list[ModuleType]:
    """Collect and import all packages to scan."""
    modules = []
    for pkg in packages:
        match pkg:
            case None:
                continue
            case str():
                if module := _import_package(pkg):
                    modules.append(module)
            case ModuleType():
                modules.append(pkg)
            case _:
                log.warning(
                    f"Invalid package type: {type(pkg)}. Must be str, ModuleType, or None"
                )
    return modules


def _discover_submodules(module: ModuleType) -> list[ModuleType]:
    """Discover all submodules within a package."""
    if not hasattr(module, "__path__"):
        return []

    submodules = []
    try:
        for _, modname, _ in pkgutil.walk_packages(
            path=module.__path__,  # type: ignore[attr-defined]
            prefix=module.__name__ + ".",
            onerror=lambda name: None,
        ):
            if submodule := _import_package(modname):
                submodules.append(submodule)
    except Exception as e:
        log.warning(f"Error walking package '{module.__name__}': {e}")

    return submodules


def _discover_all_modules(modules_to_scan: list[ModuleType]) -> list[ModuleType]:
    """Discover all modules including submodules from packages."""
    discovered = list(modules_to_scan)
    for module in modules_to_scan:
        discovered.extend(_discover_submodules(module))
    return discovered


def _extract_decorated_items(module: ModuleType) -> list[tuple[type, dict[str, Any]]]:
    """Extract @injectable decorated classes from a module."""
    items = []
    for attr_name in dir(module):
        try:
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and hasattr(attr, "__injectable_metadata__"):
                items.append((attr, attr.__injectable_metadata__))
        except (AttributeError, ImportError):
            continue
    return items


def _collect_decorated_items(
    modules: list[ModuleType],
) -> list[tuple[type, dict[str, Any]]]:
    """Collect all @injectable decorated items from modules."""
    return [item for module in modules for item in _extract_decorated_items(module)]


def scan(
    registry: svcs.Registry,
    *packages: str | ModuleType | None,
    locals_dict: dict[str, Any] | None = None,
) -> svcs.Registry:
    """
    Scan packages/modules for @injectable decorated classes and register them.

    Discovers and registers services marked with @injectable decorator. Classes with
    resource or location metadata are registered to ServiceLocator for resource-based or
    location-based resolution. Classes without resource/location metadata are registered
    directly to Registry.

    Args:
        registry: svcs.Registry to register services into
        *packages: Package/module references to scan:
                   - String names: "myapp.services" (auto-imported)
                   - ModuleType objects: myapp.services
                   - None/empty: Auto-detects caller's package
                   - Multiple: scan(registry, "app.models", "app.views")
        locals_dict: Dictionary of local variables to scan (useful for testing)

    Returns:
        The registry instance for method chaining.

    Examples:
        scan(registry)                           # Auto-detect caller's package
        scan(registry, "myapp.services")         # Specific package
        scan(registry, locals_dict=locals())     # Test pattern

    See examples/scanning/ for complete examples.
    """
    # Handle locals_dict scanning for testing
    if locals_dict is not None:
        decorated_items = _scan_locals(locals_dict)
        _register_decorated_items(registry, decorated_items)
        return registry

    # Auto-detect caller's package if not specified
    if not packages or (len(packages) == 1 and packages[0] is None):
        if caller_pkg := _caller_package(level=2):
            packages = (caller_pkg,)
        else:
            log.warning(
                "Could not auto-detect caller's package. No scanning performed."
            )
            return registry

    # Collect, discover, and register
    modules_to_scan = _collect_modules_to_scan(packages)
    discovered_modules = _discover_all_modules(modules_to_scan)
    decorated_items = _collect_decorated_items(discovered_modules)
    _register_decorated_items(registry, decorated_items)
    return registry
