# Scanning for Decorators

The `@injectable` decorator and `scan()` function provide auto-discovery for services. Instead of manually registering
each service, mark classes with `@injectable` and let `scan()` find them.

## Why Scanning?

Manual registration works for small applications:

```python
registry.register_factory(Database, Database)
registry.register_factory(Cache, Cache)
registry.register_factory(UserRepository, UserRepository)
```

But as your application grows, this becomes tedious. Scanning automates it:

```python
scan(registry)  # Finds and registers all @injectable classes
```

## Features

- **Auto-discovery**: Find all `@injectable` decorated classes automatically
- **Recursive scanning**: Discover services in nested packages
- **String package names**: Scan packages without importing them first
- **Cross-module dependencies**: Services can depend on services in other modules

```{toctree}
:maxdepth: 2
:hidden:

basic_scanning
scanning_protocols
nested_scanning
```
