# Dataclass Support

This page documents the dataclass features supported by svcs-di's dependency injection system.

## Supported Features

### Basic Fields

Standard dataclass fields with type hints work as expected:

```python
from dataclasses import dataclass
from svcs_di import Inject, auto


@dataclass
class Database:
    host: str = "localhost"
    port: int = 5432


@dataclass
class Service:
    db: Inject[Database]
    timeout: int = 30
```

### Static Defaults with `field(default=...)`

Use `field(default=value)` for static default values. **Callable defaults are stored as-is, not called:**

```python
from dataclasses import dataclass, field
from collections.abc import Callable


def default_handler(x: int) -> int:
    return x * 2


@dataclass
class Config:
    # The function itself is stored, not the result of calling it
    handler: Callable[[int], int] = default_handler

    # Same behavior with field()
    processor: Callable = field(default=default_handler)
```

When resolved, `config.handler` will be the `default_handler` function itself, not `default_handler()`.

### Factory Defaults with `field(default_factory=...)`

Use `field(default_factory=callable)` when you need to create a new instance for each object:

```python
from dataclasses import dataclass, field


@dataclass
class Service:
    # Creates a new empty list for each instance
    items: list = field(default_factory=list)

    # Creates a new dict for each instance
    config: dict = field(default_factory=dict)

    # Custom factory function
    handlers: list = field(default_factory=lambda: ["default"])
```

With `default_factory`, the callable **is** invoked each time an instance is created.

### `Inject[T]` Marker

Mark fields for automatic dependency injection:

```python
from dataclasses import dataclass
from svcs_di import Inject


@dataclass
class Repository:
    db: Inject[Database]  # Resolved from container
    cache: Inject[Cache]  # Resolved from container
    timeout: int = 30  # Static default
```

### `InitVar[T]` and `InitVar[Inject[T]]`

Init-only variables are supported, including injectable ones:

```python
from dataclasses import dataclass, InitVar, field
from svcs_di import Inject


@dataclass
class Service:
    config: InitVar[Config]  # Passed to __post_init__, not stored
    setup_data: InitVar[Inject[SetupData]]  # Injectable init var
    name: str = field(init=False)

    def __post_init__(self, config: Config, setup_data: SetupData):
        self.name = f"{config.env}-{setup_data.version}"
```

### `ClassVar` (Correctly Excluded)

Class variables are automatically excluded from injection:

```python
from dataclasses import dataclass
from typing import ClassVar


@dataclass
class Service:
    db: Inject[Database]
    counter: ClassVar[int] = 0  # Not included in __init__ or injection
```

### `kw_only=True` and `KW_ONLY` Marker

Keyword-only fields are fully supported:

```python
from dataclasses import dataclass, field, KW_ONLY


@dataclass
class Config:
    name: str
    _: KW_ONLY
    timeout: int = 30
    retries: int = 3


# Or using kw_only on individual fields
@dataclass
class Service:
    db: Inject[Database]
    timeout: int = field(default=30, kw_only=True)
```

### `frozen=True` Dataclasses

Immutable dataclasses work correctly:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ImmutableConfig:
    db: Inject[Database]
    name: str = "config"
```

### `slots=True` Dataclasses

Slotted dataclasses are supported:

```python
from dataclasses import dataclass


@dataclass(slots=True)
class SlottedService:
    db: Inject[Database]
    value: int = 42
```

### Inheritance

Dataclass inheritance works as expected:

```python
from dataclasses import dataclass, field


@dataclass
class BaseService:
    db: Inject[Database]
    items: list = field(default_factory=list)


@dataclass
class ChildService(BaseService):
    timeout: int = 30
    extra: dict = field(default_factory=dict)
```

## Field Options Behavior

| Option                     | Behavior                                                    |
|----------------------------|-------------------------------------------------------------|
| `init=False`               | Field is excluded from injection (not passed to `__init__`) |
| `default=value`            | Static default; callable values are stored as-is            |
| `default_factory=callable` | Factory is called to produce value                          |
| `repr`, `compare`, `hash`  | Not relevant to dependency injection                        |
| `metadata`                 | Not currently used by svcs-di                               |

### `init=False` Fields

Fields with `init=False` are not part of `__init__` and therefore not included in injection:

```python
from dataclasses import dataclass, field


@dataclass
class Service:
    db: Inject[Database]
    name: str = "service"
    # This field is computed, not injected
    full_name: str = field(init=False)

    def __post_init__(self):
        self.full_name = f"{self.name}@{self.db.host}"
```

## Examples

### Complete Example with Multiple Features

```python
from dataclasses import dataclass, field, KW_ONLY
from collections.abc import Callable
from typing import ClassVar
import svcs
from svcs_di import Inject, auto


@dataclass
class Database:
    host: str = "localhost"


def default_processor(data: str) -> str:
    return data.upper()


@dataclass(frozen=True)
class Config:
    db: Inject[Database]

    # Static callable default (function stored, not called)
    processor: Callable[[str], str] = default_processor

    # Factory default (creates new list each time)
    handlers: list = field(default_factory=list)

    _: KW_ONLY
    timeout: int = 30

    # Class variable (excluded from injection)
    instance_count: ClassVar[int] = 0


# Register and use
registry = svcs.Registry()
registry.register_value(Database, Database(host="prod"))
registry.register_factory(Config, auto(Config))

container = svcs.Container(registry)
config = container.get(Config)

assert config.db.host == "prod"
assert config.processor is default_processor
assert config.handlers == []
assert config.timeout == 30
```

## Known Limitations

1. **Forward references**: Type hints must be resolvable at registration time. Use string annotations with care.

2. **Generic dataclasses**: Complex generic type parameters may not be fully supported.

3. **`__post_init__` dependencies**: If `__post_init__` needs injected services, use `InitVar[Inject[T]]` to pass them.
