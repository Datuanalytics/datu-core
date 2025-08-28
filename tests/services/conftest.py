"""Sample schema fixtures for testing schema extraction and caching."""

import pytest

from datu.base.base_connector import SchemaInfo, TableInfo
from datu.schema_extractor.schema_cache import SchemaGlossary


class SchemaTestFixtures:
    """A collection of sample schemas for testing purposes."""

    @staticmethod
    def sample_schema(timestamp: float = 1234567890.0):
        """Create a sample schema with a given timestamp."""
        return [
            SchemaGlossary(
                profile_name="demo",
                output_name="dev",
                db_type="postgres",
                timestamp=timestamp,
                schema_info=[
                    SchemaInfo(
                        table_name="orders",
                        schema_name="sales",
                        columns=[
                            TableInfo(column_name="order_id", data_type="int"),
                            TableInfo(column_name="amount", data_type="float"),
                        ],
                    )
                ],
            )
        ]

    @staticmethod
    def cached_schema():
        """Return a cached schema with older timestamp."""
        return SchemaTestFixtures.sample_schema(timestamp=1111.0)

    @staticmethod
    def raw_schema_dict():
        return {
            "profile_name": "test_profile",
            "output_name": "test_output",
            "db_type": "postgres",
            "timestamp": 1234567890.0,
            "schema_info": [
                {
                    "table_name": "orders",
                    "schema_name": "public",
                    "columns": [
                        {"column_name": "order_id", "data_type": "int"},
                        {"column_name": "customer_id", "data_type": "int"},
                    ],
                }
            ],
        }


@pytest.fixture
def sample_schema():
    # Return a function that can generate schemas with parameters
    def _factory(timestamp: float = 1234567890.0):
        return SchemaTestFixtures.sample_schema(timestamp=timestamp)

    return _factory


@pytest.fixture
def raw_schema_dict():
    return SchemaTestFixtures.raw_schema_dict()
