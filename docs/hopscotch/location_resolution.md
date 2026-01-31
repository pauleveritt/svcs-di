# Location Resolution

**Complexity: Intermediate**

Shows URL-path-like service selection using `PurePath` locations with hierarchical fallback.

## What's The Big Idea?

Hopscotch is about having different variations for different parts of your application. For example, in a website, you
might want a different part of the puzzle at one URL. Or even, under a whole part of the site.

The `location` "predicate" of Hopscotch registrations does this. You register a service to be used in part of the site.
Later, a container is made for a "request". The container has a `Location` in it. Location is a `PurePath`.

The `ServiceLocator` then matches the container's location against the registered locations, to choose the best fit.

## Source Code

The complete example is available at `examples/hopscotch/location_resolution.py`:

```{literalinclude} ../../examples/hopscotch/location_resolution.py
:start-at: from dataclasses
:end-at: return service
```

## Key Concepts

### Location-Based Registration

Register implementations at specific paths:

```{literalinclude} ../../examples/hopscotch/location_resolution.py
:start-at: registry.register_implementation(Greeting, Greeting)
:end-at: location=PurePath("/public")
```

### Container API for Locations

Pass location directly to `HopscotchContainer`:

```{literalinclude} ../../examples/hopscotch/location_resolution.py
:start-at: Test 1: /public location
:end-at: assert service.location == PurePath("/public")
```

The container automatically registers the location for both `Inject[Location]` and ServiceLocator matching.

### Hierarchical Fallback

Locations follow a hierarchical fallback pattern:

- `/public/gallery` first looks for `/public/gallery`
- Falls back to `/public`
- Falls back to default (no location constraint)

```{literalinclude} ../../examples/hopscotch/location_resolution.py
:start-at: Test 2: Hierarchical fallback
:end-at: assert service.location == PurePath("/public/gallery")
```

### Location as Injectable Service

Inject `Location` to access the current path:

```{literalinclude} ../../examples/hopscotch/location_resolution.py
:start-at: class PageRenderer
:end-at: greeting.greet(name)
```

### Backward Compatibility

The old `register_local_value` pattern still works:

```{literalinclude} ../../examples/hopscotch/location_resolution.py
:start-at: Test 4: Backward compatible API
:end-at: assert service.location == PurePath("/legacy")
```
