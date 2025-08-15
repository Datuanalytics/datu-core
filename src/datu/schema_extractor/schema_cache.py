"""Schema cache management for Datu.
This module handles the extraction, caching, and indexing of database schemas.
It provides functionality to extract schemas from configured profiles,
cache them, and build a FAISS index for efficient querying.
It also includes a function to load the schema cache and refresh it if necessary.
"""

import json
import os
import time

from pydantic import BaseModel, Field

from datu.app_config import get_logger, settings
from datu.base.base_connector import BaseDBConnector, SchemaInfo
from datu.factory.db_connector import DBConnectorFactory
from datu.integrations.dbt.config import get_dbt_profiles_settings
from datu.services.llm import generate_business_glossary

logger = get_logger(__name__)

profile_settings = get_dbt_profiles_settings()


class SchemaGlossary(BaseModel):
    """SchemaGlossary class to represent a schema glossary entry.

    Args:
        timestamp (float): The timestamp of the schema extraction.
        profile_name (str): The name of the profile.
        output_name (str): The name of the output target.
        db_type (str): The type of database.
        schema_info (list[SchemaInfo]): A list of SchemaInfo objects representing the schema information.

    Attributes:
        timestamp (float): The timestamp of the schema extraction.
        profile_name (str): The name of the profile.
        output_name (str): The name of the output target.
        db_type (str): The type of database.
        schema_info (list[SchemaInfo]): A list of SchemaInfo objects representing the schema information.
    """

    timestamp: float = Field(default_factory=time.time)
    profile_name: str
    output_name: str
    db_type: str
    schema_info: list[SchemaInfo]


class SchemaExtractor:
    """SchemaExtractor class to handle schema extraction from databases.
    This class provides methods to extract schema information from all available profiles
    and their targets, as well as for specific profiles and targets.
    """

    @staticmethod
    def extract_all_schemas() -> list[SchemaGlossary]:
        """Extracts schema information from all configured profiles and targets.

        Returns:
            list[SchemaGlossary]: A list of SchemaGlossary objects containing schema information.

        Raises:
            ConnectionError: If there is an error connecting to the database.
            ValueError: If there is an error fetching the schema.
            KeyError: If there is an error with the profile or target configuration.
        """
        extracted_schemas: list[SchemaGlossary] = []

        for profile_name, profile in profile_settings.profiles.items():  # pylint: disable=no-member
            for target_name, target in profile.outputs.items():
                try:
                    connector = DBConnectorFactory.get_connector(profile_name, target_name)
                    schema_name = target.database_schema
                    schema = connector.fetch_schema(schema_name)

                    if settings.schema_categorical_detection:
                        # Detect categorical columns in the schema
                        for table in schema:
                            SchemaExtractor._detect_categorical_columns(
                                table=table,
                                connector=connector,
                                sample_limit=settings.schema_sample_limit,
                                threshold=settings.schema_categorical_threshold,
                            )

                    extracted_schemas.append(
                        SchemaGlossary(
                            timestamp=time.time(),
                            profile_name=profile_name,
                            output_name=target_name,
                            schema_info=schema,
                            db_type=target.type or "",
                        )
                    )
                except (ConnectionError, ValueError, KeyError) as e:
                    logger.error(
                        "Error extracting schema for profile '%s', target '%s': %s", profile_name, target_name, e
                    )

        return extracted_schemas

    @staticmethod
    def extract_schema(profile_name: str, target_name: str) -> SchemaGlossary:
        """Extracts schema information for a specific profile and target.

        Args:
            profile_name (str): The name of the profile.
            target_name (str): The name of the target.

        Returns:
            SchemaGlossary: A SchemaGlossary object containing schema information.

        Raises:
            Exception: If there is an error extracting the schema.
        """
        try:
            connector = DBConnectorFactory.get_connector(profile_name, target_name)
            schema_name = connector.config.database_schema
            schema = connector.fetch_schema(schema_name)

            return SchemaGlossary(
                timestamp=time.time(),
                profile_name=profile_name,
                output_name=target_name,
                schema_info=schema,
                db_type=connector.config.type,
            )
        except (ConnectionError, ValueError, KeyError) as e:
            logger.error("Error extracting schema for profile '%s', target '%s': %s", profile_name, target_name, e)
            raise

    @staticmethod
    def _detect_categorical_columns(
        table: SchemaInfo, connector: BaseDBConnector, sample_limit: int, threshold: int
    ) -> None:
        """Detects categorical columns in a given table schema and saves their values.

        Args:
            table (SchemaInfo): The table schema to analyze.

        Returns:
            list[str]: A list of column names that are detected as categorical.
        """
        try:
            sample_rows = connector.sample_table(table.table_name, sample_limit)
            column_samples: dict[str, list] = {}
            for row in sample_rows:
                for column, value in row.items():
                    if value is not None:
                        column_samples.setdefault(column, []).append(value)
            for column in table.columns:
                samples = column_samples.get(column.column_name, [])
                unique_values = set(samples)
                if 0 < len(unique_values) <= threshold:
                    column.categorical = True
                    column.values = sorted(map(str, unique_values))
        except Exception as e:
            logger.warning(f"Could not sample rows for categorical detection on table {table.table_name}: {e}")


def load_schema_cache(force_refresh: bool = False) -> list[SchemaGlossary]:
    """Load the cached schema if it is fresh, or re-discover and merge with glossary.
    This function checks if the cached schema file exists and is within the refresh threshold.
    If the cache is valid, it loads the schema from the cache.
    If the cache is invalid or does not exist, it re-discovers the schema from the databases
    and updates the cache file.

    Returns:
        list[SchemaGlossary]: A list of SchemaGlossary objects containing schema information.

    Raises:
        OSError: If there is an error reading or writing the cache file.
        ConnectionError: If there is an error connecting to the database.
        ValueError: If there is an error fetching the schema.
        KeyError: If there is an error with the profile or target configuration.
        JSONDecodeError: If there is an error decoding the JSON cache file.

    If force_refresh is True, always refresh the cache regardless of age.
    """
    cache_file = settings.schema_cache_file
    refresh_threshold_seconds = settings.schema_refresh_threshold_days * 86400

    if not force_refresh and os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            if isinstance(cache_data, dict):
                timestamp = cache_data.get("timestamp", 0)
                if time.time() - timestamp < refresh_threshold_seconds:
                    logger.info("Using cached schema info from %s", cache_file)
                    return cache_data.get("schema_info", [])
                else:
                    logger.info("Cache file is older than threshold. Refreshing schema info.")
            elif isinstance(cache_data, list):
                logger.info("Using cached schema info (legacy list format) from %s", cache_file)
                return cache_data
        except (OSError, IOError, json.JSONDecodeError) as e:
            logger.error("Error reading schema cache: %s", e)

    # Discover schema from the databases using the configured schema name.
    try:
        schema_info = SchemaExtractor.extract_all_schemas()
        logger.info("Schema discovery completed successfully.")
        logger.info(schema_info)
    except (ConnectionError, ValueError, KeyError) as e:
        logger.error("Error during schema discovery: %s", e)
        raise

    # Optionally, retrieve business glossary definitions via LLM if enabled. TODO: Fix this
    if settings.retrieve_business_glossary:
        try:
            glossary = generate_business_glossary(schema_info)  # type: ignore
            logger.info("Business glossary generated successfully.")
            logger.info(glossary)
        except (ValueError, KeyError, RuntimeError) as e:
            logger.error("Error generating business glossary: %s", e)
            glossary = {}
    else:
        glossary = {}

    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": time.time(),
                    "schema_info": [schema.model_dump(exclude_none=True) for schema in schema_info],
                },
                f,
                indent=4,
            )

        logger.info("Schema cache updated at %s", cache_file)
    except (OSError, IOError) as e:
        logger.error("Error writing schema cache: %s", e)

    return schema_info
