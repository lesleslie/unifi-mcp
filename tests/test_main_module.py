"""Tests for the __main__ module."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from unifi_mcp.__main__ import UniFiConfig, UniFiMCPServer
from unifi_mcp.config import Settings


class TestUniFiConfig:
    """Test UniFiConfig class."""

    def test_unifi_config_defaults(self):
        """Test UniFiConfig with default values."""
        config = UniFiConfig()

        assert config.http_port == 3038
        assert config.http_host == "127.0.0.1"
        assert config.enable_http_transport is True

    def test_unifi_config_with_custom_values(self):
        """Test UniFiConfig with custom values."""
        config = UniFiConfig(
            http_port=9999, http_host="0.0.0.0", enable_http_transport=False
        )

        assert config.http_port == 9999
        assert config.http_host == "0.0.0.0"
        assert config.enable_http_transport is False


class TestUniFiMCPServer:
    """Test UniFiMCPServer class."""

    def test_init(self):
        """Test initializing the server."""
        config = UniFiConfig()

        # Mock the create_server function
        with patch("unifi_mcp.__main__.create_server") as mock_create_server:
            mock_server = Mock()
            mock_create_server.return_value = mock_server

            # Mock the runtime components
            with patch(
                "unifi_mcp.__main__.create_runtime_components"
            ) as mock_create_runtime:
                mock_runtime = Mock()
                mock_create_runtime.return_value = mock_runtime

                server = UniFiMCPServer(config)

                # Verify initialization
                assert server.config == config
                mock_create_server.assert_called_once_with(server.settings)
                mock_create_runtime.assert_called_once_with(
                    server_name="unifi-mcp", cache_dir=".oneiric_cache"
                )
                assert server.server == mock_server
                assert server.runtime == mock_runtime

    def test_convert_to_unifi_settings(self):
        """Test converting Oneiric config to UniFi settings."""
        config = UniFiConfig(http_host="0.0.0.0", http_port=9999, debug=True)

        server = UniFiMCPServer(config)

        # Get the converted settings
        settings = server._convert_to_unifi_settings(config)

        # Verify the settings were converted correctly
        assert isinstance(settings, Settings)
        assert settings.server.host == "0.0.0.0"
        assert settings.server.port == 9999
        assert settings.server.debug is True

    def test_properties(self):
        """Test the convenience properties."""
        config = UniFiConfig()

        # Mock the create_server function
        with patch("unifi_mcp.__main__.create_server") as mock_create_server:
            mock_server = Mock()
            mock_create_server.return_value = mock_server

            # Mock the runtime components
            with patch(
                "unifi_mcp.__main__.create_runtime_components"
            ) as mock_create_runtime:
                mock_runtime = Mock()
                mock_health_monitor = Mock()
                mock_cache_manager = Mock()
                mock_snapshot_manager = Mock()

                mock_runtime.health_monitor = mock_health_monitor
                mock_runtime.cache_manager = mock_cache_manager
                mock_runtime.snapshot_manager = mock_snapshot_manager

                mock_create_runtime.return_value = mock_runtime

                server = UniFiMCPServer(config)

                # Test the properties
                assert server.health_monitor == mock_health_monitor
                assert server.cache_manager == mock_cache_manager
                assert server.snapshot_manager == mock_snapshot_manager

    def test_get_timestamp(self):
        """Test getting timestamp."""
        config = UniFiConfig()

        # Mock the create_server function
        with patch("unifi_mcp.__main__.create_server") as mock_create_server:
            mock_server = Mock()
            mock_create_server.return_value = mock_server

            # Mock the runtime components
            with patch(
                "unifi_mcp.__main__.create_runtime_components"
            ) as mock_create_runtime:
                mock_runtime = Mock()
                mock_create_runtime.return_value = mock_runtime

                server = UniFiMCPServer(config)

                # Test the timestamp method
                timestamp = server._get_timestamp()

                # Verify it returns a properly formatted timestamp
                assert isinstance(timestamp, str)
                assert len(timestamp) == 20  # Format: YYYY-MM-DDTHH:MM:SSZ
                assert timestamp.endswith("Z")

    async def test_startup(self):
        """Test the startup method."""
        config = UniFiConfig()

        # Mock the create_server function
        with patch("unifi_mcp.__main__.create_server") as mock_create_server:
            mock_server = Mock()
            mock_create_server.return_value = mock_server

            # Mock the runtime components
            with patch(
                "unifi_mcp.__main__.create_runtime_components"
            ) as mock_create_runtime:
                mock_runtime = Mock()
                mock_runtime.initialize = AsyncMock()
                mock_create_runtime.return_value = mock_runtime

                # Mock the settings
                mock_settings = Mock()
                mock_settings.validate_credentials_at_startup = Mock()

                server = UniFiMCPServer(config)
                # Replace the settings with our mock
                server.settings = mock_settings

                # Mock the _create_startup_snapshot method
                server._create_startup_snapshot = AsyncMock()

                # Capture print output
                with patch("builtins.print") as mock_print:
                    await server.startup()

                    # Verify the startup process
                    mock_settings.validate_credentials_at_startup.assert_called_once()
                    mock_runtime.initialize.assert_called_once()
                    server._create_startup_snapshot.assert_called_once()
                    assert mock_print.called

    async def test_shutdown(self):
        """Test the shutdown method."""
        config = UniFiConfig()

        # Mock the create_server function
        with patch("unifi_mcp.__main__.create_server") as mock_create_server:
            mock_server = Mock()
            mock_create_server.return_value = mock_server

            # Mock the runtime components
            with patch(
                "unifi_mcp.__main__.create_runtime_components"
            ) as mock_create_runtime:
                mock_runtime = Mock()
                mock_runtime.cleanup = AsyncMock()
                mock_create_runtime.return_value = mock_runtime

                server = UniFiMCPServer(config)

                # Mock the _create_shutdown_snapshot method
                server._create_shutdown_snapshot = AsyncMock()

                # Capture print output
                with patch("builtins.print") as mock_print:
                    await server.shutdown()

                    # Verify the shutdown process
                    server._create_shutdown_snapshot.assert_called_once()
                    mock_runtime.cleanup.assert_called_once()
                    mock_print.assert_called_once_with(
                        "👋 UniFi MCP Server shutdown complete"
                    )

    async def test_health_check(self):
        """Test the health check method."""
        config = UniFiConfig()

        # Mock the create_server function
        with patch("unifi_mcp.__main__.create_server") as mock_create_server:
            mock_server = Mock()
            mock_create_server.return_value = mock_server

            # Mock the runtime components
            with patch(
                "unifi_mcp.__main__.create_runtime_components"
            ) as mock_create_runtime:
                mock_runtime = Mock()
                mock_health_monitor = Mock()
                mock_component_health = Mock()
                mock_health_response = Mock()

                mock_health_monitor.create_component_health.return_value = (
                    mock_component_health
                )
                mock_health_monitor.create_health_response.return_value = (
                    mock_health_response
                )
                mock_runtime.health_monitor = mock_health_monitor
                mock_create_runtime.return_value = mock_runtime

                server = UniFiMCPServer(config)

                # Mock the settings to have no controllers configured
                mock_settings = Mock()
                mock_settings.network_controller = None
                mock_settings.access_controller = None
                mock_settings.local_api = None
                server.settings = mock_settings

                # Mock the _build_health_components method
                server._build_health_components = AsyncMock(return_value=[])

                result = await server.health_check()

                # Verify the health check process
                server._build_health_components.assert_called_once()
                mock_health_monitor.create_component_health.assert_called_once()
                mock_health_monitor.create_health_response.assert_called_once()
                assert result == mock_health_response

    def test_get_app(self):
        """Test getting the ASGI application."""
        config = UniFiConfig()

        # Mock the create_server function
        with patch("unifi_mcp.__main__.create_server") as mock_create_server:
            mock_server = Mock()
            mock_server.http_app = Mock()
            mock_create_server.return_value = mock_server

            # Mock the runtime components
            with patch(
                "unifi_mcp.__main__.create_runtime_components"
            ) as mock_create_runtime:
                mock_runtime = Mock()
                mock_create_runtime.return_value = mock_runtime

                server = UniFiMCPServer(config)

                app = server.get_app()

                # Verify the app is returned correctly
                assert app == mock_server.http_app


def test_main():
    """Test the main function."""
    # Mock the CLI factory and its methods
    with patch("unifi_mcp.__main__.MCPServerCLIFactory") as mock_cli_factory_class:
        mock_cli_factory_instance = Mock()
        mock_app = Mock()

        mock_cli_factory_class.create_server_cli.return_value = (
            mock_cli_factory_instance
        )
        mock_cli_factory_instance.create_app.return_value = mock_app

        # Import and call main function
        from unifi_mcp.__main__ import main

        main()

        # Verify the CLI factory was created and run
        mock_cli_factory_class.create_server_cli.assert_called_once()
        mock_cli_factory_instance.create_app.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
