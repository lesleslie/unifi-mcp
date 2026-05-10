"""UniFi Access Controller API client.

API Documentation:
    UniFi Access uses a REST API with the following base pattern:
    - Base URL: https://{host}:{port}
    - API prefix: /api/v1/developer/
    - Authentication: Bearer token (generated in UniFi Access interface)
    - All requests require: Authorization: Bearer {token}

Key Endpoints:
    - GET /api/v1/developer/devices - List all devices (access points, door hubs, readers)
    - GET /api/v1/developer/users - List all users
    - GET /api/v1/developer/system/logs - Get access/event logs
    - PUT /api/v1/developer/doors/{door_id} - Control door (unlock/lock)
    - PUT /api/v1/developer/users/{user_id} - Update user (including schedules)

References:
    - https://community.openhab.org/t/unifi-access-api/149584
    - https://github.com/Carter12s/unifi_access
"""

from typing import Any

import httpx

from .base_client import BaseUniFiClient


class AccessClient(BaseUniFiClient):
    """Client for UniFi Access Controller API.

    The UniFi Access API provides endpoints for managing door access control,
    including devices, users, access logs, and door control operations.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Access Controller uses /api/v1/developer/ prefix
        self.api_base = "/api/v1/developer"
        self.base_url = f"https://{self.host}:{self.port}"

    async def authenticate(self) -> bool:
        """Authenticate with the UniFi Access Controller.

        UniFi Access uses Bearer token authentication. Tokens are generated
        in the UniFi Access web interface under Settings > Developers.

        Note: This client expects the token to be passed as the password
        parameter during initialization, with username set to "token" or left empty.

        Returns:
            bool: True if authentication successful

        Raises:
            Exception: If authentication fails due to network or auth errors
        """
        try:
            # UniFi Access API uses Bearer token authentication
            # The token is generated in the UniFi Access interface
            # We'll validate the token by making a simple request
            validate_url = (
                f"{self.base_url}{self.api_base}/users?page_num=1&page_size=1"
            )

            # Set Bearer token in headers
            headers = {
                "Authorization": f"Bearer {self.password}",
                "Accept": "application/json",
            }

            response = await self.client.get(validate_url, headers=headers)

            if response.status_code in (200, 201):
                self._authenticated = True
                # Update client headers with Bearer token for future requests
                self.client.headers["Authorization"] = f"Bearer {self.password}"
                return True
            else:
                raise Exception(
                    f"Authentication failed with status {response.status_code}: {response.text}"
                )

        except httpx.RequestError as e:
            raise Exception(f"Network error during authentication: {e}")
        except Exception as e:
            raise Exception(f"Authentication error: {e}")

    async def get_access_points(self) -> list[dict[str, Any]]:
        """Get all access points and door devices from the UniFi Access Controller.

        Endpoint: GET /api/v1/developer/devices

        Returns:
            list[dict]: List of access points and door devices with their configurations.
                       Each device may include type (door_hub, reader, etc.), id, name,
                       and other device-specific properties.

        Raises:
            httpx.HTTPStatusError: If the API request fails
        """
        endpoint = f"{self.api_base}/devices"
        response = await self._make_request("GET", endpoint)
        data = response.get("data", [])  # noqa: FURB184
        return data if isinstance(data, list) else []

    async def get_users(
        self, page_num: int = 1, page_size: int = 25
    ) -> list[dict[str, Any]]:
        """Get all users from the UniFi Access Controller.

        Endpoint: GET /api/v1/developer/users

        Args:
            page_num: Page number for pagination (default: 1)
            page_size: Number of users per page (default: 25)

        Returns:
            list[dict]: List of users with their access credentials, schedules,
                       and user properties. Each user includes id, display_name,
                       and access-related information.

        Raises:
            httpx.HTTPStatusError: If the API request fails
        """
        endpoint = f"{self.api_base}/users"
        params = {"page_num": page_num, "page_size": page_size}
        response = await self._make_request("GET", endpoint, params=params)
        data = response.get("data", [])  # noqa: FURB184
        return data if isinstance(data, list) else []

    async def get_door_access_logs(
        self,
        page_num: int = 1,
        page_size: int = 25,
        since: int | None = None,
        until: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get door access logs from the UniFi Access Controller.

        Endpoint: GET /api/v1/developer/system/logs

        This retrieves event logs including door unlock events, access attempts,
        and other security-related events.

        Args:
            page_num: Page number for pagination (default: 1)
            page_size: Number of log entries per page (default: 25)
            since: Unix timestamp in milliseconds to filter logs after this time
            until: Unix timestamp in milliseconds to filter logs before this time

        Returns:
            list[dict]: List of access log entries. Each entry includes timestamp,
                       event type (e.g., access.door.unlock), actor information,
                       door/target information, and result.

        Raises:
            httpx.HTTPStatusError: If the API request fails
        """
        endpoint = f"{self.api_base}/system/logs"
        params: dict[str, Any] = {"page_num": page_num, "page_size": page_size}

        if since is not None:
            params["since"] = since
        if until is not None:
            params["until"] = until

        response = await self._make_request("GET", endpoint, params=params)
        data = response.get("data", [])  # noqa: FURB184
        return data if isinstance(data, list) else []

    async def unlock_door(
        self, door_id: str, duration: int | None = None
    ) -> dict[str, Any]:
        """Unlock a door via the UniFi Access Controller.

        Endpoint: PUT /api/v1/developer/doors/{door_id}

        This sends an unlock command to the specified door. The door can be
        unlocked indefinitely or for a specific duration.

        Args:
            door_id: Unique identifier of the door (UUID format)
            duration: Optional duration in seconds to keep door unlocked.
                     If None, door unlocks indefinitely. If provided, door
                     auto-locks after the specified duration.

        Returns:
            dict: API response indicating success/failure of the unlock command.
                 May include door status, confirmation of unlock action.

        Raises:
            httpx.HTTPStatusError: If the API request fails
        """
        endpoint = f"{self.api_base}/doors/{door_id}"
        payload: dict[str, Any] = {}

        if duration is not None:
            payload["duration"] = duration

        return await self._make_request("PUT", endpoint, payload)

    async def set_access_schedule(
        self, user_id: str, schedule: dict[str, Any]
    ) -> dict[str, Any]:
        """Set access schedule for a user via the UniFi Access Controller.

        Endpoint: PUT /api/v1/developer/users/{user_id}

        Updates a user's access schedule, defining when they have access to
        specific doors or areas.

        Args:
            user_id: Unique identifier of the user (UUID format)
            schedule: Dictionary containing schedule configuration.
                     May include time ranges, days of week, door/area
                     associations, and other access rules.

        Returns:
            dict: Updated user object with the new schedule applied.

        Raises:
            httpx.HTTPStatusError: If the API request fails
        """
        endpoint = f"{self.api_base}/users/{user_id}"
        return await self._make_request("PUT", endpoint, schedule)
