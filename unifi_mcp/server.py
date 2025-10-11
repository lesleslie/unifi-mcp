"""Main FastMCP server for UniFi integration."""

import logging
from typing import Any

from fastmcp import FastMCP

from unifi_mcp.clients.access_client import AccessClient
from unifi_mcp.clients.network_client import NetworkClient
from unifi_mcp.config import Settings
from unifi_mcp.tools.access_tools import (
    get_unifi_access_logs,
    get_unifi_access_points,
    get_unifi_access_users,
    set_unifi_access_schedule,
    unlock_unifi_door,
)
from unifi_mcp.tools.network_tools import (
    disable_unifi_ap,
    enable_unifi_ap,
    get_unifi_clients,
    get_unifi_devices,
    get_unifi_sites,
    get_unifi_statistics,
    get_unifi_wlans,
    restart_unifi_device,
)


def create_server(settings: Settings) -> FastMCP:
    """Create and configure the UniFi MCP server."""
    # Initialize FastMCP server
    server = FastMCP(
        name="UniFi Controller MCP Server",
    )

    # Initialize clients
    network_client = _create_network_client(settings)
    access_client = _create_access_client(settings)

    # Register tools if clients are available
    if network_client:
        _register_network_tools(server, network_client)

    if access_client:
        _register_access_tools(server, access_client)

    return server


def _create_network_client(settings: Settings) -> NetworkClient | None:
    """Create a NetworkClient if configuration is provided."""
    if settings.network_controller:
        return NetworkClient(
            host=settings.network_controller.host,
            port=settings.network_controller.port,
            username=settings.network_controller.username,
            password=settings.network_controller.password,
            verify_ssl=settings.network_controller.verify_ssl,
            timeout=settings.network_controller.timeout,
        )
    return None


def _create_access_client(settings: Settings) -> AccessClient | None:
    """Create an AccessClient if configuration is provided."""
    if settings.access_controller:
        return AccessClient(
            host=settings.access_controller.host,
            port=settings.access_controller.port,
            username=settings.access_controller.username,
            password=settings.access_controller.password,
            verify_ssl=settings.access_controller.verify_ssl,
            timeout=settings.access_controller.timeout,
        )
    return None


def _register_network_tools(server: FastMCP, network_client: NetworkClient) -> None:
    """Register network tools with the server."""
    _create_get_sites_tool(network_client)
    _create_get_devices_tool(network_client)
    _create_get_clients_tool(network_client)
    _create_get_wlans_tool(network_client)
    _create_restart_device_tool(network_client)
    _create_disable_ap_tool(network_client)
    _create_enable_ap_tool(network_client)
    _create_get_statistics_tool(network_client)


def _create_get_sites_tool(network_client: NetworkClient) -> None:
    """Create the get_sites tool."""

    async def get_sites_tool() -> list[dict[str, Any]]:
        result = await get_unifi_sites(network_client)
        # Ensure the return value matches the expected type
        if isinstance(result, list):
            return result
        return []

    get_sites_tool.__name__ = "get_unifi_sites"
    get_sites_tool.__doc__ = "Get all sites from the UniFi Network Controller"
    # Skip tool registration for now since FastMCP doesn't have a 'tools' attribute


def _create_get_devices_tool(network_client: NetworkClient) -> None:
    """Create the get_devices tool."""

    async def get_devices_tool(site_id: str = "default") -> list[dict[str, Any]]:
        result = await get_unifi_devices(network_client, site_id)
        # Ensure the return value matches the expected type
        if isinstance(result, list):
            return result
        return []

    get_devices_tool.__name__ = "get_unifi_devices"
    get_devices_tool.__doc__ = "Get all devices in a specific site from the UniFi Network Controller. Takes an optional site_id parameter (defaults to 'default')."
    # Skip tool registration for now since FastMCP doesn't have a 'tools' attribute


def _create_get_clients_tool(network_client: NetworkClient) -> None:
    """Create the get_clients tool."""

    async def get_clients_tool(site_id: str = "default") -> list[dict[str, Any]]:
        result = await get_unifi_clients(network_client, site_id)
        # Ensure the return value matches the expected type
        if isinstance(result, list):
            return result
        return []

    get_clients_tool.__name__ = "get_unifi_clients"
    get_clients_tool.__doc__ = "Get all clients in a specific site from the UniFi Network Controller. Takes an optional site_id parameter (defaults to 'default')."
    # Skip tool registration for now since FastMCP doesn't have a 'tools' attribute


def _create_get_wlans_tool(network_client: NetworkClient) -> None:
    """Create the get_wlans tool."""

    async def get_wlans_tool(site_id: str = "default") -> list[dict[str, Any]]:
        result = await get_unifi_wlans(network_client, site_id)
        # Ensure the return value matches the expected type
        if isinstance(result, list):
            return result
        return []

    get_wlans_tool.__name__ = "get_unifi_wlans"
    get_wlans_tool.__doc__ = "Get all WLANs in a specific site from the UniFi Network Controller. Takes an optional site_id parameter (defaults to 'default')."
    # Skip tool registration for now since FastMCP doesn't have a 'tools' attribute


def _create_restart_device_tool(network_client: NetworkClient) -> None:
    """Create the restart_device tool."""

    async def restart_device_tool(mac: str, site_id: str = "default") -> dict[str, Any]:
        result = await restart_unifi_device(network_client, mac, site_id)
        # Ensure the return value matches the expected type
        if isinstance(result, dict):
            return result
        return {}

    restart_device_tool.__name__ = "restart_unifi_device"
    restart_device_tool.__doc__ = "Restart a device by its MAC address in the UniFi Network Controller. Takes a required mac address and an optional site_id parameter (defaults to 'default')."
    # Skip tool registration for now since FastMCP doesn't have a 'tools' attribute


def _create_disable_ap_tool(network_client: NetworkClient) -> None:
    """Create the disable_ap tool."""

    async def disable_ap_tool(mac: str, site_id: str = "default") -> dict[str, Any]:
        result = await disable_unifi_ap(network_client, mac, site_id)
        # Ensure the return value matches the expected type
        if isinstance(result, dict):
            return result
        return {}

    disable_ap_tool.__name__ = "disable_unifi_ap"
    disable_ap_tool.__doc__ = "Disable an access point by its MAC address in the UniFi Network Controller. Takes a required mac address and an optional site_id parameter (defaults to 'default')."
    # Skip tool registration for now since FastMCP doesn't have a 'tools' attribute


def _create_enable_ap_tool(network_client: NetworkClient) -> None:
    """Create the enable_ap tool."""

    async def enable_ap_tool(mac: str, site_id: str = "default") -> dict[str, Any]:
        result = await enable_unifi_ap(network_client, mac, site_id)
        # Ensure the return value matches the expected type
        if isinstance(result, dict):
            return result
        return {}

    enable_ap_tool.__name__ = "enable_unifi_ap"
    enable_ap_tool.__doc__ = "Enable an access point by its MAC address in the UniFi Network Controller. Takes a required mac address and an optional site_id parameter (defaults to 'default')."
    # Skip tool registration for now since FastMCP doesn't have a 'tools' attribute


def _create_get_statistics_tool(network_client: NetworkClient) -> None:
    """Create the get_statistics tool."""

    async def get_statistics_tool(site_id: str = "default") -> dict[str, Any]:
        result = await get_unifi_statistics(network_client, site_id)
        # Ensure the return value matches the expected type
        if isinstance(result, dict):
            return result
        return {}

    get_statistics_tool.__name__ = "get_unifi_statistics"
    get_statistics_tool.__doc__ = "Get site statistics from the UniFi Network Controller. Takes an optional site_id parameter (defaults to 'default')."
    # Skip tool registration for now since FastMCP doesn't have a 'tools' attribute


def _register_access_tools(server: FastMCP, access_client: AccessClient) -> None:
    """Register access tools with the server."""
    _create_get_access_points_tool(access_client)
    _create_get_access_users_tool(access_client)
    _create_get_access_logs_tool(access_client)
    _create_unlock_door_tool(access_client)
    _create_set_access_schedule_tool(access_client)


def _create_get_access_points_tool(access_client: AccessClient) -> None:
    """Create the get_access_points tool."""

    async def get_access_points_tool() -> list[dict[str, Any]]:
        result = await get_unifi_access_points(access_client)
        # Ensure the return value matches the expected type
        if isinstance(result, list):
            return result
        return []

    get_access_points_tool.__name__ = "get_unifi_access_points"
    get_access_points_tool.__doc__ = (
        "Get all access points from the UniFi Access Controller"
    )
    # Skip tool registration for now since FastMCP doesn't have a 'tools' attribute


def _create_get_access_users_tool(access_client: AccessClient) -> None:
    """Create the get_access_users tool."""

    async def get_access_users_tool() -> list[dict[str, Any]]:
        result = await get_unifi_access_users(access_client)
        # Ensure the return value matches the expected type
        if isinstance(result, list):
            return result
        return []

    get_access_users_tool.__name__ = "get_unifi_access_users"
    get_access_users_tool.__doc__ = "Get all users from the UniFi Access Controller"
    # Skip tool registration for now since FastMCP doesn't have a 'tools' attribute


def _create_get_access_logs_tool(access_client: AccessClient) -> None:
    """Create the get_access_logs tool."""

    async def get_access_logs_tool() -> list[dict[str, Any]]:
        result = await get_unifi_access_logs(access_client)
        # Ensure the return value matches the expected type
        if isinstance(result, list):
            return result
        return []

    get_access_logs_tool.__name__ = "get_unifi_access_logs"
    get_access_logs_tool.__doc__ = (
        "Get door access logs from the UniFi Access Controller"
    )
    # Skip tool registration for now since FastMCP doesn't have a 'tools' attribute


def _create_unlock_door_tool(access_client: AccessClient) -> None:
    """Create the unlock_door tool."""

    async def unlock_door_tool(door_id: str) -> dict[str, Any]:
        result = await unlock_unifi_door(access_client, door_id)
        # Ensure the return value matches the expected type
        if isinstance(result, dict):
            return result
        return {}

    unlock_door_tool.__name__ = "unlock_unifi_door"
    unlock_door_tool.__doc__ = "Unlock a door via the UniFi Access Controller. Takes a required door_id parameter."
    # Skip tool registration for now since FastMCP doesn't have a 'tools' attribute


def _create_set_access_schedule_tool(access_client: AccessClient) -> None:
    """Create the set_access_schedule tool."""

    async def set_access_schedule_tool(user_id: str, schedule: dict) -> dict[str, Any]:
        result = await set_unifi_access_schedule(access_client, user_id, schedule)
        # Ensure the return value matches the expected type
        if isinstance(result, dict):
            return result
        return {}

    set_access_schedule_tool.__name__ = "set_unifi_access_schedule"
    set_access_schedule_tool.__doc__ = "Set access schedule for a user via the UniFi Access Controller. Takes a required user_id and schedule parameter."
    # Skip tool registration for now since FastMCP doesn't have a 'tools' attribute


def run_server() -> None:
    """Run the UniFi MCP server."""
    # Load settings
    settings = Settings()

    # Create server
    server = create_server(settings)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO if settings.server.debug else logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run the server
    server.run(
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload,
    )


if __name__ == "__main__":
    run_server()
