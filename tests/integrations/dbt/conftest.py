"""Common fixtures for tests in integrations dbt module."""

# pylint: disable=import-outside-toplevel
import os
from unittest.mock import patch

import pytest


@pytest.fixture(scope="module")
def mock_env_vars():
    """Fixture to mock environment variables for testing."""
    with patch.dict(os.environ, {"TEST_ENV_VAR": "test_value"}):
        yield


@pytest.fixture(scope="module", autouse=True)
def clear_dbt_settings_cache():
    """Automatically clear dbt profiles settings cache before each test."""
    from datu.integrations.dbt.config import get_dbt_profiles_settings

    get_dbt_profiles_settings.cache_clear()
    yield
    get_dbt_profiles_settings.cache_clear()
