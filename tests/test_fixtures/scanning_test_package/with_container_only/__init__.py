"""Test package with only svcs_container function."""

from dataclasses import dataclass

from svcs_di.injectors.decorators import injectable

# Track calls for testing
container_only_calls: list[str] = []


@injectable
@dataclass
class ContainerOnlyService:
    """Service defined alongside container-only setup."""

    name: str = "ContainerOnlyService"


def svcs_container(container) -> None:
    """Container setup function - called for each HopscotchContainer."""
    container_only_calls.append("container_only svcs_container called")
    container.register_local_value(int, 42)
