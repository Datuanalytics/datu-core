"""Factory function to create an LLM client based on the provider specified in the configuration.
This function returns an instance of the appropriate LLM client class based on the provider.
Currently supported providers are "openai" and "on_prem".
"""

from typing import Literal

from datu.llm_clients.openai_client import OpenAIClient


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
        return OpenAIClient()
    else:
        raise ValueError("Invalid LLM provider specified in configuration.")
