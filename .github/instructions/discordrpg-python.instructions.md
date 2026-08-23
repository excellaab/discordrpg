---
name: "DiscordRPG Python Workflow"
description: "Use when editing Python files or running Python, dependency, test, lint, or formatting commands in the DiscordRPG project."
applyTo: "**/*.py"
---
# DiscordRPG Python Workflow

- Use `uv` for Python execution and project dependency management.
- Run Python commands through `uv run`, such as `uv run python script.py` or `uv run pytest`.
- Use `uv add` and `uv remove` for dependency changes so `pyproject.toml` and `uv.lock` stay synchronized.
- Do not use bare `python`, `pip`, or other package-manager commands for project work.
- Follow the existing async patterns for Discord commands and database operations.
- Keep database access in `core/lib/db.py` and preserve the existing `(result, db_error)` error-reporting convention when extending it.
