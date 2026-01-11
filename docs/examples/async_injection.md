# Asynchronous Injection

**Complexity: Intermediate**

This example demonstrates async/await support in `svcs-di`. You'll learn how to:

- Register async factories for services that require asynchronous initialization
- Use `auto_async()` for services with async dependencies
- Retrieve services asynchronously with `Container.aget()` in async contexts
- Mix synchronous and asynchronous dependencies in the same service

This pattern is essential for applications that use async I/O, such as web servers, database clients, or any service
requiring asynchronous initialization.

## Source Code

The complete example is available at `examples/async_injection.py`:

```{literalinclude} ../../examples/async_injection.py
:start-at: import asyncio
:end-at: return service
```

## Key Concepts

### Async Factory Registration

When a service requires asynchronous initialization, write an async factory function:

```{literalinclude} ../../examples/async_injection.py
:start-at: async def create_database
:end-at: return Database
```

Then register that as the factory for the service:

```{literalinclude} ../../examples/async_injection.py
:start-at: Register async factory for database
:end-at: registry.register_factory
```

The async factory function can perform I/O operations, wait for connections, or execute any asynchronous initialization
logic. The container will automatically detect that the factory is async and handle it appropriately.

### auto_async() for Services with Async Dependencies

Services might have `Inject` paramaters that must be resolved asynchronously

```{literalinclude} ../../examples/async_injection.py
:start-at: A service with an injected parameter that is async
:end-at: timeout
```

Use `auto_async()` instead of `auto()` when registering:

```{literalinclude} ../../examples/async_injection.py
:start-at:  Register service with auto_async
:end-at: registry.register_factory
```

The `auto_async()` function generates an async factory that:

1. Inspects the constructor signature for `Inject` parameters
2. Resolves each dependency (using `aget()` for async dependencies)
3. Constructs the service with all resolved dependencies

If any dependency requires async resolution, you must use `auto_async()` for the consuming service.

### Container.aget() for Async Resolution

To retrieve services with async dependencies, use `Container.aget()` in an async context:

```{literalinclude} ../../examples/async_injection.py
:start-at:  Get the service asynchronously
:end-at: service = await
```

The `aget()` method is the async equivalent of `get()`. It returns an awaitable that resolves to the service instance.
Using `async with` ensures proper resource cleanup when the container is no longer needed.

As you can see in `AsyncService`, a service can depend on both synchronous and asynchronous services. As long as you use
`auto_async()` for the factory and `aget()` for resolution, the container handles the mix automatically.

The `auto_async()` factory will:

- Use `await container.aget(Database)` to resolve the async dependency
- Use `container.get(Cache)` to resolve the sync dependency (can call sync from async)
- Construct `AsyncService` with both resolved dependencies

This flexibility lets you gradually adopt async patterns without forcing all services to be async.

## Type Safety

`svcs` and `svcs-di` maintains full type safety with async operations. Type checkers understand:

- `async def create_database() -> Database` is an async factory
- `container.aget(AsyncService)` returns `Awaitable[AsyncService]`
- `await container.aget(AsyncService)` resolves to an `AsyncService` instance

