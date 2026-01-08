"""Tests for the network tools module."""

from unittest.mock import AsyncMock, Mock

import pytest

from unifi_mcp.clients.network_client import NetworkClient
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


class TestNetworkTools:
    """Test network tools functions."""

    async def test_get_unifi_sites(self):
        """Test getting sites."""
        mock_client = Mock(spec=NetworkClient)
        mock_client.get_sites = AsyncMock(
            return_value=[{"name": "default", "desc": "Default Site"}]
        )

        result = await get_unifi_sites(mock_client)

        mock_client.get_sites.assert_called_once()
        assert result == [{"name": "default", "desc": "Default Site"}]

    async def test_get_unifi_devices(self):
        """Test getting devices."""
        mock_client = Mock(spec=NetworkClient)
        mock_client.get_devices = AsyncMock(
            return_value=[{"mac": "aa:bb:cc:dd:ee:ff", "type": "uap"}]
        )

        result = await get_unifi_devices(mock_client, "test_site")

        mock_client.get_devices.assert_called_once_with("test_site")
        assert result == [{"mac": "aa:bb:cc:dd:ee:ff", "type": "uap"}]

    async def test_get_unifi_devices_default_site(self):
        """Test getting devices with default site."""
        mock_client = Mock(spec=NetworkClient)
        mock_client.get_devices = AsyncMock(return_value=[])

        result = await get_unifi_devices(mock_client)

        mock_client.get_devices.assert_called_once_with("default")
        assert result == []

    async def test_get_unifi_clients(self):
        """Test getting clients."""
        mock_client = Mock(spec=NetworkClient)
        mock_client.get_clients = AsyncMock(
            return_value=[{"mac": "aa:bb:cc:dd:ee:ff", "hostname": "test-client"}]
        )

        result = await get_unifi_clients(mock_client, "test_site")

        mock_client.get_clients.assert_called_once_with("test_site")
        assert result == [{"mac": "aa:bb:cc:dd:ee:ff", "hostname": "test-client"}]

    async def test_get_unifi_wlans(self):
        """Test getting WLANs."""
        mock_client = Mock(spec=NetworkClient)
        mock_client.get_wlans = AsyncMock(
            return_value=[{"name": "MyWiFi", "enabled": True}]
        )

        result = await get_unifi_wlans(mock_client, "test_site")

        mock_client.get_wlans.assert_called_once_with("test_site")
        assert result == [{"name": "MyWiFi", "enabled": True}]

    async def test_restart_unifi_device(self):
        """Test restarting a device."""
        mock_client = Mock(spec=NetworkClient)
        mock_client.restart_device = AsyncMock(return_value={"result": "success"})

        result = await restart_unifi_device(
            mock_client, "aa:bb:cc:dd:ee:ff", "test_site"
        )

        mock_client.restart_device.assert_called_once_with(
            "aa:bb:cc:dd:ee:ff", "test_site"
        )
        assert result == {"result": "success"}

    async def test_disable_unifi_ap(self):
        """Test disabling an access point."""
        mock_client = Mock(spec=NetworkClient)
        mock_client.disable_ap = AsyncMock(return_value={"result": "success"})

        result = await disable_unifi_ap(mock_client, "aa:bb:cc:dd:ee:ff", "test_site")

        mock_client.disable_ap.assert_called_once_with("aa:bb:cc:dd:ee:ff", "test_site")
        assert result == {"result": "success"}

    async def test_enable_unifi_ap(self):
        """Test enabling an access point."""
        mock_client = Mock(spec=NetworkClient)
        mock_client.enable_ap = AsyncMock(return_value={"result": "success"})

        result = await enable_unifi_ap(mock_client, "aa:bb:cc:dd:ee:ff", "test_site")

        mock_client.enable_ap.assert_called_once_with("aa:bb:cc:dd:ee:ff", "test_site")
        assert result == {"result": "success"}

    async def test_get_unifi_statistics(self):
        """Test getting statistics."""
        mock_client = Mock(spec=NetworkClient)
        mock_client.get_statistics = AsyncMock(
            return_value={"rx_bytes": 1000, "tx_bytes": 2000}
        )

        result = await get_unifi_statistics(mock_client, "test_site")

        mock_client.get_statistics.assert_called_once_with("test_site")
        assert result == {"rx_bytes": 1000, "tx_bytes": 2000}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
