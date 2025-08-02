"""Schema graph builder module.

This module provides a class for building, caching, and loading a semantic graph representation
of a database schema. It extracts semantic triples, and constructs a directed graph using NetworkX.
The graph, along with metadata and extracted triples, is cached to disk for reuse and performance optimization.

The module checks if a cached version of the graph is valid based on the loaded schema timestamp and rebuilds the
graph if necessary.
"""

import json
import os
import pickle  # nosec B403
from collections import defaultdict
from copy import deepcopy
from functools import lru_cache
from typing import Any, Dict, List, Set, Tuple

import networkx as nx
import numpy as np
from pydantic import TypeAdapter
from sentence_transformers import SentenceTransformer

from datu.app_config import SchemaRAGConfig, get_logger
from datu.base.base_connector import TableInfo
from datu.schema_extractor.schema_cache import SchemaGlossary, SchemaInfo, load_schema_cache

logger = get_logger(__name__)
config = SchemaRAGConfig()


class SchemaTripleExtractor:
    """Extracts semantic triples from schema profiles.

    Attributes:
        schema_profiles (list): List of SchemaGlossary objects.
    """

    def __init__(self, raw_schema) -> None:
        """Initialize the triple extractor with a parsed schema dictionary.

        Args:
            schema (dict): Parsed schema data."""
        self.raw_schema = raw_schema
        self.schema_profiles, self.timestamp = self.normalize_schema(self.raw_schema)
        self.paths = {
            "meta": os.path.join(config.rag_dir, config.rag_meta_cache_file),
            "triples": os.path.join(config.rag_dir, config.rag_triples_cache_file),
        }
        self.triples: list = []

    def ensure_directory(self, path: str):
        """Ensure the directory for the graph-rag files exists."""
        os.makedirs(os.path.dirname(path), exist_ok=True)

    def is_rag_outdated(self) -> bool:
        """Check for outdated schema timestamp or missing RAG cache and rebuild RAG."""
        if not os.path.exists(self.paths["triples"]) or not os.path.exists(self.paths["meta"]):
            return True
        if self.timestamp is None:
            logger.warning("Current schema timestamp is missing. Rebuilding RAG engine.")
            return True
        try:
            with open(self.paths["meta"], "r", encoding="utf-8") as f:
                saved = json.load(f)
                saved_ts = saved.get("rag_timestamp")
                if saved_ts is None:
                    logger.warning("Cached RAG metadata has no timestamp. Rebuilding RAG engine.")
                    return True
                if int(saved_ts) != int(self.timestamp):
                    logger.info("Schema cache has been modified since last RAG engine update.")
                    logger.info("Rebuilding RAG system with new schema cache.")
                    return True
                return False
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("Error reading RAG metadata: %s", e)
            return True

    def create_schema_triples(self) -> bool:
        """Initialize the schema RAG, extracting triples and building the RAG engine.
        If the graph is outdated or missing, it will rebuild the RAG engine from the schema.
        If the graph is up-to-date, it will load the cached RAG engine from disk.
        """
        if self.is_rag_outdated():
            self.schema_profiles, self.timestamp = self.normalize_schema(self.raw_schema)
            self.triples = self.extract_triples()
            self.save_triples()
            self.save_timestamp()
            return True
        logger.info(f"Using cached RAG egnine from {self.paths['triples']}.")
        return False

    def _get_attr(self, obj: Any, key: str) -> Any:
        return obj.get(key) if isinstance(obj, dict) else getattr(obj, key, None)

    def normalize_schema(self, raw_schema) -> tuple[list[SchemaGlossary], float | None]:
        """Normalize input to always return (schema_profiles, timestamp)."""
        try:
            if isinstance(raw_schema, dict) and "schema_info" in raw_schema:
                # single glossary
                glossary = SchemaGlossary(**raw_schema)
                return [glossary], glossary.timestamp
            if isinstance(raw_schema, list):
                # multiple glossaries
                glossary_list = TypeAdapter(list[SchemaGlossary]).validate_python(raw_schema)
                if glossary_list:
                    return glossary_list, glossary_list[0].timestamp
        except Exception as e:
            logger.warning("Failed to parse schema input into SchemaGlossary: %s", e)
        logger.warning("Invalid schema format passed to SchemaGraphBuilder.")
        return [], None

    def _extract_table_triples(self, table: SchemaInfo) -> List[Tuple[str, str, Any]]:
        table_triples = []
        table_name = table.table_name
        for key, value in table.model_dump().items():
            if key in {"table_name", "columns"} or value is None:
                continue
            if isinstance(value, list):
                value = tuple(value)
            predicate = f"has_{key}"
            table_triples.append((table_name, predicate, value))
        return table_triples

    def _extract_column_triples(self, table_name: str, columns: List[TableInfo]) -> List[Tuple[str, str, Any]]:
        column_triples = []
        for column in columns:
            col_name = column.column_name
            if not col_name:
                continue
            column_triples.append((table_name, "has_column", col_name))
            for key, value in column.model_dump().items():
                if key == "column_name" or value is None:
                    continue
                if isinstance(value, list):
                    value = tuple(value)
                predicate = f"is_{key}" if key == "categorical" else f"has_{key}"
                column_triples.append((col_name, predicate, value))
        return column_triples

    def extract_triples(self) -> list:
        """Extract schema information into triples.

        Returns:
            list: List of (subject, predicate, object) triples.
        """
        triples = []
        for profile in self.schema_profiles:
            for table in profile.schema_info:
                table_name = self._get_attr(table, "table_name")
                if not table_name:
                    continue
                triples += self._extract_table_triples(table)
                triples += self._extract_column_triples(table.table_name, table.columns or [])
        return triples

    def save_triples(self):
        """Save triples to a JSON file.

        Args:
            path (str): Output path for triples.
        """
        self.ensure_directory(self.paths["triples"])
        with open(self.paths["triples"], "w", encoding="utf-8") as f:
            json.dump(self.triples, f, indent=2)

    def save_timestamp(self):
        """Save the schema timestamp to metadata file."""
        self.ensure_directory(self.paths["meta"])
        with open(self.paths["meta"], "w", encoding="utf-8") as f:
            json.dump({"rag_timestamp": self.timestamp}, f)


class SchemaGraphBuilder:
    """Builds a graph-based semantic representation of a database schema.

    Attributes:
        schema (dict): Parsed schema data.
        timestamp (float): Timestamp of the current schema snapshot.
        triples (list): Extracted triples representing schema relations.
        graph (nx.DiGraph): Graph representation of the schema.
    """

    def __init__(self, triples, is_rag_outdated) -> None:
        """Initialize the graph builder with a parsed schema dictionary.

        Args:
            schema (dict): Parsed schema data."""
        self.graph: nx.DiGraph = nx.DiGraph()
        self.graph_path = os.path.join(config.rag_dir, config.graph_cache_file)
        self.triples = triples
        self.graph_rebuild_required = is_rag_outdated

    def ensure_directory(self, path: str):
        """Ensure the directory for the graph-rag files exists."""
        os.makedirs(os.path.dirname(path), exist_ok=True)

    def initialize_graph(self) -> bool:
        """Initialize the schema graph, extracting triples and building the graph.
        If the graph is outdated or missing, it will rebuild the graph from the schema.
        If the graph is up-to-date, it will load the cached graph from disk.
        """
        if self.graph_rebuild_required:
            logger.info("Graph is outdated or missing. Rebuilding from schema...")
            self.graph = self.build_graph()
            self.save_graph()
            logger.info(f"Schema graph rebuilt with {self.graph.number_of_nodes()} nodes.")
            return True
        logger.info(f"Using cached graph from {self.graph_path}.")
        with open(self.graph_path, "rb") as f:
            self.graph = pickle.load(f)  # nosec B301
        return False

    def build_graph(self) -> nx.DiGraph:
        """Construct a directed graph from triples.

        Args:
            triples (list): Schema triples.

        Returns:
            nx.DiGraph: Directed graph representation.
        """
        schema_graph: nx.DiGraph = nx.DiGraph()
        for subject, predicate, obj in self.triples:
            schema_graph.add_edge(subject, obj, label=predicate)
        return schema_graph

    def save_graph(self):
        """Save graph to a pickle file.

        Args:
            path (str): Output path for graph.
        """
        self.ensure_directory(self.graph_path)
        with open(self.graph_path, "wb") as f:
            pickle.dump(self.graph, f)  # nosec B301


class SubGraphRetriever:
    """Retrieves subgraph based on relevant tables and columns."""

    def __init__(self, graph: nx.DiGraph):
        self.graph = graph
        self.vectorizer = SchemaVectorizer([])

    def extract_subgraph(self, relevant_tables: Set[str], relevant_columns: Dict[str, Set[str]]) -> nx.DiGraph:
        """
        Extract a focused subgraph of only relevant nodes and edges.

        Args:
            relevant_tables (Set[str]): Set of relevant table names.
            relevant_columns (Dict[str, Set[str]]): Dict mapping table names to sets of relevant column names.

        Returns:
            nx.DiGraph: A subgraph containing only the relevant elements.
        """
        nodes_to_include = set(relevant_tables)
        for cols in relevant_columns.values():
            nodes_to_include.update(cols)

        subgraph_edges = []
        for u, v, data in self.graph.edges(data=True):
            if u in nodes_to_include or v in nodes_to_include:
                subgraph_edges.append((u, v, data))

        subgraph: nx.DiGraph = nx.DiGraph()
        subgraph.add_edges_from(subgraph_edges)
        return subgraph

    def get_subgraph_from_query(
        self,
        query: str,
    ) -> nx.DiGraph:
        """Run vector search and save relevant schema elements and subgraph."""
        _, relevant_tables, relevant_columns = self.vectorizer.map_query_to_schema(query=query)

        subgraph_data = self.extract_subgraph(relevant_tables, relevant_columns)

        if config.rag_debugging:
            logger.info("[Retriever] Saving debug outputs.")
            self.save_debug_graph_outputs(
                subgraph_data=subgraph_data,
            )
        return subgraph_data

    @staticmethod
    def save_debug_graph_outputs(
        subgraph_data: nx.DiGraph,
    ) -> None:
        """Save debug files related to the subgraph and schema extraction."""
        output_dir: str = os.path.join(config.rag_dir + "/rag_debug")
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "subgraph.json"), "w", encoding="utf-8") as f:
            json.dump(nx.readwrite.json_graph.node_link_data(subgraph_data, edges="links"), f, indent=2)
            logger.info(f"[Retriever] Extracted subgraph with {len(subgraph_data.nodes)} nodes.")
        logger.debug(f"[Retriever] Graph saved in {output_dir}.")


class SchemaVectorizer:
    """Embeds schema triples into vector space and caches them.

    Attributes:
        triples (list): List of (subject, predicate, object) triples.
        timestamp (int): Schema timestamp to track cache validity.
        embeddings (list): List of embedding vectors for triples.
        texts (list): Textual representations of triples.
    """

    def __init__(self, triples: List[Tuple[str, str, str]]):
        self.triples = triples
        self.embeddings: list[list[float]] = []
        self.texts: list[str] = []
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.paths = {
            "vecs": os.path.join(config.rag_dir, "schema_embedding_cache.pkl"),
            "meta": os.path.join(config.rag_dir, config.rag_meta_cache_file),
        }

    def initialize_embeddings(self, force_rebuild: bool = False) -> None:
        """Load or generate and save embeddings."""
        if not force_rebuild and os.path.exists(self.paths["vecs"]):
            self.load_embeddings()
            logger.info(f"Loaded cached embeddings from {self.paths['vecs']}")
            return
        self.texts = [self.format_triple(t) for t in self.triples]
        self.embeddings = self.model.encode(self.texts, normalize_embeddings=True).tolist()
        self.save_embeddings()
        logger.info(f"Built {len(self.embeddings)} embeddings from schema.")

    def ensure_directory(self, path: str):
        """Ensure the directory for the graph-rag files exists."""
        os.makedirs(os.path.dirname(path), exist_ok=True)

    def save_embeddings(self) -> None:
        """Persist triple text and their embeddings."""
        self.ensure_directory(self.paths["vecs"])
        with open(self.paths["vecs"], "wb") as f:
            pickle.dump((self.triples, self.texts, self.embeddings), f)  # nosec B301

    def load_embeddings(self) -> None:
        """Load cached triples, their text representations, and embeddings."""
        with open(self.paths["vecs"], "rb") as f:
            self.triples, self.texts, self.embeddings = pickle.load(f)  # nosec B301

    def format_triple(self, triple: Tuple[str, str, str]) -> str:
        """Convert a triple into a natural-language-like string for embedding."""
        subj, pred, obj = triple
        return f"{subj} {pred.replace('_', ' ')} {obj}"

    def _cosine_similarity(self, vec1, vec2):
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))

    def search(
        self, query: str, score_threshold: float = 0.5, min_results: int = 100
    ) -> List[Tuple[Tuple[str, str, str], float]]:
        """Search for schema embeddings most relevant to a query using cosine similarity.

        Args:
            query: Natural language query.
            score_threshold: Minimum similarity score to include an embedding.
            min_results: Minimum number of results to return if threshold filters out too many.

        Returns:
            List of ((subj, pred, obj), score) tuples.
        """
        query_vec = self.model.encode([query], normalize_embeddings=True)[0]
        sims = [self._cosine_similarity(query_vec, vec) for vec in self.embeddings]
        scored = sorted(zip(self.triples, sims, strict=True), key=lambda x: x[1], reverse=True)
        filtered = [(triple, score) for triple, score in scored if score >= score_threshold]
        if len(filtered) < min_results:
            fallback = scored[:min_results]
            logger.info(f"Triples above threshold ({score_threshold}): {len(filtered)}")
            logger.info(f"Returning fallback top {min_results} triples.")
            logger.info(f"Fallback triples: {fallback}")
            return fallback
        return filtered

    @staticmethod
    def get_relevant_tables_columns(
        top_triples: List[Tuple[Tuple[str, str, str], float]],
    ) -> Tuple[Set[str], Dict[str, Set[str]]]:
        """Extract relevant tables and columns from scored triples based on a relevance threshold.

        Args:
            top_triples: List of ((subj, pred, obj), score) tuples from semantic search.
            threshold: Minimum score to consider a triple relevant.
            min_results: Minimum number of triples to preserve if threshold filtering returns too few.

        Returns:
            relevant_tables: set of table names
            relevant_columns: dict of table -> set of column names
        """
        relevant_tables = set()
        relevant_columns = defaultdict(set)
        column_to_table = {}
        for (subj, pred, obj), _ in top_triples:
            if pred == "has_column":
                column_to_table[obj] = subj
        for (subj, pred, obj), _ in top_triples:
            if pred == "has_column":
                relevant_tables.add(subj)
                relevant_columns[subj].add(obj)
            elif subj in column_to_table:
                table = column_to_table[subj]
                if table in relevant_tables:
                    relevant_columns[table].add(subj)
        if config.rag_debugging:
            logger.info(f"Relevant tables: {relevant_tables}")
            logger.info(f"Relevant columns: {dict(relevant_columns)}")
        return (relevant_tables, relevant_columns)

    def map_query_to_schema(
        self,
        query: str,
    ) -> Tuple[List[Tuple[Tuple[str, str, str], float]], Set[str], Dict[str, Set[str]]]:
        """End-to-end workflow: search schema triples and save relevant elements.

        Args:
            query: Natural language query string.
            score_threshold: Minimum similarity score to keep a triple.
            min_results: Fallback number of top triples if filtering is too strict.
        """
        if not self.embeddings:
            logger.warning("[SchemaVectorizer] Embeddings not initialized — attempting to load...")
            self.load_embeddings()
        top_triples = self.search(
            query,
            score_threshold=config.rag_schema_query_score_threshold,
            min_results=config.rag_schema_query_min_results,
        )
        relevant_tables, relevant_columns = self.get_relevant_tables_columns(top_triples)
        return top_triples, relevant_tables, relevant_columns


class SchemaRetriever:
    """Retrieves subgraph based on relevant tables and columns."""

    def __init__(self):
        pass

    def get_relevant_schema_from_query(
        self,
        query: str,
        vectorizer: SchemaVectorizer,
        schema_profiles: List[SchemaGlossary],
    ) -> List[SchemaGlossary]:
        """Run vector search and save relevant schema elements and subgraph."""
        top_triples, relevant_tables, relevant_columns = vectorizer.map_query_to_schema(query=query)
        filtered_schema = self.reconstruct_filtered_schema(
            schema_profiles=schema_profiles, relevant_tables=relevant_tables, relevant_columns=relevant_columns
        )
        if config.rag_debugging:
            logger.info("[Retriever] Saving debug outputs.")
            self.save_debug_rag_outputs(
                relevant_tables=relevant_tables,
                relevant_columns=relevant_columns,
                top_triples=top_triples,
                filtered_schema=filtered_schema,
            )
        return filtered_schema

    def reconstruct_filtered_schema(
        self, schema_profiles: List[SchemaGlossary], relevant_tables: Set[str], relevant_columns: Dict[str, Set[str]]
    ) -> List[SchemaGlossary]:
        """
        Reconstruct a filtered schema, preserving all available metadata fields.

        Args:
            schema_profiles: Original parsed schema from cache.
            relevant_tables: Set of table names to include.
            relevant_columns: Dict of table name -> set of column names to include.

        Returns:
            Filtered schema_profiles preserving full metadata.
        """
        filtered_profiles = []

        for profile in schema_profiles:
            filtered_tables = []
            for table in profile.schema_info:
                if table.table_name not in relevant_tables:
                    continue
                keep_columns = relevant_columns.get(table.table_name, set())
                filtered_columns = [col for col in table.columns if col.column_name in keep_columns]
                if not filtered_columns:
                    continue
                table_copy = deepcopy(table)
                table_copy.columns = filtered_columns
                filtered_tables.append(table_copy)
            if filtered_tables:
                profile_copy = deepcopy(profile)
                profile_copy.schema_info = filtered_tables
                filtered_profiles.append(profile_copy)
        return filtered_profiles

    @staticmethod
    def save_debug_rag_outputs(
        relevant_tables: Set[str],
        relevant_columns: Dict[str, Set[str]],
        top_triples: List[Tuple[Tuple[str, str, str], float]],
        filtered_schema: List[SchemaGlossary],
    ) -> None:
        """Save debug files related to the subgraph and schema extraction."""
        output_dir: str = os.path.join(config.rag_dir + "/rag_debug")
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "relevant_tables.json"), "w", encoding="utf-8") as f:
            json.dump(sorted(relevant_tables), f, indent=2)
        with open(os.path.join(output_dir, "relevant_columns.json"), "w", encoding="utf-8") as f:
            json.dump({k: sorted(v) for k, v in relevant_columns.items()}, f, indent=2)
        with open(os.path.join(output_dir, "scored_triples.json"), "w", encoding="utf-8") as f:
            json.dump(
                [{"triple": list(triple), "score": round(score, 3)} for triple, score in top_triples], f, indent=2
            )
        with open(os.path.join(output_dir, "partial_schema.json"), "w", encoding="utf-8") as f:
            json.dump([schema.model_dump(exclude_none=True) for schema in filtered_schema], f, indent=2)
        logger.info(f"[Retriever] RAG outputs saved in {output_dir}.")


class SchemaRAG:
    """
    SchemaGraphRAG manages the graph-based retrieval-augmented generation (RAG) pipeline
    for a structured database schema.

    Attributes:
        graph_builder (SchemaGraphBuilder): Builder and cache manager for the schema graph.
        vectorizer (SchemaVectorizer): Embedding manager for schema triples.
    """

    def __init__(self, schema_data):
        """
        Initialize the SchemaGraphRAG pipeline with raw or cached schema data.

        Args:
            schema_data (Union[list, dict]): Schema information, either as a list of SchemaGlossary
            objects or a dict containing a 'schema_info' key.
        """
        if isinstance(schema_data, dict) and "schema_info" in schema_data:
            schema_data = schema_data["schema_info"]

        self.triple_extractor = SchemaTripleExtractor(schema_data)
        triples_rebuilt = self.triple_extractor.create_schema_triples()
        self.vectorizer = SchemaVectorizer(self.triple_extractor.triples)
        self.vectorizer.initialize_embeddings(force_rebuild=triples_rebuilt)
        if config.graph_enabled:
            logger.info("Initializing schema graph builder.")
            self.graph_builder = SchemaGraphBuilder(
                triples=self.triple_extractor.triples, is_rag_outdated=triples_rebuilt
            )
            self.graph_builder.initialize_graph()

    def run_query(self, user_messages: List[str]) -> dict[str, List[dict[str, Any]]]:
        """
        Run a semantic search over the schema graph using the provided user messages,
        and return a filtered schema relevant to the query.

        Args:
            user_messages (List[str]): List of user message strings representing the query context.

        Returns:
            str: A JSON-formatted string of the filtered schema relevant to the user's query.
        """
        query = " ".join(user_messages)

        retriever = SchemaRetriever()
        filtered_schema = retriever.get_relevant_schema_from_query(
            query=query,
            vectorizer=self.vectorizer,
            schema_profiles=self.triple_extractor.schema_profiles,
        )
        return {"schema_info": [entry.model_dump(exclude_none=True) for entry in filtered_schema]}


@lru_cache()
def get_schema_rag() -> SchemaRAG:
    """
    Load the schema from cache and initialize a cached instance of SchemaGraphRAG.
    This function uses LRU caching to avoid repeated initialization.

    Returns:
        SchemaGraphRAG: Cached instance of the graph-based RAG service.
    """
    schema_data = load_schema_cache()
    return SchemaRAG(schema_data)
