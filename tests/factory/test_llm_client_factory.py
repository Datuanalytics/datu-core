"""Unit tests for the LLM client factory module."""

# pylint: disable=import-outside-toplevel
import pytest


def test_get_llm_client_openai():
    """Test that get_llm_client returns an OpenAIClient instance when provider is 'openai'."""
    from datu.factory.llm_client_factory import get_llm_client
    from datu.llm_clients.openai_client import OpenAIClient

    client = get_llm_client(provider="openai")
    assert isinstance(client, OpenAIClient)


def test_get_llm_client_invalid_provider():
    """Test that get_llm_client raises a ValueError for an invalid provider."""
    from datu.factory.llm_client_factory import get_llm_client

    with pytest.raises(ValueError, match="Invalid LLM provider specified in configuration."):
        get_llm_client(provider="invalid_provider")


def test_get_llm_client_no_provider():
    """Test that get_llm_client raises a ValueError when no provider is specified."""
    from datu.factory.llm_client_factory import get_llm_client

    with pytest.raises(ValueError, match="Invalid LLM provider specified in configuration."):
        get_llm_client(provider=None)
