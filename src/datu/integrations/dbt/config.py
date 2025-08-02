"""DBT profiles configuration management.
This module provides functionality to load and manage DBT profiles configuration
using Pydantic models. It includes parsing environment variables, validating the configuration,
and providing access to the active profile and target configurations.
"""

import os
import re
from functools import lru_cache
from typing import Any, Dict

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field


def parse_env_var(value: str) -> str:
    """Replaces env_var placeholders with actual environment variables.

    Args:
        value (str): The string containing env_var placeholders.

    Returns:
        str: The string with env_var placeholders replaced by actual values.
    """
    load_dotenv()

    pattern = r"\{\{\s*env_var\('([^']+)'\s*,\s*'([^']+)'\)\s*\}\}"
    matches = re.findall(pattern, value)

    for match in matches:
        var_name, default_value = match
        # Use the environment variable or fallback to default_value
        env_value = os.getenv(var_name, default_value)
        value = value.replace(f"{{{{ env_var('{var_name}', '{default_value}') }}}}", env_value)
    return value


class DBTTargetConfig(BaseModel):
    """DBT target configuration model.
    This model is used to validate and parse the configuration for a specific target in a DBT profile.
    It supports parsing environment variables in the configuration values.

    Args:
        type (str): The type of database (e.g., postgres, snowflake).
        driver (str | None): The database driver.
        host (str | None): The host of the database.
        port (int | None): The port of the database.
        user (str | None): The username for the database.
        password (str | None): The password for the database.
        dbname (str | None): The name of the database.
        database_schema (str | None): The schema name in the database.
        threads (int): The number of threads to use for dbt execution.
        extra (Dict[str, Any]): Additional settings specific to the database type.

    Attributes:
        type (str | None): The type of database (e.g., postgres, snowflake).
        host (str | None): The host of the database.
        port (int | None): The port of the database.
        user (str | None): The username for the database.
        password (str | None): The password for the database.
        dbname (str | None): The name of the database.
        database_schema (str | None): The schema name in the database.
        sslmode (str | None): The SSL mode for the database connection.
        threads (int): The number of threads to use for dbt execution.
        extra (Dict[str, Any]): Additional settings specific to the database type.

    """

    type: str | None = Field(..., description="Database type (postgres, sqlserver, snowflake, etc.)")
    driver: str | None = Field(None, description="Database driver")
    host: str | None = Field(None, description="Database host")
    port: int | None = Field(None, description="Database port")
    user: str | None = Field(None, description="Database user")
    password: str | None = Field(None, description="Database password")
    dbname: str | None = Field(None, description="Database name")
    database_schema: str | None = Field(None, description="Schema name", alias="schema")
    sslmode: str | None = Field("disable", description="SSL mode for the database connection")
    threads: int = Field(1, description="Number of threads for dbt execution")
    extra: Dict[str, Any] = Field(default_factory=dict, description="Extra database-specific settings")
    model_config = ConfigDict(populate_by_name=True)

    def __init__(self, **data):
        super().__init__(**data)
        # Parse environment variables in the fields
        for field_name, field_value in self:
            if isinstance(field_value, str):
                parsed_value = parse_env_var(field_value)
                setattr(self, field_name, parsed_value)


class DBTProfile(BaseModel):
    """DBT profile model.
    This model is used to validate and parse the configuration for a DBT profile.

    Args:
        name (str): The name of the profile.
        target (str): The default target for the profile.
        outputs (Dict[str, DBTTargetConfig]): The available targets for the profile.

    Attributes:
        name (str): The name of the profile.
        target (str): The default target for the profile.
        outputs (Dict[str, DBTTargetConfig]): The available targets for the profile.
    """

    target: str = Field(..., description="Default target for the profile")
    outputs: Dict[str, DBTTargetConfig] = Field(..., description="Available targets")


class DBTProfilesConfig(BaseModel):
    """DBT profiles configuration model.
    This model is used to validate and parse the configuration for DBT profiles.

    Args:
        profiles (Dict[str, DBTProfile]): The profiles configuration.

    Attributes:
        profiles (Dict[str, DBTProfile]): The profiles configuration.
    """

    profiles: Dict[str, DBTProfile] = Field(..., description="DBT profiles configuration")

    def get_active_profile(self) -> str:
        """Returns the active profile name. If no active profile is set, returns the first available profile.

        Returns:
            str: The name of the active profile.

        Raises:
            ValueError: If no profiles are found in the configuration.
        """
        if not self.profiles:
            raise ValueError("No profiles found")
        return next(iter(self.profiles.keys()))  # pylint: disable=E1101

    def get_active_target(self) -> str:
        """Returns the active target name for the active profile.

        Returns:
            str: The name of the active target.

        Raises:
            ValueError: If no active profile is found.
        """
        active_profile = self.get_active_profile()
        if active_profile:
            return self.profiles[active_profile].target
        raise ValueError("No active profile found")

    def get_active_config(self) -> DBTTargetConfig:
        """Returns the active target configuration for the active profile.

        Returns:
            DBTTargetConfig: The active target configuration.

        Raises:
            ValueError: If no active profile is found.
        """
        active_profile = self.get_active_profile()
        if not active_profile:
            raise ValueError("No active profile found")

        target_name = self.profiles[active_profile].target
        return self.profiles[active_profile].outputs[target_name]


class DBTProfilesSettings(DBTProfilesConfig):
    """DBT profiles settings manager.
    This class is responsible for loading and validating the DBT profiles configuration.
    It uses Pydantic models to ensure the configuration is valid and provides methods
    to access the active profile and target configurations.

    Args:
        profiles (Dict[str, DBTProfile]): The profiles configuration.

    Attributes:
        profiles (Dict[str, DBTProfile]): The profiles configuration.
    """

    @classmethod
    def load_from_file(cls, config_path: str):
        """Load profiles from a YAML file.

        Args:
            config_path (str): The path to the YAML file containing the profiles configuration.

        Returns:
            DBTProfilesSettings: An instance of the DBTProfilesSettings class with the loaded configuration.

        Raises:
            FileNotFoundError: If the specified file does not exist.
        """
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                raw_config = yaml.safe_load(f)
            return cls(profiles=raw_config)
        else:
            raise FileNotFoundError(f"profiles.yml not found at {config_path}")

    @classmethod
    def load(cls):
        """Load profiles from the default locations or environment variables.
        This method checks the following locations in order:
        1. The DATU_DBT_PROFILES environment variable
        2. The current working directory
        3. The user's home directory
        If the profiles.yml file is not found in any of these locations, a FileNotFoundError is raised.

        Returns:
            DBTProfilesSettings: An instance of the DBTProfilesSettings class with the loaded configuration.

        Raises:
            FileNotFoundError: If the profiles.yml file is not found in any of the specified locations.
        """
        satu_config_path = os.getenv("DATU_DBT_PROFILES")
        possible_paths = [
            satu_config_path,
            os.path.join(os.getcwd(), "profiles.yml"),
            os.path.join(os.path.expanduser("~"), ".dbt", "profiles.yml"),
        ]

        for path in possible_paths:
            if path and os.path.exists(path):
                return cls.load_from_file(path)

        raise FileNotFoundError("profiles.yml not found in Datu config or default locations.")


@lru_cache(maxsize=1)
def get_dbt_profiles_settings() -> DBTProfilesSettings:
    """Fetches the DBT profiles settings.
    This function loads the DBT profiles configuration from the default locations
    or environment variables and returns an instance of the DBTProfilesSettings class.

    Returns:
        DBTProfilesSettings: An instance of the DBTProfilesSettings class with the loaded configuration.

    Raises:
        FileNotFoundError: If the profiles.yml file is not found in any of the specified locations.
    """
    return DBTProfilesSettings.load()


@lru_cache(maxsize=1)
def get_active_target_config(profile_name: str | None = None) -> DBTTargetConfig:
    """Fetches the active target configuration for the specified profile.
    This function loads the DBT profiles configuration and returns the active target configuration
    for the specified profile. If no profile name is provided, the active profile is used.

    Args:
        profile_name (str | None): The name of the profile. If None, the active profile is used.

    Returns:
        DBTTargetConfig: The active target configuration for the specified profile.

    Raises:
        ValueError: If the specified profile is not found in the configuration.
    """
    settings = get_dbt_profiles_settings()
    profile_name = profile_name or settings.get_active_profile()
    profile = settings.profiles.get(profile_name)  # pylint: disable=E1101

    if not profile:
        raise ValueError(f"Profile '{profile_name}' not found")

    target_name = profile.target
    return profile.outputs[target_name]
