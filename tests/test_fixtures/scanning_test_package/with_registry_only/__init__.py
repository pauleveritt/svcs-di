"""Test package with only svcs_registry function."""

from dataclasses import dataclass

from svcs_di.injectors.decorators import injectable

# Track calls for testing
registry_only_calls: list[str] = []


@injectable
@dataclass
class RegistryOnlyService:
    """Service defined alongside registry-only setup."""

    name: str = "RegistryOnlyService"


def svcs_registry(registry) -> None:
    """Registry setup function - called during scan()."""
    registry_only_calls.append("registry_only svcs_registry called")
    registry.register_value(str, "registry_only_value")
