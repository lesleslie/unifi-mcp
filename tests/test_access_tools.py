"""Tests for the access tools module."""

from unittest.mock import AsyncMock, Mock

import pytest

from unifi_mcp.clients.access_client import AccessClient
from unifi_mcp.tools.access_tools import (
    get_unifi_access_logs,
    get_unifi_access_points,
    get_unifi_access_users,
    set_unifi_access_schedule,
    unlock_unifi_door,
)


class TestAccessTools:
    """Test access tools functions."""

    async def test_get_unifi_access_points(self):
        """Test getting access points."""
        mock_client = Mock(spec=AccessClient)
        mock_client.get_access_points = AsyncMock(
            return_value=[{"id": "ap1", "name": "Access Point 1"}]
        )

        result = await get_unifi_access_points(mock_client)

        mock_client.get_access_points.assert_called_once()
        assert result == [{"id": "ap1", "name": "Access Point 1"}]

    async def test_get_unifi_access_users(self):
        """Test getting access users."""
        mock_client = Mock(spec=AccessClient)
        mock_client.get_users = AsyncMock(
            return_value=[{"id": "user1", "name": "User 1"}]
        )

        result = await get_unifi_access_users(mock_client)

        mock_client.get_users.assert_called_once()
        assert result == [{"id": "user1", "name": "User 1"}]

    async def test_get_unifi_access_logs(self):
        """Test getting access logs."""
        mock_client = Mock(spec=AccessClient)
        mock_client.get_door_access_logs = AsyncMock(
            return_value=[{"id": "log1", "timestamp": "2023-01-01T00:00:00Z"}]
        )

        result = await get_unifi_access_logs(mock_client)

        mock_client.get_door_access_logs.assert_called_once()
        assert result == [{"id": "log1", "timestamp": "2023-01-01T00:00:00Z"}]

    async def test_unlock_unifi_door(self):
        """Test unlocking a door."""
        mock_client = Mock(spec=AccessClient)
        mock_client.unlock_door = AsyncMock(return_value={"result": "success"})

        result = await unlock_unifi_door(mock_client, "door123")

        mock_client.unlock_door.assert_called_once_with("door123")
        assert result == {"result": "success"}

    async def test_set_unifi_access_schedule(self):
        """Test setting access schedule."""
        mock_client = Mock(spec=AccessClient)
        mock_client.set_access_schedule = AsyncMock(return_value={"result": "success"})

        schedule = {"monday": {"start": "09:00", "end": "17:00"}}
        result = await set_unifi_access_schedule(mock_client, "user123", schedule)

        mock_client.set_access_schedule.assert_called_once_with("user123", schedule)
        assert result == {"result": "success"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
