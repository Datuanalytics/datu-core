def test_config():
    from datu.telemetry.config import get_telemetry_settings

    settings = get_telemetry_settings()
    assert settings.api_key == "phc_m74dfR9nLpm2nipvkL2swyFDtNuQNC9o2FL2CSbh6Je"
    assert settings.package_name == "datu-core"
