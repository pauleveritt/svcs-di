---
name: Global Tooling
description: Your approach to handling global tooling. Use this skill when working on files where global tooling comes into play.
---

# Global Tooling

This Skill provides Claude Code with specific guidance on how to adhere to coding standards as they relate to how it should handle global tooling.

## Instructions

For details, refer to the information provided in this file:
[global tooling](../../../agent-os/standards/global/tooling.md)

## Quick Reference

### Astral Tools - Use Skills, Not Bash

- **uv:** `Skill(skill="astral:uv", args="...")`
- **ty:** `Skill(skill="astral:ty", args="...")` (but trust LSP diagnostics first)
- **ruff:** `Skill(skill="astral:ruff", args="...")`

### Code Exploration - Use LSP, Not Grep

- `LSP(operation="goToDefinition", ...)` - Find definitions
- `LSP(operation="findReferences", ...)` - Find usages
- `LSP(operation="hover", ...)` - Get type info
- `LSP(operation="documentSymbol", ...)` - List symbols

### Trust the LSP

Real-time diagnostics appear in `<new-diagnostics>` blocks. Don't run redundant type checks.
