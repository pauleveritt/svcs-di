"""Cache implementation in services subdirectory."""

from dataclasses import dataclass

from svcs_di.injectors.decorators import injectable

from ..protocols import Cache


@injectable(for_=Cache)
@dataclass
class CacheService:
    """Redis implementation of Cache protocol."""

    ttl: int = 300
    max_size: int = 1000

    def get(self, key: str) -> str | None:
        """Get a value from cache."""
        return f"cached_value_for_{key}"
