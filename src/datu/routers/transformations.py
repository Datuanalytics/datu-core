"""Transformation endpoints for the Datu API.
This module provides endpoints for previewing SQL transformations,
creating views, downloading data, and executing SQL transformations.
It includes functionality for previewing SQL code, creating views in the Gold layer,
downloading data for CSV export, and executing SQL transformations.
It also includes a new endpoint for retrieving data quality metrics.
"""

from fastapi import APIRouter, Body
from pydantic import BaseModel

from datu.app_config import get_logger
from datu.factory.db_connector import DBConnectorFactory

logger = get_logger(__name__)
router = APIRouter()


class PreviewRequest(BaseModel):
    """Request model for previewing SQL transformations.

    Args:
        sql_code (str): The SQL code to preview.
        limit (int): The maximum number of rows to return in the preview. Defaults to 10.

    Attributes:
        sql_code (str): The SQL code to preview.
        limit (int): The maximum number of rows to return in the preview. Defaults to 10.
    """

    sql_code: str
    limit: int = 10


@router.post("/preview/")
def preview_transformation(request: PreviewRequest):
    """Preview the SQL transformation.
    This endpoint executes the provided SQL code and returns a preview of the results.

    Args:
        request (PreviewRequest): The request object containing the SQL code and limit.

    Returns:
        dict: A dictionary containing the preview data.
    """
    conn = DBConnectorFactory.get_connector()
    logger.debug("preview_transformation called with sql_code: %s, limit: %s", request.sql_code, request.limit)
    data = conn.preview_sql(request.sql_code, request.limit)
    return {"preview": data}


class CreateViewRequest(BaseModel):
    """Request model for creating a view in the Gold layer.

    Attributes:
        view_name (str): The name of the view to create.
        sql_code (str): The SQL code to define the view.
    """

    view_name: str
    sql_code: str


@router.post("/create_view/")
def create_view_endpoint(request: CreateViewRequest):
    """Creates (or replaces) a view in the Gold layer based on the provided SQL transformation.
    The user supplies a target view name.

    Args:
        request (CreateViewRequest): The request object containing the view name and SQL code.

    Returns:
        dict: A dictionary containing the result of the view creation.
    """
    conn = DBConnectorFactory.get_connector()
    logger.debug("Creating view with name: %s", request.view_name)
    result = conn.create_view(request.sql_code, request.view_name)
    return result


class DownloadRequest(BaseModel):
    """Request model for downloading data for CSV export.

    Attributes:
        sql_code (str): The SQL code to execute for data download.
    """

    sql_code: str


@router.post("/download/")
def download_transformation(request: DownloadRequest):
    """Runs the provided SQL transformation without an effective limit,
    so that full data is returned for CSV export.

    Args:
        request (DownloadRequest): The request object containing the SQL code.

    Returns:
        dict: A dictionary containing the data for CSV export.
    """
    conn = DBConnectorFactory.get_connector()
    # Use a very high limit to approximate "all" rows.
    data = conn.preview_sql(request.sql_code, limit=1000000)
    return {"data": data}


@router.post("/execute/")
def execute_transformation(sql_code: str = Body(...)):
    """Executes the provided SQL transformation.
    This endpoint runs the SQL code and returns the result.

    Args:
        sql_code (str): The SQL code to execute.

    Returns:
        dict: A dictionary containing the result of the SQL execution.

    Todo:
        - Change this to MappingRequest
    """
    conn = DBConnectorFactory.get_connector()
    result = conn.run_transformation(sql_code)
    return result


# New endpoint for Data Quality Metrics
@router.post("/data_quality/")
def get_data_quality(request: PreviewRequest):
    """Returns dummy data quality metrics for the given SQL query.
    This is a placeholder endpoint that can be expanded later.

    Args:
        request (PreviewRequest): The request object containing the SQL code.

    Returns:
        dict: A dictionary containing dummy data quality metrics.
            1. Row count
            2. Missing values
            3. Completeness
            4. Outliers
    """
    sql_code = request.sql_code  # noqa: F841 pylint: disable=unused-variable
    # Dummy quality metrics; replace with real calculations later.
    quality_metrics = {
        "row_count": 1000,
        "missing_values": {"col1": 0, "col2": 10, "col3": 5},
        "completeness": 98.5,
        "outliers": {"col2": "No significant outliers"},
    }
    return {"data_quality": quality_metrics}
