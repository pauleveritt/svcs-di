"""Test package with both svcs_registry and svcs_container functions."""

from dataclasses import dataclass

from svcs_di.injectors.decorators import injectable

# Track calls for testing
registry_setup_calls: list[str] = []
container_setup_calls: list[str] = []


@injectable
@dataclass
class SetupService:
    """Service defined alongside setup functions."""

    name: str = "SetupService"


def svcs_registry(registry) -> None:
    """Registry setup function - called during scan()."""
    registry_setup_calls.append("svcs_registry called")
    # Register a value to prove we have access to the registry
    registry.register_value(str, "registry_setup_value")


def svcs_container(container) -> None:
    """Container setup function - called for each HopscotchContainer."""
    container_setup_calls.append("svcs_container called")
    # Register a local value to prove we have access to the container
    container.register_local_value(int, len(container_setup_calls))
