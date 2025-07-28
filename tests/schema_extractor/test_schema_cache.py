import json
import time
from unittest.mock import MagicMock, patch

import pytest

from datu import app_config as config
from datu.base.base_connector import SchemaInfo, TableInfo
from datu.schema_extractor.schema_cache import SchemaExtractor, load_schema_cache


@patch("datu.factory.db_connector.DBConnectorFactory.get_connector")
@patch.object(config.settings, "schema_categorical_detection", False)
def test_categorical_detection_disabled(mock_get_connector):
    """Test that categorical detection is skipped when the setting is disabled."""

    mock_connector = MagicMock()
    mock_connector.sample_table.return_value = [
        {"status": "active"},
        {"status": "inactive"},
        {"status": "active"},
        {"status": "pending"},
        {"status": "inactive"},
        {"status": "active"},
        {"status": "inactive"},
        {"status": "pending"},
        {"status": "active"},
        {"status": "inactive"},
    ]
    mock_connector.fetch_schema.return_value = [
        SchemaInfo(
            table_name="test_table",
            schema_name="public",
            columns=[TableInfo(column_name="status", data_type="varchar", description=None)],
        )
    ]

    mock_get_connector.return_value = mock_connector
    schemas = SchemaExtractor.extract_all_schemas()

    assert len(schemas) == 1
    table = schemas[0].schema_info[0]
    col = table.columns[0]
    assert col.categorical in (False, None)
    assert not col.values == []


@patch("datu.factory.db_connector.DBConnectorFactory.get_connector")
@patch.object(config.settings, "schema_categorical_detection", True)
def test_categorical_detection_logic(mock_get_connector):
    """Test that columns with ≤10 unique values are marked as categorical with correct values."""
    mock_connector = MagicMock()
    mock_connector.sample_table.return_value = [
        {"status": "active"},
        {"status": "inactive"},
        {"status": "active"},
        {"status": "pending"},
        {"status": "inactive"},
        {"status": "active"},
        {"status": "inactive"},
        {"status": "pending"},
        {"status": "active"},
        {"status": "inactive"},
    ]

    # Schema with one table and one column
    mock_connector.fetch_schema.return_value = [
        SchemaInfo(
            table_name="test_table",
            schema_name="public",
            columns=[TableInfo(column_name="status", data_type="varchar", description=None)],
        )
    ]

    mock_get_connector.return_value = mock_connector
    schemas = SchemaExtractor.extract_all_schemas()

    assert len(schemas) == 1
    schema = schemas[0]
    assert schema.profile_name  # Sanity check
    assert len(schema.schema_info) == 1

    table = schema.schema_info[0]
    assert table.table_name == "test_table"
    assert len(table.columns) == 1

    col = table.columns[0]
    assert col.column_name == "status"
    assert col.categorical is True
    assert sorted(col.values) == ["active", "inactive", "pending"]


@pytest.fixture
def cache_file(tmp_path, monkeypatch):
    cache_path = tmp_path / "schema_cache.json"
    monkeypatch.setattr(config.settings, "schema_cache_file", str(cache_path))
    return cache_path


def test_load_schema_cache_fresh_timestamp(cache_file, monkeypatch):
    now = time.time()
    schema_info = [{"profile_name": "demo"}]
    cache_data = {"timestamp": now, "schema_info": schema_info}
    cache_file.write_text(json.dumps(cache_data))

    monkeypatch.setattr(config.settings, "schema_refresh_threshold_days", 999)

    result = load_schema_cache()
    assert result == schema_info


def test_load_schema_cache_old_timestamp_triggers_refresh(cache_file, monkeypatch):
    old = time.time() - 999999
    cache_data = {"timestamp": old, "schema_info": [{"profile_name": "demo"}]}
    cache_file.write_text(json.dumps(cache_data))

    monkeypatch.setattr(config.settings, "schema_refresh_threshold_days", 0)

    with patch(
        "datu.schema_extractor.schema_cache.SchemaExtractor.extract_all_schemas", return_value=[]
    ) as mock_extract:
        load_schema_cache()
        assert mock_extract.called


def test_load_schema_cache_legacy_list_format(cache_file, monkeypatch):
    legacy_list = [{"profile_name": "demo"}]
    cache_file.write_text(json.dumps(legacy_list))

    result = load_schema_cache()
    assert result == legacy_list
