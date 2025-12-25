# svcs-di

Dependency injection using svcs.

## Installation

```bash
$ uv add svcs-di
```

Or using pip:

```bash
$ pip install svcs-di
```

## Requirements

- Python 3.14+

## Quick Start

### Basic Dependency Injection with Injectable Fields

```python
from dataclasses import dataclass
import svcs
from svcs_di.auto import Injectable, auto

@dataclass
class Database:
    host: str = "localhost"

@dataclass
class UserService:
    db: Injectable[Database]  # Automatically injected
    timeout: int = 30

# Setup
registry = svcs.Registry()
registry.register_value(Database, Database(host="prod.example.com"))
registry.register_factory(UserService, auto(UserService))

# Usage
container = svcs.Container(registry)
service = container.get(UserService)
print(service.db.host)  # "prod.example.com"
```

### Custom Construction with `__svcs__`

For complex initialization logic that can't be expressed through simple field injection:

```python
from dataclasses import dataclass
from typing import Self
import svcs
from svcs_di.auto import auto

@dataclass
class ValidatedService:
    name: str
    db: Database  # NOT Injectable - __svcs__ handles construction

    @classmethod
    def __svcs__(cls, container: svcs.Container, **kwargs) -> Self:
        # Custom validation and initialization
        db = container.get(Database)
        name = kwargs.get("name", "default")

        if not name or len(name) < 3:
            raise ValueError("name must be at least 3 characters")

        return cls(name=name, db=db)

# Setup
registry = svcs.Registry()
registry.register_value(Database, Database())
registry.register_factory(ValidatedService, auto(ValidatedService))

# Usage with kwargs override
container = svcs.Container(registry)
service = container.get(ValidatedService)  # Uses default name
```

**When to use `__svcs__`:**
- Custom validation or post-construction setup
- Conditional service resolution based on container contents
- Complex initialization requiring multiple dependencies
- Full control over the construction process

**Key differences:**
- **Injectable fields**: Simple, automatic dependency injection
- **`__svcs__` method**: Complete control, replaces all automatic injection

For more examples, see `examples/custom_construction.py`.

## Testing

```bash
# Run tests
pytest

# Run tests in parallel
pytest -n auto

# Run with coverage
pytest --cov=svcs_di
```

## Contributing

Contributions are welcome! Please see the project repository for contribution guidelines.

## License

[License information will be added]
