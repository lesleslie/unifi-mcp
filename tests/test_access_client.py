"""Tests for the access client module."""

from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from unifi_mcp.clients.access_client import AccessClient


class TestAccessClient:
    """Test AccessClient class."""

    def test_init(self):
        """Test initializing the access client."""
        client = AccessClient(
            host="access.example.com",
            port=8444,
            username="admin",
            password="password123",
            verify_ssl=True,
            timeout=30,
        )

        assert client.host == "access.example.com"
        assert client.port == 8444
        assert client.username == "admin"
        assert client.password == "password123"
        assert client.verify_ssl is True
        assert client.timeout == 30
        assert client.api_base == "/api/v1"
        assert client.base_url == "https://access.example.com:8444"
        assert client._authenticated is False
        assert client._csrf_token is None

    def test_init_with_custom_values(self):
        """Test initializing the access client with custom values."""
        client = AccessClient(
            host="test.example.com",
            port=9444,
            username="testuser",
            password="testpass",
            verify_ssl=False,
            timeout=60,
        )

        assert client.host == "test.example.com"
        assert client.port == 9444
        assert client.username == "testuser"
        assert client.password == "testpass"
        assert client.verify_ssl is False
        assert client.timeout == 60
        assert client.api_base == "/api/v1"
        assert client.base_url == "https://test.example.com:9444"

    async def test_authenticate_success(self):
        """Test successful authentication."""
        client = AccessClient(
            host="access.example.com",
            port=8444,
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

    async def test_authenticate_success_201(self):
        """Test successful authentication with 201 status."""
        client = AccessClient(
            host="access.example.com",
            port=8444,
            username="admin",
            password="password123",
        )

        # Mock the client's post method with 201 status
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {}

        client.client.post = AsyncMock(return_value=mock_response)

        result = await client.authenticate()

        # Verify authentication was successful with 201 status
        assert result is True
        assert client._authenticated is True
        assert client.client.post.called

    async def test_authenticate_with_csrf_token(self):
        """Test authentication with CSRF token in response."""
        client = AccessClient(
            host="access.example.com",
            port=8444,
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
        client = AccessClient(
            host="access.example.com",
            port=8444,
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
        client = AccessClient(
            host="access.example.com",
            port=8444,
            username="admin",
            password="password123",
        )

        # Mock the client's post method to raise RequestError
        client.client.post = AsyncMock(side_effect=httpx.RequestError("Network error"))

        with pytest.raises(Exception, match="Network error during authentication: "):
            await client.authenticate()

    async def test_authenticate_general_error(self):
        """Test authentication with general error."""
        client = AccessClient(
            host="access.example.com",
            port=8444,
            username="admin",
            password="password123",
        )

        # Mock the client's post method to raise a general exception
        client.client.post = AsyncMock(side_effect=Exception("General error"))

        with pytest.raises(Exception, match="Authentication error: "):
            await client.authenticate()

    async def test_get_access_points(self):
        """Test getting access points."""
        client = AccessClient(
            host="access.example.com",
            port=8444,
            username="admin",
            password="password123",
        )

        # Mock the _make_request method
        mock_response = {"data": [{"id": "ap1", "name": "Access Point 1"}]}
        client._make_request = AsyncMock(return_value=mock_response)

        result = await client.get_access_points()

        # Verify the request was made correctly
        client._make_request.assert_called_once_with("GET", "/api/v1/access-points")
        assert result == [{"id": "ap1", "name": "Access Point 1"}]

    async def test_get_access_points_empty_response(self):
        """Test getting access points with empty response."""
        client = AccessClient(
            host="access.example.com",
            port=8444,
            username="admin",
            password="password123",
        )

        # Mock the _make_request method with empty response
        mock_response = {"data": []}
        client._make_request = AsyncMock(return_value=mock_response)

        result = await client.get_access_points()

        assert result == []

    async def test_get_access_points_non_list_data(self):
        """Test getting access points with non-list data."""
        client = AccessClient(
            host="access.example.com",
            port=8444,
            username="admin",
            password="password123",
        )

        # Mock the _make_request method with non-list data
        mock_response = {"data": "not_a_list"}
        client._make_request = AsyncMock(return_value=mock_response)

        result = await client.get_access_points()

        assert result == []

    async def test_get_users(self):
        """Test getting users."""
        client = AccessClient(
            host="access.example.com",
            port=8444,
            username="admin",
            password="password123",
        )

        # Mock the _make_request method
        mock_response = {"data": [{"id": "user1", "name": "User 1"}]}
        client._make_request = AsyncMock(return_value=mock_response)

        result = await client.get_users()

        # Verify the request was made correctly
        client._make_request.assert_called_once_with("GET", "/api/v1/users")
        assert result == [{"id": "user1", "name": "User 1"}]

    async def test_get_door_access_logs(self):
        """Test getting door access logs."""
        client = AccessClient(
            host="access.example.com",
            port=8444,
            username="admin",
            password="password123",
        )

        # Mock the _make_request method
        mock_response = {"data": [{"id": "log1", "timestamp": "2023-01-01T00:00:00Z"}]}
        client._make_request = AsyncMock(return_value=mock_response)

        result = await client.get_door_access_logs()

        # Verify the request was made correctly
        client._make_request.assert_called_once_with("GET", "/api/v1/access-logs")
        assert result == [{"id": "log1", "timestamp": "2023-01-01T00:00:00Z"}]

    async def test_unlock_door(self):
        """Test unlocking a door."""
        client = AccessClient(
            host="access.example.com",
            port=8444,
            username="admin",
            password="password123",
        )

        # Mock the _make_request method
        mock_response = {"result": "success"}
        client._make_request = AsyncMock(return_value=mock_response)

        result = await client.unlock_door("door123")

        # Verify the request was made correctly
        client._make_request.assert_called_once_with(
            "POST", "/api/v1/doors/door123/unlock"
        )
        assert result == {"result": "success"}

    async def test_set_access_schedule(self):
        """Test setting access schedule."""
        client = AccessClient(
            host="access.example.com",
            port=8444,
            username="admin",
            password="password123",
        )

        # Mock the _make_request method
        mock_response = {"result": "success"}
        client._make_request = AsyncMock(return_value=mock_response)

        schedule = {"monday": {"start": "09:00", "end": "17:00"}}
        result = await client.set_access_schedule("user123", schedule)

        # Verify the request was made correctly
        client._make_request.assert_called_once_with(
            "PUT", "/api/v1/users/user123/schedule", schedule
        )
        assert result == {"result": "success"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
