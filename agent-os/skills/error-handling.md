---
description:
  Error handling standards for Python applications. Use this when designing
  exception hierarchies, implementing error boundaries, or handling failures.
---

# Error Handling Standards

## Custom Exception Design

Use dataclasses for structured exceptions with context:

```python
from dataclasses import dataclass

@dataclass
class ValidationError(Exception):
    """Validation failed with specific field information."""
    field: str
    value: str
    reason: str

    def __str__(self) -> str:
        return f"Validation failed for {self.field}: {self.reason} (got: {self.value!r})"
```

### Exception with Multiple Errors

```python
@dataclass
class BulkValidationError(Exception):
    """Multiple validation errors occurred."""
    errors: list[ValidationError]

    def __str__(self) -> str:
        return f"{len(self.errors)} validation errors occurred"
```

## Exception Hierarchy Patterns

### Domain-Specific Hierarchy

```python
class AppError(Exception):
    """Base exception for application errors."""

class NotFoundError(AppError):
    """Resource not found."""

class ConflictError(AppError):
    """Resource conflict (duplicate, version mismatch)."""

class AuthorizationError(AppError):
    """User lacks permission for this action."""
```

### Service Layer Exceptions

```python
@dataclass
class ServiceError(Exception):
    """Base for service layer errors."""
    operation: str
    detail: str | None = None

@dataclass
class ExternalServiceError(ServiceError):
    """External service call failed."""
    service_name: str
    status_code: int | None = None
```

## Pattern Matching with ExceptionGroup

Use `except*` for handling multiple exception types:

```python
async def process_batch(items: list[Item]) -> list[Result]:
    """Process items, collecting all errors."""
    results = []
    errors = []

    for item in items:
        try:
            results.append(await process_item(item))
        except ValidationError as e:
            errors.append(e)
        except ExternalServiceError as e:
            errors.append(e)

    if errors:
        raise ExceptionGroup("Batch processing failed", errors)

    return results
```

### Handling ExceptionGroup

```python
try:
    results = await process_batch(items)
except* ValidationError as eg:
    # Handle all ValidationErrors
    for exc in eg.exceptions:
        log.warning(f"Validation: {exc.field} - {exc.reason}")
except* ExternalServiceError as eg:
    # Handle all ExternalServiceErrors
    for exc in eg.exceptions:
        log.error(f"Service {exc.service_name} failed")
```

## Service Layer Error Boundaries

### Boundary Pattern

Convert low-level exceptions to domain exceptions at service boundaries:

```python
from dataclasses import dataclass

@dataclass
class UserService:
    db: DatabaseService

    def get_user(self, user_id: str) -> User:
        try:
            row = self.db.query_one("SELECT * FROM users WHERE id = ?", user_id)
        except DatabaseError as e:
            raise ServiceError(operation="get_user", detail=str(e)) from e

        if row is None:
            raise NotFoundError(f"User {user_id} not found")

        return User.from_row(row)
```

### HTTP Error Mapping

```python
def handle_service_error(error: AppError) -> tuple[int, dict]:
    """Map domain errors to HTTP responses."""
    match error:
        case NotFoundError():
            return 404, {"error": str(error)}
        case ValidationError():
            return 422, {"error": str(error), "field": error.field}
        case AuthorizationError():
            return 403, {"error": str(error)}
        case ConflictError():
            return 409, {"error": str(error)}
        case _:
            return 500, {"error": "Internal server error"}
```

## Error Context and Chaining

Always chain exceptions to preserve context:

```python
try:
    data = parse_config(path)
except ParseError as e:
    raise ConfigurationError(f"Invalid config at {path}") from e
```

### Adding Context with Notes

```python
try:
    result = process(data)
except ProcessingError as e:
    e.add_note(f"Processing item {item_id}")
    e.add_note(f"Input data: {data!r}")
    raise
```

## Result Type Pattern

For operations that can fail predictably, use Result types:

```python
from dataclasses import dataclass

@dataclass
class Ok[T]:
    value: T

@dataclass
class Err[E]:
    error: E

type Result[T, E] = Ok[T] | Err[E]

def parse_int(s: str) -> Result[int, str]:
    try:
        return Ok(int(s))
    except ValueError:
        return Err(f"Cannot parse '{s}' as integer")

# Usage with pattern matching
match parse_int(user_input):
    case Ok(value):
        print(f"Got number: {value}")
    case Err(message):
        print(f"Error: {message}")
```

## Anti-Patterns

- **Bare except**: Using `except:` or `except Exception:` without re-raising
- **Swallowing errors**: Catching and ignoring exceptions silently
- **String exceptions**: Raising strings instead of exception objects
- **Too broad**: Catching `Exception` when specific types are expected
- **No chaining**: Using `raise NewError()` instead of `raise NewError() from e`
- **Logging and raising**: Logging an error then raising it (causes duplicate logs)
- **Business logic in exceptions**: Putting complex logic in exception handlers
- **Mutable exception state**: Exceptions with mutable attributes that change after raise

## Related Skills

- [logging](logging.md) - Logging error context appropriately
- [testing](testing/testing.md) - Testing error handling paths
- [svcs](svcs.md) - Service layer error boundaries
