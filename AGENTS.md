# Repository Guidelines

## Project Structure & Module Organization

The Python package lives under `unifi_mcp/` with entry points in `__main__.py`, `main.py`, and the Typer CLI in `cli.py`. Controller integrations sit in `clients/`, Pydantic schemas in `models/`, tool implementations in `tools/`, helpers in `utils/`, and monitoring hooks in `monitoring/`. Smoke tests live in `tests/test_unifi_mcp.py`; mirror the package layout when adding modules or coverage.

## Build, Test, and Development Commands

- `uv sync` — install runtime and dev dependencies from `pyproject.toml` (Python ≥3.13).
- `uv run python -m unifi_mcp start --host 127.0.0.1 --port 8000 --debug` — run the FastMCP server locally.
- `uv run python -m unifi_mcp config` — print merged server and controller settings.
- `uv run python tests/test_unifi_mcp.py` — execute async smoke checks; export `UNIFI_*`/`UNIFI_ACCESS_*` to hit live controllers.

## Coding Style & Naming Conventions

Follow PEP 8 with 4-space indentation and triple double-quoted docstrings. Keep modules and functions snake_case (see `retry_utils.py`), classes PascalCase, and constants UPPER_SNAKE_CASE. Favor explicit type hints and Pydantic models for payloads; extend CLI commands via Typer decorators as shown in `unifi_mcp/cli.py`.

## Testing Guidelines

Reuse asyncio-friendly patterns already in `tests/test_unifi_mcp.py`. Name coroutine tests `test_*`, guard network calls with environment checks so CI can run without credentials, and supply sample credentials in messages. When touching HTTP clients, prefer stubbing controller responses or isolating them behind fixtures to avoid external calls.

## Commit & Pull Request Guidelines

History is currently empty; adopt Conventional Commit prefixes (`feat:`, `fix:`, `docs:`) in imperative mood to clarify intent. PRs should outline scope, testing performed, and any controller prerequisites, linking tracking issues or screenshots for CLI-affecting work. Never commit real credentials—use redacted examples in docs and tests.

## Configuration & Security Tips

Load configuration through environment variables or the `[tool.unifi-mcp]` table in `pyproject.toml`. Keep secrets in ignored `.env` files, enable SSL verification when targeting production controllers, and restrict exposed ports to trusted networks before deploying the server.
