"""Telemetry events for product usage."""

from typing import Any, ClassVar, Dict

from datu.app_config import settings


class ProductTelemetryEvent:
    """Base class for all telemetry events."""

    max_batch_size: ClassVar[int] = 1

    def __init__(self, **kwargs):
        self._props = kwargs
        self.batch_size = 1

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def properties(self) -> Dict[str, Any]:
        return self._props

    @property
    def batch_key(self) -> str:
        return self.name

    def batch(self, other: "ProductTelemetryEvent") -> "ProductTelemetryEvent":
        """Simple batch: append counts together."""
        if self.name != other.name:
            raise ValueError("Cannot batch different event types")
        self.batch_size += other.batch_size
        return self


class MCPClientEvent(ProductTelemetryEvent):
    """Event for when the MCP client starts."""

    def __init__(self, server_names: list[str]):
        super().__init__()
        self._props["mcp_server_names"] = server_names


class OpenAIEvent(ProductTelemetryEvent):
    """Event for OpenAI-related telemetry."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._props["openai_model"] = settings.openai_model
