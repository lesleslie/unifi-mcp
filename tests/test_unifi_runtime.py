"""Runtime integration test for UniFi MCP Server.

This test verifies the Oneiric runtime integration is working correctly.
Tests import paths, configuration loading, and basic lifecycle operations.
"""

import pytest


# Test 1: Verify Oneiric modules can be imported
def test_oneiric_imports() -> None:
    """Test that Oneiric runtime modules are accessible."""
    # Core CLI imports
    from oneiric.core.cli import MCPServerCLIFactory
    from oneiric.core.config import OneiricMCPConfig
    from oneiric.runtime.cache import RuntimeCacheManager
    from oneiric.runtime.mcp_health import (
        HealthCheckResponse,
        HealthMonitor,
        HealthStatus,
    )

    # Runtime imports
    from oneiric.runtime.snapshot import RuntimeSnapshotManager

    # Verify classes exist
    assert MCPServerCLIFactory is not None
    assert OneiricMCPConfig is not None
    assert RuntimeSnapshotManager is not None
    assert RuntimeCacheManager is not None
    assert HealthMonitor is not None
    assert HealthStatus is not None
    assert HealthCheckResponse is not None


# Test 2: Verify UniFiConfig configuration class
def test_unifi_config() -> None:
    """Test that UniFiConfig can be instantiated."""
    from unifi_mcp.__main__ import UniFiConfig

    # Create configuration with defaults
    config = UniFiConfig()

    # Verify default values
    assert config.http_port == 3038
    assert config.http_host == "127.0.0.1"
    assert config.enable_http_transport
    assert config.cache_dir is None or config.cache_dir == ".oneiric_cache"


# Test 3: Verify UniFiMCPServer can be created
def test_unifi_server_creation() -> None:
    """Test that UniFiMCPServer can be instantiated."""
    from unifi_mcp.__main__ import UniFiConfig, UniFiMCPServer

    # Create configuration
    config = UniFiConfig()

    # Create server instance
    server = UniFiMCPServer(config)

    # Verify runtime components are initialized
    assert server.config is not None
    assert server.snapshot_manager is not None
    assert server.cache_manager is not None
    assert server.health_monitor is not None
    assert server.server is not None
    assert server.settings is not None


# Test 4: Verify health check can be executed
@pytest.mark.asyncio
async def test_unifi_health_check() -> None:
    """Test that health check method works."""
    from unifi_mcp.__main__ import UniFiConfig, UniFiMCPServer

    # Create server
    config = UniFiConfig()
    server = UniFiMCPServer(config)

    # Execute health check
    health_response = await server.health_check()

    # Verify response structure
    assert health_response is not None
    assert hasattr(health_response, "status")
    assert hasattr(health_response, "components")
    assert len(health_response.components) > 0


# Test 5: Verify cache directory can be configured
def test_cache_directory_configuration() -> None:
    """Test that custom cache directory can be set."""
    from unifi_mcp.__main__ import UniFiConfig

    # Create config with custom cache dir
    config = UniFiConfig(cache_dir="/tmp/test_cache")

    # Verify cache directory is set
    assert config.cache_dir == "/tmp/test_cache"


# Test 6: Verify CLI factory can be created
def test_cli_factory_creation() -> None:
    """Test that MCPServerCLIFactory can be created for UniFi."""
    from oneiric.core.cli import MCPServerCLIFactory

    from unifi_mcp.__main__ import UniFiConfig, UniFiMCPServer

    # Create CLI factory
    cli_factory = MCPServerCLIFactory(
        server_class=UniFiMCPServer,
        config_class=UniFiConfig,
        name="unifi-mcp",
        use_subcommands=True,
        legacy_flags=False,
        description="UniFi MCP Server - UniFi Controller management",
    )

    # Verify factory configuration
    assert cli_factory.server_class == UniFiMCPServer
    assert cli_factory.config_class == UniFiConfig
    assert cli_factory.name == "unifi-mcp"
    assert cli_factory.use_subcommands is True
    assert cli_factory.legacy_flags is False


# Test 7: Verify environment prefix configuration
def test_environment_prefix() -> None:
    """Test that environment variable prefix is correctly configured."""
    from unifi_mcp.__main__ import UniFiConfig

    # Check model_config (Pydantic v2)
    assert "env_prefix" in UniFiConfig.model_config
    assert UniFiConfig.model_config["env_prefix"] == "UNIFI_MCP_"


# Test 8: Verify settings conversion
def test_settings_conversion() -> None:
    """Test that Oneiric config can be converted to UniFi Settings."""
    from unifi_mcp.__main__ import UniFiConfig, UniFiMCPServer

    # Create configuration
    config = UniFiConfig(http_host="192.168.1.1", http_port=9999)

    # Create server (which converts config)
    server = UniFiMCPServer(config)

    # Verify settings were converted correctly
    assert server.settings.server.host == "192.168.1.1"
    assert server.settings.server.port == 9999


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
