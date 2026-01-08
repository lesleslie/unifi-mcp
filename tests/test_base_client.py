"""Tests for the base client module."""

from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from unifi_mcp.clients.base_client import BaseUniFiClient


class TestBaseUniFiClient:
    """Test BaseUniFiClient class."""

    def test_init(self):
        """Test initializing the base client."""
        client = BaseUniFiClient(
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
        assert client.base_url == "https://unifi.example.com:8443"
        assert client._authenticated is False
        assert client._csrf_token is None
        assert isinstance(client.client, httpx.AsyncClient)

    def test_init_with_custom_values(self):
        """Test initializing the base client with custom values."""
        client = BaseUniFiClient(
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
        assert client.base_url == "https://test.example.com:9443"

    async def test_authenticate_not_implemented(self):
        """Test that authenticate raises NotImplementedError."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        with pytest.raises(NotImplementedError):
            await client.authenticate()

    async def test_make_request_when_authenticated(self):
        """Test making a request when already authenticated."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        # Mock the client's request method
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.text = ""  # Need to set text attribute

        client.client.request = AsyncMock(return_value=mock_response)
        client._authenticated = True  # Set as authenticated

        result = await client._make_request("GET", "/api/test")

        # Verify the request was made
        client.client.request.assert_called_once()
        assert result == {"status": "success"}

    async def test_make_request_when_not_authenticated(self):
        """Test making a request when not authenticated (should authenticate first)."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        # Mock the authenticate method
        client.authenticate = AsyncMock(return_value=True)

        # Mock the client's request method
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.text = ""

        client.client.request = AsyncMock(return_value=mock_response)

        result = await client._make_request("GET", "/api/test")

        # Verify authenticate was called
        client.authenticate.assert_called_once()
        # Verify the request was made
        client.client.request.assert_called_once()
        assert result == {"status": "success"}

    async def test_make_request_with_csrf_token(self):
        """Test making a request with CSRF token."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        # Set CSRF token
        client._csrf_token = "test_csrf_token"
        client._authenticated = True  # Set as authenticated

        # Mock the client's request method
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.text = ""

        client.client.request = AsyncMock(return_value=mock_response)

        result = await client._make_request("GET", "/api/test")

        # Verify the request was made with CSRF token in headers
        call_args = client.client.request.call_args
        headers = call_args.kwargs.get("headers", {})
        assert headers.get("X-CSRF-Token") == "test_csrf_token"
        assert result == {"status": "success"}

    async def test_make_request_authentication_expired(self):
        """Test making a request when authentication has expired."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        # Mock responses: first 401, then success
        first_response = Mock()
        first_response.status_code = 401
        first_response.text = "Login required"

        second_response = Mock()
        second_response.json.return_value = {"status": "success"}
        second_response.raise_for_status.return_value = None
        second_response.status_code = 200

        client.client.request = AsyncMock(side_effect=[first_response, second_response])
        client.authenticate = AsyncMock(return_value=True)

        result = await client._make_request("GET", "/api/test")

        # Verify authenticate was called twice (initial and after 401)
        assert client.authenticate.call_count == 2
        # Verify the request was made twice (initial and retry)
        assert client.client.request.call_count == 2
        assert result == {"status": "success"}

    async def test_make_request_non_dict_response(self):
        """Test making a request that returns non-dict response."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        # Mock the client's request method with non-dict response
        mock_response = Mock()
        mock_response.json.return_value = ["item1", "item2"]  # List instead of dict
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.text = ""

        client.client.request = AsyncMock(return_value=mock_response)
        client._authenticated = True  # Set as authenticated

        result = await client._make_request("GET", "/api/test")

        # Should return wrapped in data dict
        assert result == {"data": ["item1", "item2"]}

    async def test_close(self):
        """Test closing the client."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        # Mock the aclose method
        client.client.aclose = AsyncMock()

        await client.close()

        # Verify aclose was called
        client.client.aclose.assert_called_once()

    async def test_async_context_manager(self):
        """Test the async context manager functionality."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        # Mock the close method
        client.close = AsyncMock()

        async with client as c:
            # Verify the context manager returns self
            assert c is client

        # Verify close was called
        client.close.assert_called_once()

    async def test_make_request_with_params_and_data(self):
        """Test making a request with both params and data."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        # Mock the client's request method
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.text = ""

        client.client.request = AsyncMock(return_value=mock_response)
        client._authenticated = True  # Set as authenticated

        result = await client._make_request(
            "POST", "/api/test", data={"key": "value"}, params={"param": "value"}
        )

        # Verify the request was made with correct parameters
        client.client.request.assert_called_once_with(
            method="POST",
            url="https://unifi.example.com:8443/api/test",
            json={"key": "value"},
            params={"param": "value"},
            headers=client.client.headers,
        )
        assert result == {"status": "success"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
