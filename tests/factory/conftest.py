"""Common fixtures for tests in factory module."""

# pylint: disable=import-outside-toplevel
import pytest


@pytest.fixture(scope="module")
def clear_dbt_settings_cache():
    """Automatically clear dbt profiles settings cache before each test."""
    from datu.integrations.dbt.config import get_dbt_profiles_settings

    get_dbt_profiles_settings.cache_clear()
    yield
    get_dbt_profiles_settings.cache_clear()
