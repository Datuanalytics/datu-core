"""Factory class to create database connectors based on dbt profiles"""

from datu.integrations.dbt.config import get_dbt_profiles_settings


class DBConnectorFactory:
    """Factory class to create database connectors based on dbt profiles
    Args:
        profile_name (str | None): The name of the dbt profile to use. If None, the active profile is used.
        target_name (str | None): The name of the target to use. If None, the default target for the profile is used.

    Attributes:
        profile_name (str | None): The name of the dbt profile to use.
        target_name (str | None): The name of the target to use.
    """

    @staticmethod
    def get_connector(
        profile_name: str | None = None,
        target_name: str | None = None,
    ):
        """Fetch a database connector using structured Pydantic settings"""
        # Default to active profile if none provided
        settings = get_dbt_profiles_settings()

        profile_name = profile_name or settings.get_active_profile()
        if profile_name not in settings.profiles:
            raise ValueError(f"Profile '{profile_name}' not found in config")

        profile = settings.profiles[profile_name]
        target_name = target_name or profile.target

        if target_name not in profile.outputs:
            raise ValueError(f"Target '{target_name}' not found in profile '{profile_name}'")

        config = profile.outputs[target_name]
        db_type = config.type

        if db_type == "postgres":
            from datu.integrations.postgre_sql.postgre_connector import PostgreSQLConnector

            return PostgreSQLConnector(config)
        elif db_type == "sqlserver":
            from datu.integrations.sql_server.sqldb_connector import SQLServerConnector

            return SQLServerConnector(config)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
