# Function-Based Implementations for Protocol Services

## Overview

Can we register a function as a factory for a protocol-based service, where the protocol supports either class-based or
function-based implementations?

**Answer:** The core injection machinery already supports functions. The blocks are in the decorator and type
annotations, which can be relaxed.

## Current Restrictions

### 1. `@injectable` Decorator (Hard Block)

```python
# decorators.py:56
if not inspect.isclass(target):
    msg = "The @injectable decorator can only be applied to classes..."
    raise TypeError(msg)
```

This is the **primary block** - the decorator explicitly rejects non-classes.

### 2. Type Annotations (Soft Block - No Runtime Enforcement)

```python
# locator.py
@dataclass(frozen=True)
class FactoryRegistration:
    service_type: type
    implementation: type  # <-- Says "type" not "Callable"
    ...

class ServiceLocator:
    def register(
        self,
        service_type: type,
        implementation: type,  # <-- Says "type" not "Callable"
        ...
    ) -> "ServiceLocator":
```

These are only type hints with no runtime `isinstance` check.

### 3. Scanning Logic (Hard Block)

```python
# scanning.py:188
if isinstance(obj, type) and hasattr(obj, INJECTABLE_METADATA_ATTR)
```

Only looks for classes when scanning modules.

## What Already Works

### InjectionTarget Type Alias

```python
# auto.py
type InjectionTarget[T] = type[T] | Callable[..., T]
```

The type alias already accepts both types and callables.

### get_field_infos() Handles Both

```python
# auto.py
def get_field_infos(target: type | Callable) -> list[FieldInfo]:
    if dataclasses.is_dataclass(target):
        return _get_dataclass_field_infos(target)
    else:
        return _get_callable_field_infos(target)  # <-- Works with functions!
```

### HopscotchInjector.__call__() Works with Functions

```python
# hopscotch.py
def __call__[T](self, target: InjectionTarget[T], **kwargs: Any) -> T:
    field_infos = get_field_infos(target)  # Works with functions
    # ...
    return target(**resolved_kwargs)  # Calling a function works fine
```

### Locator Resolution Passes to Injector

```python
# hopscotch.py
implementation = locator.get_implementation(...)
if implementation is not None:
    return (True, injector_callable(implementation))  # Would work with functions
```

## Summary Table

| Component                            | Block Type              | Can Be Relaxed?                        |
|--------------------------------------|-------------------------|----------------------------------------|
| `@injectable` decorator              | Hard (raises TypeError) | Yes - could allow callables            |
| `FactoryRegistration.implementation` | Soft (type hint only)   | Yes - change to `type \| Callable`     |
| `ServiceLocator.register()` hint     | Soft (type hint only)   | Yes - change to `type \| Callable`     |
| Scanning logic                       | Hard (isinstance check) | Yes - could detect decorated functions |

## Implementation Path

To enable function-based factories for protocols:

### Option A: Relax `@injectable`

Modify the decorator to accept callables:

```python
def _mark_injectable(
    target: type | Callable,
    for_: type | None = None,
    ...
) -> type | Callable:
    if not (inspect.isclass(target) or callable(target)):
        raise TypeError("@injectable requires a class or callable")
    # ... rest unchanged
```

### Option B: New `@injectable_factory` Decorator

Create a separate decorator for function factories:

```python
@injectable_factory(for_=Greeting)
def create_greeting(config: Inject[Config]) -> Greeting:
    return CustomGreeting(salutation=config.greeting_prefix)
```

### Option C: Manual Registration (Already Works)

Skip the decorator entirely and register manually:

```python
def greeting_factory(config: Config) -> Greeting:
    return CustomGreeting(salutation=config.greeting_prefix)

# Manual registration bypasses decorator checks
locator = locator.register(Greeting, greeting_factory)  # Type error but works at runtime
```

## Type Annotation Updates

For full support, update type annotations:

```python
# In FactoryRegistration
implementation: type | Callable[..., Any]

# In ServiceLocator.register()
def register(
    self,
    service_type: type,
    implementation: type | Callable[..., Any],
    ...
) -> "ServiceLocator":
```

## Use Case Example

```python
class Greeting(Protocol):
    def greet(self, name: str) -> str: ...

@dataclass
class SimpleGreeting:
    prefix: str = "Hello"

    def greet(self, name: str) -> str:
        return f"{self.prefix}, {name}!"

# Function factory for complex construction
@injectable_factory(for_=Greeting)
def create_greeting(config: Inject[Config], logger: Inject[Logger]) -> Greeting:
    logger.info("Creating greeting with config")
    return SimpleGreeting(prefix=config.greeting_prefix)
```

## Recommendation

Start with **Option C** (manual registration) to validate the use case works at runtime. If there's demand, implement
**Option B** (`@injectable_factory`) to provide a clean decorator-based API without changing the existing `@injectable`
semantics.
