"""CLI for UniFi MCP server management."""

import typer

from unifi_mcp.config import Settings
from unifi_mcp.server import run_server

app = typer.Typer()


@app.command()
def start(
    host: str = typer.Option("127.0.0.1", help="Host to bind the server to"),
    port: int = typer.Option(8000, help="Port to bind the server to"),
    debug: bool = typer.Option(False, help="Enable debug mode"),
    reload: bool = typer.Option(False, help="Enable auto-reload on file changes"),
) -> None:
    """Start the UniFi MCP server."""
    # Update environment variables with CLI parameters
    import os

    os.environ["MCP_SERVER_HOST"] = host
    os.environ["MCP_SERVER_PORT"] = str(port)
    os.environ["MCP_DEBUG"] = str(debug).lower()
    os.environ["MCP_RELOAD"] = str(reload).lower()

    # Create settings using the updated environment variables
    Settings()

    # Start the server
    typer.echo(f"Starting UniFi MCP server on {host}:{port}")
    if debug:
        typer.echo("Debug mode enabled")
    if reload:
        typer.echo("Auto-reload enabled")

    # Run the server (this will block)

    # In a real implementation, we'd run the server in a thread
    # and provide a way to manage it, but for now we'll just call run_server()
    run_server()


@app.command()
def status() -> None:
    """Check the status of the UniFi MCP server."""
    typer.echo("UniFi MCP server status: Not implemented yet")
    # In a real implementation, this would check if the server is running


@app.command()
def config() -> None:
    """Display current configuration."""
    settings = Settings()
    typer.echo("Current UniFi MCP Server Configuration:")
    typer.echo(f"  Server Host: {settings.server.host}")
    typer.echo(f"  Server Port: {settings.server.port}")
    typer.echo(f"  Debug Mode: {settings.server.debug}")
    typer.echo(f"  Reload Mode: {settings.server.reload}")

    if settings.network_controller:
        typer.echo("  Network Controller: Configured")
        typer.echo(f"    Host: {settings.network_controller.host}")
        typer.echo(f"    Port: {settings.network_controller.port}")
        typer.echo(f"    Site ID: {settings.network_controller.site_id}")
    else:
        typer.echo("  Network Controller: Not configured")

    if settings.access_controller:
        typer.echo("  Access Controller: Configured")
        typer.echo(f"    Host: {settings.access_controller.host}")
        typer.echo(f"    Port: {settings.access_controller.port}")
        typer.echo(f"    Site ID: {settings.access_controller.site_id}")
    else:
        typer.echo("  Access Controller: Not configured")


@app.command()
def test_connection(
    controller_type: str = typer.Argument(
        ..., help="Type of controller to test (network or access)"
    ),
) -> None:
    """Test connection to UniFi controller."""
    settings = Settings()

    if controller_type.lower() == "network":
        if not settings.network_controller:
            typer.echo("Error: Network controller not configured")
            raise typer.Exit(code=1)

        typer.echo(
            f"Testing connection to Network Controller at {settings.network_controller.host}:{settings.network_controller.port}"
        )
        # In a real implementation, this would test the actual connection
        typer.echo("Network controller connection test: Not implemented yet")

    elif controller_type.lower() == "access":
        if not settings.access_controller:
            typer.echo("Error: Access controller not configured")
            raise typer.Exit(code=1)

        typer.echo(
            f"Testing connection to Access Controller at {settings.access_controller.host}:{settings.access_controller.port}"
        )
        # In a real implementation, this would test the actual connection
        typer.echo("Access controller connection test: Not implemented yet")

    else:
        typer.echo("Error: controller_type must be either 'network' or 'access'")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
