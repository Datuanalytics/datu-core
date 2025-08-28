"""Factory function to create an LLM client based on the provider specified in the configuration.
This function returns an instance of the appropriate LLM client class based on the provider.
Currently supported providers are "openai" and "on_prem".
"""

from typing import Literal

from datu.llm_clients.openai_client import OpenAIClient
from datu.telemetry.product.events import MCPClientEvent
from datu.telemetry.product.posthog import get_posthog_client


def get_llm_client(provider: Literal["openai"] | None = None) -> OpenAIClient | None:
    """Fetch an LLM client using structured Pydantic settings
    Args:
        provider (str | None): The name of the LLM provider to use. If None, the default provider is used.

    Returns:
        OpenAIClient | None: An instance of the appropriate LLM client class.

    Raises:
        ValueError: If the specified provider is not supported.
    """
    if provider == "openai":
        openai_client = OpenAIClient()
        if openai_client.agent:
            posthog_client = get_posthog_client()
            if openai_client.mcp_client and getattr(openai_client.mcp_client, "config", None):
                servers = openai_client.mcp_client.config.get("mcpServers", {})
                server_names = list(servers.keys()) if servers else []
            else:
                server_names = []
            posthog_client.capture(MCPClientEvent(server_names=server_names))
        return openai_client
    else:
        raise ValueError("Invalid LLM provider specified in configuration.")
