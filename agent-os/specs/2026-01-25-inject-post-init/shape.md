# Shape: Inject in Post Init

## Problem Statement

Users need to inject dependencies that are only used during initialization to compute derived values, not stored on the instance. Python's `dataclasses.InitVar` provides exactly this mechanism - values passed to `__post_init__` but not stored as fields.

## Use Cases

1. **Derived Values**: Compute a final value from an injected service
   ```python
   @dataclass
   class UserProfile:
       user_id: str = field(init=False)
       context: InitVar[Inject[RequestContext]]

       def __post_init__(self, context: RequestContext):
           self.user_id = context.user.id
   ```

2. **Configuration Extraction**: Extract specific config values during init
   ```python
   @dataclass
   class CacheService:
       ttl: int = field(init=False)
       config: InitVar[Inject[AppConfig]]

       def __post_init__(self, config: AppConfig):
           self.ttl = config.cache_ttl
   ```

3. **Transformation**: Transform injected data into stored form
   ```python
   @dataclass
   class Processor:
       rules: list[Rule] = field(init=False)
       rule_service: InitVar[Inject[RuleService]]

       def __post_init__(self, rule_service: RuleService):
           self.rules = rule_service.get_active_rules()
   ```

## Design Decisions

### Decision 1: Type Syntax

**Chosen:** `InitVar[Inject[T]]` - Inject marker inside InitVar

**Rationale:**
- Consistent with regular field pattern: `field: Inject[T]`
- InitVar wraps the entire type hint, so `InitVar[Inject[T]]` is the natural form
- Type checker sees `InitVar[T]` at the outer level (correct behavior)

**Alternatives considered:**
- `Inject[InitVar[T]]` - awkward, InitVar should be outermost
- New marker `InjectInit[T]` - unnecessary complexity

### Decision 2: Detection Mechanism

**Chosen:** Scan `get_type_hints()` for `InitVar[...]` entries not in `dataclasses.fields()`

**Rationale:**
- `dataclasses.fields()` excludes InitVar by design
- Type hints dictionary includes all annotated names
- Comparing sets identifies InitVar-only entries

### Decision 3: Resolution Behavior

**Chosen:** Same resolution as regular `Inject[T]` fields

**Rationale:**
- InitVar fields are passed to constructor like regular kwargs
- Dataclass routes InitVar kwargs to `__post_init__`
- No special handling needed in injector

## Scope

### In Scope
- `InitVar[Inject[T]]` with concrete types
- `InitVar[Inject[Protocol]]` with protocols
- All injector types (Default, Keyword, Hopscotch)
- Kwargs override for InitVar fields (KeywordInjector)

### Out of Scope
- InitVar without Inject (no auto-resolution)
- InitVar with default values (not supported by dataclasses anyway)
- Async InitVar (dataclasses don't support async __post_init__)

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Type checker confusion | Medium | Document pattern clearly |
| Breaking change | Low | Default `is_init_var=False` in FieldInfo |
| Performance | Low | Only scans hints for dataclasses |

## Success Criteria

1. `InitVar[Inject[T]]` fields are automatically resolved
2. All existing tests continue passing
3. New tests cover the documented patterns
4. Documentation explains the pattern
