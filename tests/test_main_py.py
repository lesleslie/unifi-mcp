"""Tests for the main module."""

from unittest.mock import patch

import pytest

from unifi_mcp.main import main


class TestMain:
    """Test main module functions."""

    def test_main(self):
        """Test the main function."""
        # Mock the run_server function
        with patch("unifi_mcp.main.run_server") as mock_run_server:
            # Call the main function
            main()

            # Verify that run_server was called
            mock_run_server.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
