"""Setup functions example.

Demonstrates convention-based setup functions for registry and container configuration:
- svcs_registry(registry) - Called during scan() for registry-time setup
- svcs_container(container) - Called when HopscotchContainer is created

These functions follow a convention-over-configuration pattern, similar to
pytest fixtures or Django settings.
"""

from dataclasses import dataclass

from svcs_di import Inject
from svcs_di.injectors import HopscotchContainer, HopscotchRegistry
from svcs_di.injectors.decorators import injectable
from svcs_di.injectors.scanning import scan


# =============================================================================
# Service definitions with @injectable
# =============================================================================


@injectable
@dataclass
class Config:
    """Application configuration."""

    debug: bool = False
    database_url: str = "sqlite:///:memory:"


@injectable
@dataclass
class Logger:
    """Simple logger service."""

    level: str = "INFO"

    def log(self, message: str) -> str:
        return f"[{self.level}] {message}"


@injectable
@dataclass
class Database:
    """Database service that depends on config and logger."""

    config: Inject[Config]
    logger: Inject[Logger]

    def connect(self) -> str:
        self.logger.log(f"Connecting to {self.config.database_url}")
        return f"Connected to {self.config.database_url}"


# =============================================================================
# Convention-based setup functions
# =============================================================================


def svcs_registry(registry: HopscotchRegistry) -> None:
    """
    Registry setup function - called during scan().

    Use this for:
    - Registering singleton services
    - Setting up default implementations
    - Configuring the ServiceLocator
    """
    # Register a global configuration value
    registry.register_value(str, "Application v1.0")
    print("svcs_registry: Registered application version")


def svcs_container(container: HopscotchContainer) -> None:
    """
    Container setup function - called for each new container.

    Use this for:
    - Per-request configuration
    - Registering request-scoped values
    - Setting up context-specific services
    """
    # Register a request-specific value
    import uuid

    request_id = str(uuid.uuid4())[:8]
    container.register_local_value(int, hash(request_id) % 1000)
    print(f"svcs_container: Set up request {request_id}")


# =============================================================================
# Main example
# =============================================================================


def main() -> None:
    """Demonstrate setup functions workflow."""
    print("=" * 60)
    print("Setup Functions Example")
    print("=" * 60)

    # Create registry and scan
    registry = HopscotchRegistry()

    print("\n1. Scanning with scan()...")
    scan(
        registry,
        locals_dict={
            "Config": Config,
            "Logger": Logger,
            "Database": Database,
            "svcs_registry": svcs_registry,
            "svcs_container": svcs_container,
        },
    )

    # Note: When using locals_dict, convention functions are NOT called.
    # They're only discovered from actual module scanning.
    # For this example, we'll call them manually or use package scanning.

    # For demonstration, manually call the registry setup
    svcs_registry(registry)

    print("\n2. Creating first container...")
    container1 = HopscotchContainer(registry)
    # Manually invoke for demo (normally done by HopscotchContainer)
    svcs_container(container1)

    print("\n3. Creating second container...")
    container2 = HopscotchContainer(registry)
    svcs_container(container2)

    print("\n4. Using services from container 1...")
    db1 = container1.inject(Database)
    result1 = db1.connect()
    print(f"   Result: {result1}")

    print("\n5. Using services from container 2...")
    db2 = container2.inject(Database)
    result2 = db2.connect()
    print(f"   Result: {result2}")

    # Each container has its own request ID
    print(f"\n6. Container 1 request ID hash: {container1.get(int)}")
    print(f"   Container 2 request ID hash: {container2.get(int)}")

    # But they share the same registry-level value
    print(f"\n7. Shared app version: {container1.get(str)}")

    print("\n" + "=" * 60)
    print("Done!")


if __name__ == "__main__":
    main()
