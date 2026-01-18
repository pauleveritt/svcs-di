# Python Tooling

## Astral Plugin for Claude Code

This project uses the **Astral plugin for Claude Code** (`astral@astral-sh`), which provides skills for Python development tools. The plugin also configures the **ty LSP** for real-time type checking.

**CRITICAL: Always invoke Astral tools via the plugin skills, NEVER via Bash commands.**

### Available Astral Skills

#### uv - Package and Project Manager

**Skill:** `/astral:uv` or invoke via `Skill` tool with `skill: "astral:uv"`

Use for:

- Package management (`uv add`, `uv remove`)
- Running scripts (`uv run`)
- Project initialization (`uv init`)
- Virtual environment management

**Don't:** Run `uv` via `Bash` tool
**Do:** Use the `Skill` tool to invoke the uv skill

#### ty - Type Checker and LSP

**Skill:** `/astral:ty` or invoke via `Skill` tool with `skill: "astral:ty"`

Use for:

- Type checking Python code
- Understanding type errors

**Important:** The ty LSP is automatically configured and provides real-time feedback via `<new-diagnostics>` blocks. *
*Trust the LSP diagnostics** - don't run redundant `ty check` commands unless verifying the full codebase.

**Don't:** Run `uv run ty check` or `ty check` via bash
**Do:**

- Trust the `<new-diagnostics>` feedback from the LSP
- Use the skill only when you need explicit type checking guidance
- Only run full codebase checks at major milestones

#### ruff - Linter and Formatter

**Skill:** `/astral:ruff` or invoke via `Skill` tool with `skill: "astral:ruff"`

Use for:

- Linting Python code
- Formatting Python code
- Fixing common issues automatically

**Don't:** Run `ruff check` or `ruff format` via bash
**Do:** Use the `Skill` tool to invoke the ruff skill

## LSP Integration

The ty language server is automatically configured for `.py` and `.pyi` files. You will receive real-time diagnostics as
you edit:

```
<new-diagnostics>
The following new diagnostic issues were detected:

filename.py:
  ✘ [Line 10:5] Error message here [error-code] (ty)
</new-diagnostics>
```

**Trust these diagnostics** - they are the type checker running in real-time. You don't need to manually run `ty check`
after every edit.

## Code Exploration - Use LSP

For exploring and understanding code, **use the LSP tool instead of bash/grep**.

### Use LSP for:

- **Finding definitions**: `LSP(operation="goToDefinition", ...)`
- **Finding references**: `LSP(operation="findReferences", ...)`
- **Getting type info**: `LSP(operation="hover", ...)`
- **Listing symbols in a file**: `LSP(operation="documentSymbol", ...)`
- **Searching workspace symbols**: `LSP(operation="workspaceSymbol", ...)`
- **Understanding call hierarchies**: `LSP(operation="incomingCalls", ...)` / `outgoingCalls`

### Don't use Bash for code exploration:

- ❌ `grep` or `rg` to find function definitions
- ❌ `grep` or `rg` to find usages/references
- ❌ Text parsing to understand types or signatures

**Example - Finding a method definition:**

Bad:
```python
Bash("grep -n 'def get' .venv/lib/.../svcs/_core.py")
```

Good:
```python
LSP(operation="goToDefinition", filePath="myfile.py", line=10, character=15)
# Or to list all symbols:
LSP(operation="documentSymbol", filePath=".venv/lib/.../svcs/_core.py", line=1, character=1)
```

## When to Use Skills vs Bash

### ALWAYS Use Astral Skills For:

| Task | Skill Invocation |
|------|------------------|
| Running Python scripts | `Skill(skill="astral:uv", args="run script.py")` |
| Running pytest | `Skill(skill="astral:uv", args="run pytest tests/")` |
| Adding packages | `Skill(skill="astral:uv", args="add <package>")` |
| Removing packages | `Skill(skill="astral:uv", args="remove <package>")` |
| Syncing dependencies | `Skill(skill="astral:uv", args="sync --all-groups")` |
| Linting | `Skill(skill="astral:ruff")` - follow guidance |
| Formatting | `Skill(skill="astral:ruff")` - follow guidance |
| Type checking | Trust LSP `<new-diagnostics>`, or `Skill(skill="astral:ty")` |

### Use Bash ONLY For:

- `git` commands
- `just docs` / `just docs-live` (Sphinx documentation)
- `just install` (initial project setup)
- `just clean` (cleanup artifacts)
- Other non-Python tools

### NEVER Use Bash For:

❌ `uv run`, `uv add`, `uv remove`, `uv sync` - use `astral:uv` skill
❌ `ruff check`, `ruff format` - use `astral:ruff` skill
❌ `ty check` - use LSP diagnostics or `astral:ty` skill
❌ `python script.py` - use `astral:uv` skill with `run script.py`
❌ `pytest` - use `astral:uv` skill with `run pytest`
❌ `just test`, `just lint`, `just fmt`, `just typecheck` - use Astral skills
❌ `grep`/`rg` for code exploration - use LSP instead

## Example: Type Checking Workflow

**❌ Bad - Using Bash:**

```python
# Edit file
Bash("uv run ty check src/")  # WRONG - don't use Bash
# Edit file again
Bash("uv run ty check src/")  # WRONG - redundant manual checks
```

**✅ Good - Trust LSP:**

```python
# Edit file
# Observe <new-diagnostics> block (ty LSP provides real-time feedback)
# Edit file to fix issues
# Observe <new-diagnostics> updated or cleared
# Only use Skill(skill="astral:ty") if you need explicit guidance
```

## Example: Running Tests

**❌ Bad:**

```python
# Using Bash directly
Bash("uv run pytest tests/")  # WRONG

# Using Just
Bash("just test")  # WRONG

# Using python directly
Bash("python -m pytest tests/")  # WRONG
```

**✅ Good - Use uv Skill:**

```python
# Run all tests
Skill(skill="astral:uv", args="run pytest tests/")

# Run specific test file
Skill(skill="astral:uv", args="run pytest tests/test_specific.py -v")

# Run with coverage
Skill(skill="astral:uv", args="run pytest --cov=src tests/")

# Run doctests
Skill(skill="astral:uv", args="run pytest src/ docs/ README.md")
```

## Example: Linting and Formatting

**❌ Bad:**

```python
Bash("ruff check .")  # WRONG
Bash("ruff format .")  # WRONG
Bash("just lint")  # WRONG
Bash("just fmt")  # WRONG
```

**✅ Good - Use ruff Skill:**

```python
# Invoke the ruff skill and follow its guidance
Skill(skill="astral:ruff")
# The skill will guide you on proper ruff check/format usage
```

## Example: Package Management

**❌ Bad:**

```python
Bash("uv add requests")  # WRONG
Bash("uv remove flask")  # WRONG
Bash("pip install requests")  # VERY WRONG
```

**✅ Good - Use uv Skill:**

```python
Skill(skill="astral:uv", args="add requests")
Skill(skill="astral:uv", args="add --group dev pytest")
Skill(skill="astral:uv", args="remove flask")
Skill(skill="astral:uv", args="sync --all-groups")
```
