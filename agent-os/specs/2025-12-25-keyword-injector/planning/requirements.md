# Spec Requirements: Keyword Injector

## Initial Description

Creating a KeywordInjector to extract kwargs functionality from DefaultInjector. The goal is to make DefaultInjector simpler by removing kwargs handling and moving it to a new, specialized injector. KeywordInjector should support both sync and async (ideally async wrapping sync), be designed as a base for future injectors via helpers, and require no backwards compatibility.

## Requirements Discussion

### First Round Questions

**Q1:** I assume we want to create a new directory structure `src/svcs_di/injectors/` to house the KeywordInjector and future injectors. Is that correct, or should KeywordInjector remain in the main `auto.py` module?
**Answer:** Correct

**Q2:** I'm thinking DefaultInjector should become even simpler - just handling Injectable[T] resolution without any kwargs support at all. Should we remove kwargs functionality from DefaultInjector?
**Answer:** Correct, remove kwargs functionality from DefaultInjector.

**Q3:** For the helper functions to make it easy to write injectors, I assume you want utility functions that can be reused (like `get_field_infos`, `_resolve_field_value`, etc.) rather than base classes to inherit from. Is that correct?
**Answer:** Utility and helper functions not base classes

**Q4:** I assume the examples that currently demonstrate kwargs (like `examples/kwargs_override.py`) should be moved to `examples/keyword/first_example.py` etc. Is that correct?
**Answer:** Correct

**Q5:** Since you mentioned "no backwards compatibility needed", I assume we can make breaking changes to the DefaultInjector API if necessary. Is that correct?
**Answer:** No backwards compatibility.

**Q6:** For tests, should we keep the existing tests for DefaultInjector (removing kwargs-related ones) and create comprehensive tests for KeywordInjector in `tests/injectors/test_keyword_injector.py`?
**Answer:** Yes

**Q7:** I'm thinking the tests should focus on protocol compliance - ensuring KeywordInjector matches the Injector/AsyncInjector protocols - and basic functionality. Should we also move the complex kwargs precedence tests to the KeywordInjector tests?
**Answer:** Remove all keyword-oriented tests from existing tests and move them to tests/injectors/test_keyword_injector.py with simple tests that ensure protocol compliance. Remember, no @runtime_checkable in `src/svcs_di`.

**Q8:** For async support, you mentioned "ideally async wrapping sync". Should we design KeywordAsyncInjector to delegate to KeywordInjector for the sync logic, then await any async dependencies?
**Answer:** Also refactor the async versions to extract kwargs, if needed. But it would be great if the async implementation could "wrap" the sync.

**Extra point:** Design KeywordInjector to also be the base of future injectors via helpers etc

### Existing Code to Reference

No similar existing features identified for reference beyond the current DefaultInjector implementation which serves as the source for extraction.

### Follow-up Questions

None - all requirements clearly specified.

## Visual Assets

### Files Provided:

No visual assets provided.

## Requirements Summary

### Functional Requirements

**Core Functionality:**
- Extract kwargs handling from DefaultInjector into KeywordInjector
- Create new directory structure: `src/svcs_di/injectors/`
- KeywordInjector implements the Injector protocol with kwargs support
- KeywordAsyncInjector implements the AsyncInjector protocol, wrapping sync implementation
- DefaultInjector simplified to only handle Injectable[T] resolution without kwargs
- DefaultAsyncInjector simplified similarly

**Three-Tier Precedence (in KeywordInjector only):**
1. kwargs passed to injector (highest priority - override everything)
2. container.get(T) or container.get_abstract(T) for Injectable[T] fields
3. default values from parameter/field definitions

**Helper Functions for Injector Authors:**
- Refactor reusable utilities into helper module (not base classes)
- Functions like `get_field_infos`, `_resolve_field_value`, `is_injectable`, etc.
- Design helpers to make writing new injectors straightforward
- KeywordInjector should serve as reference implementation using these helpers

**Protocol Compliance:**
- No @runtime_checkable decorator in `src/svcs_di` code
- KeywordInjector must implement Injector protocol: `__call__[T](self, target: type[T], **kwargs: Any) -> T`
- KeywordAsyncInjector must implement AsyncInjector protocol: `async __call__[T](self, target: type[T], **kwargs: Any) -> T`

**Async Implementation:**
- KeywordAsyncInjector should wrap KeywordInjector's sync logic where possible
- Avoid duplicating logic between sync and async versions
- Use async variants only where necessary (container.aget vs container.get)

### Code Organization

**Source Structure:**
```
src/svcs_di/
├── __init__.py                    # Update exports
├── auto.py                        # Simplified DefaultInjector, auto() function
├── injectors/
│   ├── __init__.py               # Export KeywordInjector
│   ├── keyword.py                # KeywordInjector + KeywordAsyncInjector
│   └── helpers.py                # Reusable helper functions
└── py.typed
```

**Test Structure:**
```
tests/
├── test_auto.py                   # Keep, remove kwargs tests
├── test_injector.py               # Keep, remove kwargs tests
├── test_injectable.py             # Keep as-is
├── injectors/
│   ├── __init__.py
│   └── test_keyword_injector.py  # All kwargs tests + protocol compliance
└── test_examples.py               # Update for new example paths
```

**Examples Structure:**
```
examples/
├── basic_dataclass.py             # Keep
├── protocol_injection.py          # Keep
├── async_injection.py             # Keep
├── custom_injector.py             # Keep
├── keyword/
│   ├── first_example.py          # Moved from kwargs_override.py
│   └── (future keyword examples)
└── (other example categories as needed)
```

### Changes to Existing Code

**DefaultInjector (in auto.py):**
- Remove kwargs parameter validation (`_validate_kwargs` method)
- Remove kwargs handling from `__call__` method
- Simplify to only resolve Injectable[T] fields from container
- Keep default value fallback (Tier 3)
- NO kwargs support at all

**DefaultAsyncInjector (in auto.py):**
- Remove kwargs parameter validation
- Remove kwargs handling from `async __call__` method
- Simplify to only resolve Injectable[T] fields from container
- Keep default value fallback (Tier 3)
- NO kwargs support at all

**_BaseInjector (in auto.py):**
- Remove entirely OR remove `_validate_kwargs` method if base class remains useful
- If it only contained kwargs validation, delete the class

**Helper Functions (move to injectors/helpers.py):**
- `get_field_infos(target)` - extract field/parameter metadata
- `is_injectable(type_hint)` - check if type is Injectable[T]
- `extract_inner_type(type_hint)` - get T from Injectable[T]
- `is_protocol_type(cls)` - check if type is a Protocol
- `_get_dataclass_field_infos(target)` - dataclass-specific extraction
- `_get_callable_field_infos(target)` - function parameter extraction
- Any other utilities that make writing injectors easier

### New Code Requirements

**KeywordInjector (injectors/keyword.py):**
- Implement Injector protocol
- Support kwargs with three-tier precedence
- Use helper functions from helpers.py
- Validate kwargs match actual field names
- Handle Injectable[T] resolution from container
- Support default values
- Designed to be extensible for future injectors

**KeywordAsyncInjector (injectors/keyword.py):**
- Implement AsyncInjector protocol
- Wrap KeywordInjector's sync logic where possible
- Only use async variants where necessary (aget, aget_abstract)
- Same three-tier precedence as sync version

**Helpers Module (injectors/helpers.py):**
- Clean, documented utility functions
- Type-safe with proper type hints
- Reusable across different injector implementations
- Include field resolution logic
- Include type introspection utilities

### Test Requirements

**tests/test_injector.py Changes:**
- Remove `test_injector_kwarg_precedence`
- Remove `test_injector_kwargs_override_defaults`
- Remove `test_injector_validates_kwargs`
- Keep all other tests (container resolution, protocol handling, defaults, etc.)
- Ensure DefaultInjector tests don't use kwargs

**tests/test_auto.py Changes:**
- Remove kwargs-related test cases
- Keep all auto() factory tests
- Keep nested dependency tests
- Keep protocol-based injection tests

**tests/injectors/test_keyword_injector.py (NEW):**
- Protocol compliance tests (verify it matches Injector/AsyncInjector protocol)
- Kwargs precedence tests (3-tier system)
- Kwargs validation tests (unknown params raise ValueError)
- Injectable[T] resolution with kwargs override
- Default value fallback with kwargs override
- Protocol-based injection with kwargs
- Async version tests with mixed dependencies
- Simple, focused tests demonstrating correct behavior
- NO @runtime_checkable in test code

### Documentation Requirements

**Update README/docs to reflect:**
- DefaultInjector is now simpler (no kwargs)
- KeywordInjector available for kwargs support
- How to use KeywordInjector as custom injector
- Examples showing when to use each injector type

**Example Updates:**
- Move kwargs_override.py → examples/keyword/first_example.py
- Update any documentation referencing kwargs in DefaultInjector
- Show KeywordInjector as example of custom injector pattern

### Scope Boundaries

**In Scope:**
- Extract kwargs functionality to KeywordInjector
- Simplify DefaultInjector (remove all kwargs support)
- Create injectors/ directory structure
- Refactor helpers into reusable module
- Move and update tests appropriately
- Move and update examples
- Both sync and async implementations
- Protocol compliance without @runtime_checkable

**Out of Scope:**
- Changes to Injectable[T] marker type
- Changes to auto() or auto_async() functions (except removing kwargs)
- Changes to field introspection logic (just moving it)
- New features beyond kwargs handling
- Backwards compatibility with existing kwargs usage in DefaultInjector
- Integration with __svcs__ custom construction (feature was reverted)
- Advanced injector implementations (those come later)

### Technical Considerations

**Breaking Changes:**
- DefaultInjector no longer accepts kwargs - BREAKING
- Users who rely on kwargs must switch to KeywordInjector
- auto() function signature unchanged but behavior changes if custom injector registered

**Migration Path:**
- Register KeywordInjector as DefaultInjector replacement:
  ```python
  from svcs_di.injectors import KeywordInjector
  registry.register_factory(DefaultInjector, lambda c: KeywordInjector(container=c))
  ```

**Design for Future Extensibility:**
- Helpers designed to be reusable by HopscotchInjector and others
- KeywordInjector serves as reference implementation
- Clean separation of concerns (resolution, validation, construction)
- Protocol-based design allows easy substitution

**No @runtime_checkable:**
- Protocol definitions in src/svcs_di/auto.py should NOT use @runtime_checkable
- Tests can check duck-typing behavior without runtime validation
- Rely on static type checkers (mypy, pyright) instead

**Async Wrapping Sync:**
- KeywordAsyncInjector should reuse KeywordInjector's logic
- Only differ in using aget/aget_abstract instead of get/get_abstract
- Avoid code duplication between sync and async
- Consider composition over inheritance
