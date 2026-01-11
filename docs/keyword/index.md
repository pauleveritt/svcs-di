# Keyword Injection

In `svcs`, your factory function creates an instance of your service type. Who does the calling of that function? "The
System", as part of `container.get()`. With `DefaultInjectory`, the service can help in the construction by flagging
function parameters it wants "The System" to retrieve and pass in.

But what if your app needs to pass extra arguments to the constructor, from the environment or context? That's where
the `KeywordInjector` comes in. In this example, you'll learn:

- A specific use case for keyword injection
- Write a function with a dependent service that needs injection
- Manually wrap a function call with an injector that resolves the dependency

## An Example

We're building an HTML component system. In this syntax, you create an instance of a component by passing arguments as
"props" -- meaning, HTML attributes and values:

```
<{Greeter} name="Bob">Hello</{Greeter}>
```

In this case, we want `svcs` to create a `Greeter` instance, passing the `name` argument as a keyword argument. That's
where `KeywordInjector` can help.

```{toctree}
:maxdepth: 2
:hidden:

keyword_injector
manual_injection
injection_container
override_inject
```
