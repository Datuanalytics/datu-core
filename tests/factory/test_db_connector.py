"""Unit tests for the BaseDBConnector class."""

# pylint: disable=redefined-outer-name disable=unused-import disable=import-outside-toplevel disable=unused-argument
from unittest.mock import patch

import pytest


def test_get_connector_postgres(clear_dbt_settings_cache):
    """Test the DBConnectorFactory for PostgreSQL connector."""
    from datu.factory.db_connector import DBConnectorFactory
    from datu.integrations.dbt.config import DBTProfile, DBTProfilesSettings, DBTTargetConfig

    with patch("datu.factory.db_connector.get_dbt_profiles_settings") as mock_get_settings:
        target_config = DBTTargetConfig(type="postgres", host="localhost", dbname="test_db")
        profile = DBTProfile(target="dev", outputs={"dev": target_config})
        mock_settings = DBTProfilesSettings(profiles={"default": profile})

        mock_get_settings.return_value = mock_settings

        connector = DBConnectorFactory.get_connector()

        from datu.integrations.postgre_sql.postgre_connector import PostgreSQLConnector

        assert isinstance(connector, PostgreSQLConnector)


def test_get_connector_sqlserver(clear_dbt_settings_cache):
    """Test the DBConnectorFactory for SQL Server connector."""
    from datu.factory.db_connector import DBConnectorFactory
    from datu.integrations.dbt.config import DBTProfile, DBTProfilesSettings, DBTTargetConfig

    with patch("datu.factory.db_connector.get_dbt_profiles_settings") as mock_get_settings:
        target_config = DBTTargetConfig(type="sqlserver", host="localhost", dbname="test_db")
        profile = DBTProfile(target="prod", outputs={"prod": target_config})
        mock_settings = DBTProfilesSettings(profiles={"default": profile})

        mock_get_settings.return_value = mock_settings

        connector = DBConnectorFactory.get_connector(target_name="prod")

        from datu.integrations.sql_server.sqldb_connector import SQLServerConnector

        assert isinstance(connector, SQLServerConnector)


def test_get_connector_invalid_profile(clear_dbt_settings_cache):
    """Test the DBConnectorFactory for invalid profile."""
    from datu.factory.db_connector import DBConnectorFactory
    from datu.integrations.dbt.config import DBTProfilesSettings

    with patch("datu.factory.db_connector.get_dbt_profiles_settings") as mock_get_settings:
        mock_settings = DBTProfilesSettings(profiles={})
        mock_get_settings.return_value = mock_settings

        with pytest.raises(ValueError, match="Profile 'invalid_profile' not found in config"):
            DBConnectorFactory.get_connector(profile_name="invalid_profile")


def test_get_connector_invalid_target(clear_dbt_settings_cache):
    """Test the DBConnectorFactory for invalid target."""
    from datu.factory.db_connector import DBConnectorFactory
    from datu.integrations.dbt.config import DBTProfile, DBTProfilesSettings, DBTTargetConfig

    with patch("datu.factory.db_connector.get_dbt_profiles_settings") as mock_get_settings:
        target_config = DBTTargetConfig(type="postgres", host="localhost", dbname="test_db")
        profile = DBTProfile(target="dev", outputs={"dev": target_config})
        mock_settings = DBTProfilesSettings(profiles={"default": profile})

        mock_get_settings.return_value = mock_settings

        with pytest.raises(ValueError, match="Target 'invalid_target' not found in profile 'default'"):
            DBConnectorFactory.get_connector(target_name="invalid_target")


def test_get_connector_unsupported_db_type(clear_dbt_settings_cache):
    """Test the DBConnectorFactory for unsupported database type."""
    from datu.factory.db_connector import DBConnectorFactory
    from datu.integrations.dbt.config import DBTProfile, DBTProfilesSettings, DBTTargetConfig

    with patch("datu.factory.db_connector.get_dbt_profiles_settings") as mock_get_settings:
        target_config = DBTTargetConfig(type="unsupported_db", host="localhost", dbname="test_db")
        profile = DBTProfile(target="dev", outputs={"dev": target_config})
        mock_settings = DBTProfilesSettings(profiles={"default": profile})

        mock_get_settings.return_value = mock_settings

        with pytest.raises(ValueError, match="Unsupported database type: unsupported_db"):
            DBConnectorFactory.get_connector()
