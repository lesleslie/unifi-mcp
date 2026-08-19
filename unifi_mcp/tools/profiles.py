"""Tool profile registration groups for unifi-mcp MCP server.

Maps ``ToolProfile`` levels to specific ``register_<group>_tools()`` call
lists, controlling which tools are exposed at startup based on the
``UNIFI_TOOL_PROFILE`` environment variable.

Profile tiers (2-tier, Tier-B — unifi-mcp has 2 controller groups with
~13 tools total, so a 3-tier split adds no value):

    MINIMAL:  No controller tool groups registered (only ``discover_tools``
              meta-tool + ``/healthz`` HTTP route).
    FULL:     All 13 UniFi Controller tools across 2 groups
              (``network_tools`` + ``access_tools``).
              Default behavior — matches pre-refactor inline registration.

The dispatch surface (``PROFILE_REGISTRATIONS`` + ``_build_registration_map``
+ ``register_all_tool_groups`` + ``apply_unifi_tool_profile``) is consumed
by ``unifi_mcp.server.create_app`` which delegates to
``mcp_common.tools.dispatch._apply_tool_profile``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mcp_common.tools import ToolProfile
from mcp_common.tools.dispatch import ALL_TOOLS

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from fastmcp import FastMCP

    from unifi_mcp.clients.access_client import AccessClient
    from unifi_mcp.clients.network_client import NetworkClient

# Single source of truth for tool groups (W3.2 lesson: extract _GROUP_REGISTRY
# constant so FULL_REGISTRATIONS and the docstring stay in sync).
_GROUP_REGISTRY: list[tuple[str, str]] = [
    (
        "network_tools",
        "Register the UniFi Network Controller tools "
        "(sites, devices, clients, WLANs, device control, statistics).",
    ),
    (
        "access_tools",
        "Register the UniFi Access Controller tools "
        "(access points, users, logs, door unlock, schedules).",
    ),
]

MINIMAL_REGISTRATIONS: list[str | Callable[[FastMCP], Awaitable[None] | None]] = []

FULL_REGISTRATIONS: list[str | Callable[[FastMCP], Awaitable[None] | None]] = [
    name for name, _ in _GROUP_REGISTRY
]

PROFILE_REGISTRATIONS: dict[
    ToolProfile,
    list[str | Callable[[FastMCP], Awaitable[None] | None]] | type[ALL_TOOLS],
] = {
    ToolProfile.MINIMAL: MINIMAL_REGISTRATIONS,
    ToolProfile.FULL: FULL_REGISTRATIONS,
}


def _build_registration_map(
    network_client: NetworkClient | None,
    access_client: AccessClient | None,
) -> dict[str, Callable[[FastMCP], Awaitable[None] | None]]:
    """Build the {group_key: register_fn(app)} map.

    Local imports keep ``unifi_mcp.tools.profiles`` importable without
    forcing ``unifi_mcp.clients.*`` to resolve at module-import time.

    W3.1 lesson: unifi-mcp's register functions take a 2-arg
    ``(app, client)`` signature; the W0 helper expects single-arg
    callables, so each entry uses a lambda to bind the client instance.
    Default-argument capture (``_nc=network_client``) prevents the classic
    late-binding bug where the loop variable would alias the last
    iteration's value when called.

    Always includes BOTH group keys in the map (even when the
    corresponding client is None) so the W0 dispatch can resolve every
    ``PROFILE_REGISTRATIONS`` reference at FULL profile. Groups whose
    controller is not configured register a no-op so ``UNIFI_TOOL_PROFILE=full``
    with no controllers still works (only ``discover_tools`` ends up
    registered — matching the pre-refactor behavior where no tools were
    registered when neither controller was configured).
    """
    from unifi_mcp.server import _register_access_tools, _register_network_tools

    def _noop(app: FastMCP) -> None:
        """No-op register fn used when a controller is not configured."""

    mapping: dict[str, Callable[[FastMCP], Awaitable[None] | None]] = {}
    if network_client is not None:
        nc = network_client
        mapping["network_tools"] = lambda app, _nc=nc: _register_network_tools(
            app, _nc
        )
    else:
        mapping["network_tools"] = _noop
    if access_client is not None:
        ac = access_client
        mapping["access_tools"] = lambda app, _ac=ac: _register_access_tools(
            app, _ac
        )
    else:
        mapping["access_tools"] = _noop
    return mapping


def register_all_tool_groups(
    server: FastMCP,
    network_client: NetworkClient | None,
    access_client: AccessClient | None,
) -> None:
    """Bulk register every unifi-mcp tool group (called at FULL profile).

    Used as ``register_all_fn`` for the W0 helper. Mirrors the
    conditional registration logic from the pre-refactor ``create_server``
    so behavior is identical when both controllers are configured.
    No-ops when the corresponding controller is not configured.
    """
    from unifi_mcp.server import _register_access_tools, _register_network_tools

    if network_client is not None:
        _register_network_tools(server, network_client)
    if access_client is not None:
        _register_access_tools(server, access_client)


async def apply_unifi_tool_profile(
    server: FastMCP,
    *,
    network_client: NetworkClient | None,
    access_client: AccessClient | None,
) -> None:
    """Apply the UNIFI_TOOL_PROFILE dispatch to ``server`` at startup.

    Async because the W0 helper is async; called from
    ``unifi_mcp.server.create_app`` via ``await apply_unifi_tool_profile(...)``.
    The sync ``apply_tool_profile`` wrapper raises ``RuntimeError`` in any
    async context, so this async path is the only correct entry point.

    No tools are mandatory at any profile level for unifi-mcp — every
    controller tool group is opt-in per profile. The ``/healthz`` HTTP
    route lives outside the W0 dispatch (registered via
    ``mcp_common.health.register_http_health_route``), so it is always
    available regardless of profile. We pass empty sets explicitly to
    opt out of the MANDATORY_GROUPS / MANDATORY_TOOLS subset checks.
    """
    from mcp_common.tools.dispatch import _apply_tool_profile

    nc = network_client
    ac = access_client

    await _apply_tool_profile(
        server,
        profile_env_var="UNIFI_TOOL_PROFILE",
        registrations=PROFILE_REGISTRATIONS,
        registration_map=_build_registration_map(nc, ac),
        register_all_fn=lambda srv: register_all_tool_groups(srv, nc, ac),
        mandatory_groups=set(),
        essential_tool_names=set(),
    )


__all__ = [
    "FULL_REGISTRATIONS",
    "MINIMAL_REGISTRATIONS",
    "PROFILE_REGISTRATIONS",
    "_build_registration_map",
    "apply_unifi_tool_profile",
    "register_all_tool_groups",
]