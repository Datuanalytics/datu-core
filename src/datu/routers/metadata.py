"""FastAPI router for metadata-related endpoints.
This module defines a FastAPI router for handling metadata-related requests.
It includes an endpoint for introspecting the specified schema in the database
and returning table/column information.
"""

from fastapi import APIRouter, HTTPException

from datu.integrations.dbt.config import get_dbt_profiles_settings
from datu.schema_extractor.schema_cache import SchemaExtractor, SchemaGlossary

dbt_profiles_settings = get_dbt_profiles_settings()

router = APIRouter()


@router.get("/schema")
def get_schema() -> list[SchemaGlossary]:
    """Endpoint to introspect the specified schema in the database.
    This endpoint returns a list of SchemaGlossary objects containing
    information about the tables and columns in the specified schema.

    Returns:
        list[SchemaGlossary]: A list of SchemaGlossary objects containing schema information.

    Raises:
        HTTPException: If the schema is not found or if there is an error during introspection.
    """
    schema_info = SchemaExtractor.extract_all_schemas()
    if not schema_info:
        raise HTTPException(status_code=404, detail="Schema not found")
    return schema_info
