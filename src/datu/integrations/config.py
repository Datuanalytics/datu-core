"""Integration configuration settings.
This module defines the configuration settings for various integrations used in the application.
The settings are structured using Pydantic's BaseSettings class, allowing for easy management of environment variables.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class IntegrationConfigs(BaseSettings):
    """IntegrationConfigs class to represent configuration settings for various integrations.
    This class uses Pydantic's BaseSettings to manage environment variables and
    provides a structured way to access configuration settings.
    """

    model_config = SettingsConfigDict(
        env_prefix="integrations_",
        env_nested_delimiter="__",
    )
