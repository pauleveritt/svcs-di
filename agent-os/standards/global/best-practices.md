# Development Best Practices

## Python version

- Use Python 3.14 or higher
- Prefer features available in the latest Python 

## Running Python

- **Ad-hoc scripts**: If you generate a script, run it with `uv run` from the `pyproject.toml` directory
- **Formatting**: Always use `just` for this
- **Testing**: Always use `just` for this
- **Type checking**: Always use `just` for this

## Packaging

- Source code in `src/` for proper packaging
- Use `uv` and `pyproject.toml` for managing dependencies
- Use `uv add <package>` to add dependencies
- Use `uv remove <package>` to remove dependencies
- `uv` manages `pyproject.toml` automatically
- **Never** mix with pip/poetry unless explicitly needed


## Quality Checks

After each step, run these commands to ensure code quality:

- Formatting: `just fmt`
- Linting: `just lint-fix`
- Type checking: `just typecheck`
- Tests: `just test`

## Import Best Practices

- Use absolute imports from package root
- Avoid circular dependencies
- Group imports: stdlib → third-party → local

## Documentation

Maintain these key files:

- `README.md`: Project overview, setup instructions
- `pyproject.toml`: Dependencies, metadata, tool configs
- Inline docstrings: Use modern format with type hints

## Using Just Recipes

Always check for just recipes before running raw commands:

- Run `just` to see all available recipes
- Prefer `just <recipe>` over raw `uv run` commands
- The justfile is the single source of truth for development workflows
- Common recipes: `lint`, `fmt`, `typecheck`, `test`, `ci-checks`, `install`

## Anti-Patterns to Avoid

❌ Mixing package managers (stick to uv)
❌ Relative imports beyond local modules
❌ Missing `__init__.py` in packages
❌ Ignoring type hints
❌ Skipping quality checks
❌ Using deprecated Python features (Union, List, etc.)
