# Basic Function Injection

**Complexity: Beginner**

In `svcs` you register factories by *type*. But what if you want injection on a function? You can't register a function.
In this example, you'll learn how to:

- Register a service
- Write a function with a dependent service that needs injection
- Manually wrap a function call with an injector that resolves the dependency

## Source Code

The complete example is available at `examples/basic_function.py`:

```{literalinclude} ../../examples/basic_function.py
:start-at: from dataclasses
:end-at: return result
```

## Key Concepts

### Functions Can Have Injection

Function parameters can be injected with the same `Inject` marker:

```{literalinclude} ../../examples/basic_function.py
:start-at: def create
:end-at: }
:emphasize-lines: 1
```

### An Injector Can Wrap A Function Call

We can make a `DefaultInjector` manually by passing in the container. This injector is a callable that is passed a
callable, then calls with the injected values. In this case, it sees `create_result` has a parameter of
`db: Inject[Database]`. The injector finds `Database` in the container, runs the factory, gets the value, and passes as
an argument.

```{literalinclude} ../../examples/basic_function.py
:start-at: Create container
:end-at: result = 
```

There's another way get an injector. We'll see that [in the next example](registered_injector.md).
