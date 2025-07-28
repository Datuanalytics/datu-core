"""Unit tests for integrations dbt module."""

# pylint: disable=unused-argument
from unittest.mock import mock_open, patch

import pytest
from pydantic import ValidationError


def test_parse_env_var(mock_env_vars, clear_dbt_settings_cache):
    """Test parsing environment variables in a string."""
    from datu.integrations.dbt.config import (
        parse_env_var,
    )

    value = "{{ env_var('TEST_ENV_VAR', 'default_value') }}"
    parsed_value = parse_env_var(value)
    assert parsed_value == "test_value"

    value = "{{ env_var('NON_EXISTENT_VAR', 'default_value') }}"
    parsed_value = parse_env_var(value)
    assert parsed_value == "default_value"


def test_dbt_target_config_parsing(mock_env_vars, clear_dbt_settings_cache):
    """Test parsing DBT target configuration with environment variables."""
    from datu.integrations.dbt.config import (
        DBTTargetConfig,
    )

    config_data = {
        "type": "postgres",
        "host": "{{ env_var('TEST_ENV_VAR', 'default_host') }}",
        "port": 5432,
        "user": "test_user",
        "password": "test_password",
        "dbname": "test_db",
        "schema": "public",
        "threads": 4,
        "extra": {"sslmode": "require"},
    }
    target_config = DBTTargetConfig(**config_data)
    assert target_config.host == "test_value"
    assert target_config.port == 5432
    assert target_config.user == "test_user"
    assert target_config.password == "test_password"
    assert target_config.dbname == "test_db"
    assert target_config.database_schema == "public"
    assert target_config.threads == 4
    assert target_config.extra["sslmode"] == "require"


def test_dbt_target_config_invalid_data():
    """Test validation of DBT target configuration."""
    from datu.integrations.dbt.config import DBTTargetConfig

    config_data = {
        "type": "postgres",
        "port": "invalid_port",  # Invalid port type
    }
    with pytest.raises(ValidationError):
        DBTTargetConfig(**config_data)


def test_dbt_profiles_settings_load_from_file(clear_dbt_settings_cache):
    """Test loading DBT profiles settings from a YAML file."""
    from datu.integrations.dbt.config import DBTProfilesSettings

    mock_yaml_content = """
    test-profiles:
        target: dev
        outputs:
          dev:
            type: postgres
            host: localhost
            port: 5432
            user: test_user
            password: test_password
            dbname: test_db
            schema: public
            threads: 4
    """
    with patch("builtins.open", mock_open(read_data=mock_yaml_content)), patch("os.path.exists", return_value=True):
        settings = DBTProfilesSettings.load_from_file("dummy_path")
        assert "test-profiles" in settings.profiles
        profile = settings.profiles["test-profiles"]
        assert profile.target == "dev"
        assert "dev" in profile.outputs
        target_config = profile.outputs["dev"]
        assert target_config.type == "postgres"
        assert target_config.host == "localhost"


def test_dbt_profiles_settings_load_file_not_found(clear_dbt_settings_cache):
    """Test loading DBT profiles settings from a non-existent YAML file."""
    from datu.integrations.dbt.config import DBTProfilesSettings

    with patch("os.path.exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            DBTProfilesSettings.load_from_file("dummy_path")


def test_get_active_target_config(mock_env_vars, clear_dbt_settings_cache):
    """Test getting the active target configuration."""
    from datu.integrations.dbt.config import get_active_target_config, get_dbt_profiles_settings

    mock_yaml_content = """
    profiles:
        target: dev
        outputs:
          dev:
            type: postgres
            host: localhost
            port: 5432
            user: test_user
            password: test_password
            dbname: test_db
            schema: public
            threads: 4
    """
    with patch("builtins.open", mock_open(read_data=mock_yaml_content)), patch("os.path.exists", return_value=True):
        _ = get_dbt_profiles_settings()
        target_config = get_active_target_config()
        assert target_config.type == "postgres"
        assert target_config.host == "localhost"


def test_get_active_target_config_invalid_profile():
    """Test getting the active target configuration with an invalid profile."""
    from datu.integrations.dbt.config import get_active_target_config

    with patch("datu.integrations.dbt.config.get_dbt_profiles_settings") as mock_settings:
        mock_settings.return_value.profiles = {}
        with pytest.raises(ValueError, match="Profile 'invalid_profile' not found"):
            get_active_target_config("invalid_profile")
