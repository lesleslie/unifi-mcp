"""Schema validation tests for UniFi MCP Pydantic models.

These tests ensure that all Pydantic models follow best practices for
handling API responses by verifying that extra fields are properly ignored.
This prevents issues when the UniFi API adds new fields that our models
don't yet know about.
"""

from datetime import datetime

import pytest
from pydantic import ConfigDict

from unifi_mcp.models.access import (
    AccessDoor,
    AccessLog,
    AccessPoint,
    AccessUser,
    UnifiAccessBaseModel,
)
from unifi_mcp.models.network import (
    NetworkClient,
    NetworkDevice,
    NetworkSite,
    NetworkWLAN,
    UnifiBaseModel,
)


# =============================================================================
# Sample API Response Fixtures
# =============================================================================


@pytest.fixture
def sample_network_device_response() -> dict:
    """Sample API response for a network device."""
    return {
        "mac": "aa:bb:cc:dd:ee:ff",
        "name": "USW-24-POE",
        "type": "usw",
        "model": "USW-24-POE",
        "state": 1,
        "uptime": 1234567,
        "ip": "192.168.1.100",
        "version": "6.5.56",
        "adoptable_when_upgraded": False,
        "adopted": True,
        "site_id": "default",
        "disabled": False,
        "port_table": [
            {"port_idx": 1, "name": "Port 1", "up": True},
            {"port_idx": 2, "name": "Port 2", "up": False},
        ],
    }


@pytest.fixture
def sample_network_client_response() -> dict:
    """Sample API response for a network client."""
    return {
        "mac": "11:22:33:44:55:66",
        "ip": "192.168.1.50",
        "name": "iPhone",
        "hostname": "johns-iphone",
        "oui": "Apple",
        "is_wired": False,
        "uplink": {"ap_mac": "aa:bb:cc:dd:ee:ff", "channel": 36},
        "site_id": "default",
        "first_seen": 1700000000,
        "last_seen": 1700100000,
        "is_guest": False,
        "user_id": "user123",
        "dev_id_override": None,
    }


@pytest.fixture
def sample_network_wlan_response() -> dict:
    """Sample API response for a WLAN configuration."""
    return {
        "id": "wlan123",
        "name": "Corporate WiFi",
        "site_id": "default",
        "wlan_id": "wlan_id_123",
        "ssid": "Corporate WiFi",
        "security": "wpapsk",
        "wpa3_support": True,
        "enabled": True,
        "hide_ssid": False,
        "is_guest": False,
        "dtim_mode": "auto",
        "dtim_na": 3,
        "dtim_ng": 1,
    }


@pytest.fixture
def sample_network_site_response() -> dict:
    """Sample API response for a network site."""
    return {
        "id": "site123",
        "name": "default",
        "desc": "Default Site",
        "role": "admin",
        "site_id": "default",
        "attr_no_delete": False,
        "attr_hidden_id": None,
    }


@pytest.fixture
def sample_access_point_response() -> dict:
    """Sample API response for an access point."""
    return {
        "mac": "aa:bb:cc:dd:ee:ff",
        "name": "Main Entrance Reader",
        "model": "UA-Door",
        "state": 1,
        "firmware_version": "1.2.3",
        "ip": "192.168.1.200",
        "connected_at": 1700000000,
        "site_id": "default",
        "floorplan_id": "floor123",
    }


@pytest.fixture
def sample_access_user_response() -> dict:
    """Sample API response for an access user."""
    return {
        "user_id": "user123",
        "name": "John Doe",
        "description": "Employee",
        "email": "john.doe@example.com",
        "phone": "+1-555-123-4567",
        "key": "key123",
        "site_id": "default",
        "created_time": 1700000000,
    }


@pytest.fixture
def sample_access_door_response() -> dict:
    """Sample API response for an access door."""
    return {
        "door_id": "door123",
        "name": "Front Door",
        "description": "Main entrance",
        "site_id": "default",
        "access_point_id": "ap123",
        "relay_id": 1,
        "lock_type": "maglock",
        "enabled": True,
    }


@pytest.fixture
def sample_access_log_response() -> dict:
    """Sample API response for an access log entry."""
    return {
        "log_id": "log123",
        "user_id": "user123",
        "username": "john.doe",
        "door_id": "door123",
        "door_name": "Front Door",
        "timestamp": "2024-01-15T10:30:00Z",
        "success": True,
        "site_id": "default",
        "event_type": "access_granted",
    }


# =============================================================================
# Network Model Schema Tests
# =============================================================================


class TestNetworkDeviceSchema:
    """Test NetworkDevice model schema validation."""

    def test_model_has_extra_ignore(self) -> None:
        """Verify NetworkDevice model_config has extra='ignore'."""
        assert NetworkDevice.model_config.get("extra") == "ignore"

    def test_extra_fields_ignored(
        self, sample_network_device_response: dict
    ) -> None:
        """Verify model accepts extra fields without error."""
        # Add extra fields that don't exist in the model
        data_with_extras = {
            **sample_network_device_response,
            "unknown_field_1": "some value",
            "unknown_field_2": 12345,
            "future_api_field": {"nested": "data"},
        }

        # Should not raise validation error
        device = NetworkDevice(**data_with_extras)

        # Verify expected fields are present
        assert device.mac == "aa:bb:cc:dd:ee:ff"
        assert device.name == "USW-24-POE"
        assert device.adopted is True

    def test_required_fields_validation(self) -> None:
        """Verify required fields are enforced."""
        with pytest.raises(Exception):  # ValidationError
            NetworkDevice()  # Missing required fields


class TestNetworkClientSchema:
    """Test NetworkClient model schema validation."""

    def test_model_has_extra_ignore(self) -> None:
        """Verify NetworkClient model_config has extra='ignore'."""
        assert NetworkClient.model_config.get("extra") == "ignore"

    def test_extra_fields_ignored(
        self, sample_network_client_response: dict
    ) -> None:
        """Verify model accepts extra fields without error."""
        data_with_extras = {
            **sample_network_client_response,
            "rx_bytes": 1024000,
            "tx_bytes": 512000,
            "signal": -45,
            "satisfaction": 98,
            "unknown_nested": {"data": "value"},
        }

        client = NetworkClient(**data_with_extras)

        assert client.mac == "11:22:33:44:55:66"
        assert client.is_wired is False
        assert client.name == "iPhone"

    def test_required_fields_validation(self) -> None:
        """Verify required fields are enforced."""
        with pytest.raises(Exception):  # ValidationError
            NetworkClient()  # Missing required fields


class TestNetworkWLANSchema:
    """Test NetworkWLAN model schema validation."""

    def test_model_has_extra_ignore(self) -> None:
        """Verify NetworkWLAN model_config has extra='ignore'."""
        assert NetworkWLAN.model_config.get("extra") == "ignore"

    def test_extra_fields_ignored(
        self, sample_network_wlan_response: dict
    ) -> None:
        """Verify model accepts extra fields without error."""
        data_with_extras = {
            **sample_network_wlan_response,
            "security_options": ["wpa2", "wpa3"],
            "min_rssi": -70,
            "future_field": True,
        }

        wlan = NetworkWLAN(**data_with_extras)

        assert wlan.id == "wlan123"
        assert wlan.ssid == "Corporate WiFi"
        assert wlan.enabled is True


class TestNetworkSiteSchema:
    """Test NetworkSite model schema validation."""

    def test_model_has_extra_ignore(self) -> None:
        """Verify NetworkSite model_config has extra='ignore'."""
        assert NetworkSite.model_config.get("extra") == "ignore"

    def test_extra_fields_ignored(
        self, sample_network_site_response: dict
    ) -> None:
        """Verify model accepts extra fields without error."""
        data_with_extras = {
            **sample_network_site_response,
            "health": {"status": "ok"},
            "num_devices": 25,
            "unknown_field": "ignored",
        }

        site = NetworkSite(**data_with_extras)

        assert site.id == "site123"
        assert site.name == "default"
        assert site.desc == "Default Site"


# =============================================================================
# Access Model Schema Tests
# =============================================================================


class TestAccessPointSchema:
    """Test AccessPoint model schema validation."""

    def test_model_has_extra_ignore(self) -> None:
        """Verify AccessPoint model_config has extra='ignore'."""
        assert AccessPoint.model_config.get("extra") == "ignore"

    def test_extra_fields_ignored(
        self, sample_access_point_response: dict
    ) -> None:
        """Verify model accepts extra fields without error."""
        data_with_extras = {
            **sample_access_point_response,
            "last_heartbeat": 1700100000,
            "capabilities": ["nfc", "ble"],
            "custom_field": "value",
        }

        access_point = AccessPoint(**data_with_extras)

        assert access_point.mac == "aa:bb:cc:dd:ee:ff"
        assert access_point.name == "Main Entrance Reader"
        assert access_point.state == 1

    def test_required_fields_validation(self) -> None:
        """Verify required fields are enforced."""
        with pytest.raises(Exception):  # ValidationError
            AccessPoint()  # Missing required fields


class TestAccessUserSchema:
    """Test AccessUser model schema validation."""

    def test_model_has_extra_ignore(self) -> None:
        """Verify AccessUser model_config has extra='ignore'."""
        assert AccessUser.model_config.get("extra") == "ignore"

    def test_extra_fields_ignored(
        self, sample_access_user_response: dict
    ) -> None:
        """Verify model accepts extra fields without error."""
        data_with_extras = {
            **sample_access_user_response,
            "status": "active",
            "last_access_time": 1700050000,
            "custom_attributes": {"department": "Engineering"},
        }

        user = AccessUser(**data_with_extras)

        assert user.user_id == "user123"
        assert user.name == "John Doe"
        assert user.email == "john.doe@example.com"


class TestAccessDoorSchema:
    """Test AccessDoor model schema validation."""

    def test_model_has_extra_ignore(self) -> None:
        """Verify AccessDoor model_config has extra='ignore'."""
        assert AccessDoor.model_config.get("extra") == "ignore"

    def test_extra_fields_ignored(
        self, sample_access_door_response: dict
    ) -> None:
        """Verify model accepts extra fields without error."""
        data_with_extras = {
            **sample_access_door_response,
            "schedule_id": "schedule123",
            "door_groups": ["group1", "group2"],
            "future_field": {"nested": "data"},
        }

        door = AccessDoor(**data_with_extras)

        assert door.door_id == "door123"
        assert door.name == "Front Door"
        assert door.enabled is True


class TestAccessLogSchema:
    """Test AccessLog model schema validation."""

    def test_model_has_extra_ignore(self) -> None:
        """Verify AccessLog model_config has extra='ignore'."""
        assert AccessLog.model_config.get("extra") == "ignore"

    def test_extra_fields_ignored(self, sample_access_log_response: dict) -> None:
        """Verify model accepts extra fields without error."""
        data_with_extras = {
            **sample_access_log_response,
            "access_method": "nfc_card",
            "door_position": "open",
            "video_url": "https://example.com/video.mp4",
        }

        log = AccessLog(**data_with_extras)

        assert log.log_id == "log123"
        assert log.success is True


# =============================================================================
# Base Model Configuration Tests
# =============================================================================


class TestModelConfigBestPractices:
    """Test that all models follow best practices for API response handling."""

    def test_unifi_base_model_has_extra_ignore(self) -> None:
        """Verify UnifiBaseModel has extra='ignore' configuration."""
        assert UnifiBaseModel.model_config.get("extra") == "ignore"

    def test_unifi_access_base_model_has_extra_ignore(self) -> None:
        """Verify UnifiAccessBaseModel has extra='ignore' configuration."""
        assert UnifiAccessBaseModel.model_config.get("extra") == "ignore"

    def test_all_network_models_have_proper_extra_config(self) -> None:
        """Verify all network models have extra='ignore' or 'allow'."""
        network_models = [
            NetworkDevice,
            NetworkClient,
            NetworkWLAN,
            NetworkSite,
        ]

        for model in network_models:
            extra_config = model.model_config.get("extra")
            assert extra_config in (
                "ignore",
                "allow",
            ), f"{model.__name__} has extra='{extra_config}', expected 'ignore' or 'allow'"

    def test_all_access_models_have_proper_extra_config(self) -> None:
        """Verify all access models have extra='ignore' or 'allow'."""
        access_models = [
            AccessPoint,
            AccessUser,
            AccessDoor,
            AccessLog,
        ]

        for model in access_models:
            extra_config = model.model_config.get("extra")
            assert extra_config in (
                "ignore",
                "allow",
            ), f"{model.__name__} has extra='{extra_config}', expected 'ignore' or 'allow'"

    def test_all_models_inherit_populate_by_name(self) -> None:
        """Verify all models inherit populate_by_name=True for alias handling."""
        all_models = [
            NetworkDevice,
            NetworkClient,
            NetworkWLAN,
            NetworkSite,
            AccessPoint,
            AccessUser,
            AccessDoor,
            AccessLog,
        ]

        for model in all_models:
            populate_by_name = model.model_config.get("populate_by_name")
            assert (
                populate_by_name is True
            ), f"{model.__name__} should have populate_by_name=True"


# =============================================================================
# Integration Tests - Realistic API Response Scenarios
# =============================================================================


class TestRealisticAPIResponses:
    """Test models with realistic, complex API responses."""

    def test_network_device_with_full_api_response(self) -> None:
        """Test NetworkDevice with a full, realistic API response."""
        full_response = {
            # Required fields
            "mac": "74:83:c2:aa:bb:cc",
            "state": 1,
            "adopted": True,
            "site_id": "5e9b8a7c3b1d2f0001a2b3c4",
            # Optional known fields
            "name": "Switch-24-POE",
            "type": "usw",
            "model": "USW-24-POE",
            "uptime": 864000,
            "ip": "192.168.1.10",
            "version": "6.5.59",
            "adoptable_when_upgraded": False,
            "disabled": False,
            "port_table": [
                {
                    "port_idx": 1,
                    "media": "GE",
                    "port_poe": True,
                    "poe_enable": True,
                    "portconf_id": "5e9b8a7c3b1d2f0001a2b3c5",
                    "port_security_enabled": False,
                    "name": "Port 1",
                    "up": True,
                    "speed": 1000,
                    "full_duplex": True,
                    "stp_pathcost": 20000,
                    "stp_state": "forwarding",
                    "bytes_r": 1500,
                    "tx_bytes": 1000000,
                    "rx_bytes": 500000,
                    "tx_packets": 1000,
                    "rx_packets": 500,
                    "tx_errors": 0,
                    "rx_errors": 0,
                    "tx_dropped": 0,
                    "rx_dropped": 0,
                    "rx_multicast": 10,
                    "rx_broadcast": 5,
                    "satisfaction": 100,
                    "satisfaction_reason": 0,
                }
            ],
            # Extra fields commonly present in real responses
            "serial": "74:83:C2:AA:BB:CC",
            "connection_state": 1,
            "last_seen": 1700100000,
            "next_heartbeat_at": 1700100100,
            "two_phase_adopt": False,
            "connect_request_ip": "192.168.1.10",
            "connect_request_port": 59876,
            "inform_url": "http://unifi:8080/inform",
            "kernel_version": "4.14",
            "cfgversion": "abc123",
            "config_network": {"type": "dhcp", "ip": "192.168.1.10"},
            "stat": {
                "sw": {
                    "tx_bytes": 10000000,
                    "rx_bytes": 5000000,
                    "tx_packets": 100000,
                    "rx_packets": 50000,
                }
            },
            "system_stats": {"cpu": 5.2, "mem": 45.3},
            "version_incompatible": False,
            "hostname": "USW-24-POE",
            "anonymous_node_id": "node123",
            "unsupported": False,
            "unsupported_reason": 0,
            "device_id": "device123",
            "_uptime": 864000,
            "_state": 1,
            "provisioned": True,
            "start_disconnected_millis": 0,
            "inform_ip_address": "192.168.1.1",
            "incompatible": False,
            "known_cfgversion": "abc123",
            "uagg": [],
            "port_overrides": [],
            "outdoor_mode": False,
            "led_override": "default",
            "led_override_color": "#0000ff",
            "led_override_color_brightness": 100,
            "outlet_override": [],
            "outlet_enabled": True,
            "ethernet_table": [
                {"mac": "74:83:c2:aa:bb:cc", "num_port": 26, "name": "eth0"}
            ],
            "wlan_overrides": [],
        }

        device = NetworkDevice(**full_response)

        # Verify core fields
        assert device.mac == "74:83:c2:aa:bb:cc"
        assert device.name == "Switch-24-POE"
        assert device.state == 1
        assert device.adopted is True
        assert device.site_id == "5e9b8a7c3b1d2f0001a2b3c4"
        assert device.ip == "192.168.1.10"
        assert device.model == "USW-24-POE"
        assert device.version == "6.5.59"

    def test_network_client_with_full_api_response(self) -> None:
        """Test NetworkClient with a full, realistic API response."""
        full_response = {
            # Required fields
            "mac": "a4:83:e7:11:22:33",
            "is_wired": False,
            "site_id": "5e9b8a7c3b1d2f0001a2b3c4",
            # Optional known fields
            "ip": "192.168.1.100",
            "name": "John's iPhone",
            "hostname": "Johns-iPhone",
            "oui": "Apple, Inc.",
            "uplink": {
                "ap_mac": "74:83:c2:aa:bb:cc",
                "channel": 36,
                "radio": "na",
                "rssi": -45,
                "signal": -42,
                "noise": -95,
                "tx_power": 20,
            },
            "first_seen": 1699500000,
            "last_seen": 1700100000,
            "is_guest": False,
            "user_id": "user123",
            # Extra fields commonly present
            "network_id": "network123",
            "fixed_ip": None,
            "noted": True,
            "name_oui": "Apple",
            "satisfaction": 98,
            "satisfaction_last": 100,
            "ap_mac": "74:83:c2:aa:bb:cc",
            "assoc_time": 1700000000,
            "latest_assoc_time": 1700050000,
            "disconnected_time": 1699900000,
            "dhcpend_time": 1699500100,
            "powersave_enabled": False,
            "is_11r": False,
            "ccq": 99,
            "channel": 36,
            "radio": "na",
            "radio_proto": "ac",
            "rssi": -45,
            "signal": -42,
            "noise": -95,
            "tx_power": 20,
            "tx_bytes": 50000000,
            "rx_bytes": 120000000,
            "tx_packets": 500000,
            "rx_packets": 1000000,
            "tx_retries": 5000,
            "tx_failed": 100,
            "wired_tx_bytes": 0,
            "wired_rx_bytes": 0,
            "wired_tx_packets": 0,
            "wired_rx_packets": 0,
            "channel_utilization": 15,
            "uap_mac": "74:83:c2:aa:bb:cc",
            "qos_policy_applied": True,
            "os_class": {"name": "iOS", "family": "Apple"},
            "dev_cat": 1,
            "dev_family": 1,
            "dev_vendor": 1,
            "dev_id": "device_id_123",
            "client_mac": "a4:83:e7:11:22:33",
        }

        client = NetworkClient(**full_response)

        assert client.mac == "a4:83:e7:11:22:33"
        assert client.is_wired is False
        assert client.name == "John's iPhone"
        assert client.ip == "192.168.1.100"

    def test_access_user_with_full_api_response(self) -> None:
        """Test AccessUser with a full, realistic API response."""
        full_response = {
            # Required fields
            "user_id": "5e9b8a7c3b1d2f0001a2b3c6",
            "name": "Jane Smith",
            "site_id": "5e9b8a7c3b1d2f0001a2b3c4",
            # Optional known fields
            "description": "Senior Software Engineer",
            "email": "jane.smith@company.com",
            "phone": "+1-555-987-6543",
            "key": "access_key_abc123",
            "created_time": 1699000000,
            # Extra fields commonly present
            "status": "ACTIVE",
            "status_message": None,
            "modified_time": 1700000000,
            "thumbnail_url": None,
            "fingerprints": [
                {"id": "fp1", "type": "right_index", "active": True},
                {"id": "fp2", "type": "left_index", "active": True},
            ],
            "nfc_cards": [
                {"id": "nfc1", "card_number": "12345678", "active": True}
            ],
            "pin_codes": [
                {"id": "pin1", "code": "****", "active": True}
            ],
            "groups": [
                {"group_id": "group1", "name": "Engineering"},
                {"group_id": "group2", "name": "All Users"},
            ],
            "schedules": [
                {"schedule_id": "sched1", "name": "Business Hours"}
            ],
            "access_policy_ids": ["policy1", "policy2"],
            "last_access_time": 1700050000,
            "last_access_door": "Main Entrance",
            "visitor": False,
            "expire_time": None,
            "ui_level": 0,
            "recovery_email": None,
            "recovery_phone": None,
            "ui_settings": {"theme": "light"},
        }

        user = AccessUser(**full_response)

        assert user.user_id == "5e9b8a7c3b1d2f0001a2b3c6"
        assert user.name == "Jane Smith"
        assert user.email == "jane.smith@company.com"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
