---
description:
  Python development standards for Python 3.14+. Use this when writing Python
  code, reviewing type hints, or setting up Python projects.
---

# Python Development Standards

## Language Features

- **Version**: Python 3.14+ (Aggressively use latest features).
- **Template Strings**: Use PEP 750 t-strings (`t'...'`).
- **Pattern Matching**: Prefer `match`/`case` for complex conditionals.
- **Exception Groups**: Use `except*` when appropriate.
- **Walrus Operator**: Use `:=` for assignment expressions where valuable.

## Type Hinting

- Aggressively use modern Python type hinting.
- Use `type` statements for aliases (e.g., `type Vector = list[float]`).
- Use PEP 604 union syntax (`X | Y`) instead of `Optional` or `Union`.
- Prefer `| None` instead of `Optional`.
- Use built-in generics (e.g., `list[str]` instead of `List[str]`).
- Use PEP 695 syntax for generic functions: `def func[T](x: T) -> T:`.
- Use `TypeGuard` for proper type narrowing:
  - `def _should_process_href(href: str | None) -> TypeGuard[str]:`
- Use `if TYPE_CHECKING:` guards to avoid circular imports in type hints.
- Use `Literal` in cases where we know the list of strings.
- Don't use `getattr` on dataclasses to fix type hinting—trust the dataclass.

### Semantic Type Aliases

Prefer semantically meaningful `type` definitions over inline complex types. This improves readability and documents intent:

```python
# Good: Semantic type aliases convey meaning
type InjectionTarget[T] = type[T] | Callable[..., T]
type ResolutionResult = tuple[bool, Any]
type SvcsFactory[T] = Callable[..., T]

def resolve(target: InjectionTarget[T]) -> ResolutionResult: ...

# Avoid: Inline complex types obscure intent
def resolve(target: type[T] | Callable[..., T]) -> tuple[bool, Any]: ...
```

Benefits:
- **Self-documenting**: The alias name explains the purpose
- **Reusable**: Define once, use consistently throughout codebase
- **Refactorable**: Change the definition in one place
- **Type checker friendly**: Works well with ty and other checkers

## Code Style

- Use absolute imports from the package root.
- Group imports: stdlib -> third-party -> local.
- Prefer `PurePath` and `Path` over `str` for file paths.
- Avoid `from __future__ import annotations` unless specifically required for circular generic references (e.g., `BaseNode["Subject"]`).
- Avoid local imports; use module-level imports unless circular dependencies occur.
- No redundant parentheses on tuples: use `1, 2` instead of `(1, 2)`.

## Import Standards

**Always use module-scope imports with full paths.** This makes dependencies explicit and avoids hidden coupling.

```python
# Good: Full import paths at module scope
from myapp.services.database import DatabaseService
from myapp.models.user import User

# Bad: Relative imports
from .database import DatabaseService
from ..models import User

# Bad: Local imports inside functions
def get_user():
    from myapp.models.user import User  # Don't do this
    return User()
```

Only use local imports when absolutely necessary to break circular dependencies.

## Keyword-Only Arguments

Use `*` to force keyword-only arguments in function signatures. This makes call sites self-documenting and prevents positional argument errors.

```python
# Good: Force keyword-only after *
def create_user(*, name: str, email: str, role: str = "user") -> User:
    ...

# Usage is clear and self-documenting
user = create_user(name="Alice", email="alice@example.com")

# Bad: Positional arguments are ambiguous
def create_user(name: str, email: str, role: str = "user") -> User:
    ...

# Caller must remember argument order
user = create_user("Alice", "alice@example.com")  # Which is name? email?
```

For dataclasses, use `kw_only=True`:

```python
@dataclass(kw_only=True)
class UserConfig:
    name: str
    email: str
    role: str = "user"
```

## Immutability

Embrace immutability for data structures. Use frozen dataclasses and create new instances instead of mutating.

```python
from dataclasses import dataclass, replace

@dataclass(frozen=True)
class User:
    name: str
    email: str
    role: str = "user"

# Good: Create new instance with replace()
user = User(name="Alice", email="alice@example.com")
updated_user = replace(user, role="admin")

# Bad: Mutable dataclass
@dataclass
class User:
    name: str
    email: str
    role: str = "user"

user.role = "admin"  # Mutation can cause subtle bugs
```

Benefits of immutability:
- Thread-safe by default
- Easier to reason about state
- Hashable (can use as dict keys or in sets)
- Prevents accidental modification

## Free Threading (Python 3.14t)

- Use `.python-version` file ending in `t` (e.g., `3.14.2t`) for free-threaded builds.
- Verify free-threaded build:
  ```python
  import sysconfig
  is_free_threaded_build = bool(sysconfig.get_config_var("Py_GIL_DISABLED"))
  ```
- See [Python Free Threading Guide](https://py-free-threading.github.io) for concurrency safety.
- Use `pytest-run-parallel` for testing concurrent safety.

## Packaging & Dependencies

- Source code in `src/` for proper packaging.
- Use `uv add <package>` to add dependencies.
- Use `uv remove <package>` to remove dependencies.
- **Never** mix with pip/poetry unless explicitly needed.

 ## TypeGuard Examples

Use `TypeGuard` for runtime type narrowing:

```python
from typing import TypeGuard

def is_string_list(val: list[object]) -> TypeGuard[list[str]]:
    """Narrow list[object] to list[str] if all elements are strings."""
    return all(isinstance(x, str) for x in val)

def process_items(items: list[object]) -> None:
    if is_string_list(items):
        # Type checker knows items is list[str] here
        for item in items:
            print(item.upper())  # Safe: item is str

def is_valid_config(data: dict[str, object]) -> TypeGuard[dict[str, str | int]]:
    """Validate config has only string/int values."""
    return all(isinstance(v, (str, int)) for v in data.values())
```

### TypeGuard with Optional

```python
def has_value[T](opt: T | None) -> TypeGuard[T]:
    """Narrow T | None to T."""
    return opt is not None

def process_name(name: str | None) -> str:
    if has_value(name):
        return name.title()  # Safe: name is str
    return "Unknown"
```

## Pattern Matching Examples

See [examples/pattern_matching.py](examples/pattern_matching.py) for complete runnable examples.

### Matching Dataclasses

```python
type Shape = Circle | Rectangle

def area(shape: Shape) -> float:
    match shape:
        case Circle(radius=r):
            return 3.14159 * r * r
        case Rectangle(width=w, height=h):
            return w * h
```

### Matching Result Types

```python
type Result[T, E] = Ok[T] | Err[E]

def handle_result(result: Result[int, str]) -> str:
    match result:
        case Ok(value) if value > 100:
            return f"Large value: {value}"
        case Ok(value):
            return f"Value: {value}"
        case Err(error):
            return f"Error: {error}"
```

### Matching with Guards

```python
def classify_response(status: int, body: dict[str, object]) -> str:
    match status, body:
        case 200, {"data": list() as items} if len(items) > 0:
            return f"Success with {len(items)} items"
        case 200, {"data": []}:
            return "Success but empty"
        case 400, {"error": str() as msg}:
            return f"Client error: {msg}"
        case 500, _:
            return "Server error"
        case _:
            return "Unknown response"
```

## Anti-Patterns

- Using deprecated type hints (e.g., `Union`, `List`, `Dict`, `Optional`).
- Ignoring type hints or using `Any` unnecessarily.
- Using relative imports (use full paths from package root).
- Using local imports inside functions (keep imports at module scope).
- Missing `__init__.py` in packages.
- Mixing package managers (stick to uv).
- Skipping quality checks.
- Re-exporting imports from other packages.
- Configuring an `__all__` in a module other than an `__init__.py`.
- Mutable dataclasses (use `frozen=True` and `replace()` for changes).
- Positional arguments in public APIs (use `*` or `kw_only=True`).

## Related Skills

- [ty](ty.md) - Type checking with ty
- [ruff](ruff.md) - Linting and formatting
- [uv](uv.md) - Package management
- [workflow](workflow/workflow.md) - Development lifecycle
- [error-handling](error-handling.md) - Exception patterns
- [testing](testing/testing.md) - Test writing best practices
