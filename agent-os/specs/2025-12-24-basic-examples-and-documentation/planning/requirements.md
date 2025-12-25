# Spec Requirements: Basic Examples and Documentation

## Initial Description
Create foundational examples demonstrating core DI patterns (simple injection, protocol usage, custom construction) with corresponding tests in `tests/` and documentation in `docs/examples/*.md`. Include examples from initial spec as starting point.

This is feature #4 from the product roadmap. It builds upon the completed features:
1. Core Type-Safe Dependency Injection (completed)
2. Custom Construction with `__svcs__` (completed - later reverted)

This feature forms part of the minimal viable core of svcs-di focused on type-safe DI (items 1-4 in roadmap).

## Requirements Discussion

### First Round Questions

**Q1: Example Organization and Scope**
Should we document all 5 examples or focus on a foundational subset?
**Answer:** Subset (focus on foundational examples)

**Follow-up clarification received:** Document ALL 5 examples:
1. `basic_dataclass.py` - Simple dataclass injection with Injectable
2. `protocol_injection.py` - Protocol-based dependency injection
3. `async_injection.py` - Asynchronous dependency resolution
4. `kwargs_override.py` - Overriding dependencies via kwargs
5. `custom_injector.py` - Custom injector implementations

**Q2: Documentation Structure**
Should code examples be inline in docs with references to actual files, or should docs just reference the example files?
**Answer:** Yes with reference (include full code inline with references to example files)

**Q3: Test Coverage Strategy**
Should we create a single comprehensive `test_examples.py` or separate test files per example?
**Answer:** Expand to include in one (expand the single `test_examples.py`)

**Q4: Example Complexity Progression**
Should examples be ordered by complexity (simple → advanced) in documentation?
**Answer:** Sure (order by complexity)

**Q5: Target Audience Assumptions**
Should we assume users understand DI fundamentals or explain basics?
**Answer:** Just focus (focus on svcs-di specifics, don't explain DI fundamentals)

**Q6: Integration with Sphinx Documentation**
Should documentation use Sybil to test code snippets actually run?
**Answer:** Test with Sybil (ensure code snippets actually run)

**Q7: Real-World Context**
Should examples include realistic context (e.g., database connections, config) or stay minimal?
**Answer:** No (keep examples minimal, focused on DI patterns only)

**Q8: Scope Exclusions**
Confirm we're NOT including advanced features from roadmap items 5-11?
**Answer:** Correct (no advanced features from roadmap items 5-11)

### Existing Code to Reference

No similar existing features identified for reference. This is foundational documentation for the core library.

### Follow-up Questions

None required - all requirements clearly defined.

## Visual Assets

### Files Provided:
No visual assets provided.

### Visual Insights:
N/A - No visual assets required for code examples and documentation.

## Requirements Summary

### Functional Requirements

**Example Files (5 total):**
1. `basic_dataclass.py` - Simple dataclass injection with Injectable
   - Demonstrate basic dependency injection with dataclasses
   - Show Injectable base class usage
   - Minimal, focused example

2. `protocol_injection.py` - Protocol-based dependency injection
   - Show protocol-based abstraction
   - Demonstrate interface-driven design
   - Type-safe protocol usage

3. `async_injection.py` - Asynchronous dependency resolution
   - Show async/await support
   - Demonstrate async dependency injection patterns
   - Async service resolution

4. `kwargs_override.py` - Overriding dependencies via kwargs
   - Show runtime dependency override capability
   - Demonstrate testing patterns
   - Flexible dependency substitution

5. `custom_injector.py` - Custom injector implementations
   - Show custom injection logic
   - Demonstrate extensibility
   - Advanced customization patterns

**Documentation Structure:**
- One markdown file per example in `/docs/examples/`
- Full code included inline in documentation
- Reference to actual example file location
- Ordered by complexity (simple → advanced)
- Focus on svcs-di specifics (assume DI knowledge)

**Test Strategy:**
- Single comprehensive test file: `tests/test_examples.py`
- Expand existing test file to cover all 5 examples
- Include Sybil testing to verify documentation code snippets actually run
- Ensure documentation examples are executable and correct

### Reusability Opportunities

No existing similar features to reuse. This is foundational work creating the base example and documentation patterns.

### Scope Boundaries

**In Scope:**
- 5 core example files demonstrating foundational DI patterns
- Individual markdown documentation files for each example
- Inline code in documentation with file references
- Comprehensive test coverage in single test file
- Sybil integration for testing documentation snippets
- Examples ordered by complexity
- Minimal, focused examples (no unnecessary context)

**Out of Scope:**
- Advanced features from roadmap items 5-11
- DI fundamentals explanation (assume audience knowledge)
- Real-world context (databases, config, etc.)
- The `__svcs__` classmethod feature (has been reverted)
- Multiple test files (consolidate in one)
- Separate example categories beyond the 5 defined

### Technical Considerations

**Documentation Technology:**
- Sphinx documentation system
- Sybil for testing code snippets in documentation
- Markdown format for example documentation files
- Location: `/docs/examples/*.md`

**Test Integration:**
- File: `tests/test_examples.py`
- Must verify all 5 examples work correctly
- Sybil integration to test documentation code snippets
- Ensure examples are executable and type-safe

**Example Complexity Order:**
1. Basic dataclass injection (simplest)
2. Protocol injection (abstraction)
3. Async injection (async pattern)
4. Kwargs override (flexibility)
5. Custom injector (most advanced)

**Important Constraints:**
- Do NOT include `__svcs__` classmethod (feature was reverted)
- Keep examples minimal and focused
- Assume DI knowledge in audience
- No advanced roadmap features (items 5-11)
- All code must be runnable and type-safe

**File Locations:**
- Examples: Root level example files (e.g., `basic_dataclass.py`)
- Documentation: `/docs/examples/*.md`
- Tests: `tests/test_examples.py`
