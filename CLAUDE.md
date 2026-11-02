# CLAUDE.md

## Rules

- Never add `Co-Authored-By` trailers, "Generated with Claude Code" lines, or any other
  AI attribution to commits, pull requests, issues, or comments.

## Project

- Backend code lives in `backend/`; run all commands from there.
- Lint: `ruff check .`  Tests: `pytest -q` (no Postgres, network, or API key needed).
- Tests mock the OpenAI client and use in-memory SQLite. Keep them that way.
- Dependencies are pinned in `backend/requirements.txt` / `requirements-dev.txt`.
