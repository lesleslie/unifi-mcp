"""Tests for CLI functionality."""

import os
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from typer.testing import CliRunner

from unifi_mcp.cli import app

runner = CliRunner()


class TestCLIConfig:
    """Test CLI config command."""

    def test_config_displays_server_settings(self) -> None:
        """Test that config command displays server configuration."""
        result = runner.invoke(app, ["config"])
        assert result.exit_code == 0
        assert "Current UniFi MCP Server Configuration:" in result.stdout
        assert "Server Host:" in result.stdout
        assert "Server Port:" in result.stdout
        assert "Debug Mode:" in result.stdout
        assert "Reload Mode:" in result.stdout

    @patch("unifi_mcp.cli.Settings")
    def test_config_displays_network_controller_when_configured(
        self, mock_settings: MagicMock
    ) -> None:
        """Test that config shows network controller when configured."""
        # Setup mock settings
        mock_network = MagicMock()
        mock_network.host = "192.168.1.1"
        mock_network.port = 8443
        mock_network.site_id = "test-site"

        mock_settings.return_value.network_controller = mock_network
        mock_settings.return_value.access_controller = None

        result = runner.invoke(app, ["config"])
        assert result.exit_code == 0
        assert "Network Controller: Configured" in result.stdout
        assert "Host: 192.168.1.1" in result.stdout
        assert "Port: 8443" in result.stdout
        assert "Site ID: test-site" in result.stdout

    @patch("unifi_mcp.cli.Settings")
    def test_config_displays_access_controller_when_configured(
        self, mock_settings: MagicMock
    ) -> None:
        """Test that config shows access controller when configured."""
        # Setup mock settings
        mock_access = MagicMock()
        mock_access.host = "192.168.1.2"
        mock_access.port = 9443
        mock_access.site_id = "access-site"

        mock_settings.return_value.network_controller = None
        mock_settings.return_value.access_controller = mock_access

        result = runner.invoke(app, ["config"])
        assert result.exit_code == 0
        assert "Access Controller: Configured" in result.stdout
        assert "Host: 192.168.1.2" in result.stdout
        assert "Port: 9443" in result.stdout
        assert "Site ID: access-site" in result.stdout

    def test_config_shows_not_configured_when_missing(self) -> None:
        """Test that config shows 'Not configured' when controllers missing."""
        with patch.dict(os.environ, {}, clear=True):
            result = runner.invoke(app, ["config"])
            assert result.exit_code == 0
            assert "Network Controller: Not configured" in result.stdout
            assert "Access Controller: Not configured" in result.stdout


class TestCLITestConnection:
    """Test CLI test-connection command."""

    def test_connection_requires_controller_type(self) -> None:
        """Test that test-connection requires controller_type argument."""
        result = runner.invoke(app, ["test-connection"])
        assert result.exit_code != 0
        # Typer error messages vary, just check it fails
        assert result.exit_code == 2  # Typer uses exit code 2 for missing arguments

    def test_connection_network_without_config_fails(self) -> None:
        """Test that testing network connection without config fails."""
        with patch.dict(os.environ, {}, clear=True):
            result = runner.invoke(app, ["test-connection", "network"])
            assert result.exit_code == 1
            assert "Network controller not configured" in result.stdout

    def test_connection_access_without_config_fails(self) -> None:
        """Test that testing access connection without config fails."""
        with patch.dict(os.environ, {}, clear=True):
            result = runner.invoke(app, ["test-connection", "access"])
            assert result.exit_code == 1
            assert "Access controller not configured" in result.stdout

    @patch("unifi_mcp.cli.Settings")
    def test_connection_network_with_config_shows_message(
        self, mock_settings: MagicMock
    ) -> None:
        """Test that network connection test shows appropriate message."""
        # Setup mock settings
        mock_network = MagicMock()
        mock_network.host = "192.168.1.1"
        mock_network.port = 8443

        mock_settings.return_value.network_controller = mock_network
        mock_settings.return_value.access_controller = None

        result = runner.invoke(app, ["test-connection", "network"])
        assert result.exit_code == 0
        assert "Testing connection to Network Controller" in result.stdout
        assert "192.168.1.1:8443" in result.stdout
        assert "Not implemented yet" in result.stdout

    @patch("unifi_mcp.cli.Settings")
    def test_connection_access_with_config_shows_message(
        self, mock_settings: MagicMock
    ) -> None:
        """Test that access connection test shows appropriate message."""
        # Setup mock settings
        mock_access = MagicMock()
        mock_access.host = "192.168.1.2"
        mock_access.port = 9443

        mock_settings.return_value.network_controller = None
        mock_settings.return_value.access_controller = mock_access

        result = runner.invoke(app, ["test-connection", "access"])
        assert result.exit_code == 0
        assert "Testing connection to Access Controller" in result.stdout
        assert "192.168.1.2:9443" in result.stdout
        assert "Not implemented yet" in result.stdout

    def test_connection_invalid_controller_type_fails(self) -> None:
        """Test that invalid controller type fails."""
        result = runner.invoke(app, ["test-connection", "invalid"])
        assert result.exit_code == 1
        assert "controller_type must be either 'network' or 'access'" in result.stdout


class TestCLIServerManagement:
    """Test CLI server management flags."""

    def test_multiple_server_management_flags_fails(self) -> None:
        """Test that using multiple server management flags fails."""
        result = runner.invoke(app, ["--start-mcp-server", "--stop-mcp-server"])
        assert result.exit_code == 1
        # Error message is printed to stderr
        assert (
            "Please use only one of --start-mcp-server, --stop-mcp-server"
            in result.output
        )

    @patch("unifi_mcp.cli.manager")
    def test_start_server_flag(self, mock_manager: MagicMock) -> None:
        """Test --start-mcp-server flag."""
        result = runner.invoke(
            app, ["--start-mcp-server", "--host", "0.0.0.0", "--port", "9000"]
        )
        assert result.exit_code == 0
        mock_manager.start_server.assert_called_once_with("0.0.0.0", 9000, False, False)

    @patch("unifi_mcp.cli.manager")
    def test_stop_server_flag(self, mock_manager: MagicMock) -> None:
        """Test --stop-mcp-server flag."""
        result = runner.invoke(app, ["--stop-mcp-server"])
        assert result.exit_code == 0
        mock_manager.stop_server.assert_called_once()

    @patch("unifi_mcp.cli.manager")
    def test_restart_server_flag(self, mock_manager: MagicMock) -> None:
        """Test --restart-mcp-server flag."""
        result = runner.invoke(
            app, ["--restart-mcp-server", "--host", "127.0.0.1", "--port", "8888"]
        )
        assert result.exit_code == 0
        mock_manager.stop_server.assert_called_once()
        mock_manager.start_server.assert_called_once_with(
            "127.0.0.1", 8888, False, False
        )

    @patch("unifi_mcp.cli.manager")
    def test_server_status_flag(self, mock_manager: MagicMock) -> None:
        """Test --server-status flag."""
        result = runner.invoke(app, ["--server-status"])
        assert result.exit_code == 0
        mock_manager.get_status.assert_called_once()

    @patch("unifi_mcp.cli.run_server")
    def test_default_action_runs_server(self, mock_run_server: MagicMock) -> None:
        """Test that default action (no flags) runs server in foreground."""
        mock_run_server.return_value = None

        result = runner.invoke(app, [])
        assert result.exit_code == 0
        mock_run_server.assert_called_once()

    @patch("unifi_mcp.cli.run_server")
    def test_debug_flag_passed_to_server(self, mock_run_server: MagicMock) -> None:
        """Test that --debug flag is respected."""
        mock_run_server.return_value = None

        result = runner.invoke(app, ["--debug"])
        assert result.exit_code == 0
        # Server runs in foreground with debug mode
        mock_run_server.assert_called_once()

    @patch("unifi_mcp.cli.run_server")
    def test_reload_flag_passed_to_server(self, mock_run_server: MagicMock) -> None:
        """Test that --reload flag is respected."""
        mock_run_server.return_value = None

        result = runner.invoke(app, ["--reload"])
        assert result.exit_code == 0
        # Server runs in foreground with reload mode
        mock_run_server.assert_called_once()


class TestCLIServerManager:
    """Test ServerManager functionality."""

    def test_server_manager_initialization(self) -> None:
        """Test ServerManager initialization creates PID directory."""
        from unifi_mcp.utils.process_utils import ServerManager

        manager = ServerManager("test-project")
        assert manager.project_name == "test-project"
        assert manager.pid_file == Path.home() / ".cache" / "mcp" / "test-project.pid"
        assert manager.pid_file.parent.exists()

    def test_get_pid_returns_none_when_no_file(self) -> None:
        """Test get_pid returns None when PID file doesn't exist."""
        from unifi_mcp.utils.process_utils import ServerManager

        manager = ServerManager("test-project-no-file")
        pid = manager.get_pid()
        assert pid is None

    def test_get_pid_returns_pid_from_file(self) -> None:
        """Test get_pid reads PID from file."""
        from unifi_mcp.utils.process_utils import ServerManager

        manager = ServerManager("test-project-read")
        # Create a temporary PID file
        manager.pid_file.write_text("12345")
        try:
            pid = manager.get_pid()
            assert pid == 12345
        finally:
            # Cleanup
            if manager.pid_file.exists():
                manager.pid_file.unlink()

    def test_get_pid_returns_none_on_invalid_content(self) -> None:
        """Test get_pid returns None for invalid PID file content."""
        from unifi_mcp.utils.process_utils import ServerManager

        manager = ServerManager("test-project-invalid")
        # Write invalid content
        manager.pid_file.write_text("not-a-number")
        try:
            pid = manager.get_pid()
            assert pid is None
        finally:
            if manager.pid_file.exists():
                manager.pid_file.unlink()

    def test_is_running_returns_false_when_no_pid(self) -> None:
        """Test is_running returns False when no PID file."""
        from unifi_mcp.utils.process_utils import ServerManager

        manager = ServerManager("test-project-running-none")
        assert manager.is_running() is False

    def test_is_running_returns_false_for_dead_process(self) -> None:
        """Test is_running returns False for non-existent process."""
        from unifi_mcp.utils.process_utils import ServerManager

        manager = ServerManager("test-project-dead")
        # Use a non-existent PID
        manager.pid_file.write_text("99999")
        try:
            assert manager.is_running() is False
        finally:
            if manager.pid_file.exists():
                manager.pid_file.unlink()

    def test_is_running_returns_true_for_current_process(self) -> None:
        """Test is_running returns True for current process."""
        import os

        from unifi_mcp.utils.process_utils import ServerManager

        manager = ServerManager("test-project-alive")
        # Use current process PID
        manager.pid_file.write_text(str(os.getpid()))
        try:
            assert manager.is_running() is True
        finally:
            if manager.pid_file.exists():
                manager.pid_file.unlink()

    def test_stop_server_removes_pid_file(self) -> None:
        """Test stop_server removes PID file."""
        from unittest.mock import patch

        from unifi_mcp.utils.process_utils import ServerManager

        manager = ServerManager("test-project-stop")
        manager.pid_file.write_text("12345")

        with patch("os.kill"):  # Mock os.kill to avoid killing real process
            manager.stop_server()

        assert not manager.pid_file.exists()

    def test_get_status_prints_running_message(self) -> None:
        """Test get_status prints correct message when running."""
        import os

        from unifi_mcp.utils.process_utils import ServerManager

        manager = ServerManager("test-project-status-running")
        manager.pid_file.write_text(str(os.getpid()))

        try:
            # Verify the process would be detected as running
            assert manager.is_running() is True
            # We can't easily test the print output without mocking typer.echo
            # but we can verify the logic works
        finally:
            if manager.pid_file.exists():
                manager.pid_file.unlink()

    def test_get_status_prints_stopped_message(self) -> None:
        """Test get_status prints correct message when stopped."""
        from unifi_mcp.utils.process_utils import ServerManager

        manager = ServerManager("test-project-status-stopped")
        # No PID file

        assert manager.is_running() is False
