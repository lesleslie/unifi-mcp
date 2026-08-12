"""Pydantic configuration models for UniFi MCP server."""

from __future__ import annotations

import importlib.util
import logging
import sys
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict

from unifi_mcp.credentials import get_setup_instructions, resolve_controller_credential

logger = logging.getLogger(__name__)

# Import security utilities for password validation (Phase 3 Security Hardening)
try:
    from mcp_common.security import APIKeyValidator

    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False

# Check custom exceptions availability (Phase 3.3 M3: improved pattern)
EXCEPTIONS_AVAILABLE = importlib.util.find_spec("mcp_common.exceptions") is not None

if EXCEPTIONS_AVAILABLE:
    from mcp_common.exceptions import (
        CredentialValidationError,
    )


class UniFiSettings(BaseSettings):
    """Base settings for UniFi controllers."""

    host: str
    port: int
    username: str
    password: str
    site_id: str = "default"
    verify_ssl: bool = True
    timeout: int = 30


class NetworkSettings(UniFiSettings):
    """Settings specific to UniFi Network Controller."""

    port: int = 8443  # Default Network Controller port


class AccessSettings(UniFiSettings):
    """Settings specific to UniFi Access Controller."""

    port: int = 8444  # Default Access Controller port


class LocalSettings(UniFiSettings):
    """Settings specific to UniFi Local API."""

    port: int = 1234  # Example port, may vary


class ServerSettings(BaseSettings):
    """Server configuration."""

    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False
    reload: bool = False


class Settings(BaseSettings):
    """Main application settings.

    Credentials are resolved in this order:
    1. Environment variables / .env file (via Pydantic Settings)
    2. macOS Keychain (via keyring) — tried for missing fields
    3. Soft failure — server starts in limited mode if no controllers configured
    """

    # UniFi controller settings
    network_controller: NetworkSettings | None = None
    access_controller: AccessSettings | None = None
    local_api: LocalSettings | None = None

    # Server settings
    server: ServerSettings = ServerSettings()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
    )

    def model_post_init(self, __context: Any) -> None:
        """Resolve missing credentials from macOS Keychain after Pydantic loads."""
        self.network_controller = self._resolve_controller(  # ty: ignore[invalid-assignment]
            "network-controller", self.network_controller, NetworkSettings, "8443"
        )
        self.access_controller = self._resolve_controller(  # ty: ignore[invalid-assignment]
            "access-controller", self.access_controller, AccessSettings, "8444"
        )
        self.local_api = self._resolve_controller(  # ty: ignore[invalid-assignment]
            "local-api", self.local_api, LocalSettings, "1234"
        )

    def _resolve_controller(
        self,
        controller_type: str,
        controller: UniFiSettings | None,
        settings_class: type[UniFiSettings],
        default_port: str,
    ) -> UniFiSettings | None:
        """Resolve controller credentials from keychain if missing.

        Only fills fields that are explicitly ``None``. Explicit empty strings
        (e.g. ``password=""``) are preserved as a deliberate user choice rather
        than treated as missing.

        When the caller did not provide a controller at all (``controller is
        None``), this method does NOT auto-create one from keychain alone —
        it returns ``None``. Auto-creation was problematic because tests and
        any caller wanting to opt out of keychain resolution had no way to
        signal that. To enable keychain-only setup, configure at least the
        ``UNIFI__<CONTROLLER>__HOST`` env var (or pass a partially-filled
        controller) and the keychain will fill in the remaining fields.
        """
        # If no controller was provided, do not auto-create from keychain.
        # Returning None here preserves the documented "soft failure" mode
        # and lets callers (including tests) explicitly opt out of keychain
        # resolution by not configuring a controller at all.
        if controller is None:
            return None

        # Build a dict of what we have so far
        fields: dict[str, Any] = {
            "host": controller.host,
            "port": controller.port,
            "username": controller.username,
            "password": controller.password,
            "site_id": controller.site_id,
            "verify_ssl": controller.verify_ssl,
            "timeout": controller.timeout,
        }

        # Try to fill missing fields from keychain. Use ``is None`` rather
        # than a truthy check so that explicit empty strings are preserved
        # (tests legitimately set ``password=""`` to verify the masking path).
        changed = False
        for field_name in ("host", "username", "password"):
            if fields.get(field_name) is None:
                value = resolve_controller_credential(controller_type, field_name, None)
                if value:
                    fields[field_name] = value
                    changed = True

        # If we still don't have the minimum required fields, return the
        # original controller unchanged (preserves explicit empty values).
        if (
            not fields.get("host")
            or not fields.get("username")
            or not fields.get("password")
        ):
            if changed:
                logger.warning(
                    "Partial credentials for %s in keychain — need host, username, AND password",
                    controller_type,
                )
            return controller

        # Rebuild the controller settings with resolved values
        if changed:
            return settings_class(**fields)

        return controller

    def validate_credentials_at_startup(self) -> None:
        """Validate UniFi controller credentials at server startup.

        Performs comprehensive validation of username/password credentials
        for all configured controllers (network, access, local API).

        Raises:
            SystemExit: If credentials are missing or weak passwords detected
        """
        controllers_to_validate: list[tuple[str, UniFiSettings]] = []

        if self.network_controller:
            controllers_to_validate.append(
                ("Network Controller", self.network_controller)
            )
        if self.access_controller:
            controllers_to_validate.append(
                ("Access Controller", self.access_controller)
            )
        if self.local_api:
            controllers_to_validate.append(("Local API", self.local_api))

        if not controllers_to_validate:
            # Soft warning instead of crash — server starts with reduced capability
            print(
                "\n⚠️  No UniFi controllers configured — running in limited mode",
                file=sys.stderr,
            )
            print(get_setup_instructions(), file=sys.stderr)
            return

        # Validate each configured controller
        for controller_name, controller in controllers_to_validate:
            _validate_unifi_credentials(
                controller_name=controller_name,
                username=controller.username,
                password=controller.password,
            )

    def get_masked_password(self, controller_type: str = "network") -> str:
        """Get masked password for safe logging.

        Args:
            controller_type: Type of controller ("network", "access", "local")

        Returns:
            Masked password like "...xyz1" for safe display in logs
        """
        controller: UniFiSettings | None = None
        if controller_type == "network" and self.network_controller:
            controller = self.network_controller
        elif controller_type == "access" and self.access_controller:
            controller = self.access_controller
        elif controller_type == "local" and self.local_api:
            controller = self.local_api

        if not controller:
            return "***"

        password = controller.password
        if not password:
            return "***"

        if SECURITY_AVAILABLE:
            return APIKeyValidator.mask_key(password, visible_chars=4)

        # Fallback masking
        if len(password) <= 4:
            return "***"
        return f"...{password[-4:]}"


def _validate_unifi_credentials(
    controller_name: str,
    username: str,
    password: str,
) -> None:
    """Validate UniFi controller username and password.

    Args:
        controller_name: Human-readable controller name for error messages
        username: Username for authentication
        password: Password for authentication

    Raises:
        CredentialValidationError: If credentials are invalid or password is weak (when mcp-common available)
        SystemExit: Falls back to exit if exceptions unavailable
    """
    # Check if credentials are set
    if not username or not username.strip():
        if EXCEPTIONS_AVAILABLE:
            raise CredentialValidationError(
                message=f"{controller_name} username is not set in configuration",
                field="username",
            )
        else:
            # Fallback to sys.exit if exceptions unavailable
            print(f"\n❌ {controller_name} Username Validation Failed", file=sys.stderr)
            print("   Username is not set in configuration", file=sys.stderr)
            sys.exit(1)

    if not password or not password.strip():
        if EXCEPTIONS_AVAILABLE:
            raise CredentialValidationError(
                message=f"{controller_name} password is not set in configuration",
                field="password",
            )
        else:
            # Fallback to sys.exit if exceptions unavailable
            print(f"\n❌ {controller_name} Password Validation Failed", file=sys.stderr)
            print("   Password is not set in configuration", file=sys.stderr)
            sys.exit(1)

    # Validate password strength
    if SECURITY_AVAILABLE:
        # Use generic validator with minimum 12 characters for passwords
        validator = APIKeyValidator(min_length=12)
        try:
            validator.validate(password, raise_on_invalid=True)
            print(
                f"✅ {controller_name} credentials validated (user: {username})",
                file=sys.stderr,
            )
        except ValueError:
            print(f"\n⚠️  {controller_name} Password Warning", file=sys.stderr)
            print(
                "   Password appears weak (minimum 12 characters recommended)",
                file=sys.stderr,
            )
            print(f"   Current length: {len(password)} characters", file=sys.stderr)
            print(f"   Username: {username}", file=sys.stderr)
            # Don't exit - warn but allow weak passwords for backwards compatibility
    else:
        # Basic validation without security module
        if len(password) < 8:
            print(f"\n⚠️  {controller_name} Password Warning", file=sys.stderr)
            print(
                f"   Password appears very weak ({len(password)} characters)",
                file=sys.stderr,
            )
            print("   Minimum 12 characters recommended for security", file=sys.stderr)
