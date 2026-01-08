"""Edge case tests for error handling and boundary conditions."""

from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from unifi_mcp.clients.base_client import BaseUniFiClient
from unifi_mcp.clients.network_client import NetworkClient
from unifi_mcp.tools.network_tools import (
    disable_unifi_ap,
    enable_unifi_ap,
    get_unifi_clients,
    get_unifi_devices,
    get_unifi_sites,
    get_unifi_wlans,
    restart_unifi_device,
)


class TestNetworkTimeouts:
    """Test network timeout handling."""

    async def test_request_timeout(self):
        """Test handling of request timeouts."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
            timeout=1,  # Very short timeout
        )

        client._authenticated = True

        # Mock a timeout response
        client.client.request = AsyncMock(
            side_effect=httpx.TimeoutException("Request timed out")
        )

        with pytest.raises(httpx.TimeoutException):
            await client._make_request("GET", "/api/test")

    async def test_connection_timeout(self):
        """Test handling of connection timeouts."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
            timeout=1,
        )

        # Mock authenticate to avoid NotImplementedError
        client.authenticate = AsyncMock(return_value=True)
        client._authenticated = True

        # Mock connection timeout
        client.client.request = AsyncMock(
            side_effect=httpx.ConnectTimeout("Connection timed out")
        )

        with pytest.raises(httpx.ConnectTimeout):
            await client._make_request("GET", "/api/test")


class TestConnectionFailures:
    """Test connection failure handling."""

    async def test_connection_refused(self):
        """Test handling of connection refused."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        client._authenticated = True

        # Mock connection refused
        client.client.request = AsyncMock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        with pytest.raises(httpx.ConnectError):
            await client._make_request("GET", "/api/test")

    async def test_dns_resolution_failure(self):
        """Test handling of DNS resolution failures."""
        client = BaseUniFiClient(
            host="nonexistent.invalid",
            port=8443,
            username="admin",
            password="password123",
        )

        client._authenticated = True

        # Mock DNS resolution failure
        client.client.request = AsyncMock(
            side_effect=httpx.ConnectError("DNS resolution failed")
        )

        with pytest.raises(httpx.ConnectError):
            await client._make_request("GET", "/api/test")

    async def test_network_unreachable(self):
        """Test handling of network unreachable errors."""
        client = BaseUniFiClient(
            host="192.168.255.255",  # Unreachable IP
            port=8443,
            username="admin",
            password="password123",
        )

        client._authenticated = True

        # Mock network unreachable
        client.client.request = AsyncMock(
            side_effect=httpx.NetworkError("Network unreachable")
        )

        with pytest.raises(httpx.NetworkError):
            await client._make_request("GET", "/api/test")


class TestHTTPErrorHandling:
    """Test HTTP error handling."""

    async def test_400_bad_request(self):
        """Test handling of 400 Bad Request."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        client._authenticated = True

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=Mock(), response=mock_response
        )

        client.client.request = AsyncMock(return_value=mock_response)

        with pytest.raises(httpx.HTTPStatusError):
            await client._make_request("GET", "/api/test")

    async def test_403_forbidden(self):
        """Test handling of 403 Forbidden."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        client._authenticated = True

        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Forbidden", request=Mock(), response=mock_response
        )

        client.client.request = AsyncMock(return_value=mock_response)

        with pytest.raises(httpx.HTTPStatusError):
            await client._make_request("GET", "/api/test")

    async def test_404_not_found(self):
        """Test handling of 404 Not Found."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        client._authenticated = True

        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=Mock(), response=mock_response
        )

        client.client.request = AsyncMock(return_value=mock_response)

        with pytest.raises(httpx.HTTPStatusError):
            await client._make_request("GET", "/api/test")

    async def test_500_internal_server_error(self):
        """Test handling of 500 Internal Server Error."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        client._authenticated = True

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error", request=Mock(), response=mock_response
        )

        client.client.request = AsyncMock(return_value=mock_response)

        with pytest.raises(httpx.HTTPStatusError):
            await client._make_request("GET", "/api/test")

    async def test_503_service_unavailable(self):
        """Test handling of 503 Service Unavailable."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        client._authenticated = True

        mock_response = Mock()
        mock_response.status_code = 503
        mock_response.text = "Service Unavailable"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Service Unavailable", request=Mock(), response=mock_response
        )

        client.client.request = AsyncMock(return_value=mock_response)

        with pytest.raises(httpx.HTTPStatusError):
            await client._make_request("GET", "/api/test")


class TestMalformedResponses:
    """Test handling of malformed API responses."""

    async def test_empty_json_response(self):
        """Test handling of empty JSON response."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        client._authenticated = True

        mock_response = Mock()
        mock_response.json.return_value = {}  # Empty dict
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.text = "{}"

        client.client.request = AsyncMock(return_value=mock_response)

        result = await client._make_request("GET", "/api/test")
        assert result == {}

    async def test_null_json_response(self):
        """Test handling of null JSON response."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        client._authenticated = True

        mock_response = Mock()
        mock_response.json.return_value = None
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.text = "null"

        client.client.request = AsyncMock(return_value=mock_response)

        result = await client._make_request("GET", "/api/test")
        # Base client wraps non-dict responses in {'data': ...}
        assert result == {"data": None}

    async def test_malformed_json_response(self):
        """Test handling of malformed JSON response."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        client._authenticated = True

        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.text = "Not valid JSON"

        client.client.request = AsyncMock(return_value=mock_response)

        with pytest.raises(ValueError):
            await client._make_request("GET", "/api/test")

    async def test_array_response_instead_of_object(self):
        """Test handling of array response when object expected."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        client._authenticated = True

        mock_response = Mock()
        mock_response.json.return_value = [
            {"id": "1", "name": "Item 1"},
            {"id": "2", "name": "Item 2"},
        ]
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.text = ""

        client.client.request = AsyncMock(return_value=mock_response)

        result = await client._make_request("GET", "/api/test")
        # Should wrap array in data dict
        assert result == {"data": [{"id": "1", "name": "Item 1"}, {"id": "2", "name": "Item 2"}]}


class TestEmptyAndNullInputs:
    """Test handling of empty and null inputs."""

    async def test_empty_site_id(self):
        """Test handling of empty site ID."""
        mock_client = Mock(spec=NetworkClient)
        mock_client.get_devices = AsyncMock(return_value=[])

        result = await get_unifi_devices(mock_client, "")
        mock_client.get_devices.assert_called_once_with("")

    async def test_null_device_list(self):
        """Test handling of null device list."""
        mock_client = Mock(spec=NetworkClient)
        mock_client.get_devices = AsyncMock(return_value=None)

        result = await get_unifi_devices(mock_client, "default")
        assert result is None

    async def test_empty_mac_address(self):
        """Test handling of empty MAC address."""
        mock_client = Mock(spec=NetworkClient)
        mock_client.restart_device = AsyncMock(return_value={"result": "success"})

        result = await restart_unifi_device(mock_client, "", "default")
        mock_client.restart_device.assert_called_once_with("", "default")


class TestBoundaryValues:
    """Test boundary value conditions."""

    async def test_very_long_site_id(self):
        """Test handling of very long site ID."""
        mock_client = Mock(spec=NetworkClient)
        mock_client.get_devices = AsyncMock(return_value=[])

        long_site_id = "a" * 10000  # Very long string
        result = await get_unifi_devices(mock_client, long_site_id)
        mock_client.get_devices.assert_called_once_with(long_site_id)

    async def test_unicode_in_site_id(self):
        """Test handling of unicode characters in site ID."""
        mock_client = Mock(spec=NetworkClient)
        mock_client.get_devices = AsyncMock(return_value=[])

        unicode_site_ids = [
            "default-测试",
            "default-тест",
            "default-🔥",
            "default-مرحبا",
        ]

        for site_id in unicode_site_ids:
            result = await get_unifi_devices(mock_client, site_id)
            mock_client.get_devices.assert_called_with(site_id)

    async def test_special_characters_in_inputs(self):
        """Test handling of special characters."""
        mock_client = Mock(spec=NetworkClient)
        mock_client.get_devices = AsyncMock(return_value=[])

        special_inputs = [
            "default\n\r\t",  # Control characters
            "default\x00\x01\x02",  # Null bytes
            "default💯",  # Emoji
            "default🚀",  # Another emoji
        ]

        for site_id in special_inputs:
            result = await get_unifi_devices(mock_client, site_id)
            mock_client.get_devices.assert_called_with(site_id)


class TestConcurrentRequests:
    """Test concurrent request handling."""

    async def test_concurrent_device_restarts(self):
        """Test handling of concurrent device restarts."""
        mock_client = Mock(spec=NetworkClient)
        mock_client.restart_device = AsyncMock(return_value={"result": "success"})

        import asyncio

        # Create 10 concurrent restart requests
        macs = [f"aa:bb:cc:dd:ee:{i:02x}" for i in range(10)]
        tasks = [
            restart_unifi_device(mock_client, mac, "default") for mac in macs
        ]

        results = await asyncio.gather(*tasks)

        # All requests should complete
        assert len(results) == 10
        assert all(r == {"result": "success"} for r in results)
        assert mock_client.restart_device.call_count == 10

    async def test_concurrent_auth_requests(self):
        """Test handling of concurrent authentication requests."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        client.authenticate = AsyncMock(return_value=True)
        client._authenticated = False

        mock_response = Mock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.text = ""

        client.client.request = AsyncMock(return_value=mock_response)

        # Make 10 concurrent requests
        import asyncio

        tasks = [client._make_request("GET", "/api/test") for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # Should handle concurrent authentication
        assert len(results) == 10
        assert all(r == {"status": "success"} for r in results)


class TestResourceExhaustion:
    """Test resource exhaustion scenarios."""

    async def test_too_many_open_connections(self):
        """Test handling of too many open connections."""
        mock_client = Mock(spec=NetworkClient)
        mock_client.get_devices = AsyncMock(side_effect=Exception("Too many connections"))

        with pytest.raises(Exception, match="Too many connections"):
            await get_unifi_devices(mock_client, "default")

    async def test_memory_exhaustion(self):
        """Test handling of large response that could exhaust memory."""
        mock_client = Mock(spec=NetworkClient)

        # Simulate a very large response
        large_devices = [{"mac": f"aa:bb:cc:dd:ee:{i:04x}"} for i in range(100000)]
        mock_client.get_devices = AsyncMock(return_value=large_devices)

        result = await get_unifi_devices(mock_client, "default")
        assert len(result) == 100000


class TestStateCorruption:
    """Test state corruption scenarios."""

    async def test_csrf_token_corruption(self):
        """Test handling of corrupted CSRF token."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        # Set corrupted CSRF token
        client._csrf_token = None
        client._authenticated = True

        mock_response = Mock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.text = ""

        client.client.request = AsyncMock(return_value=mock_response)

        result = await client._make_request("GET", "/api/test")

        # Should handle missing CSRF token gracefully
        call_args = client.client.request.call_args
        headers = call_args.kwargs.get("headers", {})
        assert "X-CSRF-Token" not in headers or headers.get("X-CSRF-Token") is None

    async def test_authentication_state_corruption(self):
        """Test handling of corrupted authentication state."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        # Set corrupted state - authenticated but no CSRF token
        client._authenticated = True
        client._csrf_token = "invalid_token"

        mock_response_1 = Mock()
        mock_response_1.status_code = 401
        mock_response_1.text = "Login required"

        mock_response_2 = Mock()
        mock_response_2.json.return_value = {"status": "success"}
        mock_response_2.raise_for_status.return_value = None
        mock_response_2.status_code = 200
        mock_response_2.text = ""

        client.client.request = AsyncMock(
            side_effect=[mock_response_1, mock_response_2]
        )
        client.authenticate = AsyncMock(return_value=True)

        result = await client._make_request("GET", "/api/test")

        # Should authenticate on 401 (no initial auth since already marked authenticated)
        assert client.authenticate.call_count == 1


class TestSSLCertificateErrors:
    """Test SSL certificate error handling."""

    async def test_self_signed_certificate(self):
        """Test handling of self-signed certificates."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
            verify_ssl=False,  # Allow self-signed
        )

        client._authenticated = True

        mock_response = Mock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.text = ""

        client.client.request = AsyncMock(return_value=mock_response)

        result = await client._make_request("GET", "/api/test")
        assert result == {"status": "success"}

    async def test_expired_certificate(self):
        """Test handling of expired SSL certificates."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
            verify_ssl=True,
        )

        client._authenticated = True

        # Mock certificate verification error
        client.client.request = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Certificate verify failed",
                request=Mock(),
                response=Mock(status_code=0),
            )
        )

        with pytest.raises(httpx.HTTPStatusError):
            await client._make_request("GET", "/api/test")


class TestRateLimiting:
    """Test rate limiting behavior."""

    async def test_rate_limit_response(self):
        """Test handling of rate limit responses (429)."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        client._authenticated = True

        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = "Too Many Requests"
        mock_response.headers = {"Retry-After": "60"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Too Many Requests", request=Mock(), response=mock_response
        )

        client.client.request = AsyncMock(return_value=mock_response)

        with pytest.raises(httpx.HTTPStatusError):
            await client._make_request("GET", "/api/test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
