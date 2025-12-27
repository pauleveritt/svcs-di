# Spec Requirements: Inject Container

## Initial Description

Get the KeywordInjector and HopscotchInjector to recognize `Inject[Container]` if present and add the `svcs.Container` instance to the arguments.

This feature enables injectors to automatically provide the `svcs.Container` instance itself when a function or dataclass field is annotated with `Inject[Container]`. This allows injected code to access the container for dynamic service resolution or other container operations.

Both `KeywordInjector` and `HopscotchInjector` need to support this pattern.

## Requirements Discussion

### First Round Questions

**Q1:** For the type annotation pattern, I assume we should use `Injectable[Container]` (following the existing convention established in the codebase) rather than `Inject[Container]` mentioned in the roadmap. Is that correct?

**Answer:** Yes, use `Injectable[Container]` to match the existing convention.

**Q2:** When multiple registrations exist (especially in HopscotchInjector), should the injected Container follow the same precedence/override behavior as other dependencies, or does it have special handling?

**Answer:** Follow the same precedence rules as other Injectable dependencies.

**Q3:** Should the injected Container be the same instance that's calling the injector (i.e., `self.container` in the injector's context), or could it be a different Container instance provided in kwargs?

**Answer:** Use `self.container` unless one is provided in kwargs.

**Q4:** In HopscotchInjector with context-aware resolution, should the Container injection be aware of the current context, or is it context-agnostic since the Container itself is not part of the multiple registrations?

**Answer:** No special context handling - it's not part of multiple registrations.

**Q5:** Should this feature support both sync and async injectors, or is it primarily for synchronous injection?

**Answer:** Yes, support both sync and async injectors.

**Q6:** Should the DefaultInjector (if one exists) also support Injectable[Container], or is this feature specific to KeywordInjector and HopscotchInjector?

**Answer:** Yes, DefaultInjector should also support this.

**Q7:** For type validation, should we validate that the annotated type is actually `Container` at injection time, or trust the type annotation?

**Answer:** Trust the type annotation (no runtime validation).

**Q8:** Are there any specific exclusions or features we should explicitly NOT implement in this spec?

**Answer:** No explicit exclusions.

### Existing Code to Reference

No similar existing features identified for reference.

User clarified that `SomeType` mentioned in the initial discussion was just an example, not an actual existing implementation.

### Follow-up Questions

No follow-up questions were needed. All requirements were clarified in the first round of questions.

## Visual Assets

### Files Provided:

No visual assets provided.

### Visual Insights:

No visual analysis available.

## Requirements Summary

### Functional Requirements

- **Type Annotation Support**: Recognize `Injectable[Container]` type annotation in function arguments and dataclass fields
- **Injector Coverage**: Implement this feature in:
  - KeywordInjector
  - HopscotchInjector
  - DefaultInjector
- **Container Instance Resolution**:
  - Inject `self.container` (the container instance that's calling the injector)
  - Allow override if a Container instance is provided in kwargs
- **Precedence Behavior**: Injectable[Container] follows the same precedence and override rules as other Injectable dependencies
- **Context Handling**: Container injection is context-agnostic (not part of multiple registrations system)
- **Async Support**: Works with both synchronous and asynchronous injectors
- **Type Safety**: Trust type annotations without runtime validation

### Reusability Opportunities

No specific existing features identified for reuse. This is a new capability being added to the existing injector infrastructure.

### Scope Boundaries

**In Scope:**
- Recognition of `Injectable[Container]` type annotation
- Automatic injection of the Container instance
- Support across all three injector types (Default, Keyword, Hopscotch)
- Both sync and async support
- Consistent behavior with existing Injectable dependency patterns

**Out of Scope:**
- Runtime type validation
- Special context-aware handling for Container injection
- New injector types beyond the three mentioned
- Changes to Container API or behavior
- Complex precedence rules specific to Container (uses standard precedence)

### Technical Considerations

- **Integration Points**:
  - Existing injector implementations need modification
  - Type annotation parsing logic needs to detect `Injectable[Container]`
  - Injection resolution logic needs to handle Container as a special case

- **Existing System Constraints**:
  - Must maintain compatibility with existing Injectable patterns
  - Must work within the current precedence system
  - Must support both sync and async execution contexts

- **Technology Preferences**:
  - Follow existing type annotation conventions (`Injectable[T]`)
  - Trust Python's type system (no runtime validation)
  - Maintain consistency across all injector types

- **Similar Code Patterns**:
  - This extends the existing Injectable type annotation pattern
  - Should follow the same resolution and injection flow as other Injectable dependencies
  - No breaking changes to existing injector behavior
