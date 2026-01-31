# KeywordInjector with Functions

**Complexity: Intermediate**

The `KeywordInjector` extends function factory support with three-tier precedence for parameter resolution:

1. **kwargs** (highest priority): Values passed directly to the injector call
2. **Container** (medium priority): `Inject[T]` parameters resolved via `container.get(T)`
3. **Default values** (lowest priority): Non-injectable parameters use their default values

This is especially useful for testing, where you can override injected dependencies with test doubles.

## Source Code

The complete example is available at `examples/function/keyword_injector.py`:

```{literalinclude} ../../examples/function/keyword_injector.py
:start-at: from dataclasses
:end-at: timeout=timeout,
```

## Quick Example

Here is a minimal doctest-compatible example showing the three-tier precedence:

```python
>>> from dataclasses import dataclass
>>> from svcs import Container, Registry
>>> from svcs_di import Inject
>>> from svcs_di.injectors import KeywordInjector

>>> @dataclass
... class Config:
...     environment: str = "development"

>>> @dataclass
... class Service:
...     env: str
...     timeout: int

>>> def create_service(config: Inject[Config], timeout: int = 30) -> Service:
...     return Service(env=config.environment, timeout=timeout)

>>> registry = Registry()
>>> registry.register_factory(Config, Config)
>>> container = Container(registry)
>>> injector = KeywordInjector(container=container)

>>> # Tier 2 (container) + Tier 3 (defaults)
>>> service = injector(create_service)
>>> service.env, service.timeout
('development', 30)

>>> # Tier 1 (kwargs) overrides timeout
>>> service = injector(create_service, timeout=120)
>>> service.timeout
120

>>> # Tier 1 (kwargs) overrides injectable parameter
>>> test_config = Config(environment="testing")
>>> service = injector(create_service, config=test_config)
>>> service.env
'testing'

```

## Key Concepts

### Three-Tier Precedence

The `KeywordInjector` resolves parameters in this order:

1. **kwargs**: Any keyword argument passed to the injector call takes precedence
2. **Container**: `Inject[T]` parameters are resolved from the container
3. **Defaults**: Parameters with default values use those defaults

```{literalinclude} ../../examples/function/keyword_injector.py
:start-at: def demonstrate_default_values
:end-at: return service
```

### Overriding Non-Injectable Parameters

Non-injectable parameters (those without `Inject[T]`) can be overridden via kwargs:

```{literalinclude} ../../examples/function/keyword_injector.py
:start-at: def demonstrate_kwargs_override_non_injectable
:end-at: return service
```

### Overriding Injectable Parameters

Even `Inject[T]` parameters can be overridden - useful for testing:

```{literalinclude} ../../examples/function/keyword_injector.py
:start-at: def demonstrate_kwargs_override_injectable
:end-at: return service
```

### Partial Overrides

You can override some parameters while letting others come from the container or defaults:

```{literalinclude} ../../examples/function/keyword_injector.py
:start-at: def demonstrate_partial_override
:end-at: return service
```

## Use Cases

The `KeywordInjector` with functions is particularly useful for:

- **Testing**: Override dependencies with mocks/stubs without changing registrations
- **Request-scoped values**: Pass request-specific data (user, session) alongside container services
- **Configuration overrides**: Provide runtime configuration that overrides defaults
