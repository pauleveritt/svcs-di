# Raw Idea: Inject Container

**Spec Number:** 13

**Size:** S (Small)

**Status:** Not Started

## Description from Roadmap

Get the KeywordInjector and HopscotchInjector to recognize `Inject[Container]` if present and add the `svcs.Container` instance to the arguments.

## Context

This feature enables injectors to automatically provide the `svcs.Container` instance itself when a function or dataclass field is annotated with `Inject[Container]`. This allows injected code to access the container for dynamic service resolution or other container operations.

Both `KeywordInjector` and `HopscotchInjector` need to support this pattern.
