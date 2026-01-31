# InitVar Injection

**Complexity: Intermediate**

This example demonstrates the `InitVar[Inject[T]]` pattern for injecting dependencies that are only used during
initialization to compute derived values. You'll learn how to:

- Use `InitVar[Inject[T]]` to inject dependencies into `__post_init__`
- Compute derived values with fallback (auto-resolve if `None`, allow override)
- Combine regular `Inject[T]` fields with `InitVar[Inject[T]]` fields

This pattern is useful when you need to use a dependency during initialization but don't want to store it on the instance.

## Use Cases

The `InitVar[Inject[T]]` pattern is ideal for:

1. **Extracting specific data** from a larger service or config object
2. **Computing derived values** from injected dependencies
3. **Optional with fallback** - auto-resolve when `None`, but allow kwargs override
4. **Keeping instances lean** by not storing dependencies only needed for setup

## The "Optional with Fallback" Pattern

The recommended pattern uses optional fields (`T | None = None`) that are computed from the injected dependency
only if not provided. This allows both auto-resolution AND manual override:

```python
@dataclass
class Greeting:
    """Greeting component with optional override."""

    users: InitVar[Inject[Users]]
    current_name: str | None = None  # Can be overridden via kwargs

    def __post_init__(self, users: Users) -> None:
        if self.current_name is None:
            current_user = users.get_current_user()
            self.current_name = current_user["name"]
```

This pattern enables:
- **Auto-resolution**: `injector(Greeting)` → computes `current_name` from `Users`
- **Manual override**: `injector(Greeting, current_name="Test")` → uses provided value

## Basic Example

The simplest use case is extracting configuration values during initialization:

```{literalinclude} ../../examples/init_var/basic_init_var.py
:start-at: @dataclass
:end-at: self.debug = config.debug_mode
```

### Key Points

- `InitVar[Inject[Config]]` marks a dependency that's passed to `__post_init__` but NOT stored
- Optional fields (`T | None = None`) allow override via kwargs
- `__post_init__` only computes values when they're `None`

## Mixed Injection Example

You can combine regular `Inject[T]` fields (stored on the instance) with `InitVar[Inject[T]]` fields (used only during init):

```{literalinclude} ../../examples/init_var/mixed_injection.py
:start-at: @dataclass
:end-at: self.permissions = set(context.permissions)
```

In this example:
- `cache: Inject[Cache]` is stored on the instance for later use
- `context: InitVar[Inject[UserContext]]` is used only during init, then discarded
- `user_id` and `permissions` have fallback behavior - computed from context if `None`

## How It Works

1. **Field Detection**: `get_field_infos()` scans type hints for `InitVar[...]` entries
2. **Type Unwrapping**: `InitVar[Inject[T]]` is unwrapped to detect `Inject[T]` inside
3. **Resolution**: The dependency `T` is resolved from the container like any other `Inject[T]`
4. **Construction**: The resolved value is passed to the dataclass constructor
5. **Routing**: Python's dataclass machinery routes InitVar arguments to `__post_init__`

## Understanding the Syntax

**Think of `InitVar[...]` as wrapping whatever you'd normally write.** If you'd write `db: Inject[Database]` for
a regular field, write `db: InitVar[Inject[Database]]` for an init-only field:

| Regular Field | InitVar Field |
|---------------|---------------|
| `db: Inject[Database]` | `db: InitVar[Inject[Database]]` |
| `cache: Inject[Cache]` | `cache: InitVar[Inject[Cache]]` |
| `config: Config` (not injected) | `config: InitVar[Config]` (not injected) |

The `InitVar` wrapper just changes where the value goes (to `__post_init__` instead of being stored as an attribute).
The `Inject` marker inside still means "resolve this from the container."

## Important Notes

- InitVar fields are **never** stored on the instance - they're only passed to `__post_init__`
- Use `T | None = None` for fields that should allow override (not `field(init=False)`)
- Kwargs override works with both InitVar fields and optional fields when using `KeywordInjector`
- This pattern works with protocols: `InitVar[Inject[SomeProtocol]]`

## Source Code

The complete examples are available in the `examples/init_var/` directory:

- `basic_init_var.py` - Configuration extraction with override support
- `mixed_injection.py` - Combining regular and InitVar injection with kwargs override
