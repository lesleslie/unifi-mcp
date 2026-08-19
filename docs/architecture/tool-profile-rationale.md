# Tool Profile Adoption (W3.4) — unifi-mcp

**Status:** DONE
**Date:** 2026-08-18
**Tier:** B (2-tier mapping)
**W0 helper version:** mcp-common 0.18.0

## What

unifi-mcp adopted the ``mcp_common.tools.dispatch._apply_tool_profile`` W0
helper to gate tool registration at startup, controlled by the
``UNIFI_TOOL_PROFILE`` environment variable. The previous inline pattern:

```python
if network_client:
    _register_network_tools(server, network_client)
if access_client:
    _register_access_tools(server, access_client)
```

is replaced by a single async dispatch through ``apply_unifi_tool_profile``
inside the new ``unifi_mcp.server.create_app`` (the production async
factory). The sync ``create_server`` is preserved as a thin wrapper
around ``asyncio.run(create_app(...))`` so existing call sites in
``__main__.py``, the test suite, and the CLI keep working.

## Why 2-tier, not 3-tier

| Tier | Count | Tools | Notes |
|------|-------|-------|-------|
| **MINIMAL** | 0 | + ``discover_tools`` meta-tool + ``/healthz`` HTTP route | Liveness probe only. |
| **FULL** | 13 | 8 network + 5 access (when both controllers configured) | Default; matches pre-refactor inline registration. |
| (omitted STANDARD) | — | — | 3-tier split adds no value for a 2-group repo with no health tools. |

The ``MANDATORY_GROUPS`` / ``essential_tool_names`` subset checks are
explicitly opted out (``mandatory_groups=set()``, ``essential_tool_names=set()``)
because unifi-mcp has no tools that must be present at every profile level.
The ``/healthz`` HTTP route is registered via
``mcp_common.health.register_http_health_route`` and lives outside the W0
dispatch, so it is always available regardless of profile.

## How (production path)

```python
async def create_app(settings: Settings) -> FastMCP:
    server = FastMCP(name="UniFi Controller MCP Server")
    register_http_health_route(server, service_name="unifi", version=__version__)
    # ... custom_route /healthz, rate-limiting middleware ...

    network_client = _create_network_client(settings)
    access_client = _create_access_client(settings)

    await apply_unifi_tool_profile(
        server,
        network_client=network_client,
        access_client=access_client,
    )
    return server


def create_server(settings: Settings) -> FastMCP:
    return asyncio.run(create_app(settings))
```

The dispatch surface lives at ``unifi_mcp/tools/profiles.py``:

| Symbol | Purpose |
|--------|---------|
| ``_GROUP_REGISTRY`` | Single source of truth — tuple list of (group_name, description). Used to derive ``FULL_REGISTRATIONS``. |
| ``MINIMAL_REGISTRATIONS`` | Empty list — no controller tools under MINIMAL. |
| ``FULL_REGISTRATIONS`` | Derived from ``_GROUP_REGISTRY``: ``["network_tools", "access_tools"]``. |
| ``PROFILE_REGISTRATIONS`` | Dict mapping ``ToolProfile`` → list. 2-tier only. |
| ``_build_registration_map(network_client, access_client)`` | Returns ``{group_key: register_fn(app)}`` map. Skips groups whose controller isn't configured. |
| ``register_all_tool_groups(server, network_client, access_client)`` | Bulk registration fn used as ``register_all_fn`` at FULL profile. |
| ``apply_unifi_tool_profile(server, *, network_client, access_client)`` | Async dispatch wrapper. Calls ``_apply_tool_profile`` (NOT the sync wrapper). |

## Why ``_apply_tool_profile`` (async), NOT ``apply_tool_profile`` (sync)

The W0 helper has TWO entry points:

| Helper | Type | Behavior |
|--------|------|----------|
| ``apply_tool_profile`` | Sync wrapper around ``asyncio.run(...)`` | Raises ``RuntimeError`` when called from inside a running event loop. |
| ``_apply_tool_profile`` | Async helper | Safe to call from any async context. |

The production path is ``async def create_app`` → ``await apply_unifi_tool_profile`` →
``await _apply_tool_profile``. The sync wrapper is never reached from
production code; it only exists for sync callers (CLI startup) which
bridge through ``asyncio.run(create_app(...))``.

**Critical regression check:** mutating the production code to remove the
``await`` (turning it into a bare ``apply_unifi_tool_profile(...)`` call)
causes the AST guard test ``test_server_awaits_apply_unifi_tool_profile``
to fail AND causes ``test_create_app_full_profile_real_path`` to fail at
runtime because ``apply_unifi_tool_profile`` is a coroutine that the
un-awaited call would not actually await. Both failure modes are covered.

## Lambda binding for 2-arg register fns

unifi-mcp's ``_register_network_tools(server, client)`` and
``_register_access_tools(server, client)`` take 2 arguments. The W0 helper
expects single-arg callables ``(server)``. Each registration_map entry
uses a lambda with default-argument capture:

```python
nc = network_client  # capture loop/closure variable
mapping["network_tools"] = lambda app, _nc=nc: _register_network_tools(app, _nc)
```

The ``_nc=nc`` default-arg trick prevents the late-binding bug where
``nc`` would alias the last iteration's value. (Not strictly needed
here since there is no loop, but consistent with the W3.1 lesson.)

## Behavioral parity

| Configuration | Pre-refactor | Post-refactor |
|---------------|--------------|---------------|
| No controllers, default env | 0 tools | 1 tool (``discover_tools``) — additive meta-tool |
| Network only, default env | 8 tools | 8 tools + ``discover_tools`` = 9 |
| Access only, default env | 5 tools | 5 tools + ``discover_tools`` = 6 |
| Both controllers, default env | 13 tools | 13 tools + ``discover_tools`` = 14 |
| Both controllers, UNIFI_TOOL_PROFILE=minimal | (no profile system) | ``discover_tools`` only |
| Both controllers, UNIFI_TOOL_PROFILE=full | (no profile system) | 13 + ``discover_tools`` = 14 |
| Both controllers, UNIFI_TOOL_PROFILE=bogus | (no profile system) | ``InvalidProfileError`` (fail-loud) |

The pre-refactor test suite (``tests/test_server.py`` and friends) calls
``create_server(settings)`` synchronously and asserts the server exists.
This still works because ``create_server`` wraps ``create_app`` via
``asyncio.run``.

## Files touched

| Path | Change |
|------|--------|
| ``unifi_mcp/tools/profiles.py`` | **NEW** — PROFILE_REGISTRATIONS, _build_registration_map, register_all_tool_groups, apply_unifi_tool_profile. |
| ``unifi_mcp/server.py`` | Added ``import asyncio``, import ``apply_unifi_tool_profile``, added async ``create_app``, refactored ``create_server`` to wrap ``asyncio.run(create_app(...))``. |
| ``unifi_mcp/__init__.py`` | ``__version__`` is dynamic via ``importlib.metadata`` — no manual sync needed. |
| ``pyproject.toml`` | Bumped ``mcp-common>=0.17.0`` → ``mcp-common>=0.18.0``. |
| ``tests/unit/test_tool_profile.py`` | **NEW** — 16 wiring tests covering AST guards, behavioral parity, full/minimal profiles, real production-path startup. |
| ``CLAUDE.md`` | Added "Tool Profile System" subsection. |
| ``docs/architecture/tool-profile-rationale.md`` | **NEW** — this doc. |

## Test summary

| Test class / file | Count | Notes |
|-------------------|-------|-------|
| ``tests/unit/test_tool_profile.py`` | 16 | New wiring tests. |
| ``tests/test_server.py`` (existing) | 18 | Unchanged; still pass through ``create_server`` sync wrapper. |
| Other pre-existing tests | 200+ | Unchanged. |

## Notes for the W4 wave (10 Tier-A repos)

- Tier-A repos with rich tool surfaces (mahavishnu, akosha, dhara,
  crackerjack, session-buddy, etc.) will use the 3-tier mapping
  (MINIMAL / STANDARD / FULL). The 2-tier pattern in this repo does NOT
  apply to Tier-A.
- The lambda binding pattern (default-arg capture to avoid late-binding)
  generalizes cleanly. Tier-A repos with 2-arg register fns should use
  the same pattern.
- The ``_GROUP_REGISTRY`` constant for single-source-of-truth
  ``FULL_REGISTRATIONS`` derivation scales to N groups.
- Tier-A repos MUST also expose ``create_app`` (or equivalent async
  factory) so the W2b.3 keystone test (``test_server_awaits_apply_*``)
  has a real production path to exercise. Sync-only factories cannot be
  tested under an event loop.
- AST guard MUST structurally check for ``ast.Await(value=ast.Call(
  func=ast.Name(id="apply_<repo>_tool_profile")))``. Counting ``ast.Call``
  matches is a tautology (would pass for the sync-wrapper regression).
- ``MANDATORY_GROUPS`` and ``essential_tool_names`` defaults in
  mcp-common are empty sets. Repos that want always-on health tools
  opt in explicitly. The ``test_mandatory_tools_invariant`` pattern
  (asserting the explicit opt-out is documented in source) prevents
  silent drift.
