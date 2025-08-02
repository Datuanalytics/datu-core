"""Unit tests for the OpenAI LLM client."""

import pytest
from langchain_core.messages import SystemMessage

from datu.llm_clients import openai_client


@pytest.fixture
def simulate(monkeypatch):
    """Overwritting OpenAI API settings for testing."""
    monkeypatch.setattr(openai_client.settings, "simulate_llm_response", "true")
    monkeypatch.setattr(openai_client.settings, "openai_api_key", "sk-test")
    monkeypatch.setattr(openai_client.settings, "openai_model", "gpt-4o-mini")
    return True


def test_extract_sql_from_text_cases():
    """Test that SQL is extracted correctly with and without code block."""
    test_cases = [
        ("```sql\nSELECT * FROM users;\n```", "SELECT * FROM users;"),
        ("SELECT * FROM users;", "SELECT * FROM users;"),
    ]
    for input_text, expected in test_cases:
        result = openai_client.extract_sql_from_text(input_text)
        assert result == expected


def test_extract_json_from_text_cases():
    """Test that JSON is extracted correctly with and without code block."""
    test_cases = [
        ('```json\n{ "key": "value" }\n```', '{ "key": "value" }'),
        ('{ "key": "value" }', '{ "key": "value" }'),
    ]
    for input_text, expected in test_cases:
        result = openai_client.extract_json_from_text(input_text)
        assert result.strip() == expected


@pytest.mark.usefixtures("simulate")
def test_chat_completion_simulated():
    """Test that the chat completion method returns a simulated response."""
    llm_client = openai_client.OpenAIClient()
    result = llm_client.chat_completion(messages=["Hello"], system_prompt="You are a helpful assistant.")
    assert isinstance(result, str)
    assert "SELECT" in result  # based on create_simulated_llm_response content


def test_chat_completion_raises_on_empty_messages():
    """Ensure ValueError is raised if messages list is empty."""
    llm_client = openai_client.OpenAIClient()
    with pytest.raises(ValueError, match="chat_completion was called with an empty message list"):
        llm_client.chat_completion(messages=[])


def test_chat_completion_raises_on_dict_missing_role():
    """Ensure ValueError is raised if a dict message lacks a 'role' key."""
    llm_client = openai_client.OpenAIClient()
    bad_message = {"content": "Hi, help me out."}
    with pytest.raises(ValueError, match="must have a 'role' key"):
        llm_client.chat_completion(messages=[bad_message])


def test_chat_completion_raises_on_dict_with_non_user_role():
    """Ensure ValueError is raised if a dict message has a non-'user' role."""
    llm_client = openai_client.OpenAIClient()
    bad_message = {"role": "assistant", "content": "Hi, help me out."}
    with pytest.raises(ValueError, match="must have a 'role' key with value 'user'"):
        llm_client.chat_completion(messages=[bad_message])


def test_chat_completion_raises_on_dict_missing_content():
    """Ensure ValueError is raised if a dict message lacks a 'content' key."""
    llm_client = openai_client.OpenAIClient()
    bad_message = {"role": "user"}
    with pytest.raises(ValueError, match="must contain a 'content' key"):
        llm_client.chat_completion(messages=[bad_message])


def test_chat_completion_raises_on_unsupported_message_type():
    """Ensure TypeError is raised if the message is not a dict or HumanMessage."""
    llm_client = openai_client.OpenAIClient()
    with pytest.raises(TypeError, match="Unsupported message type"):
        llm_client.chat_completion(messages=[42])  # Invalid type


def test_chat_completion_raises_on_non_human_base_message():
    """Ensure TypeError is raised if the message is a SystemMessage or other BaseMessage."""
    llm_client = openai_client.OpenAIClient()
    with pytest.raises(TypeError, match="Unsupported message type"):
        llm_client.chat_completion(messages=[SystemMessage(content="Set context.")])


@pytest.mark.usefixtures("simulate")
def test_fix_sql_error(monkeypatch):
    """Test that the fix_sql_error method returns a corrected SQL statement."""
    llm_client = openai_client.OpenAIClient()
    mock_response = """```sql
    SELECT * FROM fixed_table;
    ```"""

    class MockAIMessage:
        """Mock response message with a .content attribute."""

        content = mock_response

    monkeypatch.setattr(type(llm_client.client), "invoke", lambda self, messages: MockAIMessage())
    sql = llm_client.fix_sql_error(
        sql_code="SELECT * FRO fixed_table;", error_msg="syntax error at or near 'FRO'", loop_count=1
    )
    assert isinstance(sql, str)
    assert sql.strip().startswith("SELECT")
    assert "FROM fixed_table" in sql
    assert "```" not in sql  # Confirm that code block markers are stripped


@pytest.mark.usefixtures("simulate")
def test_generate_business_glossary(monkeypatch):
    """Test that the generate_business_glossary method returns a dictionary with definitions."""
    llm_client = openai_client.OpenAIClient()
    mock_response = """```json
    {
        "definition": "A table for sales orders.",
        "columns": {
            "order_id": "Unique ID for the order",
            "amount": "Total order amount"
        }
    }
    ```"""

    class MockAIMessage:
        content = mock_response

    monkeypatch.setattr(type(llm_client.client), "invoke", lambda self, messages: MockAIMessage())
    schema = {"SalesOrders": ["order_id", "amount"]}
    glossary = llm_client.generate_business_glossary(schema)
    assert isinstance(glossary, dict)
    assert glossary["definition"] == "A table for sales orders."
    assert "columns" in glossary
    assert glossary["columns"]["order_id"] == "Unique ID for the order"
