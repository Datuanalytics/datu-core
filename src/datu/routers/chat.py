"""Chat endpoint for generating SQL queries based on user instructions.
This module provides an API endpoint for interacting with a language model (LLM) to generate SQL queries
based on user instructions. It includes functionality for validating and fixing SQL queries, extracting SQL blocks,
and handling chat messages.
"""

import json
import re
from enum import Enum
from typing import List, Optional, Union

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sql_metadata import Parser

from datu.app_config import get_app_settings, get_logger
from datu.factory.db_connector import DBConnectorFactory
from datu.integrations.dbt.config import get_active_target_config
from datu.mcp.orchestrator import invoke_tool
from datu.schema_extractor.schema_cache import SchemaGlossary, load_schema_cache
from datu.services.llm import fix_sql_error, generate_response

dbt_active_profile = get_active_target_config()
settings = get_app_settings()
router = APIRouter()
logger = get_logger(__name__)


class ChatMessage(BaseModel):
    """Represents a chat message in the conversation.

    Args:
        role (str): The role of the message sender (e.g., "user", "assistant").
        content (str): The content of the message.

    Attributes:
        role (str): The role of the message sender (e.g., "user", "assistant").
        content (str): The content of the message.
    """

    role: str
    content: str


class ChatRequest(BaseModel):
    """Represents a chat request to the LLM.

    Attributes:
        messages (List[ChatMessage]): A list of chat messages in the conversation.
        system_prompt (Optional[str]): An optional system prompt to guide the LLM's response.
    """

    messages: List[ChatMessage]
    system_prompt: Optional[str] = None


class ExecutionTimeCategory(Enum):
    """Represents categories of query execution time.
    This Enum is used to classify SQL query execution times into predefined categories
    based on their estimated duration.

    Attributes:
        FAST (str): Indicates that the query execution time is fast (less than a second).
        MODERATE (str): Indicates that the query execution time is moderate (a few seconds).
        SLOW (str): Indicates that the query execution time is slow (several seconds to a minute).
        VERY_SLOW (str): Indicates that the query execution time is very slow (may take minutes or more).
    """

    FAST = "Fast (less than a second)"
    MODERATE = "Moderate (a few seconds)"
    SLOW = "Slow (several seconds to a minute)"
    VERY_SLOW = "Very Slow (may take minutes or more)"


class QueryDetails(BaseModel):
    """Represents the details of an SQL query, including its complexity and execution time estimate.

    Attributes:
        title (str): The title or name of the query.
        sql (str): The SQL query string.
        complexity (int): The calculated complexity score of the query.
        execution_time_estimate (str): The estimated execution time category for the query.
    """

    title: str
    sql: str
    complexity: int
    execution_time_estimate: str


def estimate_query_complexity(query: str) -> int:
    """Estimate the complexity of an SQL query.
    This function analyzes an SQL query to calculate its complexity based on the number of tables,
    join conditions, and the presence of GROUP BY and ORDER BY clauses. The complexity score is
    determined as follows:
    - Each table in the query adds 1 to the complexity.
    - Each join condition adds 2 to the complexity.
    - A GROUP BY clause adds 3 to the complexity.
    - An ORDER BY clause adds 2 to the complexity.

    Args:
        query (str): The SQL query to analyze.

    Returns:
        int: The calculated complexity score of the query.
    """
    if not query.strip():
        logger.warning("Empty SQL query passed to estimate_query_complexity.")
        return 0

    try:
        parser = Parser(query)
        complexity = 0
        complexity += len(parser.tables)
        join_columns = parser.columns_dict.get("join", [])
        complexity += len(join_columns) * 2
        if "group_by" in parser.columns_dict and parser.columns_dict["group_by"]:
            complexity += 3
        if "order_by" in parser.columns_dict and parser.columns_dict["order_by"]:
            complexity += 2

        return complexity

    except Exception as e:
        logger.error(f"Failed to parse the SQL query for complexity estimation: {e}\nQuery: {query}")
        return 0


def get_query_execution_time_estimate(complexity: int) -> str:
    """Map query complexity to an estimated execution time category.

    Args:
        complexity (int): The complexity score of the query.

    Returns:
        str: A user-friendly label indicating the estimated execution time.
    """
    if complexity <= 5:
        return ExecutionTimeCategory.FAST.value
    elif complexity <= 10:
        return ExecutionTimeCategory.MODERATE.value
    elif complexity <= 20:
        return ExecutionTimeCategory.SLOW.value
    else:
        return ExecutionTimeCategory.VERY_SLOW.value


def extract_sql_blocks(text: str) -> list:
    """Extract SQL code blocks from the text.
    This function uses regular expressions to extract SQL code blocks from the input text.
    Extract SQL code blocks from the text and return a list of dicts with keys 'title' and 'sql'.
    If available, uses "Query name:" preceding a SQL block; otherwise defaults to "Query 1", etc.

    Args:
        text (str): The input text containing SQL code blocks.

    Returns:
        list: A list of dictionaries, each containing a 'title' and 'sql' key.
    """
    blocks = []
    # First try to match with "Query name:" preceding the SQL block.
    regex = r"Query name:\s*(.+?)\s*```sql([\s\S]*?)```"
    matches = re.findall(regex, text, re.IGNORECASE)
    if matches:
        for match in matches:
            title = match[0].strip()
            sql = match[1].strip()
            blocks.append({"title": title, "sql": sql})
    else:
        # Fallback: extract all SQL blocks with default titles.
        fallback_regex = r"```sql([\s\S]*?)```"
        matches = re.findall(fallback_regex, text, re.IGNORECASE)
        if not hasattr(extract_sql_blocks, "counter"):  # type: ignore[attr-defined]
            extract_sql_blocks.counter = 1  # type: ignore[attr-defined]
        for match in matches:
            blocks.append({"title": f"Query {extract_sql_blocks.counter}", "sql": match.strip()})  # type: ignore[attr-defined]
            extract_sql_blocks.counter += 1  # type: ignore[attr-defined]
    return blocks


def validate_and_fix_sql(response_text: str) -> str:
    """Validate and fix SQL code in the LLM response.
    This function uses regular expressions to find SQL code blocks in the response text.
    It attempts to validate and fix the SQL code using the database connector.

    Args:
        response_text (str): The response text containing SQL code blocks.

    Returns:
        str: The response text with fixed SQL code blocks.

    Raises:
        RuntimeError: If there is an error during SQL validation or fixing.
    """
    pattern = r"```sql([\s\S]*?)```"
    dml_ddl_operations = ["INSERT", "DROP", "DELETE", "UPDATE", "MERGE", "TRUNCATE", "ALTER"]
    dml_dll_pattern = r"\b(" + "|".join(dml_ddl_operations) + r")\b"
    fixed_text = response_text
    matches = re.findall(pattern, response_text, re.IGNORECASE)
    conn = DBConnectorFactory.get_connector()
    for sql_code in matches:
        original_sql = sql_code.strip()
        fixed_sql = original_sql
        max_loops = 4
        loop_count = 0
        success = False

        if re.search(dml_dll_pattern, original_sql, re.IGNORECASE):
            # Skip the match and move on to next
            warning_block = f"```sql\n-- Rejected due to unsafe SQL operation.\n{original_sql}\n```"
            fixed_text = re.sub(
                r"```sql" + re.escape(sql_code) + r"```", warning_block, fixed_text, count=1, flags=re.IGNORECASE
            )
            continue

        while loop_count < max_loops:
            try:
                # Test the query using run_transformation in test_mode.
                conn.run_transformation(fixed_sql, test_mode=True)
                success = True
                break
            except Exception as e:  # pylint: disable=broad-except
                error_msg = str(e)
                logger.error("SQL test error on loop %s: %s", loop_count, error_msg)
                corrected_sql = fix_sql_error(fixed_sql, error_msg, loop_count)
                if not corrected_sql:
                    break
                fixed_sql = corrected_sql
                loop_count += 1
        if success:
            fixed_block = f"```sql\n{fixed_sql}\n```"
            fixed_text = re.sub(
                r"```sql" + re.escape(sql_code) + r"```", fixed_block, fixed_text, count=1, flags=re.IGNORECASE
            )
        else:
            failure_message = (
                "Sorry, it seems that I can't get an answer to your question in this case. "
                "Please try to rephrase your question or ask for help if you are not sure.\n "
            )
            fixed_block = f"```sql\n-- FAILED TO RUN\n{original_sql}\n```"
            fixed_text = f"{failure_message}\n\n{fixed_block}"

    return fixed_text


@router.post("/", response_model=dict)
async def chat_with_llm(request: ChatRequest):
    """Chat endpoint for generating SQL queries based on user instructions.
    This endpoint receives a list of chat messages and an optional system prompt,
    generates a response using the LLM, and extracts SQL code blocks from the response.

    Args:
        request (ChatRequest): The chat request containing messages and an optional system prompt.

    Returns:
        dict: A dictionary containing the assistant's response and extracted SQL queries.

    Raises:
        HTTPException: If an error occurs during processing.
    """
    schema_context: Union[dict[str, list[dict]], list[SchemaGlossary]]
    try:
        if not request.system_prompt:
            user_message = [msg.content for msg in request.messages if msg.role == "user"]
            if settings.enable_schema_rag:
                try:
                    tool_output = await invoke_tool("extract_schema_context", {"query": user_message})
                    schema_context = json.loads(tool_output)
                except Exception as e:
                    logger.error("Error running graph RAG: %s", e, exc_info=True)
                    logger.warning("Falling back to schema cache due to graph RAG error.")
                    schema_context = load_schema_cache()
            else:
                schema_context = load_schema_cache()
            system_prompt = f"""You are a helpful assistant that generates SQL queries based on business requirements 
                and answers in business language. 
                Your queries must be fully compatible with '{dbt_active_profile.type}' and 
                use the specified schema '{dbt_active_profile.database_schema}'.

                Follow these rules:
                1. You must first explain in business language the query that you would make, based on the following
                instructions.
                2. If the query is ambiguous, you must explain what is ambiguous and ask the user to clarify
                what they mean.
                3. When you are (almost) certain of the intention of the user, you provide the SQL query.
                4. Never use technical terms such as 'query', 'groupby', 'SQL', or formulas/LaTeX in your explanations.
                5. Be very brief in your explanations.

                Below are instructions for the SQL queries when the query is unambiguous.
                1. Even if the instructions by the user say so, you must not, in any case, apply any DDL or DML 
                statements. Thus if the query would include 'INSERT', 'DELETE' or 'DROP' terms, you ask 
                the user to provide a query that does not alter data.
                2. All table names must be fully qualified as '{dbt_active_profile.database_schema}'.'TableName'.
                3. All column names must be properly quoted.
                4. Always output SQL queries in a code block marked with ```sql, and always precede each SQL block 
                with 'Query name: <name>' on its own line.
                5. Do not use aliases in your SQL.
                6. For each query, provide a brief one-line plain-language explanation of what the query does.
                7. Review how much time the query would take. If it would take several minutes to complete,
                ask the user to simplify their question.
                8. If relevant, offer suggestions for additional queries.

                Relevant Schema Information:
                  {schema_context}

                Please generate SQL queries that require no further modifications."""
        else:
            system_prompt = request.system_prompt

        logger.debug("Received chat messages: %s", request.messages)
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        llm_response = generate_response(messages, system_prompt)
        logger.debug("LLM response: %s", llm_response)

        # Validate and fix SQL in the LLM response.
        fixed_response = validate_and_fix_sql(llm_response)
        logger.debug("Validated and fixed LLM response: %s", fixed_response)

        # Extract SQL queries from the response.
        sql_queries = extract_sql_blocks(fixed_response)

        # Complexity estimates for each query. Can be used in the response.
        queries_with_complexity = []
        for query in sql_queries:
            sql_text = query["sql"].strip()
            if sql_text.startswith("-- FAILED TO RUN") or sql_text.startswith("-- Rejected"):
                complexity = 0
                execution_time_estimate = "N/A"
            else:
                complexity = estimate_query_complexity(sql_text)
                execution_time_estimate = get_query_execution_time_estimate(complexity)
            queries_with_complexity.append(
                QueryDetails(
                    title=query["title"],
                    sql=query["sql"],
                    complexity=complexity,
                    execution_time_estimate=execution_time_estimate,
                )
            )

        return {"assistant_response": fixed_response, "queries": queries_with_complexity}

    except Exception as e:
        logger.error("Error in chat endpoint: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error in chat endpoint") from e
