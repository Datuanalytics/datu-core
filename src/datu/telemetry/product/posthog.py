"""PostHog telemetry client for product usage tracking."""

import importlib
import logging
import platform
import sys
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

import posthog

from datu.app_config import Environment, get_logger, settings
from datu.telemetry.config import TelemetryConfig as TelemetrySettings
from datu.telemetry.product.events import ProductTelemetryEvent

logger = get_logger(__name__)

POSTHOG_EVENT_SETTINGS = {"$process_person_profile": False}


class PostHogClient:
    """Telemetry client with basic batching + config via Pydantic."""

    UNKNOWN_USER_ID = "UNKNOWN"
    USER_ID_PATH = Path.home() / ".cache" / "datu-core" / "telemetry_user_id"

    def __init__(self, telemetry_settings: Optional[TelemetrySettings]) -> None:
        self.settings = telemetry_settings or TelemetrySettings()
        self._batched_events: Dict[str, ProductTelemetryEvent] = {}
        self._user_id: str = ""
        self._user_id_path: Path = self.USER_ID_PATH
        self.session_id = str(uuid.uuid4())

        if (
            not settings.enable_anonymized_telemetry
            or "pytest" in sys.modules
            or settings.app_environment in [Environment.TEST.value]
        ):
            posthog.disabled = True
        else:
            logger.info("Enabled anonymized telemetry. See https://docs.datu.fi for more information.")
        posthog.api_key = self.settings.api_key
        posthog_logger = logging.getLogger("posthog")
        posthog_logger.disabled = True

    @property
    def user_id(self) -> str:
        if self._user_id:
            return self._user_id

        try:
            if not self._user_id_path.exists():
                self._user_id_path.parent.mkdir(parents=True, exist_ok=True)
                new_id = str(uuid.uuid4())
                self._user_id_path.write_text(new_id)
                self._user_id = new_id
            else:
                self._user_id = self._user_id_path.read_text().strip()
        except Exception:
            self._user_id = self.UNKNOWN_USER_ID

        return self._user_id

    def _base_context(self) -> Dict[str, Any]:
        try:
            pkg_version = importlib.metadata.version(self.settings.package_name)
        except importlib.metadata.PackageNotFoundError:
            pkg_version = "unknown"

        extras_installed: Dict[str, bool] = {}
        try:
            dist = importlib.metadata.distribution(self.settings.package_name)
            extras = dist.metadata.get_all("Provides-Extra") or []
            for extra in extras:
                extras_installed[extra] = True
        except importlib.metadata.PackageNotFoundError:
            extras_installed = {}

        return {
            "python_version": sys.version.split()[0],
            "os": platform.system(),
            "os_version": platform.release(),
            "package_version": pkg_version,
            "extras_installed": extras_installed,
        }

    def capture(self, event: ProductTelemetryEvent) -> None:
        """Capture an event (with simple batching)."""
        if not settings.enable_anonymized_telemetry or not self.settings.api_key:
            return

        if event.max_batch_size == 1:
            self._send(event)
            return

        batch_key = event.batch_key
        if batch_key not in self._batched_events:
            self._batched_events[batch_key] = event
            return

        batched = self._batched_events[batch_key].batch(event)
        self._batched_events[batch_key] = batched

        if batched.batch_size >= batched.max_batch_size:
            self._send(batched)
            del self._batched_events[batch_key]

    def _send(self, event: ProductTelemetryEvent) -> None:
        try:
            posthog.capture(
                distinct_id=self.user_id,
                event=event.name,
                properties={**self._base_context(), **POSTHOG_EVENT_SETTINGS, **event.properties},
            )
        except Exception:
            logger.debug("Failed to send telemetry event", exc_info=True)


@lru_cache(maxsize=1)
def get_posthog_client() -> PostHogClient:
    """Get the PostHog telemetry client."""
    return PostHogClient(settings.telemetry)
