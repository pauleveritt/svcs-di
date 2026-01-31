---
description:
  PEP 750 t-strings (template strings) for Python 3.14+. Use this when working
  with template strings, template functions, or interpolation patterns.
---

# PEP 750 T-Strings

## Overview

T-strings (template strings) are a Python 3.14+ feature defined in PEP 750. They provide a way to create templates with interpolated values that can be processed by custom functions.

## Syntax

A t-string is created using the `t` prefix:

```python
name = "World"
template = t"Hello, {name}!"
```

The result is a `Template` object from `string.templatelib`, not a string.

## Template Functions

A **template function** is a Python function that accepts a `Template` object and returns a processed result (typically a string or custom object):

```python
from string.templatelib import Template, Interpolation

def my_template(template: Template) -> str:
    """Process a template and return a string."""
    parts = []
    for part in template:
        if isinstance(part, str):
            parts.append(part)
        elif isinstance(part, Interpolation):
            # part.value is the interpolated value
            parts.append(str(part.value))
    return "".join(parts)
```

## Template Structure

A `Template` is an iterable of "parts" which are either:
- `str` - Static text between interpolations
- `string.templatelib.Interpolation` - Dynamic parts representing `{...}` expressions

The `Interpolation` class has these key attributes:
- `value` - The evaluated value of the expression
- `expr` - The source expression as a string
- `conv` - Conversion specifier (`r`, `s`, `a`, or `None`)
- `format_spec` - Format specification string

## Using with tdom

tdom's `html()` function is a template function that accepts t-strings:

```python
from tdom import html

name = "World"
element = html(t"<div>Hello, {name}!</div>")
```

The `html()` function processes the template and returns a tdom `Node`.

## Interpolation Patterns

### Basic Interpolation

```python
name = "Alice"
template = t"Hello, {name}!"
```

### Expressions

```python
x = 10
template = t"Result: {x * 2}"
```

### Format Specifications

```python
value = 3.14159
template = t"Pi: {value:.2f}"
```

### Conversion Specifiers

```python
obj = MyClass()
template = t"Repr: {obj!r}, Str: {obj!s}"
```

## Best Practices

**DO**:
- Use t-strings when you need to process templates (HTML, SQL, etc.)
- Always type hint template functions with `Template` parameter
- Use `isinstance` checks to distinguish `str` and `Interpolation` parts
- Create specialized template functions for specific use cases (HTML, SQL, logging)

**DON'T**:
- Use t-strings where f-strings would suffice (simple string formatting)
- Ignore the `conv` and `format_spec` attributes when they matter
- Build HTML strings manually - use tdom's `html()` function

## Anti-Patterns

- Using f-strings when you need template processing (security, escaping)
- Not handling both `str` and `Interpolation` parts in template functions
- Mixing t-strings with manual string concatenation

## Related Skills

- [tdom](tdom.md) - UI components using t-strings and `html()` function
- [python](python.md) - Python language standards
