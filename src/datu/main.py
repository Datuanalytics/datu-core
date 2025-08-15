"""FastAPI application entry point for the LLM-Driven Data Transformations project.
This module serves as the main entry point for the FastAPI application, setting up the application,
including routers for various endpoints, and serving static files from the React build directory.
It also provides a function to start the application using Uvicorn.
"""

from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from datu.app_config import get_logger, settings
from datu.routers import chat, metadata, transformations
from datu.schema_extractor.schema_cache import load_schema_cache

logger = get_logger(__name__)

# Optionally load schema and graph-rag in cache for use in prompts or logging
if settings.app_environment != "test":
    schema_data = load_schema_cache()


# Create the FastAPI application instance.
app = FastAPI(title="LLM-Driven Data Transformations")


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint.
    This endpoint returns a simple JSON response indicating the status of the application.

    Returns:
        dict: A dictionary containing the status of the application.
    """
    return {"status": "ok"}


# Include API routers.
app.include_router(metadata.router, prefix="/api/metadata", tags=["metadata"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(transformations.router, prefix="/api/transform", tags=["transformations"])

# Mount static files from the React build directory at the root.
# This ensures that index.html and its assets are served correctly.
react_build_dir = Path(__file__).parent / "server" / "build"
if react_build_dir.exists():
    app.mount("/", StaticFiles(directory=str(react_build_dir), html=True), name="static")
else:
    logger.warning(f"React build directory '{react_build_dir}' does not exist. Static files will not be served.")


def start_app() -> None:
    """Start the FastAPI application using Uvicorn.
    This function initializes the application and runs it on the specified host and port.
    It also sets the logging level based on the configuration settings.
    """
    logger.info("Starting the FastAPI application...")
    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    start_app()
