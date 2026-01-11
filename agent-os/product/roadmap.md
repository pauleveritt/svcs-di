# Product Roadmap

1. [x] Core Type-Safe Dependency Injection — Implement basic dependency injection using Python 3.12+ type hints,
   allowing function arguments and dataclass fields to be automatically resolved from a container using protocol-based
   type annotations. Includes Registry for configuration-time setup and Container for request-time resolution. `M`

2. [x] Protocol-Based Service Registration — Add support for registering concrete implementations against protocol
   interfaces, enabling interface-based programming where services are requested by protocol type and the container
   provides the registered implementation with full type safety. `S`

3. [x] Basic Examples and Documentation — Create foundational examples demonstrating core DI patterns (simple injection,
   protocol usage, custom construction) with corresponding tests in `tests/` and documentation in `docs/examples/*.md`.
   Include examples from initial spec as starting point. `M`

4. [x] KeywordInjector — Move keyword injection out of the basic injector into `src/svcs_di/injectors/keyword.py`.
   Change
   `examples` to have `examples/keyword/firste_example.py` etc. Re-organize helpers to make it easy to write injectors
   that match the protocol.
   `S`

5. [x] Multiple Service Registrations — Start a `HopscotchInjector` that is based on the `KeywordInjector`. Add support
   for registering multiple implementations of the same protocol interface, storing them as a collection of
   registrations with metadata (factory, context, location) that will be
   resolved based on request-time criteria. `L`

6. [x] Context-Specific Service Resolution — In `HopscotchInjector` implement context-aware service resolution where
   different implementations
   are selected based on request context (e.g., CustomerContext vs EmployeeContext), allowing tenant-specific,
   role-based, or user-type-specific service behavior. Enhanced with "resource" terminology refactoring and caching. `L`

7. [x] Optional Scanning Module — Create a minimal venusian-inspired scanning system for auto-discovery of services
   using modern Python 3.12+ package discovery, simplified to work only with svcs-di registry without categories or
   complex features. Keep this as an optional module separate from core. We have a local venusian checkout in
   `/Users/pauleveritt/PycharmProjects/venusian`. `L`

8. [x] Location-Based Service Resolution — Add location/path-based service resolution where services registered with a
   location (PurePath) are selected when the request location is relative to the registered location, enabling URL-based
   or hierarchical service selection. Allow this to be combined with `request` selection but at a lower precedence.  `M`

9. [x] Precedence and Scoring System — Implement intelligent precedence rules for selecting the best matching service
   when multiple registrations could satisfy a request, with scoring that considers both context and location matches,
   and system vs site registration priority.`L`

10. [x] Free-Threaded Python Compatibility — Verify and document free-threaded Python (PEP 703) compatibility, add
    specific tests using `pytest-run-parallel`, ensure thread-safe container operations, and document any threading
    considerations or limitations. `M`

11. [x] GitHub Workflows — Analyze `~/projects/t-strings/tdom-path/` for a project with the correct structure. Look in
    its `.github` for the setup, `Justfile` for the recipes, and any `pyproject.toml` for any dependencies. Use a
    composite action for reuse. The GitHub workflows should use the Just recipes. Workflow dependency caching with `uv`.
    `S`

12. [x] Specifications Into Sphinx — Analyze this project's `agent-os/product/` and `agent-os/specs/` to link into a
    `docs/specifications/index.md` in Sphinx. Have an ordered `toctree` that brings them in. The `index.md` should have
    a descriptive listing, with a `Prooduct` heading having some text, then sections for `mission.md`, `roadmap.md`, and
    `tech-stack.md`. Each subsection heading has a "Read More" a link to the full document with some summary text. Then
    a `Features` section with subsections that do the same for each directory in `specs`: a heading, a short summary of
    that feature, and a "Read More" link. `M`

13. [x] Inject Container — Get the KeywordInjector and HopscotchInjector to recognize `Inject[Container]` if present and
    add the `svcs.Container` instance to the arguments. `S`

14. [x] InjectionContainer — Provide a `svcs.injector.InjectorContainer` variation of `svcs.Container` where `.get()`
    and `aget()` allow kwargs. This method should look for a registered injector. If not, use the base class `.get()`.
    Otherwise, find the registered injector and use it. But make sure it supports keyword injection. For example,
    `container = InjectorContainer(container); container.get(MyService, arg1=val1, arg2=val2)`. Write good tests. `M`

15. [x] Hopscotch Registry — Provide HopscotchRegistry and HopscotchContainer as pre-wired implementations. Read
    `docs/hopscotch_registry_plan.md` for instructions.

16. [x] Function Implementations — Read `docs/function_implementations_plan.md` for instructions. Allow factories to be
    functions, both for manual registrations and decorator. Have examples for DefaultInjector, KeywordInjector, and
    HopscotchInjector, plus docs for the examples.

17. [ ] Performance Optimization and Benchmarks — Optimize container resolution performance, minimize overhead of
    context/location matching, add benchmarks comparing with plain `svcs` and other DI approaches, document performance
    characteristics and trade-offs. `M`

18. [ ] Field Operators and Advanced Features — Implement special dataclass field support for advanced dependency
    features like operators, configuration injection, and enhanced metadata, re-imagined to avoid import-time instance
    construction (perhaps using generics). Keep as optional module. Look in ` `L`

19. [ ] Custom Predicates — Hopscatch has other "predicates" for matching and scoring, with a system
    for plugging in custom predicates. `M`

> Notes
> - Items 1-4 form the minimal viable core of svcs-di focused on type-safe DI
> - Items 5-10 add context-aware resolution (the "nice-to-have" features from spec)
> - Items 11-12 are optional advanced features as separate modules
> - Items 13-15 ensure production-readiness, compatibility, and performance
> - Each item represents end-to-end functionality with examples, tests, and docs
> - Order prioritizes foundational features first, then builds context-awareness, then optional features
