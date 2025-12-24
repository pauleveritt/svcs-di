# Documentation Standards

- Documentation is maintained in `docs`
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

## Using Context7 for Documentation

Try to use context7 when generating code, providing setup/configuration steps, or needing library/API documentation.
This means:

- Automatically use the Context7 MCP tools (`mcp__context7__resolve-library-id` and `mcp__context7__get-library-docs`)
  without waiting for explicit requests
- Use context7 when working with any third-party libraries or frameworks
- Consult up-to-date documentation before suggesting code patterns or API usage
- Verify current best practices and API signatures from official documentation
