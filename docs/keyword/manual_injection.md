# Manual Keyword Injection

**Complexity: Beginner**

The benefit of the `KeywordInjector`? When getting a service instance, you can override the default and injected values
when getting this instance. In this example, you'll see:

- Creating a `KeywordInjector`
- Calling it with keyword arguments

## Three-tier Precedence

We now have three ways that values can get into our service construction. Starting with the highest priority:

1. Keyword arguments from the caller
2. Values from the container
3. Default values from the service class

## Source Code

The complete example is available at `examples/keyword/manual_injection.py`:

```{literalinclude} ../../examples/keyword/manual_injection.py
:start-at: from dataclasses
:end-at: return service
```

## Key Concepts

This time, when we call `injector()`, we pass in keyword arguments:

```{literalinclude} ../../examples/keyword/manual_injection.py
:start-at: Let's pass in values
:end-before: return service
:emphasize-lines: 2
```

As you can see with the assertions, the values we passed in override the default values.

We'll see using keywords during injection in [the next example](injection_container.md).
