"""Tests for telemetry configuration."""


def test_config():
    """Test that telemetry settings are loaded correctly."""
    from datu.telemetry.config import get_telemetry_settings  # pylint: disable=import-outside-toplevel

    settings = get_telemetry_settings()
    assert settings.api_key == "phc_m74dfR9nLpm2nipvkL2swyFDtNuQNC9o2FL2CSbh6Je"
    assert settings.package_name == "datu-core"
