"""Test cases for the chat endpoint in chat.py.
This module contains test cases to ensure the functionality of the chat endpoint,
including SQL extraction, validation, and response generation.
"""

# pylint: disable=import-outside-toplevel
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def test_estimate_query_complexity() -> None:
    """Test the estimate_query_complexity function for calculating query complexity."""
    from datu.routers.chat import estimate_query_complexity

    test_cases = [
        ("SELECT * FROM users;", 1),
        (
            "SELECT u.name, o.amount FROM users u JOIN orders o ON u.id = o.user_id;",
            6,  # 2 (tables) + 4 (join)
        ),
        (
            "SELECT region, SUM(sales) FROM sales GROUP BY region;",
            4,  # 1 (table) + 3 (group by)
        ),
        (
            "SELECT u.name FROM users u ORDER BY name;",
            3,  # 1 (table) + 2 (order by)
        ),
        (
            "SELECT u.name, o.amount FROM users u JOIN orders o ON u.id = o.user_id GROUP BY u.name ORDER BY o.amount;",
            11,  # 2 (tables) + 4 (join) + 3 (group by) + 2 (order by)
        ),
    ]

    for query, expected_complexity in test_cases:
        assert estimate_query_complexity(query) == expected_complexity


def test_get_query_execution_time_estimate() -> None:
    """Test the get_query_execution_time_estimate function for mapping complexity to execution time."""
    from datu.routers.chat import get_query_execution_time_estimate

    # Test cases with expected execution time estimates
    test_cases = [
        (3, "Fast (less than a second)"),  # Complexity <= 5
        (7, "Moderate (a few seconds)"),  # Complexity <= 10
        (15, "Slow (several seconds to a minute)"),  # Complexity <= 20
        (25, "Very Slow (may take minutes or more)"),  # Complexity > 20
    ]

    for complexity, expected_time in test_cases:
        assert get_query_execution_time_estimate(complexity) == expected_time


def test_extract_sql_blocks() -> None:
    """Test the extract_sql_blocks function for extracting SQL code blocks.
    Verifies that SQL blocks are correctly extracted with titles and content.
    """
    from datu.routers.chat import extract_sql_blocks  # pylint: disable=import-outside-toplevel

    input_text = (
        "Query name: Get Users\n```sql\nSELECT * FROM users;\n```\n"
        "Query name: Get Orders\n```sql\nSELECT * FROM orders;\n```"
    )
    expected_output = [
        {"title": "Get Users", "sql": "SELECT * FROM users;"},
        {"title": "Get Orders", "sql": "SELECT * FROM orders;"},
    ]
    assert extract_sql_blocks(input_text) == expected_output


def test_validate_and_fix_sql() -> None:
    """Test the validate_and_fix_sql function for validating and fixing SQL code.
    Verifies that SQL code blocks are validated and fixed correctly.
    """
    from datu.routers.chat import validate_and_fix_sql  # pylint: disable=import-outside-toplevel

    response_text = """```sql\nSELECT * FROM invalid_table;\n```"""
    fixed_sql = "SELECT * FROM valid_table;"

    mock_connector = MagicMock()
    mock_connector.run_transformation.side_effect = [RuntimeError("Table not found"), None]

    with patch("datu.routers.chat.DBConnectorFactory.get_connector", return_value=mock_connector):
        with patch("datu.routers.chat.fix_sql_error", return_value=fixed_sql):
            fixed_response = validate_and_fix_sql(response_text)

    assert "```sql\nSELECT * FROM valid_table;\n```" in fixed_response


def test_validate_and_fix_sql_failure_message() -> None:
    """Test the 'else' block: When SQL can't be fixed, user-friendly failure message is returned."""

    from datu.routers.chat import validate_and_fix_sql  # pylint: disable=import-outside-toplevel

    response_text = """```sql\nSELECT * FROM invalid_table;\n```"""
    mock_connector = MagicMock()
    mock_connector.run_transformation.side_effect = RuntimeError("Table not found")

    with patch("datu.routers.chat.DBConnectorFactory.get_connector", return_value=mock_connector):
        with patch("datu.routers.chat.fix_sql_error", return_value=None):
            fixed_response = validate_and_fix_sql(response_text)

    assert "Sorry, it seems that I can't get an answer to your question" in fixed_response
    assert "```sql\n-- FAILED TO RUN\nSELECT * FROM invalid_table;\n```" in fixed_response


@pytest.mark.requires_service
def test_chat_with_llm(client: TestClient) -> None:
    """Test the chat_with_llm endpoint for generating SQL queries.
    Verifies that the endpoint processes requests and returns valid responses.
    Args:
        client (TestClient): The FastAPI test client fixture.
    """
    from datu.routers.chat import ChatMessage, ChatRequest  # pylint: disable=import-outside-toplevel

    mock_request = ChatRequest(
        messages=[ChatMessage(role="user", content="Get all users")],
        system_prompt="You are a helpful assistant that generates SQL queries based on user requests.",
    )

    # from datu.integrations.dbt.config import get_dbt_profiles_settings

    # print("DBTProfilesSettings", get_dbt_profiles_settings())

    mock_response = """Query name: Get Users\n```sql\nSELECT * FROM users;\n```"""

    with patch("datu.routers.chat.generate_response", return_value=mock_response):
        with patch("datu.routers.chat.validate_and_fix_sql", return_value=mock_response):
            response = client.post("/api/chat/", json=mock_request.model_dump())

    assert response.status_code == 200
    assert "assistant_response" in response.json()
    assert "queries" in response.json()
    assert len(response.json()["queries"]) == 1
    assert response.json()["queries"][0]["title"] == "Get Users"


@pytest.mark.requires_service
def test_chat_with_llm_return_format(client: TestClient) -> None:
    """Test the chat_with_llm endpoint to ensure the return format is correct.
    Verifies that the response contains the expected keys and structure.
    Args:
        client (TestClient): The FastAPI test client fixture.
    """
    from datu.routers.chat import ChatMessage, ChatRequest  # pylint: disable=import-outside-toplevel

    # Mock request
    mock_request = ChatRequest(
        messages=[ChatMessage(role="user", content="Get all users")],
        system_prompt="You are a helpful assistant that generates SQL queries based on user requests.",
    )

    # Mock response
    mock_response = """Query name: Get Users\n```sql\nSELECT * FROM users;\n```"""

    with patch("datu.routers.chat.generate_response", return_value=mock_response):
        with patch("datu.routers.chat.validate_and_fix_sql", return_value=mock_response):
            response = client.post("/api/chat/", json=mock_request.model_dump())

    assert response.status_code == 200

    response_json = response.json()

    assert "assistant_response" in response_json
    assert "queries" in response_json
    assert isinstance(response_json["assistant_response"], str)
    assert isinstance(response_json["queries"], list)

    for query in response_json["queries"]:
        assert "title" in query
        assert "sql" in query
        assert "complexity" in query
        assert "execution_time_estimate" in query
        assert isinstance(query["title"], str)
        assert isinstance(query["sql"], str)
        assert isinstance(query["complexity"], int)
        assert isinstance(query["execution_time_estimate"], str)


def test_validate_and_fix_sql_rejects_dml_ddl_operations() -> None:
    """Test that validate_and_fix_sql rejects DML and DDL operations in SQL queries."""
    from datu.routers.chat import validate_and_fix_sql  # pylint: disable=import-outside-toplevel

    response_text = (
        "```sql\nINSERT INTO users (id, name) VALUES (1, 'Alice');\n```"
        "```sql\nDROP TABLE users;\n```"
        "```sql\nDELETE FROM users WHERE id = 1;\n```"
        "```sql\nUPDATE users SET name = 'Bob' WHERE id = 1;\n```"
    )

    expected_output = (
        "```sql\n-- Rejected due to unsafe SQL operation.\nINSERT INTO users (id, name) VALUES (1, 'Alice');\n```"
        "```sql\n-- Rejected due to unsafe SQL operation.\nDROP TABLE users;\n```"
        "```sql\n-- Rejected due to unsafe SQL operation.\nDELETE FROM users WHERE id = 1;\n```"
        "```sql\n-- Rejected due to unsafe SQL operation.\nUPDATE users SET name = 'Bob' WHERE id = 1;\n```"
    )

    fixed_response = validate_and_fix_sql(response_text)
    assert fixed_response == expected_output
