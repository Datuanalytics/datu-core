"""Registry for MCP server configurations."""

from pathlib import Path
from typing import TypedDict

ROOT = Path(__file__).resolve().parent


class MCPServerConfig(TypedDict):
    """Configuration parameters for an MCP server."""

    host: str
    port: int
    script: Path
    path: str
    transport: str


mcp_server_registry: dict[str, MCPServerConfig] = {
    "schema_rag_server": {
        "script": ROOT / "tools" / "schema_rag_server.py",
        "host": "localhost",
        "port": 8001,
        "path": "/mcp/",
        "transport": "streamable_http",
    },
}


def get_server_config(server_name: str) -> dict:
    """Retrieve the configuration for a specific MCP server."""
    cfg = mcp_server_registry[server_name]
    return {
        "host": cfg["host"],
        "port": cfg["port"],
        "path": cfg["path"],
        "transport": cfg["transport"],
    }
