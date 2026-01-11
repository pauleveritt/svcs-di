# Scanning with Protocols

**Complexity: Intermediate**

Shows the recommended pattern for large-scale systems: define Protocols as contracts, then implement them.

## What's The Big Idea?

The basic scanning example works, but has a limitation: services depend on concrete classes. If you want to swap
`Database` for `MockDatabase` in tests, you'd have to change the type annotations.

Protocols solve this. A Protocol defines *what* a service does without specifying *how*. Implementations satisfy the
Protocol by having the same shape. Services depend on Protocols, making them easy to swap.

This is extra work, but Protocols provide:

- **Explicit contracts**: Clear documentation of what services must do
- **Testability**: Easy to swap implementations for mocks
- **Flexibility**: Multiple implementations of the same contract
- **Type safety**: Type checkers verify implementations match

## Source Code

The complete example is available at `examples/scanning/scanning_protocols.py`:

```{literalinclude} ../../examples/scanning/scanning_protocols.py
:start-at: from dataclasses
:end-at: return service
```

## Key Concepts

### Define Protocol Contracts

Protocols define what services must provide:

```{literalinclude} ../../examples/scanning/scanning_protocols.py
:start-at: class Database(Protocol)
:end-at: def get_user
```

### Implement with @injectable(for_=Protocol)

Use `for_=` to register implementations under their Protocol:

```{literalinclude} ../../examples/scanning/scanning_protocols.py
:start-at: @injectable(for_=Database)
:end-at: port: int = 5432
```

### Depend on Protocols

Services use `Inject[Protocol]`, not `Inject[Implementation]`:

```{literalinclude} ../../examples/scanning/scanning_protocols.py
:start-at: class UserService
:end-at: return self.repo.get_user
```

### Use HopscotchRegistry

Protocol-to-implementation mappings require `HopscotchRegistry` and `HopscotchContainer`:

```{literalinclude} ../../examples/scanning/scanning_protocols.py
:start-at: HopscotchRegistry manages
:end-at: container.inject(UserService)
```
