"""Pydantic configuration models for UniFi MCP server."""

from pydantic_settings import BaseSettings


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
    """Main application settings."""

    # UniFi controller settings
    network_controller: NetworkSettings | None = None
    access_controller: AccessSettings | None = None
    local_api: LocalSettings | None = None

    # Server settings
    server: ServerSettings = ServerSettings()

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
