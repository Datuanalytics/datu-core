"""
Data Sources endpoint for managing uploaded files and database connections.
This module provides API endpoints for listing, adding, updating, and deleting data sources
(CSV, Excel, database connections).
It supports file uploads, status indicators, and selection management for LLM context
configuration.

Endpoints:
    - GET /data-sources: List all available data sources.
    - POST /data-sources: Add a new data source (file upload or database connection).
    - PUT /data-sources/{id}: Update an existing data source (e.g., change status, details).
    - DELETE /data-sources/{id}: Remove a data source.

Returns:
    JSON responses with data source details, status, and selection summary.


Raises:
    HTTPException: For errors in data source management.

---
CORS Setup for Local Development
--------------------------------
Why is this added?
------------------
When developing a frontend (React, Vue, etc.) and backend (FastAPI) locally, they often run on
different ports (e.g., frontend on http://localhost:3000, backend on http://localhost:8000).
Browsers enforce the Same-Origin Policy, which blocks frontend JavaScript from making requests to
a backend on a different origin unless the backend explicitly allows it.

How does it work?
------------------
The FastAPI CORSMiddleware is added to the backend app to allow cross-origin requests from any
origin ("*") for development. This enables your frontend to communicate with the backend API
without CORS errors. In production, you should restrict allowed origins for security.

Reference: https://fastapi.tiangolo.com/tutorial/cors/
---
"""

import csv
import os

from fastapi import APIRouter, FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from datu.app_config import get_logger
from datu.factory.db_connector import DBConnectorFactory

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()

# Module-level logger
logger = get_logger(__name__)


# Dummy endpoint for /api/llm-context/templates
@app.get("/api/llm-context/templates")
async def get_templates():
    """
    Get a list of available LLM context templates for frontend development.
    Returns:
        JSONResponse: A JSON array of template names (list of str).
    Notes:
        This is a dummy endpoint for frontend development. Replace with real implementation as needed.
    """
    return JSONResponse(["General", "Finance", "Healthcare", "Retail", "Custom Instructions"])


app.include_router(router, prefix="/api")


router = APIRouter()

# In-memory store for demo purposes
DATA_SOURCES = [
    {
        "id": "1",
        "name": "sales_data_2024.csv",
        "type": "csv",
        "size": "2.4 MB",
        "status": "active",
        "lastModified": "2 hours ago",
    },
    {
        "id": "2",
        "name": "customer_analytics.xlsx",
        "type": "excel",
        "size": "5.1 MB",
        "status": "active",
        "lastModified": "1 day ago",
    },
    {
        "id": "3",
        "name": "inventory_database",
        "type": "database",
        "size": "45.2 MB",
        "status": "inactive",
        "lastModified": "3 days ago",
    },
]


class DataSource(BaseModel):
    id: str
    name: str
    type: str
    size: str
    status: str
    lastModified: str


@router.get("/data-sources")
async def list_data_sources():
    """List all available data sources.
    Returns:
        List[DataSource]: List of data sources with details.
    Note:
        This is dummy logic for frontend development. Replace with real implementation.
        - Query the persistent store for all data sources (CSV, Excel, database connections).
        - Return metadata for each source: id, name, type, size, status, last modified.
        - Support filtering, pagination, and sorting if needed for large datasets.
        - Ensure only sources accessible to the current user/tenant are returned.
    """
    return DATA_SOURCES


@router.post("/data-sources/files")
async def upload_data_source_file(file: UploadFile):
    """
    Upload a new CSV/Excel file as a data source and ingest it into the database.
    Args:
        file (UploadFile): The uploaded file object (CSV or Excel).
    Returns:
        dict: Metadata of the newly added data source.
    Raises:
        HTTPException: If no file is uploaded, or if table creation or row insertion fails,
        or if DBT profile/target is missing.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded or filename missing.")
    logger.debug(f"Received file upload: {file.filename}")

    # 1. Save file to disk
    upload_dir = "./uploaded_data_sources"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, str(file.filename))
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    logger.debug(f"Saved file to {file_path} ({len(content)} bytes)")

    # 2. Parse CSV header and rows
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    logger.debug(f"Parsed CSV header: {header}")
    logger.debug(f"Parsed {len(rows)} rows")

    # 3. Get DB profile/target from dbt profiles config (same as schema_cache.py)
    from datu.integrations.dbt.config import get_dbt_profiles_settings

    dbt_profiles_settings = get_dbt_profiles_settings()
    # Use first available profile/target
    try:
        profile_name, profile = next(iter(dbt_profiles_settings.profiles.items()))
        target_name, target = next(iter(profile.outputs.items()))
    except Exception as e:
        logger.error(f"No DBT profile/target found: {e}")
        raise HTTPException(status_code=500, detail="No DBT profile/target found in config.") from e

    db_schema = getattr(target, "database_schema", "public")
    db_host = getattr(target, "host", None)
    db_port = getattr(target, "port", None)
    db_user = getattr(target, "user", None)
    db_database = getattr(target, "database", None)

    # 4. Build CREATE TABLE SQL
    filename_str = str(file.filename)
    # Sanitize identifiers
    table_name = safe_identifier(os.path.splitext(filename_str)[0])
    db_schema_safe = safe_identifier(str(db_schema))
    header_safe = [safe_identifier(col) for col in header]
    columns_sql = ", ".join([f'"{col}" TEXT' for col in header_safe])
    create_table_sql = f'CREATE TABLE IF NOT EXISTS "{db_schema_safe}"."{table_name}" ({columns_sql});'
    logger.debug(f"CREATE TABLE SQL: {create_table_sql}")

    # 5. Connect to DB and run CREATE TABLE
    try:
        connector = DBConnectorFactory.get_connector(profile_name, target_name)
        connector.run_transformation(create_table_sql)
        logger.debug("Table created successfully.")
    except Exception as e:
        logger.error(f"Failed to create table: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create table: {e}") from e

    # 6. Insert rows (batch insert)
    # WARNING: Direct string interpolation in SQL is a possible SQL injection risk.
    # Identifiers are sanitized, but values should be parameterized in the connector for full safety.
    BATCH_SIZE = 5000
    total_rows = len(rows)
    for batch_start in range(0, total_rows, BATCH_SIZE):
        batch_rows = rows[batch_start : batch_start + BATCH_SIZE]
        values_list = []
        for row in batch_rows:
            safe_values = [str(val).replace("'", "''") for val in row]
            # Use single quotes around each value, join with commas, and wrap in parentheses
            quoted_values = ["'{}'".format(val) for val in safe_values]
            values_sql = "(" + ", ".join(quoted_values) + ")"
            values_list.append(values_sql)
        col_names = ", ".join(['"{}"'.format(col) for col in header_safe])
        all_values_sql = ", ".join(values_list)
        insert_sql = f'INSERT INTO "{db_schema_safe}"."{table_name}" ({col_names}) VALUES {all_values_sql};'  # nosec
        try:
            connector.run_transformation(insert_sql)
            logger.debug(f"Inserted batch rows {batch_start + 1}-{min(batch_start + BATCH_SIZE, total_rows)}")
        except Exception as e:
            logger.error(
                f"Failed to insert batch rows {batch_start + 1}-{min(batch_start + BATCH_SIZE, total_rows)}: {e}"
            )
            raise HTTPException(status_code=500, detail=f"Failed to insert batch rows: {e}") from e

    # 7. Update metadata store
    new_id = str(len(DATA_SOURCES) + 1)
    new_source = {
        "id": str(new_id),
        "name": filename_str,
        "type": "csv",
        "size": f"{len(content) / 1024 / 1024:.2f} MB",
        "status": "active",
        "lastModified": "just now",
        "schema": str(db_schema),
        "table": str(table_name),
        "dbHost": str(db_host) if db_host is not None else "",
        "dbPort": str(db_port) if db_port is not None else "",
        "dbUser": str(db_user) if db_user is not None else "",
        "dbDatabase": str(db_database) if db_database is not None else "",
    }
    DATA_SOURCES.append(new_source)
    logger.info(f"Data source metadata updated: {new_source}")

    # 8. Trigger schema extraction refresh
    try:
        from datu.schema_extractor.schema_cache import load_schema_cache

        load_schema_cache(force_refresh=True)
        logger.info("Schema cache refreshed after upload.")
    except Exception as e:
        logger.error(f"Failed to refresh schema cache: {e}")

    # 9. Return metadata
    return new_source


@router.post("/data-sources/databases")
async def add_database_source(data: dict):
    """
    Add a new database connection as a data source.

    Args:
        data (dict): Dictionary containing database connection details
        (dbType, host, port, user, password, database, schema, etc.).

    Returns:
        dict: Metadata of the newly added database data source.
    Notes:
        This is dummy logic for frontend development. Replace with real implementation.
        - Accept database connection details (dbType, host, port, user, password,
            database, schema).
        - Validate connection string and required fields.
        - Attempt connection (optional), store connection info securely.
        - Save metadata in the database.
        - Return the created data source object.
    """
    new_id = str(len(DATA_SOURCES) + 1)
    new_source = {
        "id": new_id,
        "name": data.get("name", f"database_{new_id}"),
        "type": "database",
        "size": "N/A",
        "status": data.get("status", "active"),
        "lastModified": data.get("lastModified", "just now"),
        "dbType": data.get("dbType"),
        "host": data.get("host"),
        "port": data.get("port"),
        "user": data.get("user"),
        "password": data.get("password"),
        "database": data.get("database"),
        "schema": data.get("schema"),
    }
    DATA_SOURCES.append(new_source)
    return new_source


@router.put("/data-sources/{id}")
async def update_data_source(id: str, data: dict):
    """Update an existing data source (e.g., change status, details).
    Args:
        id (str): The ID of the data source to update.
    Returns:
        DataSource: The updated data source details.
    Note:
        This is dummy logic for frontend development. Replace with real implementation.
        - Accept updates to status (active/inactive), name, or other metadata.
        - Validate changes (e.g., only allow status toggle if source is healthy).
        - Update the data source in the store.
        - Return the updated object or error if not found.
        - Log changes for audit purposes.
    """
    for ds in DATA_SOURCES:
        if ds["id"] == id:
            ds.update(data)
            return ds
    return {}


@router.delete("/data-sources/{id}")
async def delete_data_source(id: str):
    """Remove a data source.
    Args:
        id (str): The ID of the data source to delete.
    Returns:
        dict: Confirmation of deletion.
    Note:
        This is dummy logic for frontend development. Replace with real implementation.
        - Validate that the data source can be deleted (e.g., not in use or locked).
        - Remove from store and delete associated files if applicable.
        - Return confirmation of deletion (deleted: id) or error if not found.
        - Log deletion events for audit purposes.
    """
    for i, ds in enumerate(DATA_SOURCES):
        if ds["id"] == id:
            DATA_SOURCES.pop(i)
            return {"deleted": id}
    return {"deleted": None}


# Utility: sanitize SQL identifiers


def safe_identifier(name: str) -> str:
    """
    Sanitize a string to be a safe SQL identifier (alphanumeric and underscores only).
    Args:
        name (str): The input string to sanitize.
    Returns:
        str: The sanitized identifier containing only alphanumeric characters and underscores.
    """
    import re

    return re.sub(r"[^a-zA-Z0-9_]", "", name)
