# Specification: Multiple Service Registrations

## Goal

Enable registration of multiple implementations for the same protocol interface with metadata-driven resolution based on
a three-tier precedence algorithm, providing the foundation for context-aware and location-based service selection.

## User Stories

- As a developer, I want to register multiple implementations of the same class or protocol so that different
  implementations can be selected based on request context or location
- As a developer, I want explicit control over registration precedence so that later registrations can override earlier
  ones (LIFO ordering)

## Specific Requirements

**Registration Dataclass with Metadata Storage**

- Create a Registration dataclass based on Hopscotch pattern (lines 38-53 of hopscotch/registry.py)
- Fields: implementation, kind, context, field_infos, is_singleton
- Automatically extract field_infos using get_field_infos from svcs_di.auto during __post_init__ unless is_singleton is
  True
- Store context metadata for future resolution (Item 6) and location placeholder for future use (Item 7)
- Support both singleton instances and class constructors via is_singleton flag
- Use slots for performance optimization
- Try hard to avoid any changes in `auto.py` to keep out of default implementation

**Nested Storage Structure for Multiple Registrations**

- Implement nested defaultdict structure: dict[type, KindGroups]
- KindGroups TypedDict separates "singletons" and "classes" dictionaries
- Each category maps context types to list[Registration]: dict[Union[type, IsNoneType], list[Registration]]
- Use IsNoneType marker class for no-context registrations (explicit defaults)
- Store multiple registrations per protocol interface as ordered lists
- LIFO ordering: insert new registrations at position 0 to ensure later registrations override earlier ones
- Default factory function make_singletons_classes() initializes KindGroups structure

**Three-Tier Precedence Resolution Algorithm**

- Implement get_best_match() method based on Hopscotch pattern (lines 235-291 of hopscotch/registry.py)
- Create three precedence lists during resolution: high (exact context match), medium (subclass match), low (no context)
- High precedence: this_context is context_class (exact identity match)
- Medium precedence: issubclass(context_class, this_context) for inheritance-based matching
- Low precedence: this_context is IsNoneType (default/fallback registrations)
- Return first match from concatenated list: high + medium + low
- Within each precedence tier, respect LIFO ordering from storage
- Defer advanced scoring with weights and priorities to Item 8

**Registration Method with LIFO Support**

- Implement register() method that adds Registration instances to nested storage
- Automatically infer kind from implementation's base class using getmro() if not specified
- Distinguish singleton instances from class constructors using isclass() check
- Use context parameter or IsNoneType marker for storage key
- Insert at position 0 of registration list to ensure LIFO override behavior
- Extract field_infos automatically unless singleton

**Resolution with Parent Registry Fallback**

- Implement get() method that finds best match and constructs/returns instance
- Use get_best_match() to locate appropriate registration
- If no match found in current registry, recursively check parent registry
- Raise LookupError with descriptive message when no registrations match and no parent exists
- Return singleton instances directly without construction
- Construct class registrations using inject_callable pattern from Hopscotch (lines 113-164)
- Support props/kwargs with highest precedence for construction overrides via allow_singletons=False

**Inject Callable Construction Pattern**

- Implement inject_callable() function based on Hopscotch pattern
- Iterate through registration.field_infos to resolve each field
- Three-tier precedence for field values: props (highest), registry lookup, defaults (lowest)
- Check for __hopscotch_factory__ custom construction method and use if present
- For registry lookups, use inject_field_registry() to get dependencies from registry
- For non-registered dependencies during injection, use inject_field_no_registry() fallback
- Validate all fields are resolved or have defaults, raise ValueError with descriptive message if missing
- Construct target with resolved kwargs

**Field Injection Helpers**

- Implement inject_field_registry() that resolves field from registry using field_info
- Support operator-based resolution for Annotated[SomeType, SomeOperator] fields (defer operators to Item 12)
- Special case: return registry itself when field type is Registry
- Use registry.get() for normal dependencies with parent fallback on LookupError
- Implement inject_field_no_registry() for dependencies not in registry (functions, NamedTuples, dataclasses)
- Create temporary Registration and recursively call inject_callable to construct unregistered dependencies

**HopscotchLocator Protocol/Class**

- Define HopscotchLocator as a new protocol or class that represents the service type being registered
- This is what gets requested from the container, not the injector itself
- Multiple implementations can be registered with different contexts or locations
- Follows initial_spec.md pattern where HopscotchLocator is the svc_type in Registration
- Serves as the example protocol for demonstrating multiple registrations

**Sync and Async Injector Implementation**

- Implement HopscotchInjector (synchronous) following KeywordInjector pattern
- Implement HopscotchAsyncInjector (asynchronous) following KeywordAsyncInjector pattern
- Both should be dataclasses with container field
- Support kwargs validation against field_infos to ensure unknown parameters are rejected
- Implement three-tier field resolution: kwargs > container > defaults
- Use get_field_infos from svcs_di.auto for field introspection
- Resolve Injectable fields using container.get() or container.get_abstract() for protocols
- Async version uses container.aget() and container.aget_abstract()

**Container Setup Infrastructure**

- Provide basic infrastructure for collecting registrations at configuration time
- Store registrations in registry during setup/scan phase
- Foundation for future container-local registration processing (defer two-pass matching to Item 9)
- Metadata placeholders for location-based resolution (defer actual location matching to Item 7)
- Support for request-time criteria (defer advanced context resolution to Item 6)

## Visual Design

No visual assets provided.

## Existing Code to Leverage

**Hopscotch Registry Pattern (hopscotch/registry.py)**

- Registration dataclass structure with slots (lines 38-53) provides the model for metadata storage
- KindGroups nested storage with singletons/classes separation (lines 167-184) should be replicated
- Three-tier precedence algorithm in get_best_match() (lines 235-291) is the core resolution logic
- inject_callable construction pattern (lines 113-164) handles dependency injection during construction
- IsNoneType marker class for no-context registrations provides explicit default behavior

**KeywordInjector Pattern (src/svcs_di/injectors/keyword.py)**

- Three-tier precedence for value resolution (kwargs > container > defaults) should be maintained
- Dual implementation pattern (KeywordInjector and KeywordAsyncInjector) provides sync/async model
- Field validation logic with clear error messages ensures good developer experience
- Resolution returns tuple[bool, value] pattern enables explicit value presence checking
- Dataclass-based structure with container field integrates with svcs

**FieldInfo and get_field_infos (src/svcs_di/auto.py)**

- FieldInfo NamedTuple (line 154) provides comprehensive field metadata structure
- get_field_infos function (line 189) extracts metadata from dataclasses and callables
- is_injectable, extract_inner_type, is_protocol_type helpers enable type introspection
- Handles both dataclass fields and callable parameters with unified interface
- Supports default values and default_factory for field resolution

**DefaultInjector Pattern (src/svcs_di/auto.py)**

- Two-tier precedence (container > defaults) provides base pattern to extend
- _resolve_field_value helper function (line 287) shows resolution logic structure
- Integration with svcs Container via get() and get_abstract() demonstrates container usage
- DefaultAsyncInjector async pattern (line 93) shows async resolution approach

**LIFO Registration Pattern from Hopscotch**

- list.insert(0, registration) at line 377 of hopscotch/registry.py ensures later registrations override
- Multiple registrations stored as ordered lists enable precedence within same tier
- defaultdict usage creates nested structure on-demand without explicit initialization

## Out of Scope

- Advanced context-specific resolution logic beyond basic three-tier precedence (defer to Roadmap Item 6)
- Context matching only implements identity and subclass checks, not advanced patterns or scoring
- Location-based service resolution using PurePath (defer to Roadmap Item 7)
- Location metadata stored in Registration dataclass but NOT used for resolution in this spec
- Advanced precedence and scoring system with weights and priorities (defer to Roadmap Item 8)
- Only basic three-tier precedence (high/medium/low) implemented, advanced scoring deferred
- Container setup and registration processing at request time (defer to Roadmap Item 9)
- Two-pass matching logic (location OR context, then location AND context) not implemented
- Container-local registration vs registry-global registration distinction deferred
- Advanced examples for context-aware resolution (defer to Roadmap Item 10)
- Auto-discovery scanning with venusian integration (defer to Roadmap Item 11)
- Field operators for Annotated types (defer to Roadmap Item 12)
- Multi-tenant patterns, customer vs employee context examples not included
