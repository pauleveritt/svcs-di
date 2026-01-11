# Spec Initialization: Function Implementations

## Raw Idea

Feature 16 from the roadmap: Allow factories to be functions, both for manual registrations and decorator. Have examples for DefaultInjector, KeywordInjector, and HopscotchInjector, plus docs for the examples.

## Context from Roadmap

This is feature #16 in the product roadmap. The roadmap mentions:
> "Function Implementations - Read `docs/function_implementations_plan.md` for instructions. Allow factories to be functions, both for manual registrations and decorator. Have examples for DefaultInjector, KeywordInjector, and HopscotchInjector, plus docs for the examples."

Note: The referenced `docs/function_implementations_plan.md` file does not currently exist.

## Current State Analysis

### Existing Patterns

1. **Class/Dataclass Implementations**: Currently, svcs-di registers implementations as classes. The `@injectable` decorator only works with classes (raises TypeError for non-classes). Examples use dataclasses exclusively.

2. **Function Injection (Target Side)**: The `DefaultInjector` and other injectors already support calling functions with injected dependencies - see `examples/basic_function.py`. However, this is different from registering functions as *implementations*.

3. **Registration Methods**:
   - `registry.register_factory(ServiceType, auto(ServiceClass))` - uses `auto()` wrapper
   - `registry.register_implementation(ServiceType, ImplClass)` - HopscotchRegistry method
   - `@injectable` decorator - marks classes for scanning

### The Gap

Currently, if you want to provide a service via a function (e.g., a factory function that creates an object, or a function that computes a value), you cannot:
- Use `@injectable` on a function
- Register a function directly with `register_implementation()`
- Have the ServiceLocator resolve function-based implementations

### What "Function Implementations" Would Mean

Functions could serve as implementations in several ways:
1. **Factory functions** that create and return objects
2. **Pure functions** that compute values (the function itself is the "service")
3. **Async functions** for either of the above
