# Specification: Inject Container

## Goal
Enable automatic injection of the `svcs.Container` instance itself when functions or dataclass fields are annotated with `Injectable[Container]`, allowing injected code to access the container for dynamic service resolution.

## User Stories
- As a service developer, I want to inject the Container itself so that I can perform dynamic service lookups at runtime
- As a framework user, I want Container injection to follow the same precedence rules as other Injectable dependencies for consistency

## Specific Requirements

**Container Type Recognition**
- Detect `Injectable[Container]` type annotation in function parameters and dataclass fields
- Use `svcs.Container` as the inner type to match against when `Injectable[Container]` is found
- Follow existing type hint parsing logic in `get_field_infos()` and `extract_inner_type()` functions

**Container Instance Resolution**
- Inject `self.container` (the container calling the injector) by default
- Allow override via kwargs if a Container instance is explicitly provided
- No special type validation - trust the type annotation (consistent with other Injectable types)

**DefaultInjector Support**
- Add Container injection to `_resolve_field_value()` function for synchronous resolution
- Check if `inner_type is svcs.Container` when processing Injectable fields
- Return `self.container` directly without calling `.get()` or `.get_abstract()`
- Place Container check before protocol/concrete type resolution logic

**DefaultAsyncInjector Support**
- Add Container injection to `_resolve_field_value_async()` function for async resolution
- Use same logic as DefaultInjector: check `inner_type is svcs.Container` and return container
- Maintain consistency between sync and async implementations

**KeywordInjector Support**
- Add Container injection to `_resolve_field_value_sync()` method in KeywordInjector class
- Follow three-tier precedence: kwargs (Tier 1), Container injection (Tier 2), defaults (Tier 3)
- Check for Container in kwargs first, then inject `self.container` if not provided

**KeywordAsyncInjector Support**
- Add Container injection to `_resolve_field_value_async()` method in KeywordAsyncInjector class
- Mirror KeywordInjector logic with async method signature
- Maintain three-tier precedence pattern

**HopscotchInjector Support**
- Add Container injection to `_resolve_field_value_sync()` method in HopscotchInjector class
- Container is NOT part of locator resolution (context-agnostic as specified in requirements)
- Check kwargs first, then inject container directly, bypassing ServiceLocator lookup

**HopscotchAsyncInjector Support**
- Add Container injection to `_resolve_field_value_async()` method in HopscotchAsyncInjector class
- Follow same logic as HopscotchInjector with async method signature
- Skip locator resolution for Container type

**Precedence and Override Behavior**
- Container follows standard Injectable precedence rules across all injectors
- Kwargs-based injectors (Keyword, Hopscotch): kwargs > container injection > defaults
- Non-kwargs injectors (Default): container injection > defaults
- No special precedence handling needed beyond existing tier system

**Integration Pattern**
- Place Container check immediately after identifying `field_info.is_injectable` is True
- Add conditional: `if inner_type is svcs.Container: return (True, self.container)`
- For kwargs injectors: check kwargs before container injection
- Position before existing protocol/concrete type logic to catch Container early

## Visual Design
No visual assets provided.

## Existing Code to Leverage

**Injectable Type Parsing in auto.py**
- `is_injectable()` function detects `Injectable[T]` annotations via `get_origin()`
- `extract_inner_type()` extracts inner type from `Injectable[T]` using `get_args()`
- `FieldInfo` NamedTuple contains `is_injectable`, `inner_type`, and `is_protocol` fields
- Reuse this parsing infrastructure - no changes needed, it already extracts Container type

**Three-Tier Precedence Pattern in KeywordInjector**
- Tier 1 checks `if field_name in kwargs` first
- Tier 2 processes `if field_info.is_injectable` with container.get() resolution
- Tier 3 falls back to `if field_info.has_default` for default values
- Apply same pattern for Container: kwargs > container > defaults

**Field Resolution Functions**
- `_resolve_field_value()` in auto.py handles sync resolution for DefaultInjector
- `_resolve_field_value_async()` in auto.py handles async resolution for DefaultAsyncInjector
- KeywordInjector has `_resolve_field_value_sync()` method with kwargs parameter
- Each injector type has its own resolution method to modify

**Protocol Detection Logic**
- Existing code checks `field_info.is_protocol` to decide between `get_abstract()` and `get()`
- Container check should happen before protocol check to short-circuit early
- Pattern: check Container first, then protocol, then concrete types

**Locator-Based Resolution in HopscotchInjector**
- HopscotchInjector tries ServiceLocator first for Injectable types
- Falls back to standard container.get() if no locator or no implementation found
- Container should bypass locator entirely (not part of multiple registrations)

## Out of Scope
- Runtime type validation that verifies the annotated type is actually Container
- Special context-aware handling for Container injection in HopscotchInjector
- Custom precedence rules specific to Container (uses standard precedence)
- Changes to Container class itself or its API
- Support for injecting different Container instances beyond self.container and kwargs overrides
- New injector types beyond DefaultInjector, DefaultAsyncInjector, KeywordInjector, KeywordAsyncInjector, HopscotchInjector, HopscotchAsyncInjector
- Support for other svcs types like Registry or ServiceLocator via Injectable
- Nested container resolution or container hierarchy features
- Automatic registration of Container as a service in Registry
