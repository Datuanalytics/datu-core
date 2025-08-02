"""Client module for interacting with MCP servers."""

from contextlib import asynccontextmanager
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

from datu.mcp.registry import MCPServerConfig, mcp_server_registry

ROOT = Path(__file__).resolve().parents[0]
string_root = str(ROOT)


def get_server_url(cfg: MCPServerConfig) -> str:
    """Construct the URL for the MCP server based on its configuration."""
    return f"http://{cfg['host']}:{cfg['port']}{cfg['path']}"


mcp_server_urls = {
    name: {
        "url": get_server_url(cfg),
        "transport": cfg["transport"],
    }
    for name, cfg in mcp_server_registry.items()
}

_client = MultiServerMCPClient(mcp_server_urls)


def print_root() -> None:
    print("ROOT: ", string_root)


def build_mcp_client(server_registry: dict[str, MCPServerConfig] = mcp_server_registry):
    """Build a MultiServerMCPClient with a server registry as input."""
    return MultiServerMCPClient(server_registry)


def get_server_names() -> list[str]:
    """Get the names of all registered MCP servers."""
    return list(mcp_server_registry.keys())


def normalize_tool_args(args: dict) -> dict:
    """Normalize tool arguments for consistent processing."""

    def normalize(value):
        if isinstance(value, list) and all(isinstance(x, str) for x in value):
            return " ".join(value)
        return value

    return {k: normalize(v) for k, v in args.items()}


@asynccontextmanager
async def tool_session(tool_name: str):
    """Context manager to create a session for a specific MCP tool."""
    for server_name in mcp_server_registry:
        async with _client.session(server_name) as session:
            tools = await load_mcp_tools(session)
            match = next((tool for tool in tools if tool.name == tool_name), None)
            if match:
                yield match
                return
    raise ValueError(f"Tool '{tool_name}' not found")
