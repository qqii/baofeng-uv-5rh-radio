# AGENTS.md

Guidance for AI coding agents working in this repository. Codex CLI reads this
file directly; Claude Code reads it through the `CLAUDE.md` symlink. Human-facing
docs live in `README.md` and `docs/`; this is the agent-oriented companion.

## Project overview

This project generates a CHIRP-compatible memory CSV for programming a Baofeng
UV-5RH handheld radio. Almost all logic lives in a single script, `generate.py`,
which writes `res/Baofeng_UV5RH_master.csv`. There is no application runtime or
test suite - the "build" is running the generator, and quality is enforced by
linting and type checking.

## Setup

- Python is pinned to `3.14.*` (see `.python-version` and `pyproject.toml`).
- Dependency and environment management is via [`uv`](https://docs.astral.sh/uv/).
- Install the toolchain (creates `.venv` from `uv.lock`):

  ```shell
  uv sync
  ```

## Common commands

Run from the repo root. This is a Windows-primary project, but every command
below is shell-agnostic.

| Task | Command |
| --- | --- |
| Generate the CSV | `uv run python generate.py` |
| Format | `ruff format generate.py` |
| Lint | `ruff check generate.py` |
| Type check | `pyrefly check` |
| Pre-commit hooks | `uv run lefthook run pre-commit --all-files --force --no-auto-install --no-tty` |

After any change to `generate.py`, regenerate the CSV and run the format, lint,
type-check, and pre-commit commands before committing.

## Code style and conventions

- **Ruff** governs formatting and linting: line length 100, target `py314`, and
  `select = ["ALL"]` (only the exceptions in `pyproject.toml` are ignored). Treat
  a clean `ruff check` as required, not optional.
- **No relative imports** - `flake8-tidy-imports` bans them (`ban-relative-imports = "all"`).
- **Type annotations** - `pyrefly` runs with `check-unannotated-defs = true`, so
  annotate function signatures fully.
- Keep generator logic in `generate.py` unless there is a clear reason to split it.

## Repository layout

- `generate.py` - the CHIRP CSV generator (primary source file).
- `res/` - generated output and local vendor assets. **Gitignored by default**.
  CHIRP images are published as GitHub release assets, not committed to the repo.
  Do not commit files under `res/` unless explicitly asked.
- `docs/` - extracted vendor instructions.
- `.agents/` - tool-neutral agent assets (commands, skills). `.claude/` is a
  symlink to this directory and `CLAUDE.md` is a symlink to this file, so a
  single canonical copy serves every agent. See `.agents/README.md`.

## Commit conventions

- History follows **Conventional Commits** (`feat:`, `fix:`, `refactor:`,
  `chore:`, `docs:`). Match that style.
- **AI-authored commits must always include a `Co-Authored-By:` trailer** that
  identifies the agent, e.g.:

  ```
  Co-Authored-By: Codex <codex@openai.com>
  ```

  Use the trailer matching the agent that made the commit (for Claude Code:
  `Co-Authored-By: Claude <noreply@anthropic.com>`).
- Keep changes to `res/` out of commits unless the request is specifically about
  local release artifacts.
