# Specification: Basic Examples and Documentation

## Goal
Create comprehensive documentation for all 5 existing examples in `/examples/`, including inline code snippets tested with Sybil, structured by complexity, and expanded test coverage in a single test file.

## User Stories
- As a developer new to svcs-di, I want to see working examples ordered by complexity so that I can understand core DI patterns progressively
- As a library maintainer, I want all documentation code snippets to be tested via Sybil so that documentation stays accurate and executable

## Specific Requirements

**Document all 5 examples in complexity order**
- Create 5 markdown files in `/docs/examples/` directory
- Order by complexity: basic_dataclass, protocol_injection, async_injection, kwargs_override, custom_injector
- Each file includes full code inline with reference to actual example file location
- Focus on svcs-di specifics without explaining general DI fundamentals
- Keep examples minimal without real-world context (no databases, config files, etc.)

**Create examples directory in docs**
- New directory path: `/docs/examples/`
- Contains 5 markdown files, one per example
- Follow MyST Markdown format for Sphinx compatibility
- Include examples index page that links to all 5 examples in order

**Structure each documentation file consistently**
- Title with example name and complexity indicator
- Brief overview of what the example demonstrates
- Full code listing in Python code block
- Reference to actual file location in `/examples/` directory
- Key concepts section explaining what's happening
- Type safety notes where relevant
- Output example showing expected results

**Integrate with existing Sphinx documentation**
- Add examples section to main documentation index
- Use existing MyST Parser configuration in conf.py
- Leverage existing Sybil setup in docs/conftest.py
- Ensure code blocks use ```python syntax for Sybil parsing
- No changes needed to Sphinx configuration (already has MyST and extensions)

**Enable Sybil testing for documentation code snippets**
- Use existing PythonCodeBlockParser in docs/conftest.py
- Code blocks in documentation must be executable
- Import statements included in code blocks where needed
- Each code block should be self-contained and runnable
- Sybil will automatically test all ```python blocks in docs/examples/*.md

**Expand test coverage in single test file**
- Enhance existing `/tests/test_examples.py` file
- Current tests already verify all 5 examples run without error
- Current tests check specific output for each example
- Add tests for edge cases and error conditions
- Add tests verifying type safety with mypy/pyright if needed
- Keep all tests in single file as requested

**Document basic_dataclass.py example**
- Simplest example showing dataclass with Injectable dependencies
- Demonstrates auto() factory for automatic resolution
- Shows Registry registration and Container.get() usage
- Explains Injectable[T] marker usage
- Output shows successful dependency injection

**Document protocol_injection.py example**
- Shows protocol-based abstraction for loose coupling
- Demonstrates registering concrete implementation for protocol interface
- Explains how Injectable[ProtocolType] enables interface-driven design
- Shows swapping implementations by changing registration
- Type-safe protocol usage throughout

**Document async_injection.py example**
- Demonstrates async/await support in dependency injection
- Shows async factory registration for services
- Explains auto_async() for services with async dependencies
- Uses Container.aget() for async resolution
- Shows mixing sync and async dependencies

**Document kwargs_override.py example**
- Explains precedence order: kwargs > container > defaults
- Shows overriding dependencies at construction time
- Demonstrates testing patterns with dependency substitution
- Explains when Injectable parameters can be overridden
- Shows factory wrapper pattern for passing kwargs

**Document custom_injector.py example**
- Most advanced example showing extensibility
- Demonstrates creating custom injector implementations
- Shows logging injector that wraps DefaultInjector
- Shows validating injector with pre/post checks
- Explains replacing DefaultInjector registration for global effect

## Visual Design
No visual assets provided or required.

## Existing Code to Leverage

**Existing Sybil configuration in docs/conftest.py**
- Already configured with PythonCodeBlockParser for ```python blocks
- Setup for docs/*.md files with patterns matching
- No modifications needed, will automatically test new examples/*.md files
- Uses MyST parser for Markdown code blocks

**Existing test structure in tests/test_examples.py**
- Parametrized test verifying all examples run without error
- Individual tests for each example checking specific output
- Uses subprocess to run examples and capture output
- Clean pattern to extend with additional test cases

**Existing example files in /examples/ directory**
- All 5 examples already implemented and working
- Each has clear docstring explaining purpose
- Follow consistent structure with main() function
- Include print statements showing results

**MyST Parser and Sphinx configuration in docs/conf.py**
- MyST Parser extension already enabled
- Multiple MyST extensions configured (colon_fence, html_admonition, etc.)
- Pygments for syntax highlighting configured
- No changes needed to support examples documentation

**svcs Registry and Container patterns**
- Registry.register_factory() for service registration
- Registry.register_value() for pre-constructed services
- Container.get() for synchronous resolution
- Container.aget() for asynchronous resolution
- auto() and auto_async() factory generators

## Out of Scope
- Advanced features from roadmap items 5-11 (context-aware resolution, location-based, scanning, etc.)
- Explaining general dependency injection fundamentals or theory
- Real-world context in examples (actual databases, configuration files, HTTP clients)
- The reverted `__svcs__` classmethod feature (must not be documented)
- Multiple test files (consolidate all example tests in test_examples.py)
- Separate categorization beyond the 5 defined examples
- Tutorial or getting-started guide (focus only on example documentation)
- API reference documentation (separate concern)
- Performance benchmarks or optimization examples
- Integration guides for frameworks (separate roadmap item)
