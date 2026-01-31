---
description:
  Documentation standards for Python projects using Sphinx and MyST. Use this
  when writing documentation, setting up Sphinx, or maintaining README files.
---

# Documentation Standards

## General Documentation

- Documentation is maintained in `docs/`
- Use the Sphinx documentation system
- Docs are written in Markdown using the `MyST` parser
- Add new docs and link them into the relevant `index.md`
- Keep README.md up to date
- The README.md should be a terse version of what appears in `docs/*`
- Document new features in appropriate docs/ files
- Update CHANGELOG when making notable changes
- Write docstrings for public APIs
- Use clear, concise language
- Avoid repetition by having `docs/index.md` "include" (using MyST) parts from `README.md`

## Specifications Integration

### Directory Structure

```
project/
├── specs/
│   └── YYYY-MM-DD-feature-name/
│       └── spec.md
├── docs/
│   ├── specifications/
│   └── features/       # Wrapper pages
```

### Wrapper Page Pattern

Instead of linking directly to raw markdown files outside the docs tree, create wrapper pages that use `{include}` directives:

```markdown
# Product Mission

```{include} ../../../memory-bank/productContext.md
:relative-docs: docs/
:relative-images:
```
```

### Specification Discovery

- Use date prefix pattern `YYYY-MM-DD-*` for spec directories
- Alphabetical sort gives chronological order
- Extract titles from H1 headings (remove "Specification: " prefix)
- Extract summaries from `## Goal` section

### Sphinx Integration

Add specifications to main navigation:

```markdown
```{toctree}
:maxdepth: 2
:hidden:

examples/index
core-concepts
api-reference
specifications/index
```
```

## Best Practices

- **Self-Documenting Code**: Write code that explains itself through clear structure and naming
- **Living Documentation**: Keep examples tested via Sybil/doctest integration
- **Minimal Comments**: Add concise comments only for large sections of code logic
- **Evergreen Comments**: Comments should be informational texts relevant far into the future

## Anti-Patterns to Avoid

- Linking directly to external files in Sphinx (causes warnings)
- Outdated documentation with broken examples
- Comments that speak to recent or temporary changes
- Over-documenting obvious code
