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
        self.network_controller = self._resolve_controller(
            "network-controller", self.network_controller, NetworkSettings, "8443"
        )  # type: ignore
        self.access_controller = self._resolve_controller( # type: ignore
            "access-controller", self.access_controller, AccessSettings, "8444"
        )
        self.local_api = self._resolve_controller(  # type: ignore
            "local-api", self.local_api, LocalSettings, "1234"
        )

    def _resolve_controller(
        self,
        controller_type: str,
        controller: UniFiSettings | None,
        settings_class: type,
        default_port: str,
    ) -> UniFiSettings | None:
        """Resolve controller credentials from keychain if missing.

        Checks if a controller is partially or fully configured. If credentials
        are missing from env/.env, attempts to fill them from macOS Keychain.
        """
        # Build a dict of what we have so far
        if controller is not None:
            fields = {
                "host": controller.host,
                "port": controller.port,
                "username": controller.username,
                "password": controller.password,
                "site_id": controller.site_id,
                "verify_ssl": controller.verify_ssl,
                "timeout": controller.timeout,
            }
        else:
            # Check if keychain has credentials for this controller type
            fields = {
                "host": None,
                "port": int(default_port),
                "username": None,
                "password": None,
            }

        # Try to fill missing fields from keychain
        changed = False
        for field_name in ("host", "username", "password"):
            if not fields.get(field_name):
                value = resolve_controller_credential(controller_type, field_name, None)
                if value:
                    fields[field_name] = value
                    changed = True

        # If we still don't have the minimum required fields, return as-is
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
        if changed or controller is None:
            return settings_class(**fields)  # type: ignore

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
