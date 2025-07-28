from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AnonymizationConfig(BaseSettings):
    """Configuration settings for anonymization in the Datu application.

    Args:
        supported_language (str): Language code for the anonymization engine (default is 'en').
        engine_conf_file (str): Path to the configuration file for the anonymization engine.

    Attributes:
        supported_language (str): Language code for the anonymization engine.
        engine_conf_file (str): Path to the configuration file for the anonymization engine.
    """

    supported_language: str = Field(
        default="en",
        description="Language code for the anonymization engine (e.g., 'en' for English).",
    )
    engine_conf_file: str = Field(
        default="anonymizer_config.yaml",
        description="Path to the configuration file for the anonymization engine.",
    )

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
    )
