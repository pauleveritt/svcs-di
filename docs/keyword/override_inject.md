# Override `Inject`

**Complexity: Beginner**

We've seen using keyword arguments to override default values. You can also override injected values, as keyword
arguments have the highest precedence. In this example, you'll see:

- Create a `Database` instance
- Pass it in as a keyword argument to `Service`
- This instance is used instead of the one from `Inject`

## Source Code

The complete example is available at `examples/keyword/override_inject.py`:

```{literalinclude} ../../examples/keyword/override_inject.py
:start-at: from dataclasses
:end-at: return service
```

In this case, we make our own `my_database` instance and pass it in as a keyword argument to `Service`. It is used
instead of `Inject[Database]`.