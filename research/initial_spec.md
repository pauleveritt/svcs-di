# svs-di Initial Spec

## Related work

- We have a checkout of `svcs` itself in `/Users/pauleveritt/PycharmProjects/svcs/`
- An initial attempt at DI for `svcs` is below
- Earlier package for DI called `hopscotch` is at `/Users/pauleveritt/projects/pauleveritt/hopscotch`
- A [discussion about injection](https://github.com/hynek/svcs/discussions/94) that captures some of what Hynek might
  accept

## Goals

- Allow a `svcs` based application to call a function or dataclass and provide data from a container

## Requirements

- Uses the most-modern type hinting features available in Python 3.14+ (PEP 695 generics)
- Support Python protocols
- Works with free threaded Python
- Target dataclasses can have a special method `__svcs__` that governs construction (similar to `__hopscotch_factory__`
  in Hopscotch)
- Working examples under `examples`
    - With tests for the examples under `tests`
    - And docs for the examples in `docs/examples/*.md`

## Nice-to-have

- Support features from Hopscotch
    - Multiple registrations for one service type with a resolution strategy as described below
    - Special dataclass field support that allows extra features such as operators
    - Operator support on function and dataclass callables, but re-imagine a different approach (perhaps generics)
      instead of constructing an instance at import time
- This multiple-registrations resolution should work with context-specific
  registrations [as done in Hopscotch](https://hopscotch.readthedocs.io/en/latest/registry.html#context)
    - Bring over the precedence system in Hopscotch, but with a much-better implementation that fits `svcs`
    - Put these nice-to-haves in an optional part of the package, the core `svcs_di` should be very minimal
- A minimal port of [venusian][~/PycharmProjects/venusian/]
    - Leave out a bunch of features
    - Hardwired to the registry, uses a container
    - Doesn't need to support categories or advanced features
    - Uses modern Python 3.14+ features for package discovery, walking directory trees, etc.

## Initial svcs+di for multiple registrations

```python
from dataclasses import dataclass
from pathlib import PurePath
from typing import Protocol, Callable, Any

import pytest
from svcs import Container, Registry


@dataclass
class Registration:
    # Wish I could say type[Protocol] here
    svc_type: Any
    factory: Callable[..., object]
    # Per-request overrides
    context: Callable[..., object] | None = None
    location: PurePath | None = None


@dataclass
class Registrations:
    # These two go in the registry
    system: list[Registration]
    site: list[Registration]


# ---- Different kinds of people we might talk to
class Context(Protocol):
    first_name: str


@dataclass
class CustomerContext:
    first_name: str


@dataclass
class EmployeeContext:
    first_name: str


# --- Different kinds of greetings we might give
class Greeting(Protocol):
    salutation: str


@dataclass
class DefaultGreeting:
    # The system default greeting
    salutation: str = "Good Day"


# The site has two other kinds of context
@dataclass
class CustomerGreeting:
    salutation: str = "Hello"


@dataclass
class EmployeeGreeting:
    salutation: str = "Wassup"


# The site has a special greeting in the garden aisle
@dataclass
class GardenGreeting:
    salutation: str = "Hot day outside"


@dataclass
class Request:
    context: Context
    location: PurePath


@dataclass
class RegistryRegistrations:
    """Registrations discovered at startup time from system and site."""
    site: list[Registration]
    system: list[Registration]


registry_registrations = RegistryRegistrations(
    system=[
        Registration(svc_type=Greeting, factory=DefaultGreeting),
    ],
    site=[
        Registration(svc_type=Greeting, factory=EmployeeGreeting, context=EmployeeContext),
        Registration(svc_type=Greeting, factory=GardenGreeting, location=PurePath("/garden")),
    ]
)


@pytest.fixture
def registry() -> Registry:
    registry = Registry()
    # Process the non-context, non-location registrations, starting with system,
    # then doing site (thus the latter has precedence.)
    registrations = registry_registrations.system + registry_registrations.site
    for r in registrations:
        if r.location is None and r.context is None:
            # Not request-dependent, so put it in the registry.
            registry.register_factory(r.svc_type, r.factory)
    return registry


def setup_container(registry: Registry, request: Request) -> Container:
    # The big idea:
    # 1. We've already collected all the "registrations" during a configuration 
    #    step, e.g. with venusian.
    # 2. We're processing a "request" which means creating a container.
    # 3. Find the "best" request-specific registration, if any, and register 
    #    locally in the container. But only if they match the request values.
    # 4. Thus we won't have multiple container-local registrations for the same 
    #    thing and then figure out which one is best.
    container = Container(registry)
    registrations = registry_registrations.system + registry_registrations.site
    for r in registrations:
        if (r.location is not None and request.location.is_relative_to(r.location)) or (
                r.context is not None and isinstance(request.context, r.context)):
            # This registration was EITHER location or context, and it matches the
            # request value, so register it in container.
            container.register_local_factory(r.svc_type, r.factory)
    # TODO There's a smarter way to "score" registrations, dumb way for now.
    for r in registrations:
        if (r.location and request.location.is_relative_to(r.location)) and (r.context is request.context):
            # This registration was for BOTH location and context, and it matches the
            # request values, so register it.
            container.register_local_factory(r.svc_type, r.factory)

    # Finally, put the request in the container.
    container.register_local_value(Request, request)
    return container


def test_defaults(registry: Registry):
    context = CustomerContext(first_name="Mary")
    location = PurePath("/entrance")
    request = Request(context=context, location=location)
    container = setup_container(registry, request)
    request: Request = container.get_abstract(Request)
    assert request.context is context
    assert request.location == location
    greeting: Greeting = container.get_abstract(Greeting)
    assert greeting.salutation == "Good Day"


def test_employee_context(registry: Registry):
    # This is a site-local registration which depends on a value in
    # the container.
    context = EmployeeContext(first_name="Fred")
    location = PurePath("/entrance")
    request = Request(context=context, location=location)
    container = setup_container(registry, request)
    greeting: Greeting = container.get_abstract(Greeting)
    assert greeting.salutation == "Wassup"


def test_employee_garden(registry: Registry):
    # Match on both employee and location
    context = EmployeeContext(first_name="Fred")
    location = PurePath("/garden/plans")
    request = Request(context=context, location=location)
    container = setup_container(registry, request)
    greeting: Greeting = container.get_abstract(Greeting)
    assert greeting.salutation == "Hot day outside"
```