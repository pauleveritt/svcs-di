# Spec Requirements: InjectionContainer

## Initial Description

14 InjectionContainer

This is feature #14 from the product roadmap, focusing on implementing an InjectorContainer class that extends svcs.Container to provide dependency injection capabilities with injector support.

## Requirements Discussion

### First Round Questions

**Q1:** Should the InjectorContainer constructor allow an `injector` keyword argument?
**Answer:** Yes. Change the constructor to allow an `injector` keyword argument:
- Example: `__init__(self, registry: Registry, *, injector: Injector = KeywordInjector)`
- Use attrs style of subclassing to better match the `svcs.Container` implementation

**Q2:** How should type mismatches be handled when kwargs are passed to the injector?
**Answer:** Use Proposal B (Relaxed/Duck Typing - Pass Through):
- Let kwargs pass through without type checking
- Let Python's natural type errors surface during construction
- Do not add explicit type validation in the container

**Q3:** Should there be error handling when kwargs are provided but no injector is set?
**Answer:** Yes, raise an error if kwargs are provided but no injector is configured.

**Q4:** How should the `get()` method behave?
**Answer:** The `get()` method should:
- Check if an injector is configured
- If injector exists, use its `__call__` method with kwargs
- If no injector, fall back to `super().get()`

**Q5:** How should the `aget()` method behave?
**Answer:** Follow the existing async pattern for finding injectors, keep it simple.

**Q6:** Should kwargs be allowed when requesting multiple service types?
**Answer:** No. Raise an error if kwargs are provided with multiple service types.

**Q7:** What notation should be used for *args and **kwargs?
**Answer:** Use standard Python *args/**kwargs notation.

**Q8:** Where should the file be located?
**Answer:** `src/svcs_di/injector_container.py`

**Q9:** What should be the default injector?
**Answer:** Default to KeywordInjector when no injector is specified in the constructor.

**Q10:** How should "injector doesn't support kwargs" errors be handled?
**Answer:** Let them propagate naturally - duck typing approach.

### Existing Code to Reference

**Similar Features Identified:**
- Feature: KeywordInjector - Path: `src/svcs_di/injectors/keyword.py`
  - Contains the `KeywordInjector` class that will be the default injector
  - Shows the `__call__` interface pattern with `**kwargs` support
  - Contains `KeywordAsyncInjector` for async patterns
- Feature: svcs.Container - External package (svcs)
  - The base class that InjectorContainer will subclass
  - Uses attrs for its implementation
  - Provides `get()` and `aget()` methods

### Follow-up Questions

No additional follow-up questions needed. All requirements have been clarified.

## Visual Assets

### Files Provided:
No visual files found in the visuals folder.

### Visual Insights:
N/A - No visual assets provided.

## Requirements Summary

### Functional Requirements
- Create `InjectorContainer` class as a subclass of `svcs.Container`
- Use attrs style subclassing to match svcs.Container's implementation
- Constructor accepts `injector` keyword argument with default `KeywordInjector`
- `get(*svc_types, **kwargs)` method:
  - If kwargs provided and multiple service types: raise error
  - If kwargs provided and no injector: raise error
  - If injector configured: use `injector(svc_type, **kwargs)` to resolve
  - Otherwise: fall back to `super().get(*svc_types)`
- `aget(*svc_types, **kwargs)` method:
  - Follow same pattern as `get()` but for async resolution
  - Use async injector if available
- Duck typing for kwargs validation (let Python's natural errors surface)

### Reusability Opportunities
- `KeywordInjector` from `src/svcs_di/injectors/keyword.py` as default injector
- `KeywordAsyncInjector` for async injection support
- Follow patterns from existing injector implementations

### Scope Boundaries

**In Scope:**
- `InjectorContainer` class implementation
- Constructor with optional `injector` parameter
- `get()` method with kwargs support
- `aget()` method with kwargs support
- Error handling for kwargs with multiple service types
- Error handling for kwargs without injector configured
- Integration with existing `KeywordInjector`

**Out of Scope:**
- Type validation of kwargs values (duck typing approach)
- New injector implementations
- Changes to existing injector classes
- Framework-specific integrations (FastAPI, Flask, etc.)
- Documentation beyond docstrings

### Technical Considerations
- Must subclass `svcs.Container` using attrs style
- Injector interface: `__call__(target, **kwargs) -> T`
- Async injector interface: `async __call__(target, **kwargs) -> T`
- File location: `src/svcs_di/injector_container.py`
- Default injector: `KeywordInjector` from `src/svcs_di/injectors/keyword.py`
- Use standard Python `*args`/`**kwargs` notation
- Let Python's natural type errors surface (duck typing)
