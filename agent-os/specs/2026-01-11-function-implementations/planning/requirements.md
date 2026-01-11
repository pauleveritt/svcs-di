# Spec Requirements: Function Implementations

## Initial Description

Feature 16 from the roadmap: Allow factories to be functions, both for manual registrations and decorator. Have examples for DefaultInjector, KeywordInjector, and HopscotchInjector, plus docs for the examples.

The roadmap mentions:
> "Function Implementations - Read `docs/function_implementations_plan.md` for instructions. Allow factories to be functions, both for manual registrations and decorator. Have examples for DefaultInjector, KeywordInjector, and HopscotchInjector, plus docs for the examples."

Currently, svcs-di only supports class-based implementations. The `@injectable` decorator raises TypeError for non-classes, and registration methods expect classes. This feature would allow functions to serve as factory providers that create and return service instances.

## Requirements Discussion

### First Round Questions

**Q1:** When you say "function implementations," I assume this means allowing functions to be registered as factory providers (like `register_implementation(Greeting, create_greeting_func)` where the function returns a Greeting instance). Is that correct, or do you also want to support "the function itself is the service" patterns?
**Answer:** Correct - Function implementations means allowing functions to be registered as factory providers (like `register_implementation(Greeting, create_greeting_func)` where the function returns a Greeting instance)

**Q2:** For the "function as service" pattern, should we support cases where calling the function IS the service behavior (e.g., registering a `calculate_tax` function that consumers call directly), or should functions only be factory functions that return objects?
**Answer:** Do not support where the function is the service - Only factory functions that return objects, not pure functions as services

**Q3:** For the `@injectable` decorator on functions, I'm assuming the syntax should be identical to class usage (`@injectable` and `@injectable(for_=X, resource=Y)`). Should the decorator work exactly the same way, or should functions have different options?
**Answer:** Identical - The `@injectable` decorator syntax should be identical for both classes and functions (`@injectable` and `@injectable(for_=X, resource=Y)`)

**Q4:** For function parameter injection, should the injector automatically resolve function parameters (like it does for dataclass fields), or should function authors manually call the injector within the function body?
**Answer:** Automatic - The injector should automatically resolve function parameters (like it does for dataclass fields) for parameters marked with `Inject[T]`

**Q5:** Should `register_implementation()` be overloaded to accept both classes and functions, or should there be a separate method like `register_factory_function()`?
**Answer:** Overloading - Overload the existing `register_implementation()` method to accept `Callable` in addition to `type`, no separate method

**Q6:** For async functions, I assume we should support them in the same way we support async dataclass injection. Is that correct?
**Answer:** Same - Support async functions in the same way we support async dataclass injection

**Q7:** Is there anything you explicitly want OUT of scope for this feature? For example, should we exclude lambda support, generator functions, or partial functions?
**Answer:** Yes - During implementation, we decided to exclude lambdas, partials, and generator functions to simplify the implementation. Only named functions (`def`) are supported.

### Existing Code to Reference

No similar existing features identified for reference by the user. However, based on initialization analysis:

- **Current class injection patterns**: `src/svcs_di/` - the existing `@injectable` decorator and registration methods
- **Function injection (target side)**: `examples/basic_function.py` - shows functions receiving injected dependencies
- **Async patterns**: `examples/async_injection.py` - shows async injection patterns to follow

### Follow-up Questions

No follow-up questions were needed.

## Visual Assets

### Files Provided:
No visual assets provided.

### Visual Insights:
N/A

## Requirements Summary

### Functional Requirements
- Functions can be registered as factory providers via `register_implementation(ServiceType, factory_function)`
- The `@injectable` decorator works on functions with similar syntax to classes (`@injectable(for_=X)` and `@injectable(for_=X, resource=Y)`)
- Functions MUST specify `for_` parameter (return type inference is NOT supported)
- Function parameters marked with `Inject[T]` are automatically resolved by the injector
- Async factory functions are supported with the same patterns as async class injection
- Only named functions (`def`) are supported; lambdas, generators, and partials are NOT supported

### Reusability Opportunities
- Existing `@injectable` decorator implementation to extend
- Current `register_implementation()` method to overload
- Async injection patterns already established in the codebase
- Parameter resolution logic from dataclass field injection

### Scope Boundaries
**In Scope:**
- Named factory functions (`def`) that return objects/instances
- `@injectable(for_=X)` decorator support for functions (for_ is required)
- Automatic parameter injection via `Inject[T]` type hints
- Overloaded `register_implementation()` accepting `Callable`
- Async factory function support
- Examples for DefaultInjector, KeywordInjector, and HopscotchInjector
- Documentation for all examples

**Out of Scope:**
- Pure functions as services (where the function itself is the service behavior)
- Separate registration method for functions (will use overloaded existing method)
- Lambda functions (lack proper introspection)
- `functools.partial` wrapped functions (don't pass `inspect.isfunction()`)
- Generator functions as factory providers
- Return type inference for functions (must specify `for_` explicitly)

### Technical Considerations
- Must maintain backward compatibility with existing class-based registration
- The `@injectable` decorator currently raises TypeError for non-classes - this needs to change
- Functions must explicitly specify `for_` parameter (no return type inference)
- Function parameter inspection differs from dataclass field inspection - uses `_get_callable_field_infos()`
- Use `inspect.isfunction()` to detect named functions (excludes lambdas and partials)
- `DecoratedItem` type alias used for scanned items: `tuple[Implementation, InjectableMetadata]`
