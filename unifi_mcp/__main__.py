#!/usr/bin/env python3
"""UniFi MCP Server - Oneiric CLI Entry Point."""

from datetime import UTC
from typing import Any

from mcp_common.cli import MCPServerCLIFactory
from mcp_common.server import BaseOneiricServerMixin
from mcp_common.server.runtime import create_runtime_components
from oneiric.core.config import OneiricMCPConfig
from oneiric.runtime.mcp_health import HealthStatus

from unifi_mcp.config import Settings

# Import the main server from the existing codebase
from unifi_mcp.server import create_server


class UniFiConfig(OneiricMCPConfig):
    """UniFi MCP Server Configuration."""

    http_port: int = 3038
    http_host: str = "127.0.0.1"
    enable_http_transport: bool = True

    class Config:
        env_prefix = "UNIFI_MCP_"
        env_file = ".env"


class UniFiMCPServer(BaseOneiricServerMixin):
    """UniFi MCP Server with Oneiric integration."""

    def __init__(self, config: UniFiConfig):
        self.config = config
        # Convert to UniFi Settings for compatibility
        self.settings = self._convert_to_unifi_settings(config)
        self.server = create_server(self.settings)

        # Initialize runtime components using mcp-common helper
        self.runtime = create_runtime_components(
            server_name="unifi-mcp", cache_dir=config.cache_dir or ".oneiric_cache"
        )

    def _convert_to_unifi_settings(self, config: UniFiConfig) -> Settings:
        """Convert Oneiric config to UniFi Settings."""
        # Create a basic Settings object and override with config values
        settings = Settings()

        # Override server settings from config
        settings.server.host = config.http_host
        settings.server.port = config.http_port
        settings.server.debug = config.debug

        return settings

    @property
    def health_monitor(self) -> Any:
        """Convenience property to access runtime health monitor."""
        return self.runtime.health_monitor

    @property
    def cache_manager(self) -> Any:
        """Convenience property to access runtime cache manager."""
        return self.runtime.cache_manager

    @property
    def snapshot_manager(self) -> Any:
        """Convenience property to access runtime snapshot manager."""
        return self.runtime.snapshot_manager

    def _get_timestamp(self) -> str:
        """Get current timestamp for snapshots."""
        from datetime import datetime

        return datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    async def startup(self) -> None:
        """Server startup lifecycle hook."""
        # Validate credentials at startup
        self.settings.validate_credentials_at_startup()

        # Initialize runtime components
        await self.runtime.initialize()

        # Create startup snapshot with custom components
        await self._create_startup_snapshot(
            custom_components={
                "controllers": {
                    "status": "validated",
                    "timestamp": self._get_timestamp(),
                    "network_controller": bool(self.settings.network_controller),
                    "access_controller": bool(self.settings.access_controller),
                    "local_api": bool(self.settings.local_api),
                },
            }
        )

        print("✅ UniFi MCP Server started successfully")
        print(f"   Listening on {self.config.http_host}:{self.config.http_port}")
        print(f"   Cache directory: {self.runtime.cache_dir}")
        print("   Snapshot manager: Initialized")
        print("   Cache manager: Initialized")

    async def shutdown(self) -> None:
        """Server shutdown lifecycle hook."""
        # Create shutdown snapshot
        await self._create_shutdown_snapshot()

        # Clean up runtime components
        await self.runtime.cleanup()

        print("👋 UniFi MCP Server shutdown complete")

    async def health_check(self) -> Any:
        """Perform health check."""
        # Build base health components using mixin helper
        base_components = await self._build_health_components()

        # Check controller configuration
        controllers_configured = (
            bool(self.settings.network_controller)
            or bool(self.settings.access_controller)
            or bool(self.settings.local_api)
        )

        # Add unifi-specific health checks
        base_components.append(
            self.runtime.health_monitor.create_component_health(
                name="controllers",
                status=HealthStatus.HEALTHY
                if controllers_configured
                else HealthStatus.UNHEALTHY,
                details={
                    "configured": controllers_configured,
                    "network": bool(self.settings.network_controller),
                    "access": bool(self.settings.access_controller),
                    "local": bool(self.settings.local_api),
                },
            )
        )

        # Create health response
        return self.runtime.health_monitor.create_health_response(base_components)

    def get_app(self) -> Any:
        """Get the ASGI application."""
        return self.server.http_app


def main() -> None:
    """Main entry point for UniFi MCP Server."""

    # Create CLI factory using mcp-common's enhanced factory
    cli_factory = MCPServerCLIFactory.create_server_cli(
        server_class=UniFiMCPServer,
        config_class=UniFiConfig,
        name="unifi-mcp",
        _description="UniFi MCP Server - UniFi Controller management",
    )

    # Create and run CLI
    cli_factory.create_app()()


if __name__ == "__main__":
    main()
