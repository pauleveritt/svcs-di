# Basic Scanning

**Complexity: Beginner**

Shows the simplest use case of scanning: mark services with `@injectable`, call `scan()`, and retrieve services.

## What's The Big Idea?

Manual registration with `registry.register_factory()` works, but adds boilerplate. The `@injectable` decorator and
`scan()` function let you declare registration intent directly on the class.

## Source Code

The complete example is available at `examples/scanning/basic_scanning.py`:

```{literalinclude} ../../examples/scanning/basic_scanning.py
:start-at: from dataclasses
:end-at: return repo
```

## Key Concepts

### The @injectable Decorator

Mark classes for auto-discovery:

```{literalinclude} ../../examples/scanning/basic_scanning.py
:start-at: @injectable
:end-at: port: int = 5432
```

### Services with Dependencies

Services can depend on other `@injectable` services using `Inject[ServiceType]`:

```{literalinclude} ../../examples/scanning/basic_scanning.py
:start-at: class UserRepository
:end-at: return f"User
```

### Using scan()

Call `scan()` to discover and register all decorated classes:

```{literalinclude} ../../examples/scanning/basic_scanning.py
:start-at: scan() discovers
:end-at: },
```
