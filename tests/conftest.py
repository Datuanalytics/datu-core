import os
from typing import Iterator, Mapping

import pytest
from dotenv import dotenv_values
from fastapi import FastAPI
from fastapi.testclient import TestClient
from responses import RequestsMock


@pytest.fixture(name="datu_environment", autouse=True, scope="session")
def load_environment(request: pytest.FixtureRequest):
    """Fixture to load environment variables from .env.test file for testing.
    This fixture loads the environment variables from the .env.test file
    and updates the os.environ dictionary with the loaded variables.
    It also allows skipping the loading of environment variables for certain test cases.
    Args:
        request (pytest.FixtureRequest): The pytest request object.
    """
    test_env_vars = dotenv_values(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            ".env.test",
        )
    )

    for key in test_env_vars:
        if key in os.environ:
            os.environ.pop(key)

    # Allow skipping loading of the environment varaibles on certain test cases
    if request.node.get_closest_marker("no_env"):
        print("Skiping loading environment variables from .env.test")
        return

    os.environ.update({key: value for key, value in test_env_vars.items() if key and value})
    print("Loaded environment variables from .env.test")
    print(os.environ)


@pytest.fixture(name="app", scope="session")
def mock_app(datu_environment: None) -> Iterator[FastAPI]:
    from datu.app_config import get_app_settings  # pylint: disable=import-outside-toplevel

    get_app_settings.cache_clear()

    from datu.main import app  # pylint: disable=import-outside-toplevel

    yield app


@pytest.fixture(name="client")
def mock_client(app: FastAPI) -> Iterator[TestClient]:
    """Fixture to create a mock FastAPI client for testing.
    This fixture sets up a FastAPI application with a mock endpoint
    and returns a TestClient instance for testing purposes.
    """

    @app.get("/mock_endpoint")
    def mock_get_endpoint() -> Mapping[str, str]:
        return {"status": "OK"}

    with TestClient(app=app) as client:
        yield client


@pytest.fixture(name="responses")
def mock_responses() -> Iterator[RequestsMock]:
    """Fixture to create a mock response object for testing.
    This fixture sets up a RequestsMock instance for mocking HTTP requests
    and responses during testing.
    It yields the RequestsMock instance for use in tests.
    """
    with RequestsMock() as resp:
        yield resp
