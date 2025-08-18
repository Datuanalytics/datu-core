"""Datu configuration module.
This module defines the configuration settings for the Datu application.
The settings are structured using Pydantic's BaseSettings class, allowing for easy management of environment variables.
It includes settings for the host, port, logging level, OpenAI API key, and other application-specific configurations.
It also provides a function to retrieve the application settings and a
function to create a logger with the specified configuration.
"""

import logging
from enum import Enum
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from datu.integrations.config import IntegrationConfigs
from datu.mcp.config import MCPConfig
from datu.services.config import SchemaRAGConfig


class Environment(Enum):
    """Environment enumeration for different deployment environments.
    This enumeration defines the different environments in which the application can run.

    Attributes:
        PROD (str): Production environment.
        DEV (str): Development environment.
        TEST (str): Testing environment.
    """

    PROD = "prod"
    DEV = "dev"
    TEST = "test"


class DatuConfig(BaseSettings):
    """DatuConfig class to represent the configuration settings for the Datu application.
    This class uses Pydantic's BaseSettings to manage environment variables and
    provides a structured way to access configuration settings.

    Args:
        host (str): The host address for the application.
        port (int): The port number for the application.
        reload (bool): Whether to enable auto-reload for the application.
        openai_api_key (str): The OpenAI API key for accessing OpenAI services.
        llm_provider (str): The LLM provider to use (default is "openai").
        schema_refresh_threshold_days (int): The threshold in days for refreshing the schema cache.
        retrieve_business_glossary (bool): Whether to retrieve the business glossary.
        integrations (IntegrationConfigs | None): Configuration settings for various integrations.
        schema_cache_file (str): The file path for the schema cache.
        dbt_profiles (str | None): The path to the dbt profiles directory.
        logging_level (str): The logging level for the application.
        openai_model (str): The OpenAI model to use.
        simulate_llm_response (str): Whether to simulate LLM responses.
        schema_sample_limit (int): The maximum number of rows to sample from the schema.
        schema_categorical_threshold (int): The threshold for categorical columns in the schema.
        enable_schema_rag (bool): Enable RAG for schema extraction.

    Attributes:
        host (str): The host address for the application.
        port (int): The port number for the application.
        reload (bool): Whether to enable auto-reload for the application.
        openai_api_key (str): The OpenAI API key for accessing OpenAI services.
        llm_provider (str): The LLM provider to use (default is "openai").
        schema_refresh_threshold_days (int): The threshold in days for refreshing the schema cache.
        retrieve_business_glossary (bool): Whether to retrieve the business glossary.
        integrations (IntegrationConfigs | None): Configuration settings for various integrations.
        schema_cache_file (str): The file path for the schema cache.
        dbt_profiles (str | None): The path to the dbt profiles directory.
        logging_level (str): The logging level for the application.
        openai_model (str): The OpenAI model to use.
        simulate_llm_response (str): Whether to simulate LLM responses.
        schema_sample_limit (int): The maximum number of rows to sample from the schema.
        schema_categorical_threshold (int): The threshold for categorical columns in the schema.
        enable_mcp (bool): Whether to enable MCP integration.
        mcp (MCPConfig | None): Configuration settings for MCP integration.
        enable_schema_rag (bool): Enable RAG for schema extraction.
        schema_rag (SchemaRAGConfig | None): Configuration settings for schema RAG.


    """

    app_environment: str = Field(default=Environment.DEV.value)
    host: str = "0.0.0.0"  # nosec: safe in Docker; internal service only
    port: int = 8000
    reload: bool = True
    llm_provider: Literal["openai"] = "openai"
    openai_api_key: str = Field(default="sk-")
    openai_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.2
    schema_refresh_threshold_days: int = 2
    retrieve_business_glossary: bool = False
    integrations: IntegrationConfigs | None = None
    schema_cache_file: str = Field(default="schema_cache.json")
    dbt_profiles: str | None = None
    logging_level: str = Field(default="DEBUG")
    simulate_llm_response: bool = False
    schema_categorical_detection: bool = True
    schema_sample_limit: int = 1000
    schema_categorical_threshold: int = 10
    enable_mcp: bool = False
    mcp: MCPConfig | None = Field(
        default_factory=MCPConfig,
        description="Configuration settings for MCP integration.",
    )
    enable_schema_rag: bool = False
    schema_rag: SchemaRAGConfig | None = Field(
        default_factory=SchemaRAGConfig,
        description="Configuration settings for schema RAG (Retrieval-Augmented Generation).",
    )
    enable_anonymization: bool = False

    model_config = SettingsConfigDict(
        env_prefix="datu_",
        env_nested_delimiter="__",
        env_file=".env",
        extra="allow",
    )


@lru_cache(maxsize=1)
def get_app_settings() -> DatuConfig:
    """Get the application settings.
    This function retrieves the application settings from environment variables
    and returns an instance of the DatuConfig class.

    Returns:
        DatuConfig: An instance of the DatuConfig class containing the application settings.
    """
    return DatuConfig()


@lru_cache()
def get_logger(name: str, datu_config: DatuConfig | None = None) -> logging.Logger:
    """Get a logger instance.
    This function creates a logger instance with the specified name and configuration settings.
    It sets up stream and file handlers for logging and configures the logging level.

    Args:
        name (str): The name of the logger.
        datu_config (DatuConfig | None): An optional DatuConfig instance for configuration settings.

    Returns:
        logging.Logger: A logger instance configured with the specified settings.
    """
    if datu_config is None:
        datu_config = get_app_settings()
    parent_logger = logging.getLogger("datu")

    if name:
        if not name.startswith(parent_logger.name + "."):
            logger = parent_logger.getChild(name)
        else:
            logger = logging.getLogger(name)
    else:
        logger = parent_logger

    stream_handler = logging.StreamHandler()
    file_handler = logging.FileHandler("app.log")

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    logger.setLevel(getattr(logging, datu_config.logging_level))

    return logger


settings = get_app_settings()

__all__ = ["settings"]
