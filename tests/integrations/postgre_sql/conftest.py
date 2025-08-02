"""Common fixtures for tests in integrations postgre module."""

# pylint: disable=redefined-outer-name disable=unused-import disable=import-outside-toplevel
import pytest


@pytest.fixture(scope="module")
def mock_config():
    """Fixture to provide a mock DBT target configuration."""
    from datu.integrations.dbt.config import DBTTargetConfig

    return DBTTargetConfig(
        type="postgres",
        host="localhost",
        port=5432,
        user="test_user",
        password="test_password",
        dbname="test_db",
    )


@pytest.fixture(scope="module")
def connector(mock_config):
    """Fixture to provide a PostgreSQL connector instance."""
    from datu.integrations.postgre_sql.postgre_connector import PostgreSQLConnector

    return PostgreSQLConnector(config=mock_config)
