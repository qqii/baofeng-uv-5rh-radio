# .agents/

Tool-neutral home for AI coding-agent assets in this repository.

## The mirror convention

This directory is the **canonical** location. Tool-specific paths are symlinks
that point here, so a single copy of every asset serves all agents:

| Canonical (tracked here) | Symlink (tool-specific) |
| --- | --- |
| `.agents/` | `.claude/` |
| `AGENTS.md` (repo root) | `CLAUDE.md` (repo root) |

Edit the canonical files — never the symlinks. Anything added under `.agents/`
is automatically visible to Claude Code through `.claude/`.

## Layout

- `commands/` — shared slash-command definitions.
- `skills/` — shared skill definitions.

Both start empty (`.gitkeep` placeholders); populate them as shared agent
tooling is added.

## Symlinks on Windows

These symlinks require, on Windows: Developer Mode (or admin), `git config
core.symlinks true`, and — when creating links from Git Bash —
`MSYS=winsymlinks:nativestrict`. They are stored in git as real symlinks, so a
clone on a correctly configured machine reproduces them automatically.
