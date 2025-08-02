"""Unit tests for the BaseDBConnector class."""

# pylint: disable=redefined-outer-name

import pytest

from datu.base.base_connector import BaseDBConnector, SchemaInfo, TableInfo
from datu.integrations.dbt.config import DBTTargetConfig


class MockDBConnector(BaseDBConnector):
    """Mock implementation of BaseDBConnector for testing purposes."""

    def connect(self):
        """Mock connection method."""
        return "Connected"

    def fetch_schema(self, schema_name: str) -> list[SchemaInfo]:
        """Mock schema fetching method."""
        return [
            SchemaInfo(
                schema_name=schema_name,
                table_name="test_table",
                columns=[
                    TableInfo(column_name="id", data_type="int", description="Primary key"),
                    TableInfo(column_name="name", data_type="varchar", description="Name of the entity"),
                ],
            )
        ]

    def run_transformation(self, sql_code: str, test_mode: bool = False) -> dict:
        """Mock transformation execution method."""
        return {"status": "success", "rows_affected": 10}

    def preview_sql(self, sql_code: str, limit: int = 10) -> list:
        """Mock SQL preview method."""
        return [{"id": 1, "name": "Test"}]

    def ensure_schema_exists(self, schema_name: str) -> None:
        pass

    def create_view(self, sql_code: str, view_name: str) -> dict:
        """Mock view creation method."""
        return {"status": "success", "view_name": view_name}

    def sample_table(self, table_name: str, limit: int) -> list[dict]:
        return [{"dummy_column": "dummy_value"}]


@pytest.fixture(scope="module")
def mock_connector():
    """Fixture to provide a mock DB connector for testing."""
    config = DBTTargetConfig(
        type="postgres",
        host="localhost",
        user="user",
        password="password",
        dbname="test_db",
        schema="public",
    )
    return MockDBConnector(config)


def test_connect(mock_connector):
    """Test the connection method of the mock connector."""
    assert mock_connector.connect() == "Connected"


def test_fetch_schema(mock_connector):
    """Test the fetch_schema method of the mock connector."""
    schema_info = mock_connector.fetch_schema("public")
    assert len(schema_info) == 1
    assert schema_info[0].schema_name == "public"
    assert schema_info[0].table_name == "test_table"
    assert len(schema_info[0].columns) == 2
    assert schema_info[0].columns[0].column_name == "id"


def test_run_transformation(mock_connector):
    """Test the run_transformation method of the mock connector."""
    result = mock_connector.run_transformation("SELECT * FROM test_table")
    assert result["status"] == "success"
    assert result["rows_affected"] == 10


def test_preview_sql(mock_connector):
    """Test the preview_sql method of the mock connector."""
    result = mock_connector.preview_sql("SELECT * FROM test_table", limit=5)
    assert len(result) == 1
    assert result[0]["id"] == 1
    assert result[0]["name"] == "Test"


def test_ensure_schema_exists(mock_connector):
    """Test the ensure_schema_exists method of the mock connector."""
    # Ensure no exceptions are raised
    mock_connector.ensure_schema_exists("public")


def test_create_view(mock_connector):
    """Test the create_view method of the mock connector."""
    result = mock_connector.create_view("SELECT * FROM test_table", "test_view")
    assert result["status"] == "success"
    assert result["view_name"] == "test_view"
