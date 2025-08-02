"""Unit tests for the BaseDBConnector class."""

# pylint: disable=redefined-outer-name
import pytest

from datu.base.llm_client import BaseLLMClient


class MockLLMClient(BaseLLMClient):
    """Mock implementation of BaseLLMClient for testing purposes."""

    def chat_completion(self, messages: list, system_prompt: str | None = None) -> str:
        """Mock chat completion method."""
        return "Mock response"

    def fix_sql_error(self, sql_code: str, error_msg: str, loop_count: int) -> str:
        """Mock SQL error fixing method."""
        return "Corrected SQL query"

    def generate_business_glossary(self, schema_info: dict) -> dict:
        """Mock business glossary generation method."""
        return {
            "table_name": {"description": "Mock description", "columns": {"column_name": "Mock column description"}}
        }


@pytest.fixture
def mock_llm_client():
    """Fixture to provide a mock LLM client for testing."""
    return MockLLMClient()


def test_chat_completion(mock_llm_client):
    """Test the chat_completion method of the mock LLM client."""
    messages = [{"role": "user", "content": "Hello"}]
    response = mock_llm_client.chat_completion(messages)
    assert response == "Mock response"


def test_fix_sql_error(mock_llm_client):
    """Test the fix_sql_error method of the mock LLM client."""
    sql_code = "SELECT * FROM non_existing_table"
    error_msg = "Table does not exist"
    response = mock_llm_client.fix_sql_error(sql_code, error_msg, loop_count=1)
    assert response == "Corrected SQL query"


def test_generate_business_glossary(mock_llm_client):
    """Test the generate_business_glossary method of the mock LLM client."""
    schema_info = {"table_name": {"columns": ["column_name"]}}
    response = mock_llm_client.generate_business_glossary(schema_info)
    assert "table_name" in response
    assert "description" in response["table_name"]
    assert "columns" in response["table_name"]
    assert "column_name" in response["table_name"]["columns"]
