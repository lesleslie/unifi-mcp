"""Base HTTP client for UniFi API interactions."""

from abc import ABC
from typing import Any

import httpx


class AuthenticationError(Exception):
    """Authentication error for UniFi API."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class SessionExpiredError(Exception):
    """Session has expired and needs re-authentication."""

    pass


class BaseUniFiClient(ABC):
    """Base client for UniFi API interactions."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        verify_ssl: bool = True,
        timeout: int = 30,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.base_url = f"https://{host}:{port}"

        # HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            verify=verify_ssl,
            timeout=httpx.Timeout(timeout),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "UniFi-MCP-Client/1.0",
            },
        )

        # Store authentication state
        self._authenticated = False
        self._csrf_token = None

    async def authenticate(self) -> bool:
        """Authenticate with the UniFi controller.

        Uses session-based authentication with username/password.
        Posts credentials to /api/login endpoint and stores session cookie.

        Returns:
            True if authentication successful, False otherwise.

        Raises:
            httpx.HTTPStatusError: If authentication fails.
        """
        login_url = f"{self.base_url}/api/login"

        # Prepare credentials
        credentials = {
            "username": self.username,
            "password": self.password,
        }

        try:
            # POST to login endpoint
            response = await self.client.post(login_url, json=credentials)
            response.raise_for_status()

            # Extract CSRF token from response headers or cookies
            self._csrf_token = self._extract_csrf_token(response)

            # Mark as authenticated
            self._authenticated = True

            return True

        except httpx.HTTPStatusError as e:
            self._authenticated = False
            if e.response.status_code == 401:
                raise AuthenticationError(
                    "Invalid credentials",
                    status_code=401,
                ) from e
            raise

    def _extract_csrf_token(self, response: httpx.Response) -> str | None:
        """Extract CSRF token from response headers or cookies.

        UniFi controllers may return CSRF token in:
        - X-CSRF-Token header
        - Set-Cookie header with csrf_token

        Args:
            response: HTTP response from login request.

        Returns:
            CSRF token string or None if not found.
        """
        # Check headers first
        if "X-CSRF-Token" in response.headers:
            return response.headers["X-CSRF-Token"]

        # Check cookies
        for cookie in response.cookies.jar:
            if "csrf" in cookie.name.lower():
                return cookie.value

        return None

    async def logout(self) -> bool:
        """Logout from the UniFi controller.

        Returns:
            True if logout successful.
        """
        if not self._authenticated:
            return True

        try:
            logout_url = f"{self.base_url}/api/logout"
            response = await self.client.post(logout_url)
            response.raise_for_status()
        except Exception:
            pass  # Ignore logout errors
        finally:
            self._authenticated = False
            self._csrf_token = None

        return True

    async def refresh_session(self) -> bool:
        """Refresh the authentication session.

        Returns:
            True if refresh successful.
        """
        self._authenticated = False
        return await self.authenticate()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an authenticated HTTP request to the UniFi controller."""
        if not self._authenticated:
            await self.authenticate()

        url = f"{self.base_url}{endpoint}"

        # Add CSRF token to headers if available
        headers = self.client.headers.copy()
        if self._csrf_token:
            headers["X-CSRF-Token"] = self._csrf_token

        response = await self.client.request(
            method=method, url=url, json=data, params=params, headers=headers
        )

        # Check if authentication expired
        if response.status_code == 401 or "Login required" in response.text:
            self._authenticated = False
            await self.authenticate()
            # Retry the request
            response = await self.client.request(
                method=method, url=url, json=data, params=params, headers=headers
            )

        response.raise_for_status()
        json_data = response.json()
        if isinstance(json_data, dict):
            return json_data
        # Handle case where response is not a dict
        return {"data": json_data}

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self) -> "BaseUniFiClient":
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """Async context manager exit."""
        await self.close()
