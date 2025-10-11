# UniFi MCP Server - Project Context

## Overview

The UniFi MCP Server is a Python-based Model Context Protocol (MCP) server designed to interface with UniFi Network and Access controllers. It enables external systems to interact with UniFi infrastructure through a standardized MCP interface, providing tools for device management, site configuration, user management, and more.

## Project Structure

```
unifi_mcp/
├── __init__.py           # Package initialization and exports
├── __main__.py           # Main entry point for module execution
├── main.py               # Application entry point
├── server.py             # FastMCP server implementation
├── config.py             # Configuration management with Pydantic models
├── cli.py                # Typer-based CLI for server management
├── clients/              # API clients for UniFi controllers
│   ├── base_client.py    # Base HTTP client with authentication
│   ├── network_client.py # UniFi Network Controller API client
│   └── access_client.py  # UniFi Access Controller API client
├── models/               # Data models for UniFi entities
│   ├── network.py        # Network controller data models
│   └── access.py         # Access controller data models
├── tools/                # MCP tools for UniFi operations
│   ├── network_tools.py  # Network-specific tools
│   └── access_tools.py   # Access-specific tools
├── utils/                # Utility functions
│   └── retry_utils.py    # Retry logic with exponential backoff
└── monitoring/           # Monitoring utilities (empty directory)
```

## Core Components

### Configuration Management

- Uses Pydantic with Pydantic Settings for type-safe configuration
- Supports configuration via environment variables and pyproject.toml
- Separate settings for Network Controller, Access Controller, and server configuration

### API Clients

- **BaseClient**: Abstract base class with connection pooling, authentication management, and request handling
- **NetworkClient**: Implementation for UniFi Network Controller API with endpoints for sites, devices, clients, and WLANs
- **AccessClient**: Implementation for UniFi Access Controller API with endpoints for access points, users, and door access

### MCP Tools

The server exposes various tools through the MCP protocol:

- Network operations: site management, device control, client information, WLAN configuration
- Access operations: access point management, user management, door access control
- Device operations: restart, enable/disable access points, get statistics

### Server Architecture

- Built on FastMCP framework for MCP protocol compliance
- Async/await implementation for efficient performance
- Modular design with clear separation of concerns
- Comprehensive error handling and retry mechanisms

## Dependencies

The project requires:

- fastmcp: Core MCP framework
- httpx: Async HTTP client for API interactions
- pydantic: Data validation and settings management
- pydantic-settings: Configuration management
- typer: CLI interface creation

## Building and Running

### Installation

```bash
pip install -r requirements.txt
# Or if using pyproject.toml
pip install uv && uv sync
pip install -e .
```

### Configuration

Configure via environment variables:

```bash
# Server configuration
MCP_SERVER_HOST=127.0.0.1
MCP_SERVER_PORT=8000
MCP_DEBUG=true

# Network Controller
UNIFI__NETWORK_CONTROLLER__HOST=unifi.example.com
UNIFI__NETWORK_CONTROLLER__PORT=8443
UNIFI__NETWORK_CONTROLLER__USERNAME=admin
UNIFI__NETWORK_CONTROLLER__PASSWORD=password

# Access Controller
UNIFI__ACCESS_CONTROLLER__HOST=unifi-access.example.com
UNIFI__ACCESS_CONTROLLER__PORT=8444
UNIFI__ACCESS_CONTROLLER__USERNAME=admin
UNIFI__ACCESS_CONTROLLER__PASSWORD=password
```

### Running the Server

```bash
# Using the CLI
python -m unifi_mcp start --host 127.0.0.1 --port 8000

# Or directly
python -c "from unifi_mcp.main import main; main()"
```

### CLI Commands

- `start`: Start the server with optional host, port, debug, and reload flags
- `config`: Display current configuration
- `status`: Check server status
- `test-connection`: Test connection to controllers

## Development

- Code follows Python async/await patterns for efficient API interactions
- Uses type hints for better IDE support and code maintainability
- Separate modules for clients, models, and tools for clear organization
- Comprehensive error handling and authentication management

## Testing

Run the test script to verify connections:

```bash
python tests/test_unifi_mcp.py
```

## Security Considerations

- Store credentials securely and never commit them to version control
- Use appropriate firewall rules to restrict access to the MCP server
- Enable SSL/TLS if the server is exposed to untrusted networks
- Regularly update dependencies to address security vulnerabilities
