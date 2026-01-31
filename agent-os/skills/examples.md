---
description:
  Standards for creating project examples. Use this when building example code,
  setting up example directories, or integrating examples with documentation.
---

# Examples Development Workflow

Standards for creating, structuring, and documenting project examples to ensure consistency and high-quality documentation.

## Overview

Examples should follow a uniform structure that makes them easy to understand, test, and integrate into the main documentation. Every example is both a runnable codebase and a source for Sphinx documentation.

## Directory Layout

Each example lives in a subdirectory of `examples/` named after the concept it demonstrates (e.g., `examples/nested-components/`).

```
examples/my-example/
├── README.md               # User-friendly explanation
├── app.py                  # Application entry point/wiring
├── site.py                 # Service registry configuration
├── components/             # tdom components (if applicable)
├── services/               # svcs services (if applicable)
└── test_example.py         # Pytest test suite
```

## Documentation Standards

### 1. README.md

Every example must have a `README.md` that provides:

- A clear, concise description of the example's purpose
- Key concepts being demonstrated
- How to run the example manually

### 2. Sphinx Integration

Create a corresponding file in `docs/examples/` with the same name as the example directory. Use `{include}` and `{literalinclude}` directives:

````markdown
# My Example Title

```{include} ../../../examples/my-example/README.md
:relative-docs: docs/
```

## Implementation

### Application (app.py)

```{literalinclude} ../../../examples/my-example/app.py
:language: python
```
````

## Code Standards

- Put imports at the top of the file
- Don't use relative imports

### app.py

The `app.py` file wires everything together:

- Creates a `Registry`
- Scans for decorators (e.g., `@injectable`)
- Provides a function for per-request containers
- Includes a `main()` function and `if __name__ == "__main__":` block
- Make the `main()` function testable and add a test in `test_example.py`

```python
from svcs import Registry, Container
from svcs_di.injectors.locator import scan
from examples.my_example import site


def get_container(registry: Registry):
    """Create a per-request/operation container."""
    return Container(registry)


def main():
    registry = Registry()
    # Auto-discovery
    scan(registry)
    # Custom setup
    site.svcs_setup(registry)

    with get_container(registry) as container:
        # Perform application logic
        print("Example running...")


if __name__ == "__main__":
    main()
```

### site.py

Handles custom service registration and binding.

```python
from svcs import Registry


def svcs_setup(registry: Registry):
    """Configure the service registry for this application."""
    # Custom registrations
    # registry.register_factory(MyService, MyService)
```

## Testing Standards

- Every example must have a `test_example.py`.
- Tests should verify the core functionality of the example.
- Use `pytest` for all tests.
- Ensure the example follows the "Testing with Fakes" standard where appropriate.

## Best Practices

- **No Relative Imports**: Always use absolute imports from the project root (e.g., `from examples.my_example import site`).
- **Explicit svcs Imports**: Avoid `import svcs`. Instead, import specific names (e.g., `from svcs import Container, Registry`).
- **Avoid register_value()**: Prefer `register_factory` or auto-discovery via `@injectable`.
- **Keep it Simple**: Each example should focus on one or two key concepts.
- **Runnable**: Ensure the example can be run directly with `uv run python examples/my-example/app.py`.
- **MyST-Heavy**: Use MyST directives (`{include}`, `{literalinclude}`) to keep documentation in sync with code.
- **Consistent Naming**: Use `snake_case` for filenames and `PascalCase` for classes.
