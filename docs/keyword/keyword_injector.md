# Keyword Injector

**Complexity: Beginner**

The `KeywordInjector` is just the same as the `DefaultInjector`, but with extra features. In this example, you'll learn:

- How you can use the `KeywordInjector`, without actually providing keywords
- Meaning: how to manually call it the same way you would call `DefaultInjector`

## Source Code

The complete example is available at `examples/keyword/keyword_injector.py`:

```{literalinclude} ../../examples/keyword/keyword_injector.py
:start-at: from dataclasses
:end-at: return service
```

## Key Concepts

Careful eyes will notice: we're not using keywords yet. This example just shows we can create a
`KeywordInjector` and manually inject, as we saw in [the basic function example](../examples/basic_function.md):

```{literalinclude} ../../examples/keyword/keyword_injector.py
:start-at: Per-request container
:end-at: injector(
```
