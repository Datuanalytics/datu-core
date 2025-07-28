from unittest.mock import MagicMock, patch


@patch("pyodbc.connect")
def test_connect(mock_connect, connector):
    """Test the connection method of the SQLServerConnector."""
    connector.connect()
    mock_connect.assert_called_once_with(
        "DRIVER=SQL Server;SERVER=localhost;DATABASE=test_db;UID=test_user;"
        "PWD=test_password;TrustServerCertificate=yes;"
    )


@patch("pyodbc.connect")
def test_fetch_schema(mock_connect, connector):
    """Test the fetch_schema method of the SQLServerConnector."""
    mock_cursor = MagicMock()
    mock_connect.return_value.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.side_effect = [
        [("table1",), ("table2",)],
        [("col1", "int"), ("col2", "varchar")],
        [("col1", "int"), ("col2", "varchar")],
    ]

    schema_name = "test_schema"
    result = connector.fetch_schema(schema_name)

    assert len(result) == 2
    assert result[0].table_name == "table1"
    assert result[1].table_name == "table2"
    mock_cursor.execute.assert_any_call(
        """
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = ?
            ORDER BY TABLE_NAME;
        """,
        (schema_name,),
    )


@patch("pyodbc.connect")
def test_run_transformation(mock_connect, connector):
    """Test the run_transformation method of the SQLServerConnector."""
    mock_cursor = MagicMock()
    mock_connect.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    sql_code = "UPDATE test_table SET col1 = 1"
    result = connector.run_transformation(sql_code)

    assert result["success"] is True
    mock_cursor.execute.assert_called_once_with(sql_code)


@patch("pyodbc.connect")
def test_preview_sql(mock_connect, connector):
    """Test the preview_sql method of the SQLServerConnector."""
    mock_cursor = MagicMock()
    mock_connect.return_value.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.description = [("col1",), ("col2",)]
    mock_cursor.fetchall.return_value = [(1, "value1"), (2, "value2")]

    sql_code = "SELECT * FROM test_table"
    result = connector.preview_sql(sql_code, limit=2)

    assert len(result) == 2
    assert result[0] == {"col1": 1, "col2": "value1"}
    mock_cursor.execute.assert_called_once_with("SELECT * FROM (SELECT * FROM test_table) as subquery LIMIT 2;")


@patch("pyodbc.connect")
def test_ensure_schema_exists(mock_connect, connector):
    """Test the ensure_schema_exists method of the SQLServerConnector."""
    mock_cursor = MagicMock()
    mock_connect.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    schema_name = "test_schema"
    connector.ensure_schema_exists(schema_name)

    mock_cursor.execute.assert_called_once_with('CREATE SCHEMA IF NOT EXISTS "test_schema";')


@patch("pyodbc.connect")
def test_create_view(mock_connect, connector):
    """Test the create_view method of the SQLServerConnector."""
    mock_cursor = MagicMock()
    mock_connect.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    sql_code = "SELECT * FROM test_table"
    view_name = "test_schema.test_view"
    result = connector.create_view(sql_code, view_name)

    assert result["success"] is True
    mock_cursor.execute.assert_any_call('CREATE OR REPLACE VIEW "test_schema"."test_view" AS SELECT * FROM test_table;')


@patch("pyodbc.connect")
def test_sample_table_success(mock_connect, connector):
    """Test sampling of rows from a SQL Server table."""
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
    mock_connect.return_value = mock_conn

    mock_cursor.description = [("col1",), ("col2",)]
    mock_cursor.fetchall.return_value = [
        ("value1", 123),
        ("value2", 456),
    ]

    result = connector.sample_table("test_table", limit=2)

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0] == {"col1": "value1", "col2": 123}
    assert result[1] == {"col1": "value2", "col2": 456}
