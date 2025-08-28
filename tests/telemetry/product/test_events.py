import pytest

from datu.telemetry.product.events import MCPClientEvent, OpenAIEvent, ProductTelemetryEvent


def test_event_initialization(event, sample_event_data):
    assert event.properties["event_name"] == sample_event_data["event_name"]
    assert event.properties["user_id"] == sample_event_data["user_id"]
    assert event.properties["timestamp"] == sample_event_data["timestamp"]
    assert event.properties["properties"] == sample_event_data["properties"]


def test_event_name_and_batch_key(event):
    assert event.name == "ProductTelemetryEvent"
    assert event.batch_key == event.name


def test_batching_same_type(event):
    other = ProductTelemetryEvent(event_name="other_event")
    batched = event.batch(other)

    # Batch size increments
    assert batched.batch_size == 2
    assert batched is event  # batching modifies self


def test_batching_different_type_raises():
    class AnotherEvent(ProductTelemetryEvent):
        pass

    e1 = ProductTelemetryEvent()
    e2 = AnotherEvent()
    with pytest.raises(ValueError):
        e1.batch(e2)


def test_batch_size_increment(event):
    # Initial batch_size
    assert event.batch_size == 1
    event.batch(ProductTelemetryEvent())
    assert event.batch_size == 2
    event.batch(ProductTelemetryEvent())
    assert event.batch_size == 3


def test_mcp_client_event_properties():
    servers = ["playwright", "puppeteer"]
    event = MCPClientEvent(server_names=servers)

    # Check properties
    assert event.properties["mcp_server_names"] == servers
    # Name and batch_key should come from base class
    assert event.name == "MCPClientEvent"
    assert event.batch_key == event.name
    assert event.batch_size == 1


def test_openai_event_properties():
    from datu.app_config import get_app_settings

    app_settings = get_app_settings()
    data = {"user_id": "123", "action": "test"}
    event = OpenAIEvent(**data)

    # Base properties
    for k, v in data.items():
        assert event.properties[k] == v

    # Extra property added in subclass
    assert event.properties["openai_model"] == app_settings.openai_model

    # Name and batch_key
    assert event.name == "OpenAIEvent"
    assert event.batch_key == event.name
    assert event.batch_size == 1
