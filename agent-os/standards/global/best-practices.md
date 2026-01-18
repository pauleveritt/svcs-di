# Development Best Practices

## Python version

- Use Python 3.14 or higher
- Prefer features available in the latest Python

## Running Python - Always Use Astral Skills

**All Python execution MUST go through the Astral plugin skills.** Never use Bash to run Python directly.

### Running Scripts
Use the `uv` skill:
```python
Skill(skill="astral:uv", args="run script.py")
```

### Running Tests
Use the `uv` skill with pytest:
```python
Skill(skill="astral:uv", args="run pytest tests/")
Skill(skill="astral:uv", args="run pytest tests/test_specific.py -v")
```

### Formatting Code
Use the `ruff` skill:
```python
Skill(skill="astral:ruff")  # Then follow skill guidance for formatting
```

### Linting Code
Use the `ruff` skill:
```python
Skill(skill="astral:ruff")  # Then follow skill guidance for linting
```

### Type Checking
**Trust the ty LSP diagnostics** in `<new-diagnostics>` blocks. Only invoke the skill for explicit guidance:
```python
Skill(skill="astral:ty")  # When you need type checking guidance
```

## Packaging - Use the uv Skill

- Source code in `src/` for proper packaging
- Use the `uv` skill for all package management
- **Never** use Bash for `uv` commands

### Adding Dependencies
```python
Skill(skill="astral:uv", args="add <package>")
Skill(skill="astral:uv", args="add --group dev <package>")  # Dev dependency
```

### Removing Dependencies
```python
Skill(skill="astral:uv", args="remove <package>")
```

### Syncing Dependencies
```python
Skill(skill="astral:uv", args="sync --all-groups")
```

## Quality Checks - Use Astral Skills

After each significant change, ensure code quality using the Astral skills:

1. **Formatting**: `Skill(skill="astral:ruff")` - follow guidance for `ruff format`
2. **Linting**: `Skill(skill="astral:ruff")` - follow guidance for `ruff check --fix`
3. **Type checking**: Trust `<new-diagnostics>` from LSP, or `Skill(skill="astral:ty")` for full check
4. **Tests**: `Skill(skill="astral:uv", args="run pytest")`

## Import Best Practices

- Use absolute imports from package root
- Avoid circular dependencies
- Group imports: stdlib → third-party → local

## Documentation

Maintain these key files:

- `README.md`: Project overview, setup instructions
- `pyproject.toml`: Dependencies, metadata, tool configs
- Inline docstrings: Use modern format with type hints

## Code Exploration - Use LSP

**Always prefer LSP over grep/bash for code exploration:**

- **Finding definitions**: `LSP(operation="goToDefinition", ...)`
- **Finding references**: `LSP(operation="findReferences", ...)`
- **Getting type info**: `LSP(operation="hover", ...)`
- **Listing symbols**: `LSP(operation="documentSymbol", ...)`
- **Searching workspace**: `LSP(operation="workspaceSymbol", ...)`

## Just Recipes - For Manual/CI Use Only

The Justfile provides recipes for **manual command-line use** and **CI pipelines**.

**Agent OS should NOT use Just recipes** - use Astral skills instead:

| Manual Command | Agent OS Equivalent |
|----------------|---------------------|
| `just test` | `Skill(skill="astral:uv", args="run pytest")` |
| `just lint` | `Skill(skill="astral:ruff")` |
| `just fmt` | `Skill(skill="astral:ruff")` |
| `just typecheck` | `Skill(skill="astral:ty")` or trust LSP |

## Anti-Patterns to Avoid

❌ Running `python` or `uv` via Bash - use Astral skills
❌ Running `pytest` via Bash - use `Skill(skill="astral:uv", args="run pytest")`
❌ Running `ruff` via Bash - use `Skill(skill="astral:ruff")`
❌ Running `ty` via Bash - use LSP diagnostics or `Skill(skill="astral:ty")`
❌ Using `just` recipes for linting/formatting/testing - use Astral skills
❌ Using grep/rg for code exploration - use LSP
❌ Mixing package managers (stick to uv via skill)
❌ Relative imports beyond local modules
❌ Missing `__init__.py` in packages
❌ Ignoring type hints
❌ Using deprecated Python features (Union, List, etc.)
