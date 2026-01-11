# Specification: Function Implementations

## Goal

Enable functions to serve as factory providers in svcs-di, allowing registration via `register_implementation()` and the
`@injectable` decorator with identical syntax to class-based implementations.

## User Stories

- As a developer, I want to register functions as factory providers so that I can use simpler, functional patterns
  instead of always creating classes for service creation.
- As a developer, I want the `@injectable` decorator to work identically on functions and classes so that I have a
  consistent API regardless of implementation style.

## Specific Requirements

**Extend register_implementation() to Accept Callables**

- Overload `HopscotchRegistry.register_implementation()` to accept `Callable` in addition to `type`
- The callable must return an instance compatible with the service type
- Use return type annotation inference to validate the factory function returns the correct type
- Maintain full backward compatibility with existing class-based registrations

**Extend @injectable Decorator for Functions**

- Remove the `TypeError` check in `_mark_injectable()` that restricts to classes only (line 56-61 in decorators.py)
- Use `inspect.isfunction()` to detect named function targets (lambdas and partials are NOT supported)
- Support both `@injectable` and `@injectable(for_=X, resource=Y)` syntax on functions
- Functions MUST specify `for_` parameter explicitly (return type inference is NOT supported for simplicity)
- Classes can omit `for_` (defaults to the class itself); functions cannot

**Automatic Parameter Injection for Functions**

- Extend `_get_callable_field_infos()` in auto.py to handle function parameters marked with `Inject[T]`
- The existing logic already handles callables via `_get_callable_field_infos()` - ensure it works for factory function
  patterns
- Function parameters with `Inject[T]` annotations are automatically resolved from the container
- Non-injectable parameters with defaults continue to use their default values

**Async Factory Function Support**

- Support async functions with `async def create_service(...) -> ServiceType` pattern
- Use `inspect.iscoroutinefunction()` to detect async functions (already used in keyword.py and hopscotch.py)
- Async factory functions are awaited when resolving dependencies
- Follow the same patterns established in `DefaultAsyncInjector` and `KeywordAsyncInjector`

**Scanning Integration for Functions**

- Update `_create_injector_factory()` in scanning.py to handle function targets
- Use `inspect.isfunction()` to differentiate between class and function targets
- For functions, the factory wraps the function call with dependency injection
- The scan() function should discover and register `@injectable` decorated functions

**Examples for All Injector Types**

- Create example file for DefaultInjector with function factory: `examples/function/default_injector.py`
- Create example file for KeywordInjector with function factory: `examples/function/keyword_injector.py`
- Create example file for HopscotchInjector with function factory: `examples/function/hopscotch_injector.py`
- Each example should demonstrate: registration, parameter injection, and usage

**Documentation for Examples**

- Create doc file `docs/function/index.md` with overview of function implementations
- Create doc file `docs/function/default_injector.md` documenting the DefaultInjector example
- Create doc file `docs/function/keyword_injector.md` documenting the KeywordInjector example
- Create doc file `docs/function/hopscotch_injector.md` documenting the HopscotchInjector example
- Include doctest-compatible code snippets in documentation

**Lambda and Special Callable Support**

- Lambda functions are NOT supported (they lack proper introspection and `__name__`)
- `functools.partial` wrapped functions are NOT supported (they don't pass `inspect.isfunction()`)
- Only named functions defined with `def` are supported for scanning
- Generator functions are out of scope for this implementation

## Existing Code to Leverage

**`_get_callable_field_infos()` in src/svcs_di/auto.py**

- Already handles function parameter extraction via `inspect.signature()`
- Extracts `Inject[T]` annotations from function parameters
- Can be reused directly for factory function parameter injection

**`_mark_injectable()` in src/svcs_di/injectors/decorators.py**

- Current implementation raises TypeError for non-classes
- The type check at line 56-61 needs modification to allow functions
- The `InjectableMetadata` TypedDict can store metadata on functions via `setattr`

**Async patterns in src/svcs_di/injectors/keyword.py and hopscotch.py**

- `inspect.iscoroutinefunction()` detection pattern already established
- `cast(Awaitable[T], result)` pattern for awaiting async callables
- Resolution helper functions handle both sync and async cases

**`register_implementation()` in src/svcs_di/hopscotch_registry.py**

- Currently accepts `type` for implementation parameter
- Type signature needs to be broadened to `type | Callable[..., T]`
- ServiceLocator.register() may also need similar updates

**examples/basic_function.py and examples/async_injection.py**

- Show existing patterns for function injection (target side, not factory side)
- The `create_result()` function pattern demonstrates `Inject[T]` on function parameters
- These patterns should be mirrored for factory functions

## Out of Scope

- Pure functions as services (where calling the function IS the service behavior)
- Separate registration method for functions (e.g., `register_factory_function()`)
- Function overloading or dispatch based on argument types
- Decorator stacking order enforcement beyond current dataclass conventions
- Runtime type checking of factory function return values
- Automatic protocol implementation verification for function returns
- Function-based resource cleanup or context manager patterns
- Caching or memoization of factory function results
- Thread-safety guarantees beyond what svcs already provides
- Support for class methods or static methods as factory functions
- Lambda functions as factory providers (lack proper introspection)
- `functools.partial` wrapped functions (don't pass `inspect.isfunction()`)
- Return type inference for functions (functions must specify `for_` explicitly)
- Generator functions as factory providers
