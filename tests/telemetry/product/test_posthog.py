"""Tests for PostHog telemetry client."""

from pathlib import Path
from unittest.mock import patch

# pylint: disable=import-outside-toplevel disable=redefined-outer-name disable=unused-argument


def test_posthog_client_initialization(posthog_client, telemetry_settings):
    """Test that PostHogClient initializes correctly."""
    from datu.telemetry.product.posthog import PostHogClient

    assert posthog_client.settings == telemetry_settings
    assert isinstance(posthog_client._batched_events, dict)
    assert isinstance(posthog_client.session_id, str)
    assert posthog_client._user_id == ""
    assert posthog_client._user_id_path == PostHogClient.USER_ID_PATH


def test_user_id_creation(tmp_path):
    """Test that user ID is created and read correctly."""
    from datu.telemetry.config import TelemetryConfig
    from datu.telemetry.product.posthog import PostHogClient

    path = tmp_path / "telemetry_user_id"
    client = PostHogClient(telemetry_settings=TelemetryConfig())
    client._user_id_path = path

    # file does not exist yet
    uid = client.user_id
    assert uid != PostHogClient.UNKNOWN_USER_ID
    assert path.read_text().strip() == uid

    # file exists, reads the same
    uid2 = client.user_id
    assert uid2 == uid


def test_user_id_fallback_patch():
    """Test that user ID falls back to unknown when file access fails."""
    from datu.telemetry.config import TelemetryConfig
    from datu.telemetry.product.posthog import PostHogClient

    client = PostHogClient(telemetry_settings=TelemetryConfig())

    with (
        patch.object(Path, "exists", side_effect=OSError("fail")),
        patch.object(Path, "read_text", side_effect=OSError("fail")),
    ):
        uid = client.user_id

    assert uid == PostHogClient.UNKNOWN_USER_ID


def test_base_context(monkeypatch):
    """Test that base context is created correctly."""
    from datu.telemetry.config import TelemetryConfig
    from datu.telemetry.product.posthog import PostHogClient

    client = PostHogClient(telemetry_settings=TelemetryConfig(package_name="nonexistent_pkg"))

    context = client._base_context()
    assert "python_version" in context
    assert "os" in context
    assert "os_version" in context
    assert context["package_version"] == "unknown"
    assert isinstance(context["extras_installed"], dict)


def test_capture_single_event(monkeypatch, posthog_client, sample_event):
    """Test that a single event is captured correctly."""
    # Ensure _send is called
    called = {}

    def fake_send(event):
        called["event_name"] = event.name

    posthog_client._send = fake_send

    posthog_client.capture(sample_event)
    assert called["event_name"] == sample_event.name


def test_capture_batching(monkeypatch):
    """Test that event batching works correctly."""
    from datu.telemetry.config import TelemetryConfig
    from datu.telemetry.product.events import ProductTelemetryEvent
    from datu.telemetry.product.posthog import PostHogClient

    settings = TelemetryConfig(api_key="dummy")
    client = PostHogClient(telemetry_settings=settings)

    class BatchEvent(ProductTelemetryEvent):
        max_batch_size = 2

    e1 = BatchEvent(foo=1)
    e2 = BatchEvent(foo=2)

    sent = []

    def fake_send(event):
        sent.append(event)

    client._send = fake_send

    client.capture(e1)
    assert client._batched_events[e1.batch_key].batch_size == 1
    assert sent == []

    client.capture(e2)
    assert sent[0].batch_size == 2
    assert e1.batch_key not in client._batched_events
