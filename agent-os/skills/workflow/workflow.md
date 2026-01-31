---
description:
  Global workflow standards for Python development. Use this when setting up
  projects, running quality checks, or establishing development workflows.
allowed-tools: Bash(uv run*)
---

# Global Workflow Standards

## Technical Stack

- **Package Manager**: `uv` (Single source of truth for dependencies).
- **Project Structure**: Use `src/` layout for Python projects.

## Development Lifecycle

After any code modification, ensure quality by running:

1. `uv run ruff format`: Standardize formatting.
2. `uv run ruff check --fix`: Check for static errors.
3. `uv run ty check`: Verify type safety.
4. `uv run pytest`: Run the test suite.

## Tooling Usage

- Use `uv run` for all command execution.
- Prefer absolute imports and structured project layouts.

## Documentation Standards

- **Package Installation**: In documentation, instruct users to use `uv add <package_name>` instead of `uv pip install`.
- Provide clear, reproducible examples for all workflows.
- Include version constraints when appropriate.

## Pre-Commit Hooks

### Using just enable-pre-push

The recommended approach is to use the Justfile recipe:

```bash
just enable-pre-push
```

This installs a git pre-push hook that runs `just ci-checks` before every push.

To disable:

```bash
just disable-pre-push
```

### Manual Pre-Commit Configuration

For more granular control, create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: ruff-format
        name: ruff format
        entry: uv run ruff format --check
        language: system
        types: [python]

      - id: ruff-check
        name: ruff check
        entry: uv run ruff check
        language: system
        types: [python]

      - id: ty-check
        name: ty check
        entry: uv run ty check
        language: system
        types: [python]
        pass_filenames: false
```

Install with:

```bash
uv add --dev pre-commit
uv run pre-commit install
```

### Workflow Integration

- **Development**: Run checks manually or on save in IDE
- **Pre-push**: Use `just enable-pre-push` for automated checks before push
- **CI**: Always run full `just ci-checks` in CI pipeline

## Anti-Patterns

- Mixing `pip`, `poetry`, and `uv`.
- Hardcoding paths (use `PurePath` or `Path`).
- Submitting code without running quality checks.
- Skipping pre-commit hooks with `--no-verify`.
- Running quality tools directly instead of via `uv run`.

## Related Skills

- [uv](../uv.md) - Package management
- [ruff](../ruff.md) - Linting and formatting
- [ty](../ty.md) - Type checking
- [testing](../testing/testing.md) - Test standards
- [justfile](../justfile.md) - Task automation
