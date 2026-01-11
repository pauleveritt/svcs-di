# Scanning

**Complexity: Intermediate**

Shows auto-discovery with `@injectable` decorator and `scan()` function.

## What's The Big Idea?

Manual registration with `registry.register_implementation()` works well for small systems. But as your application
grows, registration boilerplate adds up. The `@injectable` decorator and `scan()` function let you declare registration
intent directly on the class, then auto-discover all decorated classes.

## Source Code

The complete example is available at `examples/hopscotch/scanning.py`:

```{literalinclude} ../../examples/hopscotch/scanning.py
:start-at: from dataclasses
:end-at: return service
```

## Key Concepts

### The @injectable Decorator

Mark a class for auto-discovery with `@injectable`:

```{literalinclude} ../../examples/hopscotch/scanning.py
:start-at: @injectable
:end-at: return f"{self.salutation}, {name}!"
:lines: 1-10
```

### Decorator Parameters

Add parameters to control how the class is registered:

- **`for_=ServiceType`**: Register as implementation of a base class or protocol
- **`resource=ContextType`**: Constrain to a specific resource context
- **`location=PurePath(...)`**: Constrain to a specific location

```{literalinclude} ../../examples/hopscotch/scanning.py
:start-at: @injectable(for_=Greeting, resource=EmployeeContext)
:end-at: return f"{self.salutation}, {name}!"
```

### Using scan()

Call `scan()` to discover and register all decorated classes:

```{literalinclude} ../../examples/hopscotch/scanning.py
:start-at: scan() discovers
:end-at: },
```
