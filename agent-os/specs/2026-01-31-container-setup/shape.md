# Shape: Container Setup Functions

## Problem Statement

When scanning packages with `scan()`, there's no way for packages to perform setup logic at:
1. Registry-time (when the package is scanned)
2. Container-time (when a new container is created)

This limits the ability for packages to configure services, register defaults, or perform per-request setup.

## Solution

Add convention-based setup functions discovered during `scan()`:

- `svcs_registry(registry)` — Called immediately during scan
- `svcs_container(container)` — Stored, called when HopscotchContainer is created

## Key Decisions

### 1. Convention over Configuration

Functions are discovered by name, not by decorator. This follows Python conventions like `pytest` fixtures and `Django` settings.

**Rationale**:
- Simpler API (no new decorators needed)
- Clear intent (function name describes when it runs)
- Easy to spot in code reviews

### 2. HopscotchRegistry Required

Convention functions only work with `HopscotchRegistry`, not plain `svcs.Registry`. Attempting to use them with plain registry raises `TypeError`.

**Rationale**:
- `svcs_container` needs storage in registry
- Avoids silent failures
- Clear error message guides users

### 3. Order = Priority

When scanning multiple packages, later packages' setup functions run after earlier ones. This allows overriding.

**Rationale**:
- Consistent with other scan() behavior
- Predictable ordering
- Enables "override" packages

### 4. Per-Container Invocation

`svcs_container` is called for **each** new container, not just once. This enables request-scoped setup.

**Rationale**:
- Containers often represent requests
- Per-request configuration is common
- Matches container lifecycle semantics

### 5. No Return Value Processing

Setup functions return None. Any configuration is done via the passed registry/container.

**Rationale**:
- Simpler API
- Side-effect based (mutation)
- Matches existing patterns

## Type Signatures

```python
def svcs_registry(registry: HopscotchRegistry) -> None:
    """Configure registry at scan time."""
    ...

def svcs_container(container: HopscotchContainer) -> None:
    """Configure container at creation time."""
    ...
```

## Alternatives Considered

### Decorator-based

```python
@registry_setup
def configure(registry):
    ...
```

Rejected: Adds complexity, convention is simpler.

### Return-based configuration

```python
def svcs_registry(registry):
    return {"services": [...]}
```

Rejected: Side-effect mutation is simpler and more flexible.

### Separate scan_setup() call

```python
scan(registry, packages)
scan_setup(registry)  # Separate call for setup
```

Rejected: More API surface, easy to forget.
