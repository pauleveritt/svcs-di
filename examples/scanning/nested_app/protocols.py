"""Protocol definitions for nested_app services."""

from typing import Protocol


class Database(Protocol):
    """Protocol for database services."""

    host: str
    port: int
    database: str

    def query(self, sql: str) -> str: ...


class Cache(Protocol):
    """Protocol for cache services."""

    ttl: int
    max_size: int

    def get(self, key: str) -> str | None: ...


class Email(Protocol):
    """Protocol for email services."""

    smtp_host: str
    smtp_port: int

    def send(self, to: str, subject: str, body: str) -> str: ...


class UserRepository(Protocol):
    """Protocol for user repository services."""

    def get_user(self, user_id: int) -> str: ...
