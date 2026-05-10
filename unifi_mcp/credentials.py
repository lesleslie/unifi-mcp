"""Credential resolution for UniFi MCP server.

Resolution order:
1. Environment variables / .env file (via Pydantic Settings) — already handled
2. macOS Keychain (via keyring) — fills missing fields at model_post_init time
3. Soft failure — server starts in limited mode if no controllers configured

Note: Uses keyring directly (sync) because Pydantic's model_post_init is synchronous.
Oneiric's async KeyringSecretAdapter is available for runtime resolution but is not
compatible with the sync model initialization phase.
"""

from __future__ import annotations

import importlib.util
import logging

logger = logging.getLogger(__name__)

KEYRING_AVAILABLE = importlib.util.find_spec("keyring") is not None

KEYRING_SERVICE = "unifi-mcp"


def resolve_controller_credential(
    controller_type: str, field: str, env_value: str | None = None
) -> str | None:
    """Resolve a controller credential from keychain.

    Args:
        controller_type: Controller type (e.g., "network-controller")
        field: Field name (e.g., "username", "password")
        env_value: Value already loaded from env/.env by Pydantic

    Returns:
        Resolved credential value or None.
    """
    if env_value:
        return env_value

    key = f"{controller_type}-{field}"

    if not KEYRING_AVAILABLE:
        logger.debug("Keyring unavailable — cannot resolve credential '%s'", key)
        return None

    try:
        import keyring

        value = keyring.get_password(KEYRING_SERVICE, key)
        if value:
            logger.debug("Resolved credential '%s' from keychain", key)
            return value
    except Exception:
        logger.debug("Keychain lookup failed for '%s'", key, exc_info=True)

    return None


def store_credential(controller_type: str, field: str, value: str) -> bool:
    """Store a credential in the macOS Keychain.

    Args:
        controller_type: Controller type (e.g., "network-controller")
        field: Field name (e.g., "username", "password")
        value: Secret value to store

    Returns:
        True if stored successfully.
    """
    if not KEYRING_AVAILABLE:
        logger.warning("keyring not available — credential not stored")
        return False

    try:
        import keyring

        key = f"{controller_type}-{field}"
        keyring.set_password(KEYRING_SERVICE, key, value)
        logger.info("Stored credential '%s' in keychain", key)
        return True
    except Exception:
        logger.error("Failed to store credential in keychain", exc_info=True)
        return False


def get_setup_instructions() -> str:
    """Return instructions for setting up keychain credentials."""
    return f"""
UniFi MCP Credential Setup
===========================

Option 1 — macOS Keychain (recommended):
  keyring set {KEYRING_SERVICE} network-controller-username
  keyring set {KEYRING_SERVICE} network-controller-password

Option 2 — .env file ({KEYRING_SERVICE}/.env):
  UNIFI__NETWORK_CONTROLLER__HOST=192.168.1.1
  UNIFI__NETWORK_CONTROLLER__USERNAME=admin
  UNIFI__NETWORK_CONTROLLER__PASSWORD=your-password

Option 3 — Environment variables:
  export UNIFI__NETWORK_CONTROLLER__HOST=192.168.1.1
  export UNIFI__NETWORK_CONTROLLER__USERNAME=admin
  export UNIFI__NETWORK_CONTROLLER__PASSWORD=your-password
""".strip()
