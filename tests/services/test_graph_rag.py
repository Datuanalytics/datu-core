"""Sample schema fixtures for testing schema extraction and caching."""
# pylint: disable=protected-access

import os
import shutil

import networkx as nx
import pytest

from datu.services.schema_rag import SchemaGraphBuilder, SchemaRAG, SchemaTripleExtractor

from tests.helpers.sample_schemas import SchemaTestFixtures

TEST_GRAPH_DIR = "test_graph_rag"


@pytest.fixture(autouse=True)
def clean_test_graph_cache():
    """Ensure the test graph directory is cleaned up before and after each test."""
    if os.path.exists(TEST_GRAPH_DIR):
        shutil.rmtree(TEST_GRAPH_DIR)
    os.makedirs(TEST_GRAPH_DIR)
    yield
    shutil.rmtree(TEST_GRAPH_DIR)


def test_init_with_dict_schema():
    """Test SchemaGraphBuilder initialization with a raw schema dictionary."""
    schema_dict = SchemaTestFixtures.raw_schema_dict()
    extractor = SchemaTripleExtractor(schema_dict)
    extractor.create_schema_triples()
    assert extractor.timestamp == 1234567890.0
    assert len(extractor.schema_profiles) == 1


def test_extract_triples_output():
    """Test that triples are extracted correctly from schema objects."""
    schema_profiles = SchemaTestFixtures.sample_schema()
    extractor = SchemaTripleExtractor(schema_profiles)
    extractor.paths["triples"] = os.path.join(TEST_GRAPH_DIR, "triples.json")
    extractor.paths["meta"] = os.path.join(TEST_GRAPH_DIR, "meta.json")
    extractor.create_schema_triples()
    assert ("orders", "has_column", "order_id") in extractor.triples


def test_get_attr_dict_vs_object():
    """Test the helper method _get_attr for both dicts and objects."""
    extractor = SchemaTripleExtractor([])
    obj_dict = {"key1": "val1"}
    obj_class = type("Dummy", (), {"attr1": "key2"})()
    assert extractor._get_attr(obj_dict, "key1") == "val1"
    assert extractor._get_attr(obj_class, "attr1") == "key2"


def test_is_graph_outdated_returns_true_for_missing_files(tmp_path):
    """Test is_graph_outdated returns True when graph or meta files are missing."""
    extractor = SchemaTripleExtractor({"timestamp": 1234, "schema_info": []})
    extractor.graph_path = str(tmp_path / "missing_triples.json")
    extractor.meta_path = str(tmp_path / "missing_meta.json")
    assert extractor.is_rag_outdated() is True


def test_initialize_graph_rebuild_and_cache():
    """Test graph initialization rebuilds and caches the graph correctly."""
    schema = SchemaTestFixtures.sample_schema(timestamp=9999.0)
    extractor = SchemaTripleExtractor(schema)
    extractor.create_schema_triples()
    builder = SchemaGraphBuilder(triples=extractor.triples, is_rag_outdated=True)
    builder.graph_path = os.path.join(TEST_GRAPH_DIR, "graph.pkl")

    # Initial build (no cache yet)
    builder.initialize_graph()
    assert os.path.exists(builder.graph_path)
    assert builder.graph.number_of_nodes() > 0

    # Second init with same timestamp (should reuse cache)
    builder2 = SchemaGraphBuilder(triples=extractor.triples, is_rag_outdated=False)
    builder2.graph_path = builder.graph_path
    builder2.initialize_graph()
    assert isinstance(builder2.graph, nx.DiGraph)
    assert set(builder2.graph.nodes) == set(builder.graph.nodes)
    assert set(builder2.graph.edges) == set(builder.graph.edges)


def test_graph_contains_expected_edges():
    """Verify specific graph edges exist after initialization and triple extraction."""
    schema = SchemaTestFixtures.sample_schema()
    extractor = SchemaTripleExtractor(schema)
    extractor.create_schema_triples()
    builder = SchemaGraphBuilder(triples=extractor.triples, is_rag_outdated=True)
    builder.initialize_graph()
    test_graph = builder.graph

    assert test_graph.has_edge("orders", "order_id")
    assert test_graph.has_edge("order_id", "int") or any(
        d["label"] == "has_data_type" for _, _, d in test_graph.edges(data=True)
    )


@pytest.mark.requires_service
def test_schema_rag_run_query_returns_filtered_schema_dict():
    """Test SchemaRAG end-to-end run_query method returns filtered schema."""
    schema = SchemaTestFixtures.sample_schema()
    rag = SchemaRAG(schema)
    result = rag.run_query(["List all customer orders"])
    assert isinstance(result, dict)
    assert "schema_info" in result
    assert isinstance(result["schema_info"], list)
    flattened_columns = [
        col for table in result["schema_info"] for col in table.get("schema_info", [])[0].get("columns", [])
    ]
    column_names = [col.get("column_name") for col in flattened_columns]
    assert isinstance(column_names, list)
