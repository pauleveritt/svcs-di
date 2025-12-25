# Spec Requirements: Multiple Service Registrations

## Initial Description

Start a `HopscotchInjector` that is based on the `KeywordInjector`. Add support for registering multiple implementations of the same protocol interface, storing them as a collection of registrations with metadata (factory, context, location) that will be resolved based on request-time criteria.

**Source:** agent-os/product/roadmap.md (Roadmap Item 5, Size: L)

## Requirements Discussion

### First Round Questions

**Q1: HopscotchLocator Clarification**
I see the raw idea mentions "HopscotchInjector" but I want to clarify - are we building:
- A new HopscotchInjector class (separate from KeywordInjector)?
- A new HopscotchLocator class that gets registered as a service and requested from the container?
- Or both?

Based on the roadmap context, it seems like HopscotchInjector would be the injector that knows how to resolve HopscotchLocator services. Can you clarify the relationship between these two?

**Answer:** New class, new everything. In the registry. Being requested. Multiple but look in initial_spec for details.

**Interpretation:**
- HopscotchLocator is a completely new class (separate from HopscotchInjector)
- HopscotchLocator gets registered in the Registry
- HopscotchLocator is the thing "being requested" (the protocol type being requested from the container)
- There can be multiple HopscotchLocator implementations
- The initial spec should be checked for more details

**Q2: Default Registration Behavior**
For registrations without context or location specified, should they:
- Be treated as "default" registrations (matches when no better match exists)?
- Be treated as explicit registrations (only matches when no context/location is provided)?
- Be invalid (all registrations must specify criteria)?

I'm assuming they should be treated as explicit "default" registrations - meaning they match only when the request has no context/location specified. Is that correct?

**Answer:** Explicit.

**Interpretation:** Registrations without context/location should be treated as explicit "default" registrations, matching only when the request has no context/location specified.

**Q3: No Match Scenario**
When a service is requested but NO registrations match the criteria, should the system:
- Return None (indicating no match)?
- Raise an exception (service not found)?
- Fall back to a global default registration (if one exists)?

I'm assuming we should raise an exception since this is more explicit and prevents silent failures. Is that correct?

**Answer:** Raise exception.

**Interpretation:** When NO registrations match, the system should raise an exception.

**Q4: Sync vs Async Support**
Should HopscotchInjector support:
- Only synchronous resolution (like KeywordInjector)?
- Only async resolution (like KeywordAsyncInjector)?
- Both sync and async versions (HopscotchInjector and HopscotchAsyncInjector)?

I'm assuming both, following the KeywordInjector pattern. Is that correct?

**Answer:** Both.

**Interpretation:** Implement both synchronous and asynchronous versions: HopscotchInjector and HopscotchAsyncInjector.

**Q5: Explicit Exclusions**
Looking at the roadmap, I see future items for:
- Item 6: Context-Specific Service Resolution
- Item 7: Location-Based Service Resolution
- Item 8: Precedence and Scoring System

Should this spec (Item 5) explicitly EXCLUDE those features and focus ONLY on:
- Storing multiple registrations with metadata placeholders for context/location
- Basic resolution based on EXACT matches (no scoring/precedence logic yet)
- Infrastructure to support future context/location resolution

Or should we include a simplified version of context/location matching now?

**Answer:** Yes keyword.

**Interpretation:** Focus on keyword-based approach similar to KeywordInjector. Defer context matching (item 6), location matching (item 7), and precedence/scoring (item 8) to those later specs.

**Q6: Existing Code Reference**
The user mentioned looking at "initial_spec" for details. Are there existing features in your codebase with similar patterns we should reference? For example:
- Similar interface elements or UI components to re-use
- Comparable registration/resolution patterns
- Related backend logic or service objects
- Existing models or data structures with similar functionality

**Answer:** (Implied) Check the raw-idea.md (which was provided) and the KeywordInjector implementation at `src/svcs_di/injectors/keyword.py`.

### Existing Code to Reference

**Similar Features Identified:**

- **KeywordInjector Pattern:** `src/svcs_di/injectors/keyword.py`
  - Base pattern for building HopscotchInjector
  - Three-tier precedence for value resolution (kwargs > container > defaults)
  - Both sync (KeywordInjector) and async (KeywordAsyncInjector) implementations
  - Field validation and resolution logic
  - Uses FieldInfo and get_field_infos helpers from svcs_di.auto

- **Hopscotch Registry Implementation:** `/Users/pauleveritt/projects/pauleveritt/hopscotch/src/hopscotch/registry.py`
  - Registration dataclass structure (lines 38-53)
  - Nested storage pattern with KindGroups (lines 167-184)
  - Three-tier precedence algorithm: high/medium/low (lines 235-291)
  - Multiple registrations per context stored as list
  - get_best_match() resolution logic

- **Upstream svcs Library:**
  - Registry and Container abstractions
  - Service registration and resolution patterns
  - get() and get_abstract() methods for retrieving services

- **Related Roadmap Context:**
  - Item 4 (COMPLETED): KeywordInjector - provides the foundation
  - Item 6 (FUTURE): Context-Specific Service Resolution - will build on this
  - Item 7 (FUTURE): Location-Based Service Resolution - will build on this
  - Item 8 (FUTURE): Precedence and Scoring System - will build on this

**Components to Potentially Reuse:**
- Field resolution logic from KeywordInjector
- FieldInfo and get_field_infos helpers from svcs_di.auto
- Sync/async pattern from KeywordInjector and KeywordAsyncInjector
- Validation patterns for kwargs and field names
- Registration dataclass pattern from Hopscotch
- KindGroups nested storage pattern from Hopscotch
- Three-tier precedence matching from Hopscotch

**Backend Logic to Reference:**
- Container.get() and Container.get_abstract() for service resolution
- Registry registration patterns from svcs
- Hopscotch's get_best_match() for precedence-based resolution
- Hopscotch's nested defaultdict storage structure

### Follow-up Questions

No follow-up questions needed. The answers provided clear direction on:
- The focus on keyword-based matching (similar to KeywordInjector)
- Explicit default registration behavior
- Exception-raising for no matches
- Both sync and async support required
- Deferring context/location/precedence to future specs

### Additional Hopscotch Implementation Details

**Critical Patterns from Hopscotch to Incorporate:**

**1. Registration Dataclass Structure** (from `registry.py` lines 38-53):
```python
@dataclass()
class Registration:
    implementation: Union[Callable[..., object], object]
    kind: Optional[Callable[..., object]] = None
    context: Optional[Callable[..., object]] = None
    field_infos: FieldInfos = field(default_factory=list)
    is_singleton: bool = False
```

**2. Multiple Registrations Storage Pattern** (from `registry.py` lines 167-184):
- Uses nested defaultdict structure: `dict[type, KindGroups]`
- KindGroups separates "singletons" and "classes"
- Each has `dict[Union[type, IsNoneType], list[Registration]]`
- Multiple registrations per context stored as list
- This allows LIFO (last-in-first-out) ordering where later registrations override earlier ones

**3. Three-Tier Precedence Algorithm** (from `registry.py` lines 235-291 - `get_best_match`):
- **High precedence**: Exact context match (`this_context is context_class`)
- **Medium precedence**: Subclass match (`issubclass(context_class, this_context)`)
- **Low precedence**: No context (`this_context is IsNoneType`)
- Returns first match from: `high + medium + low`
- Falls back to parent registry if no match in current registry
- This is the MINIMAL scoring system for this spec (defer advanced scoring to Item 8)

**4. HopscotchLocator Concept** (from initial spec context):
```python
@dataclass
class Registration:
    svc_type: Any  # The protocol being registered (e.g., HopscotchLocator)
    factory: Callable[..., object]
    context: Callable[..., object] | None = None
    location: PurePath | None = None
```
- HopscotchLocator is a NEW class that gets registered IN the registry
- It's what gets "requested" (the protocol type)
- Multiple implementations can be registered for it
- Resolution uses the precedence/scoring from Hopscotch

**5. Container Setup Logic Pattern** (from initial spec context):
- Collect all registrations at configuration time
- At request/container creation time, find best matches
- Register matching services locally in container
- Two-pass matching: (1) location OR context, (2) location AND context
- Register the request itself as a service

**6. Clarification on Scope:**
- This spec implements the BASIC three-tier precedence (high/medium/low)
- Advanced scoring with weights and priorities is deferred to Roadmap Item 8
- This provides the foundation for context-aware resolution (Item 6)
- This provides the foundation for location-based resolution (Item 7)

## Visual Assets

### Files Provided:
No visual assets provided.

### Visual Insights:
No visual assets to analyze.

## Requirements Summary

### Functional Requirements

**Core Functionality:**

1. **New HopscotchLocator Class:**
   - A new protocol/class that can be registered in the Registry
   - The thing being requested from the container (not the injector itself)
   - Multiple implementations can be registered
   - Follows the pattern from Hopscotch where HopscotchLocator is the `svc_type` being registered

2. **Registration Dataclass:**
   - Create a Registration dataclass (based on Hopscotch pattern)
   - Fields: implementation, kind, context, field_infos, is_singleton
   - Store metadata for factory, context (for future use), location (for future use)
   - Support both singleton and class registrations
   - Extract field_infos automatically during registration (unless singleton)

3. **Multiple Service Registrations Storage:**
   - Implement nested defaultdict structure: `dict[type, KindGroups]`
   - KindGroups separates "singletons" and "classes"
   - Each has `dict[Union[type, IsNoneType], list[Registration]]`
   - Multiple registrations per context stored as list
   - LIFO ordering: later registrations override earlier ones (insert at position 0)
   - Registrations without context use `IsNoneType` as key

4. **Three-Tier Precedence Resolution:**
   - Implement `get_best_match()` method based on Hopscotch pattern
   - **High precedence**: Exact context match (`this_context is context_class`)
   - **Medium precedence**: Subclass match (`issubclass(context_class, this_context)`)
   - **Low precedence**: No context (`this_context is IsNoneType`)
   - Return first match from: `high + medium + low` lists
   - This is the MINIMAL precedence system for this spec
   - Defer advanced scoring with weights to Item 8

5. **Resolution Logic:**
   - When HopscotchLocator is requested, use get_best_match() to find appropriate implementation
   - If NO registrations match: raise LookupError exception
   - Fall back to parent registry if no match in current registry
   - Handle singleton vs class registrations differently (return singleton directly, construct class)
   - Support props/kwargs that have highest precedence for construction

6. **Sync and Async Support:**
   - Implement both HopscotchInjector (synchronous) and HopscotchAsyncInjector (asynchronous)
   - Follow the pattern established by KeywordInjector and KeywordAsyncInjector
   - Use inject_callable pattern from Hopscotch for construction

7. **Container Setup (Basic Foundation):**
   - Provide infrastructure for collecting registrations at configuration time
   - Support for future container creation time processing (Item 9)
   - Metadata placeholders for location-based resolution (Item 7)
   - Foundation for two-pass matching logic (defer to Item 9)

**User Actions Enabled:**
- Register multiple implementations of HopscotchLocator with the Registry
- Specify context during registration (stored but minimal matching in this spec)
- Request HopscotchLocator from the Container
- Get the appropriate implementation based on three-tier precedence
- Store metadata (context, location) for future resolution strategies
- Override earlier registrations with later ones (LIFO)

**Data to be Managed:**
- Nested storage structure: `dict[type, KindGroups]`
- Registration instances with metadata (implementation, kind, context, field_infos, is_singleton)
- Three precedence lists (high/medium/low) during resolution
- Parent registry references for fallback resolution
- Props/kwargs for construction-time overrides

### Reusability Opportunities

**Components that Exist:**
- KeywordInjector pattern at `src/svcs_di/injectors/keyword.py`
- KeywordAsyncInjector pattern at `src/svcs_di/injectors/keyword.py`
- FieldInfo and get_field_infos helpers from `svcs_di.auto`
- Field validation and resolution logic
- Three-tier precedence pattern (kwargs > container > defaults)

**Hopscotch Patterns to Adapt:**
- Registration dataclass from `hopscotch/registry.py` lines 38-53
- KindGroups nested storage from `hopscotch/registry.py` lines 167-184
- Three-tier precedence algorithm from `hopscotch/registry.py` lines 235-291
- inject_callable pattern for construction from `hopscotch/registry.py` lines 113-164
- get_best_match resolution logic from `hopscotch/registry.py` lines 235-291
- IsNoneType marker for no-context registrations

**Backend Patterns to Follow:**
- Registry and Container abstractions from svcs
- get() and get_abstract() for service resolution
- Sync/async dual implementation pattern
- Dataclass-based injector structure
- Parent registry fallback pattern

**Similar Features to Model After:**
- KeywordInjector's field resolution approach
- KeywordInjector's validation logic
- KeywordAsyncInjector's async resolution pattern
- Hopscotch's registration and resolution architecture

### Scope Boundaries

**In Scope:**
- New HopscotchLocator class/protocol
- Registration dataclass with metadata (implementation, kind, context, field_infos, is_singleton)
- Nested defaultdict storage structure (dict[type, KindGroups])
- Multiple registrations for the same protocol interface
- LIFO ordering (later registrations override earlier ones)
- Three-tier BASIC precedence resolution (high/medium/low)
- get_best_match() method for finding appropriate registration
- Parent registry fallback
- Exception raising (LookupError) when no matches found
- Both synchronous and asynchronous implementations
- inject_callable pattern for construction
- Following KeywordInjector patterns and structure
- Explicit default registration behavior (no context = IsNoneType key)
- Props/kwargs support for construction overrides
- Infrastructure for future container setup logic

**Out of Scope (Deferred to Future Specs):**
- Context-specific service resolution LOGIC (Roadmap Item 6)
  - Context matching is stored but only BASIC precedence is used
  - Advanced context resolution deferred to Item 6
- Location-based service resolution (Roadmap Item 7)
  - Location metadata stored but NOT used for resolution yet
- Advanced precedence and scoring system (Roadmap Item 8)
  - Only basic three-tier precedence in this spec
  - Weights, priorities, and advanced scoring deferred to Item 8
- Container setup and registration processing (Roadmap Item 9)
  - Only basic infrastructure provided
  - Two-pass matching and container-local registration deferred
- Advanced examples for context resolution (Roadmap Item 10)
- Auto-discovery scanning (Roadmap Item 11)
- Field operators (Roadmap Item 12)

**Future Enhancements Mentioned:**
- Advanced context-aware resolution with scoring weights
- Location/path-based service resolution (PurePath)
- Intelligent precedence rules with complex scoring
- System vs site registration priority
- Multi-tenant, customer vs employee patterns
- Location-based routing examples
- Two-pass matching: (1) location OR context, (2) location AND context
- Container-local vs registry-global registration processing

### Technical Considerations

**Integration Points:**
- Built on top of svcs Registry and Container abstractions
- Uses svcs.Container.get() and get_abstract() methods
- Integrates with FieldInfo and get_field_infos from svcs_di.auto
- Follows patterns from KeywordInjector implementation
- Adapts patterns from Hopscotch Registry implementation
- Uses nested defaultdict for storage
- Parent registry references for fallback

**Existing System Constraints:**
- Must work with Python 3.14+ (modern type hints and protocol support)
- Must be compatible with free-threaded Python (PEP 703)
- Must support both sync and async resolution
- Must maintain svcs' non-magical, explicit approach
- Must use protocols for interface-based programming
- Must provide full type safety and IDE support
- Must handle singleton vs class registrations differently

**Technology Preferences:**
- Python 3.14+ type hints, protocols, dataclasses
- svcs library for Registry and Container
- Dataclass-based structure for injectors and registrations
- Protocol-based interfaces for type safety
- No dependencies beyond Python stdlib and svcs
- defaultdict from collections for nested storage
- Union types for flexible type annotations

**Similar Code Patterns to Follow:**
- KeywordInjector's three-tier precedence approach
- Dual sync/async implementation pattern
- Dataclass-based injector with container field
- Field validation with clear error messages
- Resolution logic that returns tuples (has_value, value)
- Use of get_field_infos for introspection
- Hopscotch's Registration dataclass pattern
- Hopscotch's KindGroups nested storage
- Hopscotch's three-tier precedence (high/medium/low)
- Hopscotch's inject_callable construction pattern
- Hopscotch's get_best_match resolution logic
- Hopscotch's parent registry fallback pattern
- LIFO ordering with list.insert(0, registration)

**Key Implementation Details:**
1. Registration dataclass must extract field_infos automatically (unless singleton)
2. Storage uses nested defaultdict: type -> KindGroups -> context -> list[Registration]
3. IsNoneType is a marker class for no-context registrations
4. get_best_match() creates three precedence lists and concatenates them
5. First match from concatenated list wins (LIFO within each precedence level)
6. LookupError raised when no matches found and no parent registry
7. Singletons returned directly, classes constructed via inject_callable
8. Props/kwargs have highest precedence during construction
9. Context metadata stored but only basic three-tier matching used (defer advanced to Item 8)
10. Location metadata stored but NOT used (defer to Item 7)
