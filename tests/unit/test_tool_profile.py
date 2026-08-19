"""unifi-mcp tool profile wiring tests.

Verifies the W3.4 adoption of ``mcp_common.tools.dispatch._apply_tool_profile``
replaces the inline ``_register_*_tools(...)`` calls with a 2-tier
callable-mode architecture (MINIMAL / FULL) gated by the
``UNIFI_TOOL_PROFILE`` environment variable.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_profiles_py_exists() -> None:
    """profiles.py must exist under unifi_mcp/tools/."""
    profiles = REPO_ROOT / "unifi_mcp" / "tools" / "profiles.py"
    assert profiles.exists(), f"{profiles} missing"


def test_profiles_py_defines_profile_registrations() -> None:
    """profiles.py must export a PROFILE_REGISTRATIONS dict."""
    profiles = REPO_ROOT / "unifi_mcp" / "tools" / "profiles.py"
    tree = ast.parse(profiles.read_text())
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "PROFILE_REGISTRATIONS"
            for t in node.targets
        ):
            found = True
            break
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == "PROFILE_REGISTRATIONS":
                found = True
                break
    assert found, "PROFILE_REGISTRATIONS not defined in profiles.py"


def test_profiles_py_defines_build_registration_map() -> None:
    """profiles.py must export ``_build_registration_map`` (consumed by apply_unifi_tool_profile)."""
    profiles = REPO_ROOT / "unifi_mcp" / "tools" / "profiles.py"
    tree = ast.parse(profiles.read_text())
    found = any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "_build_registration_map"
        for node in ast.walk(tree)
    )
    assert found, "_build_registration_map not defined in profiles.py"


def test_profiles_py_defines_register_all_tool_groups() -> None:
    """profiles.py must export ``register_all_tool_groups`` (used as register_all_fn at FULL profile)."""
    profiles = REPO_ROOT / "unifi_mcp" / "tools" / "profiles.py"
    tree = ast.parse(profiles.read_text())
    found = any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "register_all_tool_groups"
        for node in ast.walk(tree)
    )
    assert found, "register_all_tool_groups not defined in profiles.py"


def test_profiles_py_defines_apply_unifi_tool_profile() -> None:
    """profiles.py must export ``apply_unifi_tool_profile`` (async wrapper)."""
    profiles = REPO_ROOT / "unifi_mcp" / "tools" / "profiles.py"
    tree = ast.parse(profiles.read_text())
    found = any(
        isinstance(node, ast.AsyncFunctionDef)
        and node.name == "apply_unifi_tool_profile"
        for node in ast.walk(tree)
    )
    assert found, "apply_unifi_tool_profile (async) not defined in profiles.py"


def test_profiles_py_references_unifi_tool_profile_env_var() -> None:
    """UNIFI_TOOL_PROFILE env var must be referenced in profiles.py."""
    profiles = REPO_ROOT / "unifi_mcp" / "tools" / "profiles.py"
    text = profiles.read_text()
    assert "UNIFI_TOOL_PROFILE" in text, (
        "UNIFI_TOOL_PROFILE env var not referenced in profiles.py"
    )


def test_server_uses_async_create_app() -> None:
    """server.py must have an ``async def create_app`` so it can await the dispatch helper."""
    server = REPO_ROOT / "unifi_mcp" / "server.py"
    tree = ast.parse(server.read_text())
    found = any(
        isinstance(node, ast.AsyncFunctionDef) and node.name == "create_app"
        for node in ast.walk(tree)
    )
    assert found, "async def create_app not found in server.py"


def test_server_awaits_apply_unifi_tool_profile() -> None:
    """server.py must ``await apply_unifi_tool_profile(...)`` (the async wrapper).

    Per the W2b.3 lesson: the production path must use the async helper,
    NOT the sync wrapper. The sync wrapper raises ``RuntimeError`` when
    called from inside a running event loop, which would break any test
    that runs ``create_app`` under an async context.

    Per the W3.2 round-1 fix lesson: the AST guard MUST structurally
    check for ``ast.Await(value=ast.Call(func=ast.Name(...)))``. A guard
    that just counts ``ast.Call`` matches would be a tautology that
    passes even for a bare (non-awaited) call — which is exactly the
    W2b.3 spline regression. Verified to catch a regression: temporarily
    changing ``await apply_unifi_tool_profile(...)`` to
    ``apply_unifi_tool_profile(...)`` causes this test to fail.
    """
    server = REPO_ROOT / "unifi_mcp" / "server.py"
    tree = ast.parse(server.read_text())
    found = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Await):
            continue
        if not isinstance(node.value, ast.Call):
            continue
        if not (
            isinstance(node.value.func, ast.Name)
            and node.value.func.id == "apply_unifi_tool_profile"
        ):
            continue
        found = True
        break
    assert found, (
        "await apply_unifi_tool_profile(...) not found in server.py. "
        "Production path MUST use the async helper, not the sync wrapper."
    )


def test_server_does_not_use_sync_wrapper() -> None:
    """server.py must NOT call the sync ``apply_tool_profile`` wrapper.

    W2b.3 round-1 review fix: the sync wrapper raises RuntimeError in
    event loops. The production path must use the async
    ``apply_unifi_tool_profile`` defined in profiles.py.
    """
    server = REPO_ROOT / "unifi_mcp" / "server.py"
    tree = ast.parse(server.read_text())
    sync_call = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == "apply_tool_profile":
            sync_call = True
    assert not sync_call, (
        "server.py must NOT call the sync apply_tool_profile() wrapper "
        "(raises RuntimeError in event loops). Use apply_unifi_tool_profile "
        "instead."
    )


def test_profiles_uses_async_helper_not_sync_wrapper() -> None:
    """profiles.py must call ``_apply_tool_profile`` (async helper), NOT the sync wrapper.

    This is the AST guard for the production W0 dispatch surface — the
    W2b.3 keystone. Both names ``_apply_tool_profile`` and
    ``apply_tool_profile`` are scanned so a future aliasing regression
    (e.g. ``apply_tool_profile = _apply_tool_profile``) is caught.
    """
    profiles = REPO_ROOT / "unifi_mcp" / "tools" / "profiles.py"
    tree = ast.parse(profiles.read_text())

    # The async helper name MUST be referenced somewhere (called, imported).
    helper_referenced = False
    # The sync wrapper name must NOT appear as a bare call.
    sync_call = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "_apply_tool_profile":
                helper_referenced = True
            if node.func.id == "apply_tool_profile":
                sync_call = True
    assert helper_referenced, (
        "profiles.py must call _apply_tool_profile(...) — the async helper, "
        "not the sync wrapper."
    )
    assert not sync_call, (
        "profiles.py must NOT call apply_tool_profile(...) — the sync wrapper "
        "raises RuntimeError in event loops."
    )


def test_server_no_inline_register_calls() -> None:
    """server.py must NOT call _register_*_tools directly outside create_app.

    That call must be routed through the W0 dispatch helper so the
    profile env var controls which groups register. Uses AST to allow
    function definitions but forbid call sites.
    """
    server = REPO_ROOT / "unifi_mcp" / "server.py"
    tree = ast.parse(server.read_text())
    bad_calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"_register_network_tools", "_register_access_tools"}:
                bad_calls.append(node.func.id)
    assert not bad_calls, (
        f"server.py must not call {' or '.join(bad_calls)}() directly; "
        "route through apply_unifi_tool_profile(...) instead."
    )


def test_pyproject_bumps_mcp_common_to_0_18() -> None:
    """mcp-common pin must be >=0.18.0 (the W0 helper version)."""
    pyproject = REPO_ROOT / "pyproject.toml"
    text = pyproject.read_text()
    assert "mcp-common>=0.18.0" in text, (
        "mcp-common pin must be >=0.18.0 in pyproject.toml"
    )


def test_decision_doc_exists_at_tracked_path() -> None:
    """Rationale doc must live at docs/architecture/tool-profile-rationale.md."""
    path = REPO_ROOT / "docs" / "architecture" / "tool-profile-rationale.md"
    assert path.exists(), f"{path} missing"


def test_profile_registrations_subset_of_map() -> None:
    """Every key referenced in PROFILE_REGISTRATIONS must exist in REGISTRATION_MAP.

    Inline assertion (per W2b.1 lesson: prefer inline ``assert set == {...}``
    over golden fixtures for parity tests).
    """
    from mcp_common.tools import ToolProfile

    from unifi_mcp.tools.profiles import (
        _build_registration_map,
        PROFILE_REGISTRATIONS,
    )

    # With no clients, the map still includes both group keys but each
    # binds to a no-op so the W0 dispatch can resolve every
    # PROFILE_REGISTRATIONS reference without raising ValueError.
    mapping_empty = _build_registration_map(None, None)
    assert set(mapping_empty.keys()) == {"network_tools", "access_tools"}, (
        f"_build_registration_map(None, None) keys must be exactly the "
        f"two group names; got {sorted(mapping_empty.keys())}"
    )

    # PROFILE_REGISTRATIONS values that reference group names should be
    # present in REGISTRATION_MAP regardless of which clients are configured.
    mapping_full = _build_registration_map(object(), object())
    for profile, regs in PROFILE_REGISTRATIONS.items():
        for group in regs:
            if not isinstance(group, str):
                continue
            assert group in mapping_full, (
                f"{profile.value} references group {group!r} but REGISTRATION_MAP "
                f"is missing it; keys={sorted(mapping_full)}"
            )


def test_profile_registrations_has_2_tiers() -> None:
    """PROFILE_REGISTRATIONS must have exactly MINIMAL + FULL (Tier-B 2-tier mapping).

    Per the W3 brief: unifi-mcp is Tier-B and uses a 2-tier mapping.
    STANDARD is intentionally absent (3-tier adds no value for a
    2-group repo with no health tools).
    """
    from mcp_common.tools import ToolProfile

    from unifi_mcp.tools.profiles import PROFILE_REGISTRATIONS

    assert set(PROFILE_REGISTRATIONS.keys()) == {
        ToolProfile.MINIMAL,
        ToolProfile.FULL,
    }, (
        f"PROFILE_REGISTRATIONS must have exactly MINIMAL + FULL; "
        f"got {sorted(PROFILE_REGISTRATIONS.keys())}"
    )


def test_mandatory_tools_invariant() -> None:
    """MANDATORY_TOOLS ⊆ REGISTRATION_MAP.keys() must hold.

    No tools are mandatory at any profile level for unifi-mcp — every
    tool group (including any future health-related tools) is opt-in
    per profile. The /healthz HTTP route lives outside the W0 dispatch
    (registered via ``mcp_common.health.register_http_health_route``)
    so it is always available regardless of profile.

    This test pins the explicit opt-out so the relationship cannot drift
    silently:
    - MANDATORY_TOOLS from mcp-common is empty by default
    - apply_unifi_tool_profile passes mandatory_groups=set()
    - apply_unifi_tool_profile passes essential_tool_names=set()

    If any of these change, this test must be updated to reflect the
    new invariant.
    """
    import inspect

    from mcp_common.tools.profiles import MANDATORY_TOOLS

    from unifi_mcp.tools.profiles import (
        _build_registration_map,
        apply_unifi_tool_profile,
    )

    mapping = _build_registration_map(object(), object())
    # Vacuous: MANDATORY_TOOLS empty, so any subset holds
    assert MANDATORY_TOOLS.issubset(set(mapping.keys())), (
        f"MANDATORY_TOOLS {sorted(MANDATORY_TOOLS)} not in REGISTRATION_MAP "
        f"keys {sorted(mapping.keys())}"
    )

    # Verify the explicit opt-out is documented in the implementation
    source = inspect.getsource(apply_unifi_tool_profile)
    assert "mandatory_groups=set()" in source, (
        "apply_unifi_tool_profile must pass mandatory_groups=set() to "
        "explicitly opt out of the MANDATORY_GROUPS invariant"
    )
    assert "essential_tool_names=set()" in source, (
        "apply_unifi_tool_profile must pass essential_tool_names=set() to "
        "explicitly opt out of the MANDATORY_TOOLS subset check"
    )


@pytest.mark.asyncio
async def test_full_registers_all_13_unifi_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FULL profile must register all 13 UniFi tools + discover_tools = 14 total.

    Behavioral parity: original inline registration registered 8 network
    tools + 5 access tools = 13 tools when both controllers are
    configured. The W0 helper additionally registers ``discover_tools``
    (the meta-tool the W2b.3 spec requires).
    """
    from unittest.mock import MagicMock

    from fastmcp import FastMCP

    from unifi_mcp.tools.profiles import apply_unifi_tool_profile

    monkeypatch.setenv("UNIFI_TOOL_PROFILE", "full")
    server = FastMCP(name="Test", instructions="test")
    # MagicMock with __aenter__/__aexit__ not strictly needed since the
    # register functions only capture the client reference; they don't
    # hit the network.
    network_client = MagicMock()
    access_client = MagicMock()
    await apply_unifi_tool_profile(
        server,
        network_client=network_client,
        access_client=access_client,
    )
    names = {t.name for t in await server.list_tools()}

    expected_network = {
        "unifi_get_sites",
        "unifi_get_devices",
        "unifi_get_clients",
        "unifi_get_wlans",
        "unifi_restart_device",
        "unifi_disable_ap",
        "unifi_enable_ap",
        "unifi_get_statistics",
    }
    expected_access = {
        "unifi_get_access_points",
        "unifi_get_access_users",
        "unifi_get_access_logs",
        "unifi_unlock_door",
        "unifi_set_access_schedule",
    }
    expected_all = expected_network | expected_access
    assert expected_all.issubset(names), (
        f"FULL profile missing tools: {sorted(expected_all - names)}"
    )
    assert "discover_tools" in names, (
        "W0 helper must register discover_tools meta-tool"
    )
    assert len(names) == len(expected_all) + 1, (
        f"Expected {len(expected_all) + 1} ({len(expected_all)} UniFi + "
        f"discover_tools); got {len(names)}: {sorted(names)}"
    )


@pytest.mark.asyncio
async def test_full_default_when_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No UNIFI_TOOL_PROFILE env var must default to FULL (matches pre-refactor)."""
    from unittest.mock import MagicMock

    from fastmcp import FastMCP

    from unifi_mcp.tools.profiles import apply_unifi_tool_profile

    monkeypatch.delenv("UNIFI_TOOL_PROFILE", raising=False)
    server = FastMCP(name="Test", instructions="test")
    await apply_unifi_tool_profile(
        server,
        network_client=MagicMock(),
        access_client=MagicMock(),
    )
    names = {t.name for t in await server.list_tools()}

    assert "unifi_get_sites" in names, "FULL default missing unifi_get_sites"
    assert "unifi_unlock_door" in names, "FULL default missing unifi_unlock_door"
    assert "discover_tools" in names


@pytest.mark.asyncio
async def test_minimal_has_only_discover_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MINIMAL profile registers only ``discover_tools`` (no UniFi domain tools)."""
    from unittest.mock import MagicMock

    from fastmcp import FastMCP

    from unifi_mcp.tools.profiles import apply_unifi_tool_profile

    monkeypatch.setenv("UNIFI_TOOL_PROFILE", "minimal")
    server = FastMCP(name="Test", instructions="test")
    await apply_unifi_tool_profile(
        server,
        network_client=MagicMock(),
        access_client=MagicMock(),
    )
    names = {t.name for t in await server.list_tools()}

    assert names == {"discover_tools"}, (
        f"MINIMAL must only register discover_tools; got: {sorted(names)}"
    )


@pytest.mark.asyncio
async def test_invalid_profile_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """An invalid profile value must raise InvalidProfileError (fail-loud)."""
    from unittest.mock import MagicMock

    from fastmcp import FastMCP
    from mcp_common.tools.dispatch import InvalidProfileError

    from unifi_mcp.tools.profiles import apply_unifi_tool_profile

    monkeypatch.setenv("UNIFI_TOOL_PROFILE", "bogus")
    server = FastMCP(name="Test", instructions="test")
    with pytest.raises(InvalidProfileError):
        await apply_unifi_tool_profile(
            server,
            network_client=MagicMock(),
            access_client=MagicMock(),
        )


@pytest.mark.asyncio
async def test_no_clients_only_discover_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FULL profile with no clients configured must register only discover_tools.

    Pre-refactor behavior: when neither controller is configured, no
    controller tools were registered. Post-refactor preserves this:
    the registration_map is empty, so the W0 helper registers only the
    discover_tools meta-tool.
    """
    from fastmcp import FastMCP

    from unifi_mcp.tools.profiles import apply_unifi_tool_profile

    monkeypatch.setenv("UNIFI_TOOL_PROFILE", "full")
    server = FastMCP(name="Test", instructions="test")
    await apply_unifi_tool_profile(
        server,
        network_client=None,
        access_client=None,
    )
    names = {t.name for t in await server.list_tools()}

    assert names == {"discover_tools"}, (
        f"FULL with no clients must only register discover_tools; "
        f"got: {sorted(names)}"
    )


@pytest.mark.asyncio
async def test_create_app_full_profile_real_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Production-path test: exercise the real ``create_app`` async startup.

    This test does NOT mock the dispatch helper (per W2b.3 lesson: mock-based
    tests can mask bugs where the wrong sync wrapper is used). It awaits
    ``create_app()`` directly in the test's event loop and verifies the
    actual tool set.

    If the production path ever uses the sync ``apply_tool_profile()`` wrapper
    (which raises RuntimeError in event loops), this test will fail because
    ``create_app`` is now ``async def`` and the sync wrapper raises before
    the registration can complete.
    """
    monkeypatch.setenv("UNIFI_TOOL_PROFILE", "full")
    from fastmcp import FastMCP

    from unifi_mcp.config import AccessSettings, NetworkSettings, Settings
    from unifi_mcp.server import create_app

    settings = Settings(
        network_controller=NetworkSettings(
            host="unifi.example.com",
            username="admin",
            password="password12345678",
        ),
        access_controller=AccessSettings(
            host="access.example.com",
            username="admin",
            password="password12345678",
        ),
    )
    app: FastMCP = await create_app(settings)
    names = {t.name for t in await app.list_tools()}

    # All 13 UniFi tools + discover_tools = 14
    assert "unifi_get_sites" in names
    assert "unifi_get_statistics" in names
    assert "unifi_unlock_door" in names
    assert "unifi_set_access_schedule" in names
    assert "discover_tools" in names
    assert len(names) == 14, (
        f"Real production path expected 14 tools; "
        f"got {len(names)}: {sorted(names)}"
    )


@pytest.mark.asyncio
async def test_create_app_minimal_profile_real_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Production-path test: MINIMAL profile via the real ``create_app`` async startup."""
    monkeypatch.setenv("UNIFI_TOOL_PROFILE", "minimal")
    from fastmcp import FastMCP

    from unifi_mcp.config import AccessSettings, NetworkSettings, Settings
    from unifi_mcp.server import create_app

    settings = Settings(
        network_controller=NetworkSettings(
            host="unifi.example.com",
            username="admin",
            password="password12345678",
        ),
        access_controller=AccessSettings(
            host="access.example.com",
            username="admin",
            password="password12345678",
        ),
    )
    app: FastMCP = await create_app(settings)
    names = {t.name for t in await app.list_tools()}

    # Only discover_tools under MINIMAL
    assert names == {"discover_tools"}, (
        f"Real production MINIMAL must only register discover_tools; "
        f"got: {sorted(names)}"
    )
