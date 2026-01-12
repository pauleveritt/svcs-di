"""Nested scanning example with protocols.

Shows scanning a nested application structure using protocols.
The scan() function discovers all @injectable(for_=Protocol) classes
in subdirectories recursively.

Directory structure:
    nested_app/
    ├── protocols.py          # Protocol definitions
    ├── services/
    │   ├── cache.py          # CacheService (for_=Cache)
    │   └── email.py          # EmailService (for_=Email)
    ├── models/
    │   └── database.py       # DatabaseConnection (for_=Database)
    └── repositories/
        └── user_repository.py  # SqlUserRepository (for_=UserRepository)
"""

from dataclasses import dataclass

from svcs_di import HopscotchContainer, HopscotchRegistry, Inject
from svcs_di.injectors.scanning import scan


def main():
    """Demonstrate nested package scanning with protocols."""
    # Import protocols inside main() to ensure we get fresh types after any module reloads
    from nested_app.protocols import Email, UserRepository

    @dataclass
    class AppService:
        """Application service that depends on protocols."""

        repo: Inject[UserRepository]
        email: Inject[Email]

        def welcome_user(self, user_id: int) -> str:
            user = self.repo.get_user(user_id)
            self.email.send("admin@example.com", "User Login", f"{user} logged in")
            return user

    # HopscotchRegistry manages protocol-to-implementation mappings
    registry = HopscotchRegistry()

    # scan() discovers all @injectable(for_=Protocol) classes recursively
    scan(registry, "nested_app")

    # HopscotchContainer resolves protocols to implementations
    container = HopscotchContainer(registry)

    # inject() resolves Inject[Protocol] fields to implementations
    service = container.inject(AppService)

    # Verify implementations were found and wired correctly
    assert service.email.smtp_host == "localhost"
    assert service.email.smtp_port == 587
    assert "42" in service.welcome_user(42)

    return service


if __name__ == "__main__":
    print(main())
