import pytest

from datu.telemetry.product.events import ProductTelemetryEvent


@pytest.fixture
def sample_event_data():
    return {
        "event_name": "test_event",
        "user_id": "12345",
        "timestamp": "2024-06-01T12:00:00Z",
        "properties": {"plan": "pro", "source": "web"},
    }


@pytest.fixture
def event(sample_event_data):
    return ProductTelemetryEvent(
        event_name=sample_event_data["event_name"],
        user_id=sample_event_data["user_id"],
        timestamp=sample_event_data["timestamp"],
        properties=sample_event_data["properties"],
    )


@pytest.fixture
def sample_event():
    return ProductTelemetryEvent(foo="bar")


@pytest.fixture
def telemetry_settings():
    from datu.telemetry.config import TelemetryConfig

    return TelemetryConfig(api_key="dummy_key", package_name="datu-core")


@pytest.fixture
def posthog_client(telemetry_settings):
    from datu.telemetry.product.posthog import PostHogClient

    return PostHogClient(settings=telemetry_settings)
