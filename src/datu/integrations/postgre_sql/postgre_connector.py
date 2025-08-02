"""PostgreSQL connector for Datu.
This module provides a PostgreSQL connector for Datu, allowing
interactions with PostgreSQL databases.
"""

from typing import Tuple

import psycopg2
from psycopg2 import sql

from datu.app_config import get_logger
from datu.base.base_connector import BaseDBConnector, SchemaInfo, TableInfo
from datu.integrations.dbt.config import DBTTargetConfig

logger = get_logger(__name__)


class PostgreSQLConnector(BaseDBConnector):
    """PostgreSQL connector for Datu.
    This class provides methods to connect to a PostgreSQL database,
    fetch schema information, run SQL transformations, and create views.

    Args:
        config (DBTTargetConfig): Configuration object for the PostgreSQL connection.

    Attributes:
        config (DBTTargetConfig): Configuration object for the PostgreSQL connection.
    """

    def __init__(self, config: DBTTargetConfig):
        super().__init__(config)
        self.config = config

    def connect(self):
        """Establish a connection to the PostgreSQL database.

        Returns:
            conn: psycopg2 connection object.
        """
        conn = psycopg2.connect(
            host=self.config.host,
            port=self.config.port,
            user=self.config.user,
            password=self.config.password,
            dbname=self.config.dbname,
            sslmode=self.config.sslmode,
        )
        return conn

    def fetch_schema(self, schema_name: str) -> list[SchemaInfo]:
        """Fetches schema information from the PostgreSQL database.

        Args:
            schema_name (str): The name of the schema to fetch.

        Returns:
            list[SchemaInfo]: A list of SchemaInfo objects representing the schema information.

        Raises:
            psycopg2.Error: If there is an error connecting to the database or executing the query.
        """
        query_tables = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
            ORDER BY table_name;
        """

        query_columns = """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = %s
            AND table_name = %s
            ORDER BY ordinal_position;
        """

        conn = self.connect()
        try:
            with conn.cursor() as cur:
                cur.execute(query_tables, (schema_name,))
                tables = cur.fetchall()

                schema_info_list: list[SchemaInfo] = []
                for (table_name,) in tables:
                    cur.execute(query_columns, (schema_name, table_name))
                    columns = cur.fetchall()
                    schema_info = SchemaInfo(
                        table_name=table_name,
                        schema_name=schema_name,
                        columns=[
                            TableInfo(column_name=col_name, data_type=data_type) for (col_name, data_type) in columns
                        ],
                    )
                    schema_info_list.append(schema_info)

        finally:
            conn.close()

        return schema_info_list

    def run_transformation(
        self,
        sql_code: str,
        test_mode: bool = False,
    ) -> dict:
        """Executes a SQL transformation in the PostgreSQL database.

        Args:
            sql_code (str): The SQL code to execute.
            test_mode (bool): If True, the transformation is executed in test mode (no commit).

        Returns:
            dict: A dictionary containing the result of the transformation.
                - success (bool): Indicates if the transformation was successful.
                - error (str | None): Error message if the transformation failed.
                - row_count (int | None): Number of rows affected by the transformation.

        Raises:
            psycopg2.Error: If there is an error executing the SQL code.
        """
        conn = self.connect()
        result_info = {"success": False, "error": None, "row_count": None}
        try:
            with conn.cursor() as cur:
                logger.debug("Executing SQL transformation%s: %s", " in test mode" if test_mode else "", sql_code)
                cur.execute(sql_code)
                # In test mode, we rollback immediately.
                if test_mode:
                    conn.rollback()
                else:
                    conn.commit()
                result_info["row_count"] = cur.rowcount
                result_info["success"] = True
                logger.debug("Transformation executed successfully: %s", result_info)
        except psycopg2.Error as e:
            conn.rollback()
            logger.error("SQL transformation error: %s", e, exc_info=True)
            result_info["error"] = False
            raise e  # Propagate the error so that the feedback loop can catch it.
        finally:
            conn.close()
        return result_info

    def preview_sql(self, sql_code: str, limit: int = 10) -> list:
        """Previews the SQL code by executing it with a limit on the number of rows.

        Args:
            sql_code (str): The SQL code to preview.
            limit (int): The maximum number of rows to return in the preview.

        Returns:
            list: A list of dictionaries representing the preview data.

        Raises:
            psycopg2.Error: If there is an error executing the SQL code.
        """
        preview_data = []
        sql_code = sql_code.strip().rstrip(";")
        limited_sql = f"SELECT * FROM ({sql_code}) as subquery LIMIT {limit};"  # nosec: Fix this in the future
        conn = self.connect()
        try:
            with conn.cursor() as cur:
                logger.debug("Executing SQL preview: %s", limited_sql)
                cur.execute(limited_sql)
                colnames = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                for row in rows:
                    row_dict = {colname: val for colname, val in zip(colnames, row, strict=False)}
                    preview_data.append(row_dict)
                logger.debug("Preview data: %s", preview_data)
        except psycopg2.Error as e:
            logger.error("SQL preview error: %s", e, exc_info=True)
            raise e
        finally:
            conn.close()
        return preview_data

    def ensure_schema_exists(
        self,
        schema_name: str,
    ) -> None:
        """Ensures that the specified schema exists in the PostgreSQL database.

        Args:
            schema_name (str): The name of the schema to ensure.

        Raises:
            psycopg2.Error: If there is an error creating the schema.
        """
        conn = self.connect()
        try:
            with conn.cursor() as cur:
                cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}";')
                conn.commit()
                logger.debug("Schema '%s' ensured to exist.", schema_name)
        except psycopg2.Error as e:
            conn.rollback()
            logger.error("Error creating schema %s: %s", schema_name, e, exc_info=True)
            raise
        finally:
            conn.close()

    def parse_view_name(self, view_name: str) -> Tuple[str, str]:
        """Parses the view name to extract the schema and view name.

        Args:
            view_name (str): The view name to parse.

        Returns:
            Tuple[str, str]: A tuple containing the schema name and view name.
        """
        if "." in view_name:
            parts = view_name.split(".", 1)
            return parts[0].strip(), parts[1].strip()
        else:
            logger.debug("Parsing view_name: %s", view_name)  # debug log for view_name parsing
            logger.warning("Falling back to default schema 'gold' for unqualified view_name: %s", view_name)
            return "gold", view_name.strip()

    def create_view(
        self,
        sql_code: str,
        view_name: str,
    ) -> dict:
        """Creates or replaces a view in the PostgreSQL database.

        Args:
            sql_code (str): The SQL code to create the view.
            view_name (str): The name of the view to create.

        Returns:
            dict: A dictionary containing the result of the view creation.
                - success (bool): Indicates if the view was created successfully.
                - error (str | None): Error message if the view creation failed.

        Raises:
            psycopg2.Error: If there is an error creating the view.
        """
        conn = self.connect()
        result_info = {"success": False, "error": None}
        sql_code = sql_code.strip().rstrip(";")
        target_schema, target_view = self.parse_view_name(view_name)
        try:
            self.ensure_schema_exists(
                schema_name=target_schema,
            )
        except psycopg2.Error as e:
            logger.error("Failed to ensure schema '%s' exists: %s", target_schema, e, exc_info=True)
            result_info["error"] = None
            return result_info

        create_view_sql = f'CREATE OR REPLACE VIEW "{target_schema}"."{target_view}" AS {sql_code};'
        try:
            with conn.cursor() as cur:
                logger.debug("Creating view with SQL: %s", create_view_sql)
                cur.execute(create_view_sql)
                conn.commit()
                result_info["success"] = True
                logger.debug("View created successfully: %s", result_info)
        except psycopg2.Error as e:
            conn.rollback()
            logger.error("Error creating view: %s", e, exc_info=True)
            result_info["error"] = str(e)  # type: ignore[assignment]
        finally:
            conn.close()
        return result_info

    def sample_table(self, table_name: str, limit: int) -> list[dict]:
        """Samples rows from a table in the PostgreSQL database.

        Args:
            table_name (str): The name of the table to sample.
            limit (int): The maximum number of rows to sample.

        Returns:
            list[dict]: A list of dictionaries representing the sampled rows.

        Raises:
            psycopg2.Error: If there is an error sampling the table.
        """
        schema = self.config.database_schema
        if schema is None:
            raise ValueError("Configured database schema is None. Please set a valid schema in your DBT profile.")
        table = table_name
        try:
            self.ensure_schema_exists(
                schema_name=schema,
            )
        except psycopg2.Error as e:
            logger.error("Failed to ensure schema '%s' exists: %s", schema, e, exc_info=True)
            raise e
        query = sql.SQL("SELECT * FROM {}.{} ORDER BY RANDOM() LIMIT {}").format(
            sql.Identifier(str(schema)), sql.Identifier(table), sql.Literal(limit)
        )
        sample_data = []
        conn = self.connect()
        try:
            with conn.cursor() as cur:
                logger.debug(f"Sampling table {schema}.{table} with limit {limit}")
                cur.execute(query, (limit,))
                colnames = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                for row in rows:
                    row_dict = dict(zip(colnames, row, strict=False))
                    sample_data.append(row_dict)
                logger.debug("Sampled data: %s", sample_data)
        except psycopg2.Error as e:
            logger.error("Error sampling table %s: %s", table, e, exc_info=True)
            raise e
        finally:
            conn.close()
        return sample_data
