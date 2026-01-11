# Nested Scanning

**Complexity: Intermediate**

Shows scanning a nested application structure with protocols using a string package name.

## What's The Big Idea?

Real applications organize code into subdirectories. The `scan()` function can recursively discover all
`@injectable(for_=Protocol)` classes in a package and its subpackages using a string package name.

## Source Code

The complete example is available at `examples/scanning/nested_with_string.py`:

```{literalinclude} ../../examples/scanning/nested_with_string.py
:start-at: from dataclasses
:end-at: return service
```

## Directory Structure

The `nested_app` package has this structure:

```
nested_app/
├── protocols.py          # Protocol definitions
├── services/
│   ├── cache.py          # CacheService (for_=Cache)
│   └── email.py          # EmailService (for_=Email)
├── models/
│   └── database.py       # DatabaseConnection (for_=Database)
└── repositories/
    └── user_repository.py  # SqlUserRepository (for_=UserRepository)
```

## Key Concepts

### Centralized Protocol Definitions

Define all protocols in one place for your package:

```{literalinclude} ../../examples/scanning/nested_app/protocols.py
:start-at: from typing
:end-at: def get_user
```

### Protocol-Based Registration

Implementations use `@injectable(for_=Protocol)` to register against their protocol:

```{literalinclude} ../../examples/scanning/nested_app/services/email.py
:start-at: @injectable
:end-at: smtp_port
```

### Cross-Module Dependencies on Protocols

Services depend on Protocols, not implementations:

```{literalinclude} ../../examples/scanning/nested_app/repositories/user_repository.py
:start-at: @injectable
:end-at: cache: Inject
```

### String-Based Package Scanning

Pass a string package name to `scan()` - no imports needed:

```{literalinclude} ../../examples/scanning/nested_with_string.py
:start-at: scan() discovers
:end-at: scan(registry
```

### Recursive Discovery

`scan()` automatically discovers services in all subdirectories - no need to list them individually.
