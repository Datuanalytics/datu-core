"""Common fixtures for tests in telemetry product module."""

import pytest

from datu.telemetry.product.events import ProductTelemetryEvent


# pylint: disable=import-outside-toplevel
@pytest.fixture
def sample_event_data():
    """Fixture for sample event data."""
    return {
        "event_name": "test_event",
        "user_id": "12345",
        "timestamp": "2024-06-01T12:00:00Z",
        "properties": {"plan": "pro", "source": "web"},
    }


@pytest.fixture
def event(sample_event_data):
    """Fixture for a ProductTelemetryEvent."""
    return ProductTelemetryEvent(
        event_name=sample_event_data["event_name"],
        user_id=sample_event_data["user_id"],
        timestamp=sample_event_data["timestamp"],
        properties=sample_event_data["properties"],
    )


@pytest.fixture
def sample_event():
    """Fixture for a sample ProductTelemetryEvent."""
    return ProductTelemetryEvent(foo="bar")


@pytest.fixture
def telemetry_settings():
    """Fixture for telemetry settings."""
    from datu.telemetry.config import TelemetryConfig

    return TelemetryConfig(api_key="dummy_key", package_name="datu-core")


@pytest.fixture
def posthog_client(telemetry_settings):
    """Fixture for PostHog client."""
    from datu.telemetry.product.posthog import PostHogClient

    return PostHogClient(telemetry_settings=telemetry_settings)
