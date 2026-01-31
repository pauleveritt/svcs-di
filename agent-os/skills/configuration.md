---
description:
  Configuration management standards for Python applications. Use this when
  setting up application settings, environment variables, or config hierarchies.
---

# Configuration Standards

## Settings Pattern with Frozen Dataclasses

Use frozen dataclasses for immutable, type-safe configuration:

```python
from dataclasses import dataclass
import os

@dataclass(frozen=True)
class DatabaseSettings:
    """Database connection settings."""
    host: str
    port: int
    name: str
    user: str
    password: str

    @classmethod
    def from_env(cls, prefix: str = "DB") -> "DatabaseSettings":
        return cls(
            host=os.environ.get(f"{prefix}_HOST", "localhost"),
            port=int(os.environ.get(f"{prefix}_PORT", "5432")),
            name=os.environ[f"{prefix}_NAME"],  # Required
            user=os.environ[f"{prefix}_USER"],  # Required
            password=os.environ[f"{prefix}_PASSWORD"],  # Required
        )

@dataclass(frozen=True)
class AppSettings:
    """Application settings composed of subsections."""
    debug: bool
    secret_key: str
    database: DatabaseSettings

    @classmethod
    def from_env(cls) -> "AppSettings":
        return cls(
            debug=os.environ.get("APP_DEBUG", "false").lower() == "true",
            secret_key=os.environ["APP_SECRET_KEY"],
            database=DatabaseSettings.from_env(),
        )
```

## Environment Variable Conventions

Use consistent prefixes for environment variables:

| Prefix | Purpose | Example |
|--------|---------|---------|
| `APP_` | Application settings | `APP_DEBUG`, `APP_SECRET_KEY` |
| `DB_` | Database settings | `DB_HOST`, `DB_PORT`, `DB_NAME` |
| `CACHE_` | Cache settings | `CACHE_URL`, `CACHE_TTL` |
| `LOG_` | Logging settings | `LOG_LEVEL`, `LOG_FORMAT` |
| `{SERVICE}_` | External services | `STRIPE_API_KEY`, `AWS_REGION` |

### Naming Rules

- Use `SCREAMING_SNAKE_CASE`
- Use descriptive, unambiguous names
- Group related settings with common prefix
- Use `_URL` suffix for connection strings
- Use `_KEY` or `_SECRET` suffix for credentials

## Configuration Hierarchy

Load configuration in order of precedence (later overrides earlier):

1. **Defaults** - Hardcoded sensible defaults
2. **Config files** - `config.toml` or `settings.yaml`
3. **Environment variables** - `APP_*` variables
4. **Command-line arguments** - Runtime overrides

```python
@dataclass(frozen=True)
class Settings:
    host: str = "localhost"
    port: int = 8000
    debug: bool = False

    @classmethod
    def load(cls, config_path: str | None = None) -> "Settings":
        # Start with defaults (from dataclass)
        values: dict[str, str | int | bool] = {}

        # Load from config file if provided
        if config_path and Path(config_path).exists():
            values.update(load_toml(config_path))

        # Override with environment variables
        if host := os.environ.get("APP_HOST"):
            values["host"] = host
        if port := os.environ.get("APP_PORT"):
            values["port"] = int(port)
        if debug := os.environ.get("APP_DEBUG"):
            values["debug"] = debug.lower() == "true"

        return cls(**values)
```

## Integration with svcs

Register settings as a service for dependency injection:

```python
import svcs
from svcs_di import Inject, auto

@dataclass(frozen=True)
class Settings:
    debug: bool
    database_url: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            debug=os.environ.get("APP_DEBUG", "false").lower() == "true",
            database_url=os.environ["DATABASE_URL"],
        )

@dataclass
class DatabaseService:
    """Service that depends on settings."""
    settings: Inject[Settings]

    def connect(self) -> Connection:
        return create_connection(self.settings.database_url)

# Registration
registry = svcs.Registry()
registry.register_value(Settings, Settings.from_env())
registry.register_factory(DatabaseService, auto(DatabaseService))
```

## Validation

Validate configuration at startup:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    port: int
    database_url: str
    log_level: str

    def __post_init__(self) -> None:
        if not 1 <= self.port <= 65535:
            raise ValueError(f"Invalid port: {self.port}")

        if not self.database_url.startswith(("postgresql://", "sqlite://")):
            raise ValueError(f"Invalid database URL scheme: {self.database_url}")

        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {self.log_level}")
```

## Environment-Specific Configuration

```python
from enum import Enum

class Environment(Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"

@dataclass(frozen=True)
class Settings:
    environment: Environment
    debug: bool
    log_level: str

    @classmethod
    def for_environment(cls, env: Environment) -> "Settings":
        match env:
            case Environment.DEVELOPMENT:
                return cls(environment=env, debug=True, log_level="DEBUG")
            case Environment.TESTING:
                return cls(environment=env, debug=True, log_level="WARNING")
            case Environment.PRODUCTION:
                return cls(environment=env, debug=False, log_level="INFO")

    @classmethod
    def from_env(cls) -> "Settings":
        env_str = os.environ.get("APP_ENVIRONMENT", "development")
        env = Environment(env_str)
        base = cls.for_environment(env)

        # Allow environment variables to override
        return cls(
            environment=env,
            debug=os.environ.get("APP_DEBUG", str(base.debug)).lower() == "true",
            log_level=os.environ.get("LOG_LEVEL", base.log_level),
        )
```

## Secrets Management

Never commit secrets to version control:

```python
@dataclass(frozen=True)
class Secrets:
    """Secrets loaded from secure sources."""
    api_key: str
    database_password: str

    @classmethod
    def from_env(cls) -> "Secrets":
        """Load from environment (set by deployment)."""
        return cls(
            api_key=os.environ["API_KEY"],
            database_password=os.environ["DB_PASSWORD"],
        )

    def __repr__(self) -> str:
        """Never expose secret values in repr."""
        return "Secrets(api_key=***, database_password=***)"
```

## Anti-Patterns

- **Mutable settings**: Using non-frozen dataclasses or dicts for configuration
- **Global state**: Modifying settings at runtime
- **Hardcoded secrets**: Committing API keys or passwords to version control
- **Missing validation**: Not validating configuration at startup
- **Scattered env access**: Calling `os.environ` throughout the codebase
- **No defaults**: Requiring all settings to be explicitly set
- **Inconsistent naming**: Mixing naming conventions for environment variables
- **Late failure**: Discovering missing config during request handling instead of startup

## Related Skills

- [svcs](svcs.md) - Dependency injection for settings
- [error-handling](error-handling.md) - Configuration validation errors
- [logging](logging.md) - Configuring log levels
- [testing](testing/testing.md) - Testing with different configurations
