# Python Tooling

## Astral Tools via Skills

This project uses Astral's modern Python tooling suite. **Always invoke these tools via their skills, not via bash
commands.**

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

## When to Use Bash vs Skills

### Use Skills for:

- `uv` commands (package management, running scripts, **testing with pytest**)
- `ty` type checking (when needed beyond LSP)
- `ruff` linting/formatting

**Important:** For testing, invoke `pytest` via the `uv` skill: `Skill` tool with `skill: "astral:uv"` and `args: "run pytest"`.

### Use Bash for:

- `git` commands
- `just` commands (only when needed for non-Astral tasks)
- Other non-Astral tools

**Do NOT use:**

- Just recipes for `lint`, `format`, or `typecheck` - use Astral skills instead
- Bash commands for `uv`, `ruff`, or `ty`
- `grep`/`rg` for code exploration - use LSP instead

## Example: Type Checking Workflow

**Bad:**

```python
# Edit file
# Run: Bash("uv run ty check src/")
# Read output
# Edit file again
# Run: Bash("uv run ty check src/") again
```

**Good:**

```python
# Edit file
# Observe <new-diagnostics> block (LSP provides feedback)
# Edit file to fix issues
# Observe <new-diagnostics> updated or cleared
# Final verification: only if needed for entire codebase
```

## Example: Running Tests

**Bad:**

```python
# Using bash
Bash("uv run pytest tests/")

# Or using Just
Bash("just test")
```

**Good:**

```python
# Using the uv skill
Skill(skill="astral:uv", args="run pytest tests/")

# With additional arguments
Skill(skill="astral:uv", args="run pytest tests/test_specific.py -v")
```
