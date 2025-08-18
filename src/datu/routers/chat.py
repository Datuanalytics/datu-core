"""Chat endpoint for generating SQL queries based on user instructions.
This module provides an API endpoint for interacting with a language model (LLM) to generate SQL queries
based on user instructions. It includes functionality for validating and fixing SQL queries, extracting SQL blocks,
and handling chat messages.
"""

from fastapi import APIRouter, HTTPException

from datu.app_config import get_app_settings, get_logger
from datu.base.chat_schema import ChatRequest
from datu.integrations.dbt.config import get_active_target_config
from datu.services.llm import generate_response
from datu.services.sql_generator.core import (
    QueryDetails,
    estimate_query_complexity,
    extract_sql_blocks,
    generate_sql_core,
    get_query_execution_time_estimate,
)
from datu.services.sql_generator.normalizer import normalize_for_preview

dbt_active_profile = get_active_target_config()
settings = get_app_settings()
logger = get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=dict)
async def chat_with_llm(request: ChatRequest):
    """
    Chat endpoint for the AI data analyst.
    Delegates SQL-related generation to the `sql_generate` MCP tool by default,
    while keeping the prompt open to use other MCP tools when appropriate.

    Returns:
        dict: {
            "assistant_response": str,
            "queries": [ {title, sql, complexity, execution_time_estimate}, ... ]  # may be empty
        }
    """
    try:
        if not settings.enable_mcp:
            return await generate_sql_core(request)

        if not request.system_prompt:
            system_prompt = """
You have access to MCP tools (e.g., SQL generation, web browsing, file operations, data retrieval).
Always check if a question is better answered by invoking one or more MCP tools; if so, use them first.

- Connect to the `sql_generator` server first and keep it active.
- Unless otherwise specified, use the `sql_generate` tool by default.

If the user query is generic and not related to a specific tool, you can greet the user with a friendly message,
providing a brief overview of available tools and how to use them.
If the user asks for SQL generation, use the `sql_generate` tool by default. 

A short list of greetings you can use:
1) "Hello! I'm your Datu AI Analyst, I can assist you with SQL generation and data exploration."
2) "Hi! I'm your Datu AI Analyst. I can help you with SQL queries, data analysis, and more."
3) "Hi there! I'm your Datu AI Analyst. Need help with SQL or data insights? Just ask!"

If the user query is business or data related and no other tool is available,
use the sql_generator tool as described below.

Contract for `sql_generate`:
- Call the tool with the user message.
- When the tool returns, respond to the user with the tool’s `assistant_response` verbatim.
- Do not add headings, summaries, bullets, complexity lines, or any extra text before/after.
- Do not reformat or rephrase the tool output.
- The tool already includes the required format:
  `Query name: <name>` followed immediately by a ```sql fenced block.

If the user asks for something that is not SQL, you may use other MCP tools; otherwise prefer `sql_generate`.
"""
        else:
            system_prompt = request.system_prompt

        logger.debug("Received chat messages: %s", request.messages)
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        llm_response = await generate_response(messages, system_prompt)
        logger.debug("LLM response: %s", llm_response)
    except Exception as e:
        logger.error("Error in chat endpoint: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error in chat endpoint") from e

    if not isinstance(llm_response, str):
        llm_response = getattr(llm_response, "content", str(llm_response))
    normalized = normalize_for_preview(llm_response)
    logger.debug("Assistant (post-normalize): %s", normalized)
    blocks = extract_sql_blocks(normalized)
    queries_with_complexity = []
    for idx, b in enumerate(blocks, start=1):
        sql_text = (b.get("sql") or "").strip()
        title = (b.get("title") or f"Query {idx}").strip()
        if not sql_text:
            continue
        complexity = estimate_query_complexity(sql_text)
        exec_time = get_query_execution_time_estimate(complexity)
        queries_with_complexity.append(
            QueryDetails(
                title=title,
                sql=sql_text,
                complexity=complexity,
                execution_time_estimate=exec_time,
            )
        )

    logger.debug("Extracted %d queries for preview.", len(queries_with_complexity))
    if queries_with_complexity:
        logger.debug("First query title: %s", queries_with_complexity[0].title)
        logger.debug("First query sql: %s", queries_with_complexity[0].sql)

    return {
        "assistant_response": normalized,
        "queries": queries_with_complexity,
    }
