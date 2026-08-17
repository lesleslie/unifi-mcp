"""CI guard: ensure __version__ matches pyproject.toml distribution version."""

from importlib.metadata import version

from unifi_mcp import __version__


def test_version_sync() -> None:
    """Guard against __version__ drifting from pyproject.toml."""
    dist_version = version("unifi-mcp")
    assert __version__ == dist_version, (
        f"__version__ ({__version__}) drifted from pyproject ({dist_version})"
    )