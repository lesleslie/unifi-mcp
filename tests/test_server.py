"""Tests for the server module."""

from unittest.mock import Mock, patch

import pytest

from unifi_mcp.clients.access_client import AccessClient
from unifi_mcp.clients.network_client import NetworkClient
from unifi_mcp.config import AccessSettings, NetworkSettings, Settings
from unifi_mcp.server import (
    _build_feature_list,
    _configure_logging,
    _create_access_client,
    _create_dict_tool,
    _create_list_tool,
    _create_network_client,
    _create_server_with_error_handling,
    _display_startup_message,
    _load_and_validate_settings,
    _register_access_tools,
    _register_network_tools,
    _run_server_instance,
    create_server,
)


class TestCreateServer:
    """Test create_server function."""

    def test_create_server_basic(self):
        """Test creating a server with default settings."""
        settings = Settings()
        server = create_server(settings)

        # Verify server is created
        assert server is not None
        assert hasattr(server, "add_middleware") or hasattr(server, "http_app")

    def test_create_server_with_network_controller(self):
        """Test creating a server with network controller configured."""
        network_controller = NetworkSettings(
            host="unifi.example.com",
            username="admin",
            password="password12345678",  # Long enough to pass validation
        )
        settings = Settings(network_controller=network_controller)

        server = create_server(settings)
        assert server is not None

    def test_create_server_with_access_controller(self):
        """Test creating a server with access controller configured."""
        access_controller = AccessSettings(
            host="access.example.com",
            username="admin",
            password="password12345678",  # Long enough to pass validation
        )
        settings = Settings(access_controller=access_controller)

        server = create_server(settings)
        assert server is not None

    def test_create_server_with_rate_limiting(self):
        """Test creating a server with rate limiting middleware."""
        settings = Settings()

        # Mock the rate limiting availability
        with patch("unifi_mcp.server.RATE_LIMITING_AVAILABLE", True):
            server = create_server(settings)
            assert server is not None


class TestCreateNetworkClient:
    """Test _create_network_client function."""

    def test_create_network_client_with_settings(self):
        """Test creating a network client with settings."""
        network_controller = NetworkSettings(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )
        settings = Settings(network_controller=network_controller)

        client = _create_network_client(settings)
        assert isinstance(client, NetworkClient)
        assert client.host == "unifi.example.com"
        assert client.port == 8443
        assert client.username == "admin"

    def test_create_network_client_no_settings(self):
        """Test creating a network client when no settings are provided."""
        settings = Settings()

        client = _create_network_client(settings)
        assert client is None


class TestCreateAccessClient:
    """Test _create_access_client function."""

    def test_create_access_client_with_settings(self):
        """Test creating an access client with settings."""
        access_controller = AccessSettings(
            host="access.example.com",
            port=8444,
            username="admin",
            password="password123",
        )
        settings = Settings(access_controller=access_controller)

        client = _create_access_client(settings)
        assert isinstance(client, AccessClient)
        assert client.host == "access.example.com"
        assert client.port == 8444
        assert client.username == "admin"

    def test_create_access_client_no_settings(self):
        """Test creating an access client when no settings are provided."""
        settings = Settings()

        client = _create_access_client(settings)
        assert client is None


class TestRegisterNetworkTools:
    """Test network tools registration."""

    def test_register_network_tools(self):
        """Test registering network tools."""
        from fastmcp import FastMCP

        server = FastMCP(name="Test Server")

        # Create a mock network client
        network_client = Mock(spec=NetworkClient)

        # This should not raise an exception
        _register_network_tools(server, network_client)


class TestRegisterAccessTools:
    """Test access tools registration."""

    def test_register_access_tools(self):
        """Test registering access tools."""
        from fastmcp import FastMCP

        server = FastMCP(name="Test Server")

        # Create a mock access client
        access_client = Mock(spec=AccessClient)

        # This should not raise an exception
        _register_access_tools(server, access_client)


class TestCreateListTool:
    """Test _create_list_tool function."""

    async def test_create_list_tool(self):
        """Test creating a list tool."""
        access_client = Mock(spec=AccessClient)

        # Create a mock async function that returns a list
        async def mock_fetch_func(client, **kwargs):
            return [{"id": 1, "name": "test"}]

        tool_func = _create_list_tool(access_client, mock_fetch_func)

        # Call the tool function
        result = await tool_func()
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == 1

    async def test_create_list_tool_returns_non_list(self):
        """Test creating a list tool when the function returns non-list."""
        access_client = Mock(spec=AccessClient)

        # Create a mock async function that returns a non-list
        async def mock_fetch_func(client, **kwargs):
            return "not a list"

        tool_func = _create_list_tool(access_client, mock_fetch_func)

        # Call the tool function - should return empty list
        result = await tool_func()
        assert isinstance(result, list)
        assert len(result) == 0


class TestCreateDictTool:
    """Test _create_dict_tool function."""

    async def test_create_dict_tool(self):
        """Test creating a dict tool."""
        access_client = Mock(spec=AccessClient)

        # Create a mock async function that returns a dict
        async def mock_fetch_func(client, **kwargs):
            return {"status": "success", "data": "test"}

        tool_func = _create_dict_tool(access_client, mock_fetch_func)

        # Call the tool function
        result = await tool_func()
        assert isinstance(result, dict)
        assert result["status"] == "success"

    async def test_create_dict_tool_returns_non_dict(self):
        """Test creating a dict tool when the function returns non-dict."""
        access_client = Mock(spec=AccessClient)

        # Create a mock async function that returns a non-dict
        async def mock_fetch_func(client, **kwargs):
            return ["not", "a", "dict"]

        tool_func = _create_dict_tool(access_client, mock_fetch_func)

        # Call the tool function - should return empty dict
        result = await tool_func()
        assert isinstance(result, dict)
        assert len(result) == 0


class TestLoadAndValidateSettings:
    """Test _load_and_validate_settings function."""

    def test_load_and_validate_settings_success(self):
        """Test loading and validating settings successfully."""
        # Mock the Settings class
        with patch("unifi_mcp.server.Settings") as mock_settings_class:
            mock_settings_instance = Mock()
            mock_settings_instance.validate_credentials_at_startup = Mock()
            mock_settings_class.return_value = mock_settings_instance

            settings = _load_and_validate_settings()

            # Verify the settings were loaded and validated
            mock_settings_class.assert_called_once()
            mock_settings_instance.validate_credentials_at_startup.assert_called_once()
            assert settings == mock_settings_instance

    def test_load_and_validate_settings_with_exception(self):
        """Test loading settings when an exception occurs."""
        # Mock the Settings class to raise an exception
        with patch("unifi_mcp.server.Settings") as mock_settings_class:
            mock_settings_class.side_effect = Exception("Test error")

            # This should raise the exception
            with pytest.raises(Exception, match="Test error"):
                _load_and_validate_settings()


class TestConfigureLogging:
    """Test _configure_logging function."""

    def test_configure_logging_debug(self):
        """Test configuring logging with debug enabled."""
        settings = Settings()
        settings.server.debug = True

        # Mock the logging.basicConfig function
        with patch("unifi_mcp.server.logging.basicConfig") as mock_basic_config:
            _configure_logging(settings)

            # Verify logging was configured with the correct level
            mock_basic_config.assert_called_once()
            call_kwargs = mock_basic_config.call_args[1]
            assert call_kwargs["level"] == 20  # INFO level

    def test_configure_logging_no_debug(self):
        """Test configuring logging with debug disabled."""
        settings = Settings()
        settings.server.debug = False

        # Mock the logging.basicConfig function
        with patch("unifi_mcp.server.logging.basicConfig") as mock_basic_config:
            _configure_logging(settings)

            # Verify logging was configured with the correct level
            mock_basic_config.assert_called_once()
            call_kwargs = mock_basic_config.call_args[1]
            assert call_kwargs["level"] == 30  # WARNING level


class TestBuildFeatureList:
    """Test _build_feature_list function."""

    def test_build_feature_list_no_controllers(self):
        """Test building feature list with no controllers."""
        settings = Settings()

        features = _build_feature_list(settings)

        # Should have basic features but no controller-specific ones
        assert len(features) >= 3  # Basic features should be present
        assert any("Connection Pooling" in feature for feature in features)
        assert any("Credential Validation" in feature for feature in features)

    def test_build_feature_list_with_network_controller(self):
        """Test building feature list with network controller."""
        network_controller = NetworkSettings(
            host="unifi.example.com",
            username="admin",
            password="password12345678",
        )
        settings = Settings(network_controller=network_controller)

        features = _build_feature_list(settings)

        # Should have network controller features
        assert any("Network Controller Integration" in feature for feature in features)
        assert any("Site Management & Statistics" in feature for feature in features)

    def test_build_feature_list_with_access_controller(self):
        """Test building feature list with access controller."""
        access_controller = AccessSettings(
            host="access.example.com",
            username="admin",
            password="password12345678",
        )
        settings = Settings(access_controller=access_controller)

        features = _build_feature_list(settings)

        # Should have access controller features
        assert any("Access Controller Integration" in feature for feature in features)
        assert any("Door Access Control & Unlock" in feature for feature in features)

    def test_build_feature_list_with_rate_limiting(self):
        """Test building feature list with rate limiting."""
        settings = Settings()

        # Mock rate limiting availability
        with patch("unifi_mcp.server.RATE_LIMITING_AVAILABLE", True):
            features = _build_feature_list(settings)

            # Should include rate limiting feature
            assert any("Rate Limiting" in feature for feature in features)


class TestDisplayStartupMessage:
    """Test _display_startup_message function."""

    def test_display_startup_message_with_server_panels(self):
        """Test displaying startup message with ServerPanels available."""
        settings = Settings()
        features = ["Feature 1", "Feature 2"]

        # Mock ServerPanels availability and import
        with patch("unifi_mcp.server.SERVERPANELS_AVAILABLE", True):
            with patch("mcp_common.ui.ServerPanels") as mock_server_panels_class:
                _display_startup_message(settings, features)

                # Verify ServerPanels.startup_success was called
                mock_server_panels_class.startup_success.assert_called_once()

    def test_display_startup_message_without_server_panels(self):
        """Test displaying startup message without ServerPanels."""
        settings = Settings()
        features = ["Feature 1", "Feature 2"]

        # Mock ServerPanels not available
        with patch("unifi_mcp.server.SERVERPANELS_AVAILABLE", False):
            # Capture stderr output
            with patch("sys.stderr") as mock_stderr:
                _display_startup_message(settings, features)

                # Should write to stderr
                assert mock_stderr.write.called


class TestRunServerInstance:
    """Test _run_server_instance function."""

    def test_run_server_instance(self):
        """Test running server instance."""
        # Create a mock server
        mock_server = Mock()
        settings = Settings()

        _run_server_instance(mock_server, settings)

        # Verify the server's run method was called with correct parameters
        mock_server.run.assert_called_once_with(
            host=settings.server.host,
            port=settings.server.port,
            reload=settings.server.reload,
        )


class TestCreateServerWithErrorHandling:
    """Test _create_server_with_error_handling function."""

    def test_create_server_with_error_handling(self):
        """Test creating server with error handling."""
        settings = Settings()

        # Mock the create_server function
        with patch("unifi_mcp.server.create_server") as mock_create_server:
            mock_server = Mock()
            mock_create_server.return_value = mock_server

            server = _create_server_with_error_handling(settings)

            # Verify the server was created
            mock_create_server.assert_called_once_with(settings)
            assert server == mock_server


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
