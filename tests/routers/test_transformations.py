"""Test cases for the transformation endpoints in transformations.py.
This module contains test cases to ensure the functionality of the transformation endpoints,
including previewing SQL transformations, creating views, downloading data, executing transformations,
and retrieving data quality metrics.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient


def test_preview_transformation(client: TestClient) -> None:
    """Test the /preview/ endpoint for SQL transformation preview.
    Verifies that the endpoint returns a preview of the SQL transformation.
    Args:
        client (TestClient): The FastAPI test client fixture.
    """
    from datu.routers.transformations import PreviewRequest  # pylint: disable=import-outside-toplevel

    mock_request = PreviewRequest(sql_code="SELECT * FROM users", limit=5)
    mock_preview_data = [{"id": 1, "name": "John Doe"}]

    with patch("datu.routers.transformations.DBConnectorFactory.get_connector") as mock_connector:
        mock_connector.return_value.preview_sql.return_value = mock_preview_data
        response = client.post("/api/transform/preview/", json=mock_request.model_dump())

    assert response.status_code == 200
    assert response.json() == {"preview": mock_preview_data}


def test_create_view_endpoint(client: TestClient) -> None:
    """Test the /create_view/ endpoint for creating views.
    Verifies that the endpoint creates a view in the Gold layer.
    Args:
        client (TestClient): The FastAPI test client fixture.
    """
    from datu.routers.transformations import CreateViewRequest  # pylint: disable=import-outside-toplevel

    mock_request = CreateViewRequest(view_name="gold.users_view", sql_code="SELECT * FROM users")
    mock_result = {"success": True}

    with patch("datu.routers.transformations.DBConnectorFactory.get_connector") as mock_connector:
        mock_connector.return_value.create_view.return_value = mock_result
        response = client.post("/api/transform/create_view/", json=mock_request.model_dump())

    assert response.status_code == 200
    assert response.json() == mock_result


def test_download_transformation(client: TestClient) -> None:
    """Test the /download/ endpoint for downloading data.
    Verifies that the endpoint returns data for CSV export.
    Args:
        client (TestClient): The FastAPI test client fixture.
    """
    from datu.routers.transformations import DownloadRequest  # pylint: disable=import-outside-toplevel

    mock_request = DownloadRequest(sql_code="SELECT * FROM users")
    mock_data = [{"id": 1, "name": "John Doe"}]

    with patch("datu.routers.transformations.DBConnectorFactory.get_connector") as mock_connector:
        mock_connector.return_value.preview_sql.return_value = mock_data
        response = client.post("/api/transform/download/", json=mock_request.model_dump())

    assert response.status_code == 200
    assert response.json() == {"data": mock_data}


def test_execute_transformation(client: TestClient) -> None:
    """Test the /execute/ endpoint for executing SQL transformations.
    Verifies that the endpoint executes the SQL transformation and returns the result.
    Args:
        client (TestClient): The FastAPI test client fixture.
    """
    mock_sql_code = "INSERT INTO users (id, name) VALUES (1, 'John Doe')"
    mock_result = {"success": True, "row_count": 1}

    with patch("datu.routers.transformations.DBConnectorFactory.get_connector") as mock_connector:
        mock_connector.return_value.run_transformation.return_value = mock_result
        response = client.post(
            "/api/transform/execute/",
            data=mock_sql_code,  # type: ignore[arg-type]
            headers={"Content-Type": "text/plain"},
        )

    assert response.status_code == 200
    assert response.json() == mock_result


def test_get_data_quality(client: TestClient) -> None:
    """Test the /data_quality/ endpoint for retrieving data quality metrics.
    Verifies that the endpoint returns dummy data quality metrics.
    Args:
        client (TestClient): The FastAPI test client fixture.
    """
    from datu.routers.transformations import PreviewRequest  # pylint: disable=import-outside-toplevel

    mock_request = PreviewRequest(sql_code="SELECT * FROM users", limit=10)
    mock_quality_metrics = {
        "row_count": 1000,
        "missing_values": {"col1": 0, "col2": 10, "col3": 5},
        "completeness": 98.5,
        "outliers": {"col2": "No significant outliers"},
    }

    response = client.post("/api/transform/data_quality/", json=mock_request.model_dump())

    assert response.status_code == 200
    assert response.json() == {"data_quality": mock_quality_metrics}
