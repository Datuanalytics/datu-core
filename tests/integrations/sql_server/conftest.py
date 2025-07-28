"""Common fixtures for tests in integrations sql_server module ."""

# pylint: disable=redefined-outer-name
import pytest


@pytest.fixture
def mock_config():
    """Fixture to provide a mock DBT target configuration for SQL Server."""

    from datu.integrations.dbt.config import DBTTargetConfig

    return DBTTargetConfig(
        driver="SQL Server",
        host="localhost",
        dbname="test_db",
        user="test_user",
        password="test_password",
        type="sqlserver",
    )


@pytest.fixture
def connector(mock_config):
    """Fixture to provide a SQL Server connector instance."""
    from datu.integrations.sql_server.sqldb_connector import SQLServerConnector

    return SQLServerConnector(config=mock_config)
