# Resource Resolution

**Complexity: Intermediate**

Shows resource-based multi-implementation selection using `HopscotchRegistry` and `HopscotchContainer`.

- Register more than one implementation for a service
- The services vary based on other information in the container
- Get the correct implementation and instantiate it

## What's The Big Idea?

This example shows the key idea for Hopscotch.

With regular `svcs`, you can already do something big. You can get a base service from an app, then customize it in a
container, replacing just one part of the system -- without forking. That's super-valuable.

But what if you wanted to vary a service, but just in one case? For example, show the default `Header` component on all
pages of the site, but have a custom `Header` in this site section? Or have a `Greeting` service that can vary its
message based on `EnglishCustomer` or `FrenchCustomer`?

This kind of fine-grained customization is possible with Hopscotch. It can be really valuable when creating a "big
market of quality, customizable themes, components, and tools." These ideas come directly from the
fabulous [ideas in Pyramid](https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/viewconfig.html).

This comes at a cost, of course. It's a lot more complex/magical and, like the `KeywordInjector`, impacts caching.

## Source Code

The complete example is available at `examples/hopscotch/resource_resolution.py`:

```{literalinclude} ../../examples/hopscotch/resource_resolution.py
:start-at: from dataclasses
:end-at: return service
```

## Key Concepts

### HopscotchRegistry Simplification

`HopscotchRegistry` manages the `ServiceLocator` internally. We can then register each implementation, but using the
registry:

```{literalinclude} ../../examples/hopscotch/resource_resolution.py
:start-at: registry = HopscotchRegistry()
:end-at: A variation when talking to an Employee
```

Compare this to the manual approach in `resource_resolution_manual.py` which requires:

- Creating a `ServiceLocator` manually
- Calling `locator.register()` for each implementation
- Registering the locator as a value service

### Resource-Based Resolution

Pass the `resource` instance directly to `HopscotchContainer` to enable resource-based selection:

```{literalinclude} ../../examples/hopscotch/resource_resolution.py
:start-at: Request 2: With resource instance
:end-at: assert service.greeting.salutation == "Hey"
```

The container automatically derives `type(resource)` for ServiceLocator matching.

For all other cases, when there is no resource, the default implementation is used:

```{literalinclude} ../../examples/hopscotch/resource_resolution.py
:start-at: Request 1
:end-at: assert service.greeting.salutation == "Hello"
```

### Accessing the Resource with Resource[T]

Services can access the current resource via `Resource[T]`:

```python
from svcs_di import Resource

@dataclass
class ResourceAwareService:
    resource: Resource[Employee]  # Gets container.resource, typed as Employee
```

This separates concerns from `Inject[T]`:
- `Inject[T]` = "resolve service of type T from registry"
- `Resource[T]` = "give me the current resource, I expect type T"

The type parameter `T` is for static type checking only - at runtime, the injector simply returns
`container.resource` regardless of `T`.

```{literalinclude} ../../examples/hopscotch/resource_resolution.py
:start-at: Request 3: ResourceAwareService
:end-at: aware_service.welcome("Alice")
```

### Override Resource Type

You can override the resource type used for ServiceLocator matching by passing it to `inject()`:

```{literalinclude} ../../examples/hopscotch/resource_resolution.py
:start-at: Request 4: Override resource
:end-at: assert service.greeting.salutation == "Hello"
```
