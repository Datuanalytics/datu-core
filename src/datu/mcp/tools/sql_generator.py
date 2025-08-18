# datu/mcp/sql_generator_server.py
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ValidationError

from datu.app_config import get_app_settings, get_logger
from datu.base.chat_schema import ChatMessage, ChatRequest
from datu.services.sql_generator.core import generate_sql_core

logger = get_logger(__name__)
mcp = FastMCP("SQL Generator")
settings = get_app_settings()


class GenerateSQLInput(BaseModel):
    """Input model for the SQL generation tool.
    Attributes:
        messages (List[ChatMessage]): A list of chat messages in the format [{role, content}, ...].
        system_prompt (Optional[str]): Optional system prompt text.
        timeout_sec (int): Timeout in seconds. Defaults to 45.
        disable_schema_rag (bool): Whether to disable schema RAG. Defaults to True.
    """

    messages: List[ChatMessage]
    system_prompt: Optional[str] = None
    timeout_sec: int = 45
    disable_schema_rag: bool = True


def _make_chat_request(payload: GenerateSQLInput) -> ChatRequest:
    """Convert the GenerateSQLInput payload to a ChatRequest."""
    return ChatRequest(messages=payload.messages, system_prompt=payload.system_prompt)


@mcp.tool()
async def sql_generate(
    messages: List[ChatMessage],
    system_prompt: Optional[str] = None,
    timeout_sec: int = 45,
    disable_schema_rag: bool = True,
) -> Dict[str, Any]:
    """
    Generate SQL via the existing core pipeline.

    Args:
        messages (List[ChatMessage]): A list of chat messages in the format [{role, content}, ...].
        system_prompt (Optional[str]): Optional system prompt text.
        timeout_sec (int): Timeout in seconds. Defaults to 45.
        disable_schema_rag (bool): Whether to disable schema RAG. Defaults to True.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - assistant_response (str): The assistant's text response.
            - queries (List[Dict[str, Any]]): List of query metadata with keys:
                - title (str)
                - sql (str)
                - complexity (str)
                - execution_time_estimate (str)
    """
    try:
        payload = GenerateSQLInput.model_validate(
            {
                "messages": messages,
                "system_prompt": system_prompt,
                "timeout_sec": timeout_sec,
                "disable_schema_rag": disable_schema_rag,
            }
        )
    except ValidationError as ve:
        return {"error": "invalid_request", "details": ve.errors()}

    try:
        chat_req = _make_chat_request(payload)
        result = await asyncio.wait_for(
            generate_sql_core(
                chat_req,
                use_schema_rag=(not payload.disable_schema_rag),
            ),
            timeout=payload.timeout_sec,
        )

        queries = result.get("queries", [])
        if queries and hasattr(queries[0], "model_dump"):
            queries = [q.model_dump() for q in queries]

        return {
            "assistant_response": result.get("assistant_response", ""),
            "queries": queries,
        }

    except asyncio.TimeoutError:
        return {"error": "timeout", "details": f"sql_generate exceeded {payload.timeout_sec}s"}
    except Exception as e:
        logger.error("sql_generate failed: %s", e, exc_info=True)
        return {"error": "internal_error", "details": str(e)}


if __name__ == "__main__":
    mcp.run()
