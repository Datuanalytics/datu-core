"""Telemetry configuration settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class TelemetryConfig(BaseSettings):
    """Telemetry configuration settings."""

    api_key: str = "phc_m74dfR9nLpm2nipvkL2swyFDtNuQNC9o2FL2CSbh6Je"
    package_name: str = "datu-core"

    model_config = SettingsConfigDict(
        env_prefix="telemetry_",
        env_nested_delimiter="__",
    )


def get_telemetry_settings() -> TelemetryConfig:
    return TelemetryConfig()
