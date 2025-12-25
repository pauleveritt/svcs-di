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

4. [x] KeywordInjector — Move keyword injection out of the basic injector into `src/svcs_di/injectors/keyword.py`. Change
   `examples` to have `examples/keyword/firste_example.py` etc. Re-organize helpers to make it easy to write injectors
   that match the protocol.
   `S`

5. [ ] Multiple Service Registrations — Start a `HopscotchInjector` that is based on the `KeywordInjector`. Add support
   for registering multiple implementations of the same protocol interface, storing them as a collection of
   registrations with metadata (factory, context, location) that will be
   resolved based on request-time criteria. `L`

6. [ ] Context-Specific Service Resolution — In `HopscotchInjector` implement context-aware service resolution where different implementations
   are selected based on request context (e.g., CustomerContext vs EmployeeContext), allowing tenant-specific,
   role-based, or user-type-specific service behavior. `L`

7. [ ] Location-Based Service Resolution — Add location/path-based service resolution where services registered with a
   location (PurePath) are selected when the request location is relative to the registered location, enabling URL-based
   or hierarchical service selection. `M`

8. [ ] Precedence and Scoring System — Implement intelligent precedence rules for selecting the best matching service
   when multiple registrations could satisfy a request, with scoring that considers both context and location matches,
   and system vs site registration priority. `L`

9. [ ] Container Setup and Registration Processing — Create the setup logic that processes Registry registrations at
   container creation time, determining which registrations go into the registry (non-context, non-location) vs
   container-local (context/location-specific), and registering the request itself as a service. `M`

10. [ ] Advanced Examples for Context Resolution — Build comprehensive examples demonstrating context-aware patterns (
    multi-tenant, customer vs employee, location-based routing) with full test coverage and documentation explaining the
    resolution strategy and precedence rules. `M`

11. [ ] Optional Scanning Module — Create a minimal venusian-inspired scanning system for auto-discovery of services
    using modern Python 3.12+ package discovery, simplified to work only with svcs-di registry without categories or
    complex features. Keep this as an optional module separate from core. `L`

12. [ ] Field Operators and Advanced Features — Implement special dataclass field support for advanced dependency
    features like operators, configuration injection, and enhanced metadata, re-imagined to avoid import-time instance
    construction (perhaps using generics). Keep as optional module. `L`

13. [ ] Free-Threaded Python Compatibility — Verify and document free-threaded Python (PEP 703) compatibility, add
    specific tests using pytest-freethreaded, ensure thread-safe container operations, and document any threading
    considerations or limitations. `M`

14. [ ] Integration Documentation and Migration Guide — Create comprehensive guides for integrating svcs-di into
    existing `svcs` applications, migration path from Hopscotch to svcs-di, comparison with other DI frameworks, and
    best practices for structuring large applications. `S`

15. [ ] Performance Optimization and Benchmarks — Optimize container resolution performance, minimize overhead of
    context/location matching, add benchmarks comparing with plain `svcs` and other DI approaches, document performance
    characteristics and trade-offs. `M`

> Notes
> - Items 1-4 form the minimal viable core of svcs-di focused on type-safe DI
> - Items 5-10 add context-aware resolution (the "nice-to-have" features from spec)
> - Items 11-12 are optional advanced features as separate modules
> - Items 13-15 ensure production-readiness, compatibility, and performance
> - Each item represents end-to-end functionality with examples, tests, and docs
> - Order prioritizes foundational features first, then builds context-awareness, then optional features
