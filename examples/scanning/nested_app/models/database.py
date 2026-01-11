"""Database implementation in models subdirectory."""

from dataclasses import dataclass

from svcs_di.injectors.decorators import injectable

from ..protocols import Database


@injectable(for_=Database)
@dataclass
class DatabaseConnection:
    """PostgreSQL implementation of Database protocol."""

    host: str = "localhost"
    port: int = 5432
    database: str = "myapp"

    def query(self, sql: str) -> str:
        """Execute a database query."""
        return f"Query result for: {sql}"
