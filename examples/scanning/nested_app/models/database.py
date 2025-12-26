"""Database model in models subdirectory."""

from dataclasses import dataclass

from svcs_di.injectors.decorators import injectable


@injectable
@dataclass
class DatabaseConnection:
    """Database connection found in models/database.py."""

    host: str = "localhost"
    port: int = 5432
    database: str = "myapp"

    def query(self, sql: str) -> str:
        """Simulate database query."""
        return f"Query result for: {sql}"
