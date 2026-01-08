"""Tests for the network client module."""

from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from unifi_mcp.clients.network_client import NetworkClient


class TestNetworkClient:
    """Test NetworkClient class."""

    def test_init(self):
        """Test initializing the network client."""
        client = NetworkClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
            verify_ssl=True,
            timeout=30,
        )

        assert client.host == "unifi.example.com"
        assert client.port == 8443
        assert client.username == "admin"
        assert client.password == "password123"
        assert client.verify_ssl is True
        assert client.timeout == 30
        assert client.api_base == "/api"
        assert client.base_url == "https://unifi.example.com:8443"
        assert client._authenticated is False
        assert client._csrf_token is None

    def test_init_with_custom_values(self):
        """Test initializing the network client with custom values."""
        client = NetworkClient(
            host="test.example.com",
            port=9443,
            username="testuser",
            password="testpass",
            verify_ssl=False,
            timeout=60,
        )

        assert client.host == "test.example.com"
        assert client.port == 9443
        assert client.username == "testuser"
        assert client.password == "testpass"
        assert client.verify_ssl is False
        assert client.timeout == 60
        assert client.api_base == "/api"
        assert client.base_url == "https://test.example.com:9443"

    async def test_authenticate_success(self):
        """Test successful authentication."""
        client = NetworkClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        # Mock the client's post method
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}

        client.client.post = AsyncMock(return_value=mock_response)

        result = await client.authenticate()

        # Verify authentication was successful
        assert result is True
        assert client._authenticated is True
        assert client.client.post.called

    async def test_authenticate_with_csrf_token(self):
        """Test authentication with CSRF token in response."""
        client = NetworkClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        # Mock the client's post method with CSRF token
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"x-csrf-token": "test_csrf_token"}

        client.client.post = AsyncMock(return_value=mock_response)

        result = await client.authenticate()

        # Verify authentication was successful and CSRF token was stored
        assert result is True
        assert client._authenticated is True
        assert client._csrf_token == "test_csrf_token"

    async def test_authenticate_failure(self):
        """Test authentication failure."""
        client = NetworkClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        # Mock the client's post method with failure status
        mock_response = Mock()
        mock_response.status_code = 401

        client.client.post = AsyncMock(return_value=mock_response)

        with pytest.raises(Exception, match="Authentication failed with status 401"):
            await client.authenticate()

    async def test_authenticate_network_error(self):
        """Test authentication with network error."""
        client = NetworkClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        # Mock the client's post method to raise RequestError
        client.client.post = AsyncMock(side_effect=httpx.RequestError("Network error"))

        with pytest.raises(Exception, match="Network error during authentication: "):
            await client.authenticate()

    async def test_authenticate_general_error(self):
        """Test authentication with general error."""
        client = NetworkClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        # Mock the client's post method to raise a general exception
        client.client.post = AsyncMock(side_effect=Exception("General error"))

        with pytest.raises(Exception, match="Authentication error: "):
            await client.authenticate()

    async def test_get_sites(self):
        """Test getting sites."""
        client = NetworkClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        # Mock the _make_request method
        mock_response = {"data": [{"name": "default", "desc": "Default Site"}]}
        client._make_request = AsyncMock(return_value=mock_response)

        result = await client.get_sites()

        # Verify the request was made correctly
        client._make_request.assert_called_once_with("GET", "/api/self/sites")
        assert result == [{"name": "default", "desc": "Default Site"}]

    async def test_get_sites_empty_response(self):
        """Test getting sites with empty response."""
        client = NetworkClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        # Mock the _make_request method with empty response
        mock_response = {"data": []}
        client._make_request = AsyncMock(return_value=mock_response)

        result = await client.get_sites()

        assert result == []

    async def test_get_sites_non_list_data(self):
        """Test getting sites with non-list data."""
        client = NetworkClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        # Mock the _make_request method with non-list data
        mock_response = {"data": "not_a_list"}
        client._make_request = AsyncMock(return_value=mock_response)

        result = await client.get_sites()

        assert result == []

    async def test_get_devices(self):
        """Test getting devices."""
        client = NetworkClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        # Mock the _make_request method
        mock_response = {"data": [{"mac": "aa:bb:cc:dd:ee:ff", "type": "uap"}]}
        client._make_request = AsyncMock(return_value=mock_response)

        result = await client.get_devices("test_site")

        # Verify the request was made correctly
        client._make_request.assert_called_once_with(
            "GET", "/api/s/test_site/stat/device"
        )
        assert result == [{"mac": "aa:bb:cc:dd:ee:ff", "type": "uap"}]

    async def test_get_devices_default_site(self):
        """Test getting devices with default site."""
        client = NetworkClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        # Mock the _make_request method
        mock_response = {"data": []}
        client._make_request = AsyncMock(return_value=mock_response)

        result = await client.get_devices()

        # Verify the request was made with default site
        client._make_request.assert_called_once_with(
            "GET", "/api/s/default/stat/device"
        )
        assert result == []

    async def test_get_clients(self):
        """Test getting clients."""
        client = NetworkClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        # Mock the _make_request method
        mock_response = {
            "data": [{"mac": "aa:bb:cc:dd:ee:ff", "hostname": "test-client"}]
        }
        client._make_request = AsyncMock(return_value=mock_response)

        result = await client.get_clients("test_site")

        # Verify the request was made correctly
        client._make_request.assert_called_once_with("GET", "/api/s/test_site/stat/sta")
        assert result == [{"mac": "aa:bb:cc:dd:ee:ff", "hostname": "test-client"}]

    async def test_get_wlans(self):
        """Test getting WLANs."""
        client = NetworkClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        # Mock the _make_request method
        mock_response = {"data": [{"name": "MyWiFi", "enabled": True}]}
        client._make_request = AsyncMock(return_value=mock_response)

        result = await client.get_wlans("test_site")

        # Verify the request was made correctly
        client._make_request.assert_called_once_with(
            "GET", "/api/s/test_site/rest/wlanconf"
        )
        assert result == [{"name": "MyWiFi", "enabled": True}]

    async def test_restart_device(self):
        """Test restarting a device."""
        client = NetworkClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        # Mock the _make_request method
        mock_response = {"result": "success"}
        client._make_request = AsyncMock(return_value=mock_response)

        result = await client.restart_device("aa:bb:cc:dd:ee:ff", "test_site")

        # Verify the request was made correctly
        client._make_request.assert_called_once_with(
            "POST",
            "/api/s/test_site/cmd/devmgr",
            {"cmd": "restart", "mac": "aa:bb:cc:dd:ee:ff"},
        )
        assert result == {"result": "success"}

    async def test_disable_ap(self):
        """Test disabling an access point."""
        client = NetworkClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        # Mock the _make_request method
        mock_response = {"result": "success"}
        client._make_request = AsyncMock(return_value=mock_response)

        result = await client.disable_ap("aa:bb:cc:dd:ee:ff", "test_site")

        # Verify the request was made correctly
        client._make_request.assert_called_once_with(
            "PUT", "/api/s/test_site/rest/device/aa:bb:cc:dd:ee:ff", {"disabled": True}
        )
        assert result == {"result": "success"}

    async def test_enable_ap(self):
        """Test enabling an access point."""
        client = NetworkClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        # Mock the _make_request method
        mock_response = {"result": "success"}
        client._make_request = AsyncMock(return_value=mock_response)

        result = await client.enable_ap("aa:bb:cc:dd:ee:ff", "test_site")

        # Verify the request was made correctly
        client._make_request.assert_called_once_with(
            "PUT", "/api/s/test_site/rest/device/aa:bb:cc:dd:ee:ff", {"disabled": False}
        )
        assert result == {"result": "success"}

    async def test_get_statistics(self):
        """Test getting statistics."""
        client = NetworkClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        # Mock the _make_request method
        mock_response = {"rx_bytes": 1000, "tx_bytes": 2000}
        client._make_request = AsyncMock(return_value=mock_response)

        result = await client.get_statistics("test_site")

        # Verify the request was made correctly
        client._make_request.assert_called_once_with(
            "GET", "/api/s/test_site/stat/statistics"
        )
        assert result == {"rx_bytes": 1000, "tx_bytes": 2000}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
