"""Base connector class for database interactions.
This class serves as an abstract base class for all database connectors,
providing a common interface and shared functionality.
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel

from datu.integrations.dbt.config import DBTTargetConfig


class TableInfo(BaseModel):
    """TableInfo class to represent information about a table in the database.

    Args:
        column_name (str): The name of the column in the table.
        data_type (str): The data type of the column.
        description (str | None): An optional description of the column. Defaults to None.

    Attributes:
        column_name (str): The name of the column in the table.
        data_type (str): The data type of the column.
        description (str | None): An optional description of the column. Defaults to None.
    """

    column_name: str
    data_type: str
    description: str | None = None
    categorical: bool | None = None
    values: list[str] | None = None


class SchemaInfo(BaseModel):
    """SchemaInfo class to represent information about a schema in the database.

    Args:
        schema_name (str): The name of the schema.
        table_name (str): The name of the table in the schema.
        columns (list[TableInfo]): A list of TableInfo objects representing the columns in the table.

    Attributes:
        schema_name (str): The name of the schema.
        table_name (str): The name of the table in the schema.
        columns (list[TableInfo]): A list of TableInfo objects representing the columns in the table.
    """

    table_name: str
    schema_name: str
    columns: list[TableInfo]


class BaseDBConnector(ABC):
    """BaseDBConnector class to provide a common interface for database connectors.

    Args:
        config (DBTTargetConfig): Configuration object for the database connection.

    Attributes:
        config (DBTTargetConfig): Configuration object for the database connection.
    """

    def __init__(self, config: DBTTargetConfig):
        self.config = config

    @abstractmethod
    def connect(self):
        """Establish a connection to the database"""

    @abstractmethod
    def fetch_schema(self, schema_name: str) -> list[SchemaInfo]:
        """Retrieve schema information"""

    @abstractmethod
    def run_transformation(self, sql_code: str, test_mode: bool = False) -> dict:
        """Execute a SQL transformation"""

    @abstractmethod
    def preview_sql(self, sql_code: str, limit: int = 10) -> list:
        """Preview SQL results with a limit"""

    @abstractmethod
    def ensure_schema_exists(self, schema_name: str) -> None:
        """Ensure the schema exists in the database"""

    @abstractmethod
    def create_view(self, sql_code: str, view_name: str) -> dict:
        """Create or replace a view in the database"""

    @abstractmethod
    def sample_table(self, table_name: str, limit: int) -> list[dict]:
        """Sample data from a table"""

    def close(self, conn):
        """Close the connection"""
        conn.close()
