# Spec Requirements: Context-Specific Service Resolution

## Initial Description

This is roadmap item 6 from the project. The user wants to implement context-specific service resolution as the next
feature after completing the multiple service registrations (roadmap item 5, which included ServiceLocator and
HopscotchInjector).

The goal is to enhance the existing ServiceLocator and HopscotchInjector implementation to better support context-based
service resolution with improved terminology, caching, and reference to proven patterns from the Hopscotch project.

## Requirements Discussion

### First Round Questions

**Q1: Context Matching Strategies** - What matching logic should be used for context resolution?
**Answer:** Change the word `Context` to `Resource`. Focus on business entities. Follow the same logic and
implementation that Hopscotch does, which looks like `is` and `isinstance`, unless there is a better idea.

**Q2: Scope Boundaries** - What aspects of context-specific resolution should be included?
**Answer:** Context improvements only (now called Resource).

**Q3: Context Hierarchies** - How should the system handle context hierarchies and inheritance?
**Answer:** Keep the single approach but change the name from `context_key` to `resource`.

**Q4: Performance & Caching** - What caching strategy should be used for context lookups?
**Answer:** See if there is a way to easily use a `svcs` style cache. For the case where the only lookup "predicate" is
`Resource`, that information never changes after import-time and building the map. It should be very cacheable,
hopefully using `svcs` caching.

**Q5: Architecture Integration** - How does this fit with the existing implementation?
**Answer:** Existing but it dispatches to helpers.

**Q6: Context Transformation** - How should context values be transformed for matching?
**Answer:** Current approach (clean type from container).

**Q7: Multi-Attribute Contexts** - How should multi-attribute context matching work?
**Answer:** Current approach (class-based).

**Q8: Explicit Exclusions** - What features should NOT be included in this implementation?
**Answer:** Leave out complex scoring, location-based matching, registration validation, lifecycle management, and
middleware integration.

### Existing Code to Reference

**Similar Features Identified:**

- Feature: Hopscotch implementation - Path: `/Users/pauleveritt/projects/pauleveritt/hopscotch/`
- Description: Hopscotch has a feature-ful implementation with lots of tests. Reference implementation patterns and test
  cases from there, especially for re-using tests.
- Pattern focus: `is` and `isinstance` matching patterns for resource resolution

**Current Implementation to Enhance:**

- File: `src/svcs_di/injectors/locator.py` - ServiceLocator and HopscotchInjector classes
- File: `tests/test_locator.py` - 22 comprehensive tests covering current functionality
- Current features:
    - Three-tier precedence: exact > subclass > default
    - LIFO ordering for overrides
    - Single locator for all service types
    - Support for multiple service types in one locator
    - HopscotchInjector with Injectable[T] field support
    - Async support via HopscotchAsyncInjector

### Follow-up Questions

None required - all requirements clarified in first round.

## Visual Assets

### Files Provided:

No visual files found.

### Visual Insights:

No visual assets provided.

## Requirements Summary

### Functional Requirements

**Core Functionality:**

- Rename all `context` terminology to `resource` throughout the codebase
- Focus on business entity matching (e.g., Customer, Employee, Product) rather than request contexts
- Implement `is` and `isinstance` matching logic following Hopscotch patterns
- Add svcs-style caching for resource-based lookups
- Maintain existing three-tier precedence system (exact > subclass > default)
- Maintain existing LIFO ordering for registration overrides

**Specific Renaming Required:**

1. `context` parameter → `resource` parameter
2. `context_key` → `resource` (in HopscotchInjector configuration)
3. `request_context` → `resource` (in matching logic)
4. `FactoryRegistration.context` field → `FactoryRegistration.resource` field
5. Method names: `_get_request_context()` → `_get_resource()`
6. Variable names throughout implementation

**Caching Strategy:**

- Leverage svcs caching mechanisms where possible
- Cache resource-to-implementation mappings at import time
- Since resource type information is static after imports, the lookup map should be highly cacheable
- Investigate svcs.Registry caching patterns for inspiration
- Goal: Fast O(1) lookups after initial map construction

### Reusability Opportunities

**From Hopscotch:**

- Study and adapt the `is` and `isinstance` matching implementation
- Reuse test patterns and test cases from Hopscotch's test suite
- Reference Hopscotch's approach to resource-based resolution
- Path to reference: `/Users/pauleveritt/projects/pauleveritt/hopscotch/`

**From Current Implementation:**

- Reuse FactoryRegistration matching logic (with terminology updates)
- Reuse ServiceLocator registration and lookup structure
- Reuse HopscotchInjector's three-tier precedence system
- Reuse existing test infrastructure (22 tests in test_locator.py)

### Scope Boundaries

**In Scope:**

- Terminology changes: context → resource throughout codebase
- Enhanced matching using `is` and `isinstance` patterns from Hopscotch
- Caching implementation using svcs-style patterns
- Focus on business entity resources (Customer, Employee, Product types)
- Maintain backward compatibility with existing three-tier precedence
- Maintain existing LIFO override behavior
- Update all tests to reflect new terminology
- Update docstrings and comments to reflect resource-based thinking

**Out of Scope:**

- Complex scoring algorithms beyond existing three-tier system
- Location-based matching
- Registration validation beyond current implementation
- Lifecycle management features
- Middleware integration
- Changes to Injectable[T] field resolution logic (keep existing)
- Changes to async support (keep existing HopscotchAsyncInjector)

### Technical Considerations

**Integration Points:**

- ServiceLocator.register() method - rename context parameter to resource
- ServiceLocator.get_implementation() method - rename request_context parameter to resource
- FactoryRegistration.matches() method - rename request_context parameter to resource
- HopscotchInjector.context_key attribute - rename to resource
- HopscotchInjector._get_request_context() method - rename to _get_resource()
- HopscotchAsyncInjector (async version) - apply same renamings

**Existing System Constraints:**

- Must maintain compatibility with svcs.Container and svcs.Registry
- Must work with existing Injectable[T] type hint system
- Must preserve three-tier precedence: exact match (2) > subclass match (1) > default (0)
- Must preserve LIFO ordering for registrations
- Must continue to raise LookupError when no implementation matches

**Technology Stack:**

- Python 3.12+ (using modern type hints with generic syntax)
- svcs library for container/registry
- dataclasses for data structures
- pytest for testing
- pytest-anyio for async testing

**Similar Code Patterns to Follow:**

- Hopscotch's resource matching patterns (is/isinstance checks)
- Hopscotch's test organization and coverage
- Current ServiceLocator registration and lookup patterns
- Current three-tier precedence scoring system
- Current LIFO override mechanism

**Performance Goals:**

- Achieve O(1) or near-O(1) lookups after initial cache construction
- Minimize overhead for resource type extraction from container
- Cache resource-to-implementation mappings when possible
- Leverage svcs caching infrastructure to avoid rebuilding maps

### Key Design Decisions

1. **Terminology Shift:** Moving from "context" to "resource" emphasizes business entities over request-scoped contexts,
   making the API more intuitive for domain modeling.

2. **Hopscotch Alignment:** Following Hopscotch's proven `is` and `isinstance` patterns provides battle-tested matching
   logic and comprehensive test coverage to adapt.

3. **Caching Priority:** Resource type information is static after import time, making it an ideal candidate for
   caching. This should significantly improve performance for repeated lookups.

4. **Minimal Scope:** Focusing only on terminology and caching improvements (not expanding features) keeps the change
   focused and reduces risk.

5. **Backward Compatibility:** Maintaining existing three-tier precedence and LIFO ordering ensures existing code
   continues to work as expected.
