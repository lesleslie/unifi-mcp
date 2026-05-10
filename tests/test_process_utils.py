"""Tests for the process_utils module."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import typer

from unifi_mcp.utils.process_utils import ServerManager


class TestServerManagerInit:
    """Test ServerManager initialization."""

    def test_init_creates_pid_file_directory(self, tmp_path):
        """Test that initialization creates the PID file directory."""
        # Mock Path.home to return tmp_path
        with patch("pathlib.Path.home", return_value=tmp_path):
            manager = ServerManager("test-project")
            assert manager.project_name == "test-project"
            assert manager.pid_file == tmp_path / ".cache" / "mcp" / "test-project.pid"
            # Check directory was created
            cache_dir = tmp_path / ".cache" / "mcp"
            assert cache_dir.exists()
            assert cache_dir.is_dir()


class TestGetPid:
    """Test get_pid method."""

    def test_get_pid_returns_none_when_no_file(self, tmp_path):
        """Test get_pid returns None when PID file doesn't exist."""
        manager = ServerManager("test-project")
        manager.pid_file = tmp_path / "nonexistent.pid"

        assert manager.get_pid() is None

    def test_get_pid_returns_valid_pid(self, tmp_path):
        """Test get_pid returns valid PID from file."""
        manager = ServerManager("test-project")
        manager.pid_file = tmp_path / "test.pid"
        manager.pid_file.write_text("12345")

        assert manager.get_pid() == 12345

    def test_get_pid_returns_none_on_invalid_content(self, tmp_path):
        """Test get_pid returns None for invalid PID content."""
        manager = ServerManager("test-project")
        manager.pid_file = tmp_path / "invalid.pid"
        manager.pid_file.write_text("not_a_number")

        assert manager.get_pid() is None

    def test_get_pid_returns_none_on_empty_file(self, tmp_path):
        """Test get_pid returns None for empty file."""
        manager = ServerManager("test-project")
        manager.pid_file = tmp_path / "empty.pid"
        manager.pid_file.write_text("")

        assert manager.get_pid() is None

    def test_get_pid_handles_whitespace(self, tmp_path):
        """Test get_pid handles whitespace in PID file."""
        manager = ServerManager("test-project")
        manager.pid_file = tmp_path / "whitespace.pid"
        manager.pid_file.write_text("  12345  ")

        assert manager.get_pid() == 12345


class TestIsRunning:
    """Test is_running method."""

    def test_is_running_returns_false_when_no_pid(self, tmp_path):
        """Test is_running returns False when no PID file."""
        manager = ServerManager("test-project")
        manager.pid_file = tmp_path / "nonexistent.pid"

        assert manager.is_running() is False

    def test_is_running_returns_false_for_dead_process(self, tmp_path):
        """Test is_running returns False for dead process."""
        manager = ServerManager("test-project")
        manager.pid_file = tmp_path / "dead.pid"
        # Use a PID that doesn't exist
        manager.pid_file.write_text("99999")

        assert manager.is_running() is False

    def test_is_running_returns_true_for_current_process(self, tmp_path):
        """Test is_running returns True for current process."""
        manager = ServerManager("test-project")
        manager.pid_file = tmp_path / "current.pid"
        manager.pid_file.write_text(str(__import__("os").getpid()))

        assert manager.is_running() is True


class TestStartServer:
    """Test start_server method."""

    def test_start_server_when_already_running(self, tmp_path):
        """Test start_server raises when server is already running."""
        manager = ServerManager("test-project")
        manager.pid_file = tmp_path / "test.pid"

        # Mock is_running to return True
        with patch.object(manager, "is_running", return_value=True):
            with pytest.raises(typer.Exit):
                manager.start_server("127.0.0.1", 8000, False, False)

    @patch("subprocess.Popen")
    def test_start_server_creates_process_with_env_vars(self, mock_popen, tmp_path):
        """Test start_server creates process with correct environment."""
        manager = ServerManager("test-project")
        manager.pid_file = tmp_path / "test.pid"

        # Mock process
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        # Mock is_running to return False
        with patch.object(manager, "is_running", return_value=False):
            manager.start_server("192.168.1.1", 9000, True, True)

            # Verify Popen was called
            assert mock_popen.called
            call_args = mock_popen.call_args
            env = call_args[1]["env"]

            # Check environment variables
            assert env["MCP_SERVER_HOST"] == "192.168.1.1"
            assert env["MCP_SERVER_PORT"] == "9000"
            assert env["MCP_DEBUG"] == "true"
            assert env["MCP_RELOAD"] == "true"

    @patch("subprocess.Popen")
    def test_start_server_writes_pid_file(self, mock_popen, tmp_path):
        """Test start_server writes PID to file."""
        manager = ServerManager("test-project")
        manager.pid_file = tmp_path / "test.pid"

        # Mock process
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        with patch.object(manager, "is_running", return_value=False):
            manager.start_server("127.0.0.1", 8000, False, False)

            # Verify PID file was written
            assert manager.pid_file.exists()
            assert manager.pid_file.read_text() == "12345"

    @patch("subprocess.Popen")
    def test_start_server_handles_pid_write_error(self, mock_popen, tmp_path):
        """Test start_server handles PID file write errors."""
        manager = ServerManager("test-project")
        # Make PID file a directory to cause write error
        manager.pid_file = tmp_path / "test.pid"
        manager.pid_file.mkdir()

        # Mock process
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        with patch.object(manager, "is_running", return_value=False):
            with pytest.raises(typer.Exit) as exc_info:
                manager.start_server("127.0.0.1", 8000, False, False)

            assert exc_info.value.exit_code == 1
            # Verify process was killed
            mock_process.kill.assert_called_once()


class TestStopServer:
    """Test stop_server method."""

    def test_stop_server_when_not_running(self, tmp_path, capsys):
        """Test stop_server when server is not running."""
        manager = ServerManager("test-project")
        manager.pid_file = tmp_path / "nonexistent.pid"

        manager.stop_server()

        captured = capsys.readouterr()
        assert "not running" in captured.out.lower()

    def test_stop_server_kills_process(self, tmp_path, capsys):
        """Test stop_server kills running process."""
        manager = ServerManager("test-project")
        manager.pid_file = tmp_path / "test.pid"

        # Use current process PID (safe to kill in test)
        current_pid = __import__("os").getpid()
        manager.pid_file.write_text(str(current_pid))

        # Mock os.kill to avoid actually killing the test process
        with patch("os.kill") as mock_kill:
            manager.stop_server()

            # Verify kill was called (is_running calls os.kill with signal 0, then stop_server calls with SIGTERM)
            assert mock_kill.called
            # Check that SIGTERM was called
            calls = mock_kill.call_args_list
            assert any(call[0][1] == 15 for call in calls)  # 15 = SIGTERM

    def test_stop_server_handles_dead_process(self, tmp_path, capsys):
        """Test stop_server handles already dead process."""
        manager = ServerManager("test-project")
        manager.pid_file = tmp_path / "test.pid"
        manager.pid_file.write_text("99999")  # Non-existent PID

        # This should not raise an error
        # The PID file exists but process is not running, so is_running will return False
        # and stop_server will print "not running" and return early
        manager.stop_server()

        captured = capsys.readouterr()
        assert "not running" in captured.out.lower()
        # PID file still exists because we returned early
        assert manager.pid_file.exists()

    def test_stop_server_removes_pid_file(self, tmp_path):
        """Test stop_server removes PID file."""
        manager = ServerManager("test-project")
        manager.pid_file = tmp_path / "test.pid"
        manager.pid_file.write_text("12345")

        with patch("os.kill"):
            manager.stop_server()

            # Verify PID file was removed
            assert not manager.pid_file.exists()


class TestGetStatus:
    """Test get_status method."""

    def test_get_status_when_running(self, tmp_path, capsys):
        """Test get_status shows running message."""
        manager = ServerManager("test-project")
        manager.pid_file = tmp_path / "test.pid"
        current_pid = __import__("os").getpid()
        manager.pid_file.write_text(str(current_pid))

        manager.get_status()

        captured = capsys.readouterr()
        assert "running" in captured.out.lower()
        assert str(current_pid) in captured.out

    def test_get_status_when_stopped(self, tmp_path, capsys):
        """Test get_status shows stopped message."""
        manager = ServerManager("test-project")
        manager.pid_file = tmp_path / "nonexistent.pid"

        manager.get_status()

        captured = capsys.readouterr()
        assert "stopped" in captured.out.lower()
