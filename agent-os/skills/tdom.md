---
description:
  tdom development standards for building UI components with PEP 750 t-strings.
  Use this when creating tdom components, views, or working with HTML templates.
---

# tdom Development Standards

## Overview

- **tdom**: A modern Python UI library leveraging PEP 750 t-strings.

## Components

- **Location**: Place in `components/` directory with `snake_case` filenames.
- **Function Signatures**: Always start with `*` to force keyword-only arguments.
- **Implementation**: Component dataclasses should declare `children: Element | Fragment | Node | None = None`.
- **Docstrings**: Use HTML template string examples (e.g., `html(t'<div>...</div>')`).

## Nested Syntax & Children

- **Pass Children**: Use nested syntax, **not** props.
  ```python
  <{MyComponent} prop1={value1}>
    <div>Child content</div>
  </{MyComponent}>
  ```
- **Automatic Binding**: The nested content is automatically populated into the `children` prop of the component.
- **Self-Closing**: Use `<{Component} />` only when no children are passed.

## Component Implementation

Components should declare `children` in their dataclass.

See [examples/tdom_component.py](examples/tdom_component.py) for complete examples including form inputs.

```python
@dataclass
class MyComponent:
    prop1: str
    children: Element | Fragment | Node | None = None

    def __call__(self) -> Node:
        return html(t'''
<div class="wrapper">
  <h2>{self.prop1}</h2>
  {self.children}
</div>
''')
```

### Components with __post_init__ for Data Extraction

Use `__post_init__` with `InitVar` and `field(init=False)` when a component needs to extract data from a context object. This pattern separates initialization data from stored state, making components more testable.

```python
from dataclasses import dataclass, field, InitVar

@dataclass(kw_only=True)
class UserCard:
    """Component that extracts user info from context."""
    # InitVar: passed to __post_init__ but NOT stored on instance
    context: InitVar[RequestContext]

    # field(init=False): stored on instance but NOT passed to constructor
    user_name: str = field(init=False)
    avatar_url: str = field(init=False)
    is_admin: bool = field(init=False)

    # Regular field: passed to constructor AND stored
    show_email: bool = True
    children: Element | Fragment | Node | None = None

    def __post_init__(self, context: RequestContext) -> None:
        # Extract what we need from context
        self.user_name = context.user.display_name
        self.avatar_url = context.user.avatar_url or "/default-avatar.png"
        self.is_admin = "admin" in context.user.roles

    def __call__(self) -> Node:
        return html(t'''
<div class="user-card">
  <img src={self.avatar_url} alt={self.user_name} />
  <h3>{self.user_name}</h3>
  {html(t'<span class="badge">Admin</span>') if self.is_admin else ""}
  {self.children}
</div>
''')
```

**Benefits:**
- **Testable data setup**: Test all extracted state without rendering
- **Explicit dependencies**: `InitVar` shows what's needed for setup
- **Clear stored state**: `field(init=False)` marks derived data
- **Simpler templates**: Use extracted fields directly in render

```python
# Testing the data extraction without rendering
def test_user_card_extracts_admin_status():
    context = make_context(user=User(roles=["admin", "user"]))
    card = UserCard(context=context)
    assert card.is_admin is True
    assert card.user_name == context.user.display_name
    # No need to render to test data extraction
```

## Example Usage

```python
# Layout component using proper children syntax
return html(t'''
<body>
  <{Header} title="Catalog" />
  <{Main} current_path="/home">
    <article>
      <h1>Page Content</h1>
      <p>This gets passed as children</p>
    </article>
  </{Main}>
  <{Footer} year={2025} />
</body>
''')
```

## Anti-Patterns

- **Passing `children` as a prop** (e.g. `<{Comp} children={...} />`) - CANNOT use `children=` prop, must use nested tags
- Missing `children` declaration in component dataclass.
- Using inline styles instead of semantic CSS classes.
- Creating components that are too large or handle multiple responsibilities.
- Not using type guards to narrow `Node` to `Element` in views.

## Form Handling

### Basic Form with Fieldsets

```python
@dataclass
class ContactForm:
    action: str
    method: str = "POST"

    def __call__(self) -> Node:
        return html(t'''
<form action={self.action} method={self.method}>
  <fieldset>
    <legend>Contact Information</legend>
    <label>
      Name
      <input type="text" name="name" required />
    </label>
    <label>
      Email
      <input type="email" name="email" required />
    </label>
  </fieldset>
  <fieldset>
    <legend>Message</legend>
    <label>
      Subject
      <input type="text" name="subject" />
    </label>
    <label>
      Message
      <textarea name="message" rows="5" required></textarea>
    </label>
  </fieldset>
  <button type="submit">Send</button>
</form>
''')
```

### Input Components

```python
@dataclass
class TextInput:
    name: str
    label: str
    required: bool = False
    value: str = ""
    error: str | None = None

    def __call__(self) -> Node:
        return html(t'''
<label>
  {self.label}
  <input
    type="text"
    name={self.name}
    value={self.value}
    required={self.required}
    aria-invalid={self.error is not None}
  />
  {html(t'<small class="error">{self.error}</small>') if self.error else ""}
</label>
''')
```

## Event Handling

### Progressive Enhancement with JavaScript

```python
@dataclass
class ExpandableSection:
    title: str
    children: Element | Fragment | Node | None = None

    def __call__(self) -> Node:
        return html(t'''
<details>
  <summary>{self.title}</summary>
  <div class="content">
    {self.children}
  </div>
</details>
''')
```

### HTMX Integration

```python
@dataclass
class LoadMoreButton:
    endpoint: str
    target: str

    def __call__(self) -> Node:
        return html(t'''
<button
  hx-get={self.endpoint}
  hx-target={self.target}
  hx-swap="beforeend"
>
  Load More
</button>
''')

@dataclass
class SearchForm:
    endpoint: str
    target: str

    def __call__(self) -> Node:
        return html(t'''
<form hx-get={self.endpoint} hx-target={self.target} hx-trigger="input delay:300ms">
  <input type="search" name="q" placeholder="Search..." />
</form>
''')
```

## State Management

### URL Parameters for State

```python
@dataclass
class Pagination:
    current_page: int
    total_pages: int
    base_url: str

    def __call__(self) -> Node:
        return html(t'''
<nav aria-label="Pagination">
  <ul>
    {self._prev_link()}
    {self._page_links()}
    {self._next_link()}
  </ul>
</nav>
''')

    def _prev_link(self) -> Node:
        if self.current_page > 1:
            return html(t'<li><a href="{self.base_url}?page={self.current_page - 1}">Previous</a></li>')
        return html(t'<li><span>Previous</span></li>')

    def _page_links(self) -> Node:
        links = []
        for page in range(1, self.total_pages + 1):
            if page == self.current_page:
                links.append(html(t'<li><strong>{page}</strong></li>'))
            else:
                links.append(html(t'<li><a href="{self.base_url}?page={page}">{page}</a></li>'))
        return Fragment(links)

    def _next_link(self) -> Node:
        if self.current_page < self.total_pages:
            return html(t'<li><a href="{self.base_url}?page={self.current_page + 1}">Next</a></li>')
        return html(t'<li><span>Next</span></li>')
```

### Form Submission State

```python
@dataclass
class FormWithValidation:
    action: str
    errors: dict[str, str] | None = None
    values: dict[str, str] | None = None

    def __call__(self) -> Node:
        errors = self.errors or {}
        values = self.values or {}
        return html(t'''
<form action={self.action} method="POST">
  <{TextInput}
    name="email"
    label="Email"
    value={values.get("email", "")}
    error={errors.get("email")}
    required={True}
  />
  <{TextInput}
    name="username"
    label="Username"
    value={values.get("username", "")}
    error={errors.get("username")}
    required={True}
  />
  <button type="submit">Submit</button>
</form>
''')
```

## Views

- A "View" accepts the resource that is being rendered
- It should return a `tdom.Element`
- It will have an HTML template, meaning `html(t'''<div>Some html</div>''')`
- That returns a `tdom.Node` but use a type guard or some type narrowing, and have the view return a `tdom.Element`

## Styling

- CSS Framework: PicoCSS
- Semantic, classless CSS framework
- Minimal, clean UI without custom classes
- Used for catalog browser interface

## JavaScript

- **JavaScript:** Vanilla JavaScript
- No framework dependencies
- Minimal client-side scripting
- Progressive enhancement approach
- Include into HTML with `<script type="module">` to avoid use of IIFE

## Related Skills

- [t-strings](t-strings.md) - PEP 750 t-strings for template strings
- [python](python.md) - Python language standards
- [testing](testing/testing.md) - Component testing with aria-testing
- [frontend](frontend.md) - Frontend best practices
- [examples](examples.md) - Working examples in documentation
