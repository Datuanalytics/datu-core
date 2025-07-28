"""Test cases for metadata-related endpoints in metadata.py.
This module contains test cases to ensure the functionality of the metadata endpoints,
including schema introspection and error handling.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient


def test_get_schema_success(client: TestClient) -> None:
    """Test the /schema endpoint for successful schema introspection.
    Verifies that the endpoint returns a list of SchemaGlossary objects.
    Args:
        client (TestClient): The FastAPI test client fixture.
    """
    mock_schema = [
        {
            "timestamp": 1680000000.0,
            "profile_name": "default",
            "output_name": "dev",
            "db_type": "postgres",
            "schema_info": [
                {
                    "schema_name": "public",
                    "table_name": "users",
                    "columns": [
                        {
                            "column_name": "id",
                            "data_type": "integer",
                            "description": None,
                            "categorical": None,
                            "values": None,
                        },
                        {
                            "column_name": "name",
                            "data_type": "text",
                            "description": None,
                            "categorical": None,
                            "values": None,
                        },
                    ],
                }
            ],
        }
    ]

    with patch("datu.routers.metadata.SchemaExtractor.extract_all_schemas", return_value=mock_schema):
        response = client.get("/api/metadata/schema")

    assert response.status_code == 200
    assert response.json() == mock_schema


def test_get_schema_not_found(client: TestClient) -> None:
    """Test the /schema endpoint when no schema is found.
    Verifies that the endpoint returns a 404 status code with an appropriate error message.
    Args:
        client (TestClient): The FastAPI test client fixture.
    """
    with patch("datu.routers.metadata.SchemaExtractor.extract_all_schemas", return_value=[]):
        response = client.get("/api/metadata/schema")

    assert response.status_code == 404
    assert response.json() == {"detail": "Schema not found"}
