# Override Registration

**Complexity: Beginner**

You're using an app or framework from a famous Python package.

You have a local use – for example, your own "site." You like everything *except* for the database service. Fork? Monkey
patch? In this example, you'll learn how to:

- Create a replacement class for the `Database` service
- Register the replacement class in the container
- The injector then provides the replacement when you ask for `Database`

This idea of "replaceability" is a central benefit of `svcs-di`.

## Source Code

The complete example is available at `examples/override_registration.py`:

```{literalinclude} ../../examples/override_registration.py
:start-at: from dataclasses
:end-at: return service
```

## Key Concepts

### Later Registration

In this scenario, most of this code is in a library. We have a section in *your* part, which we'll call the "site." You
just need to register a different dataclass:

```{literalinclude} ../../examples/override_registration.py
:start-at: ---- Start a
:end-at: ---- Finish
:emphasize-lines: 11
```

Since your "local" registration came last, yours wins and overrides the library's registration.

### Registry or Container

In `svcs`, you can also register a factory in the container. This registration of course is lost on the next "request"
when you get a new container. But this behavior can be useful if the registration depends on information unique to that
request.

### Application Doesn't Care

All other parts of the application won't know that you've provided an alternate implementation. They'll ask for a
`Database` and get your custom database.

### Keep an Eye on the Shape

Your `CustomDatabase` has the same fields as the original `Database`. Which means any code that expects `host` and
`port` will be happy at runtime and tools like type checkers will be happy in static analysis.

But you can run into problems:

- `isinstance` will fail because `CustomDatabase` is not a subclass of `Database`
- If you remove fields from `CustomDatabase`, runtime errors might happen
- If you add extra fields to `CustomDatabase`, type checkers will complain

We'll talk more about "shapes" and types next when we cover [protocol injection](protocol_injection.md).