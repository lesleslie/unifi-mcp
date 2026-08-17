"""UniFi MCP Server package."""

from importlib.metadata import version as _importlib_version

__version__ = _importlib_version("unifi-mcp")

from unifi_mcp.clients.access_client import AccessClient
from unifi_mcp.clients.network_client import NetworkClient
from unifi_mcp.config import Settings
from unifi_mcp.server import create_server, run_server

__all__ = ["create_server", "run_server", "Settings", "NetworkClient", "AccessClient"]
