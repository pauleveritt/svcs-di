# Plan: Using attrs to Improve svcs-di Internals

## Executive Summary

Several svcs-di internal classes could benefit from attrs, primarily for **better immutability guarantees**,
**validators**, **cleaner evolution patterns**, and **memory efficiency**. The main candidates are `ServiceLocator`,
`FactoryRegistration`, and `FieldInfo`.

## 1. ServiceLocator - The Primary Candidate

### Current Implementation Problems

```python
@dataclass(frozen=True)
class ServiceLocator:
    _single_registrations: dict[type, FactoryRegistration] = field(default_factory=dict)
    _multi_registrations: dict[type, tuple[FactoryRegistration, ...]] = field(default_factory=dict)
```

**Issues:**

- The dicts are **not truly immutable** - `frozen=True` only prevents reassignment, not mutation
- Manual dict copying in `register()` is verbose and error-prone
- No validation that dict contents are correct types

### attrs Solution

```python
from typing import Mapping
import attrs


@attrs.frozen  # Equivalent to frozen=True + slots=True
class ServiceLocator:
    _single_registrations: Mapping[type, FactoryRegistration] = attrs.Factory(dict)
    _multi_registrations: Mapping[type, tuple[FactoryRegistration, ...]] = attrs.Factory(dict)

    @_single_registrations.validator
    def _validate_single(self, attribute, value):
        for k, v in value.items():
            if not isinstance(k, type):
                raise TypeError(f"Key must be a type, got {type(k)}")
            if not isinstance(v, FactoryRegistration):
                raise TypeError(f"Value must be FactoryRegistration")

    def register(self, service_type, implementation, ...) -> "ServiceLocator":
        new_reg = FactoryRegistration(service_type, implementation, resource, location)

        # attrs.evolve() for cleaner immutable updates
        if service_type not in self._single_registrations and service_type not in self._multi_registrations:
            return attrs.evolve(self, _single_registrations={**self._single_registrations, service_type: new_reg})
        # ... rest of logic
```

### Benefits

- `attrs.evolve()` provides cleaner immutable updates
- Validators catch type errors early
- `@attrs.frozen` implies `slots=True` for memory efficiency (~40% less memory)
- Better `__repr__` for debugging

### True Immutability with MappingProxyType

Could use `types.MappingProxyType` to wrap dicts for true read-only views:

```python
from types import MappingProxyType


def _freeze_dict(d: dict) -> MappingProxyType:
    return MappingProxyType(d)


# In converter
_single_registrations: Mapping[...] = attrs.field(converter=_freeze_dict, factory=dict)
```

## 2. FactoryRegistration - Minor Improvements

### Current

```python
@dataclass(frozen=True)
class FactoryRegistration:
    service_type: type
    implementation: type
    resource: type | None = None
    location: PurePath | None = None
```

### attrs Version

```python
@attrs.frozen
class FactoryRegistration:
    service_type: type = attrs.field(validator=attrs.validators.instance_of(type))
    implementation: type = attrs.field(validator=attrs.validators.instance_of(type))
    resource: type | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(type))
    )
    location: PurePath | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(PurePath))
    )
```

### Benefits

- Validators ensure types are correct at construction
- Slots for memory efficiency
- Could add custom validator: implementation must be callable or a class

## 3. FieldInfo - NamedTuple to attrs

### Current

```python
class FieldInfo(NamedTuple):
    name: str
    type_hint: Any
    is_injectable: bool
    inner_type: type | None
    is_protocol: bool
    has_default: bool
    default_value: Any
```

### attrs Version

```python
@attrs.frozen
class FieldInfo:
    name: str
    type_hint: Any
    is_injectable: bool
    inner_type: type | None
    is_protocol: bool
    has_default: bool
    default_value: Any

    @inner_type.validator
    def _validate_inner_type(self, attribute, value):
        # If injectable, inner_type should be set
        if self.is_injectable and value is None:
            raise ValueError(f"Injectable field '{self.name}' must have inner_type")

    @is_protocol.validator
    def _validate_protocol(self, attribute, value):
        # is_protocol only makes sense if inner_type is set
        if value and self.inner_type is None:
            raise ValueError("is_protocol=True requires inner_type")
```

### Benefits

- Validators enforce invariants (injectable implies inner_type exists)
- Could add computed properties via `@property`
- Memory efficient with slots

## 4. Injectors (HopscotchInjector, KeywordInjector, etc.)

**Current:** All use `@dataclass(frozen=True)`

**Benefit of attrs:** Minimal - these are simple containers. Could switch for consistency but not critical.

## 5. InjectableMetadata - TypedDict to attrs

### Current

```python
class InjectableMetadata(TypedDict):
    for_: type | None
    resource: type | None
    location: PurePath | None
```

### attrs Version

```python
@attrs.frozen
class InjectableMetadata:
    for_: type | None = None
    resource: type | None = None
    location: PurePath | None = None
```

### Benefits

- Validators for type checking
- Better repr
- Hashable (can be used in sets/dicts as keys)

## Implementation Phases

### Phase 1: FactoryRegistration and FieldInfo (Low Risk)

- Convert these first as they're simpler
- Add validators
- Update tests

### Phase 2: ServiceLocator (Medium Risk)

- Convert to attrs with `evolve()` pattern
- Consider MappingProxyType for true immutability
- Ensure cache invalidation still works correctly
- Update tests

### Phase 3: InjectableMetadata and Injectors (Low Risk)

- Convert for consistency
- Minimal functional change

## Migration Concerns

1. **attrs Dependency**: svcs-di would need to add `attrs` as a dependency (svcs itself doesn't require it)

2. **API Compatibility**: If external code accesses `_single_registrations` directly (even though underscore-prefixed),
   changing to MappingProxyType could break them

3. **Performance**: Need to benchmark - attrs is generally faster but should verify

4. **Type Stubs**: May need to update `.pyi` files if return types change

## Key Decision Points

1. **Should we require true immutability?** (MappingProxyType vs regular dicts)
2. **How strict should validators be?** (e.g., validate that implementation is subclass of service_type?)
3. **Should attrs be an optional dependency?** (Could support both dataclass and attrs versions)

## Recommendation

Start with **Phase 1** (FactoryRegistration + FieldInfo) as a proof of concept. These have the clearest benefits and
lowest risk. If successful, proceed to ServiceLocator which has the most to gain from `attrs.evolve()` and validators.
