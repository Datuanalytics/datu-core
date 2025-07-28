"""Unit tests for postgreSQL connector."""

# pylint: disable=redefined-outer-name disable=unused-argument disable=import-outside-toplevel
from unittest.mock import MagicMock, patch

import pytest
from psycopg2 import OperationalError


@patch("psycopg2.connect")
def test_connect_success(mock_connect, connector):
    """Test successful connection to PostgreSQL database."""
    mock_connect.return_value = MagicMock()
    conn = connector.connect()
    assert conn is not None
    mock_connect.assert_called_once_with(
        host="localhost",
        port=5432,
        user="test_user",
        password="test_password",
        dbname="test_db",
        sslmode="disable",
    )


@patch("psycopg2.connect", side_effect=OperationalError("Connection failed"))
def test_connect_failure(mock_connect, connector):
    """Test connection failure to PostgreSQL database."""
    with pytest.raises(OperationalError):
        connector.connect()


@patch("psycopg2.connect")
def test_fetch_schema(mock_connect, connector):
    """Test fetching schema information from PostgreSQL database."""
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
    mock_connect.return_value = mock_conn

    mock_cursor.fetchall.side_effect = [
        [("table1",), ("table2",)],
        [("col1", "text"), ("col2", "integer")],
        [("col1", "varchar"), ("col2", "boolean")],
    ]

    schema_info = connector.fetch_schema("public")
    assert len(schema_info) == 2
    assert schema_info[0].table_name == "table1"
    assert schema_info[1].table_name == "table2"


@patch("psycopg2.connect")
def test_run_transformation_success(mock_connect, connector):
    """Test successful execution of a transformation in PostgreSQL database."""
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
    mock_connect.return_value = mock_conn

    mock_cursor.rowcount = 5
    result = connector.run_transformation("UPDATE table SET col = 1")

    assert result["success"] is True
    assert result["row_count"] == 5
    mock_conn.commit.assert_called_once()


@patch("psycopg2.connect")
def test_run_transformation_failure(mock_connect, connector):
    """Test failure during execution of a transformation in PostgreSQL database."""
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
    mock_connect.return_value = mock_conn

    mock_cursor.execute.side_effect = OperationalError("SQL error")
    with pytest.raises(OperationalError):
        connector.run_transformation("INVALID SQL")

    mock_conn.rollback.assert_called_once()


@patch("psycopg2.connect")
def test_preview_sql(mock_connect, connector):
    """Test previewing SQL results from PostgreSQL database."""
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
    mock_connect.return_value = mock_conn

    mock_cursor.description = [("col1",), ("col2",)]
    mock_cursor.fetchall.return_value = [("val1", "val2"), ("val3", "val4")]

    result = connector.preview_sql("SELECT * FROM table", limit=2)
    assert len(result) == 2
    assert result[0] == {"col1": "val1", "col2": "val2"}
    assert result[1] == {"col1": "val3", "col2": "val4"}


@patch("psycopg2.connect")
def test_ensure_schema_exists(mock_connect, connector):
    """Test ensuring a schema exists in PostgreSQL database."""
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn

    connector.ensure_schema_exists("test_schema")
    mock_conn.cursor.return_value.__enter__.return_value.execute.assert_called_once_with(
        'CREATE SCHEMA IF NOT EXISTS "test_schema";'
    )
    mock_conn.commit.assert_called_once()


@patch("psycopg2.connect")
def test_create_view_success(mock_connect, connector):
    """Test successful creation of a view in PostgreSQL database."""
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn

    with patch.object(connector, "ensure_schema_exists") as mock_ensure_schema:
        result = connector.create_view("SELECT * FROM table", "public.view_name")
        assert result["success"] is True
        mock_ensure_schema.assert_called_once_with(schema_name="public")
        mock_conn.cursor.return_value.__enter__.return_value.execute.assert_called_once_with(
            'CREATE OR REPLACE VIEW "public"."view_name" AS SELECT * FROM table;'
        )
        mock_conn.commit.assert_called_once()


@patch("psycopg2.connect")
def test_create_view_failure(mock_connect, connector):
    """Test failure during creation of a view in PostgreSQL database."""
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
    mock_connect.return_value = mock_conn

    mock_cursor.execute.side_effect = OperationalError("View creation error")
    with patch.object(connector, "ensure_schema_exists"):
        result = connector.create_view("SELECT * FROM table", "public.view_name")
        assert result["success"] is False
        assert "error" in result
        mock_conn.rollback.assert_called_once()


@patch("psycopg2.connect")
def test_sample_table_success(mock_connect, connector):
    """Test successful sampling of a from a PostgreSQL table."""
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
    mock_connect.return_value = mock_conn
    mock_cursor.description = [("col1",), ("col2",)]
    mock_cursor.fetchall.return_value = [
        ("value1", 123),
        ("value2", 456),
    ]
    connector.config.database_schema = "test_schema"
    result = connector.sample_table("test_table", limit=2)
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0] == {"col1": "value1", "col2": 123}
    assert result[1] == {"col1": "value2", "col2": 456}
