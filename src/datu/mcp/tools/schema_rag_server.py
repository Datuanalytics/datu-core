"""SchemaRAG Server Tool"""

import json
from typing import List, Union

from fastmcp import FastMCP

from datu.mcp.registry import get_server_config
from datu.services.schema_rag import get_schema_rag

mcp: FastMCP = FastMCP("SchemaRAG")
schema_rag_engine = get_schema_rag()


@mcp.tool(name="extract_schema_context", description="Extract relevant schema for a query")
def extract_schema_context(query: Union[str, List[str]]) -> str:
    """Extract relevant schema context for a given query."""
    if isinstance(query, list):
        query_list = query
    else:
        query_list = [query]
    result = schema_rag_engine.run_query(query_list)
    return json.dumps(result)


if __name__ == "__main__":
    """Run the SchemaRAG server."""
    cfg = get_server_config("schema_rag_server")
    mcp.run(host=cfg["host"], port=cfg["port"], path=cfg["path"], transport="http")
