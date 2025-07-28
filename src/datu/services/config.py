"""RAG configuration module.
This module defines the configuration settings for the Datu application.
The settings are structured using Pydantic's BaseSettings class, allowing for easy management of environment variables.
It includes settings for RAG and graph files path, embeddings similarity scoring threshold and minimum results fallback.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SchemaRAGConfig(BaseSettings):
    """
    Configuration settings for schema RAG (Retrieval-Augmented Generation).

    Args:
        rag_debugging (bool): Save debug files for the schema graph RAG.
        rag_dir (str): Directory to store RAG-related cache files.
        rag_meta_cache_file (str): File name for cached RAG metadata (e.g., timestamp).
        rag_triples_cache_file (str): File name for the extracted schema triples.
        rag_schema_query_score_threshold (float): Similarity threshold for selecting relevant triples in schema queries.
        rag_schema_query_min_results (int): Minimum number of schema triples to return if threshold is not met.
        rag_schema_query_output_dir (str): Directory path where filtered schema and subgraph files are saved.
        graph_rag_enabled (bool): Toggle to enable or disable schema graph RAG.
        graph_dir (str): Directory path for storing graph-related cache files.
    """

    rag_debugging: bool = Field(
        default=True,
        description="Save debug files for the schema graph RAG.",
    )
    rag_dir: str = Field(
        default="graph_cache",
        description="Directory to store RAG-related cache files.",
    )
    rag_meta_cache_file: str = Field(
        default="schema_rag_meta.json",
        description="File name for cached RAG metadata (e.g., timestamp).",
    )
    rag_triples_cache_file: str = Field(
        default="schema_triples.json",
        description="File name for the extracted schema triples.",
    )
    rag_schema_query_score_threshold: float = Field(
        default=0.5,
        description="Similarity threshold for selecting relevant triples in schema queries.",
    )
    rag_schema_query_min_results: int = Field(
        default=10,
        description="Minimum number of schema triples to return if threshold is not met.",
    )
    rag_schema_query_output_dir: str = Field(
        default="output/schema_selection",
        description="Directory path where filtered schema and subgraph files are saved.",
    )
    graph_enabled: bool = Field(
        default=True,
        description="Enable or disable the schema graph RAG functionality.",
    )
    graph_cache_file: str = Field(
        default="schema_graph.pkl",
        description="File name for the cached schema graph.",
    )

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
    )
