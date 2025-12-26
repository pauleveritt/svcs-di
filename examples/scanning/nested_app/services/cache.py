"""Cache service in services subdirectory."""

from dataclasses import dataclass

from svcs_di.injectors.decorators import injectable


@injectable
@dataclass
class CacheService:
    """Cache service found in services/cache.py."""

    ttl: int = 300
    max_size: int = 1000

    def get(self, key: str) -> str | None:
        """Simulate cache get."""
        return f"cached_value_for_{key}"
