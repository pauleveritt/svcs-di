# svcs Development Standards

## Best Practices

- ✅ Add a `classmethod` named `from_container` when everything needed is in the container, but some logic is needed to
  transform the data passed in for instantiation. Then use `SomeService.from_container` as the factory during
  `registry.register(SomeService, SomeService.from_container)`.
- ✅ Bind the factory argument with `from svcs import auto` when the service wants to `Inject` a value.
- ✅ If there are complex dependencies, create the instance manually and register it with `register_value`.
- ✅ Global dependencies whose values last the lifetime of the application should be registered in the `registry`.
- ✅ Values that change from request to request should be registered in the `container`.
- ✅ Use a context manager for container lifecycle management such as `with svcs.Container(registry) as container:` 

## Anti-Patterns

- ❌ Registering a service with `register_value` when everything it needs for instantiation is available in the
  container.