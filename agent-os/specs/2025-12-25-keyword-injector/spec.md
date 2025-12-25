# Specification: Keyword Injector

## Goal
Extract kwargs handling from DefaultInjector into a specialized KeywordInjector, simplifying DefaultInjector to only handle Injectable[T] resolution while creating reusable helper functions for future injector implementations.

## User Stories
- As a developer, I want DefaultInjector to be simpler and focused only on Injectable[T] resolution without kwargs complexity
- As a library user, I want to use KeywordInjector when I need kwargs override support with three-tier precedence
- As an injector author, I want reusable helper functions to easily create custom injectors that match the protocol

## Specific Requirements

**Create src/svcs_di/injectors/ directory structure**
- New directory `src/svcs_di/injectors/` to house specialized injectors
- `__init__.py` exports KeywordInjector and KeywordAsyncInjector
- `keyword.py` contains KeywordInjector and KeywordAsyncInjector implementations
- Update `src/svcs_di/__init__.py` to export KeywordInjector from injectors module
- **Important:** Helper functions stay in `auto.py` to keep DefaultInjector standalone

**Simplify DefaultInjector to remove all kwargs support**
- Remove `_validate_kwargs` method from _BaseInjector class
- Remove kwargs parameter validation logic from DefaultInjector.__call__
- Remove kwargs parameter validation logic from DefaultAsyncInjector.__call__
- Keep only two-tier precedence: container.get() for Injectable[T], then default values
- No kwargs override capability in DefaultInjector at all
- Delete _BaseInjector class if it becomes empty after removing kwargs validation

**Extract kwargs logic to KeywordInjector**
- Implement Injector protocol: `__call__[T](self, target: type[T], **kwargs: Any) -> T`
- Support three-tier precedence: kwargs (highest), container.get(T), defaults (lowest)
- Validate kwargs match actual field names, raise ValueError for unknown params
- Use helper functions from helpers.py for field resolution and type introspection
- Handle Injectable[T] resolution using container.get() or container.get_abstract()
- Support both dataclass fields and function parameters

**Implement KeywordAsyncInjector wrapping sync logic**
- Implement AsyncInjector protocol: `async __call__[T](self, target: type[T], **kwargs: Any) -> T`
- Reuse KeywordInjector's sync logic where possible to avoid duplication
- Only use async variants where necessary: container.aget() and container.aget_abstract()
- Maintain same three-tier precedence as sync version
- Same kwargs validation as sync version

**Create helpers.py with reusable injector utilities**
- Move `get_field_infos(target)` from auto.py to extract field/parameter metadata
- Move `is_injectable(type_hint)` to check if type is Injectable[T]
- Move `extract_inner_type(type_hint)` to get T from Injectable[T]
- Move `is_protocol_type(cls)` to check if type is a Protocol
- Move `_get_dataclass_field_infos(target)` for dataclass-specific extraction
- Move `_get_callable_field_infos(target)` for function parameter extraction
- Move FieldInfo NamedTuple to helpers.py as it's used by helper functions
- Keep all functions type-safe with proper type hints and documentation

**Update test structure for injectors**
- Remove kwargs tests from tests/test_injector.py: test_injector_kwarg_precedence, test_injector_kwargs_override_defaults, test_injector_validates_kwargs
- Remove kwargs tests from tests/test_auto.py if any exist
- Create tests/injectors/ directory with __init__.py
- Create tests/injectors/test_keyword_injector.py with all kwargs-related tests
- Include protocol compliance tests verifying Injector/AsyncInjector protocol match
- No @runtime_checkable decorator usage in test code
- Simple focused tests demonstrating three-tier precedence and kwargs validation

**Reorganize examples for keyword injection**
- Create examples/keyword/ directory
- Move examples/kwargs_override.py to examples/keyword/first_example.py
- Update example to show KeywordInjector usage instead of DefaultInjector
- Keep existing examples (basic_dataclass.py, protocol_injection.py, async_injection.py, custom_injector.py)
- Update tests/test_examples.py to reflect new example paths

**Protocol compliance without @runtime_checkable**
- Remove @runtime_checkable decorator from Injector protocol definition if present
- Remove @runtime_checkable decorator from AsyncInjector protocol definition if present
- Rely on structural typing and static type checkers (mypy, pyright)
- Tests verify duck-typing behavior without runtime protocol checks
- Keep @runtime_checkable in test protocols (like GreeterProtocol) for testing purposes only

**Update auto() and auto_async() functions**
- Keep auto() function signature unchanged: `auto[T](target: type[T]) -> SvcsFactory[T]`
- Keep auto_async() function signature unchanged
- No changes to factory behavior except internal injector simplification
- Users can still register custom injectors like KeywordInjector as replacement for DefaultInjector
- Document migration path in docstrings

## Visual Design
No visual assets provided.

## Existing Code to Leverage

**_BaseInjector class with _validate_kwargs method (src/svcs_di/auto.py lines 60-76)**
- Extract kwargs validation logic to KeywordInjector
- Method validates kwargs match actual field names from FieldInfo list
- Raises ValueError with helpful message showing valid parameter names
- This exact validation logic should be preserved in KeywordInjector
- After extraction, _BaseInjector may be deleted if empty

**_resolve_field_value function (src/svcs_di/auto.py lines 265-296)**
- Implements three-tier precedence: kwargs, container.get(), defaults
- Returns tuple (has_value: bool, value: Any)
- Handles Injectable[T] detection and protocol vs concrete resolution
- Should be adapted for KeywordInjector (currently used by DefaultInjector)
- Keep tier 1 (kwargs) in KeywordInjector, remove from DefaultInjector

**_resolve_field_value_async function (src/svcs_di/auto.py lines 299-330)**
- Async version of _resolve_field_value using aget/aget_abstract
- Same three-tier logic but with async container methods
- KeywordAsyncInjector should reuse this pattern
- DefaultAsyncInjector should use simplified two-tier version

**Helper functions for type introspection (src/svcs_di/auto.py lines 156-262)**
- is_injectable, extract_inner_type, is_protocol_type, get_field_infos
- _get_dataclass_field_infos and _get_callable_field_infos
- FieldInfo NamedTuple definition
- All should move to src/svcs_di/injectors/helpers.py
- Keep same implementation, just new location

**Test patterns from tests/test_injector.py (lines 43-169)**
- test_injector_kwarg_precedence demonstrates kwargs override Injectable params
- test_injector_validates_kwargs shows ValueError for unknown kwargs
- test_injector_kwargs_override_defaults shows kwargs override default values
- test_async_injector_with_mixed_dependencies shows async handling
- All these tests should move to tests/injectors/test_keyword_injector.py

## Out of Scope
- Changes to Injectable[T] marker type definition or behavior
- Changes to auto() or auto_async() function signatures
- Backwards compatibility for DefaultInjector kwargs usage (breaking change accepted)
- Integration with __svcs__ custom construction (feature was reverted)
- New injector features beyond kwargs handling
- Changes to existing field introspection logic beyond moving to helpers.py
- Advanced injector implementations like HopscotchInjector
- Changes to svcs.Container or svcs.Registry behavior
- Migration of existing user code (users must update to KeywordInjector manually)
- Documentation updates beyond code comments and docstrings
