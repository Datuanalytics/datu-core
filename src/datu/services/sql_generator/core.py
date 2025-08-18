# services/sql_generation/core.py

import re
from enum import Enum
from typing import Union

from pydantic import BaseModel
from sql_metadata import Parser

from datu.app_config import get_app_settings, get_logger
from datu.base.chat_schema import ChatRequest
from datu.factory.db_connector import DBConnectorFactory
from datu.integrations.dbt.config import get_active_target_config
from datu.schema_extractor.schema_cache import SchemaGlossary, load_schema_cache
from datu.services.llm import fix_sql_error, generate_response
from datu.services.schema_rag import get_schema_rag

dbt_active_profile = get_active_target_config()
settings = get_app_settings()
logger = get_logger(__name__)


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
    regex = r"Query name:\s*(.+?)\s*```(?:sql)?\s*([\s\S]*?)```"
    matches = re.findall(regex, text, re.IGNORECASE)
    if matches:
        for match in matches:
            title = match[0].strip()
            sql = match[1].strip()
            blocks.append({"title": title, "sql": sql})
    else:
        # Fallback: extract all SQL blocks with default titles.
        fallback_regex = r"```(?:sql)?\s*([\s\S]*?)```"
        matches = re.findall(fallback_regex, text, re.IGNORECASE)
        if not hasattr(extract_sql_blocks, "counter"):  # type: ignore[attr-defined]
            extract_sql_blocks.counter = 1  # type: ignore[attr-defined]
        for match in matches:
            blocks.append({"title": f"Query {extract_sql_blocks.counter}", "sql": match.strip()})  # type: ignore[attr-defined]
            extract_sql_blocks.counter += 1  # type: ignore[attr-defined]
    return blocks


def validate_and_fix_sql(response_text: str) -> str:
    pattern = r"```(?:sql)?\s*([\s\S]*?)```"
    dml_ddl_ops = ["INSERT", "DROP", "DELETE", "UPDATE", "MERGE", "TRUNCATE", "ALTER"]
    dml_ddl_pattern = re.compile(r"\b(" + "|".join(dml_ddl_ops) + r")\b", re.IGNORECASE)

    def strip_comments(sql: str) -> str:
        return re.sub(r"--.*?$|/\*[\s\S]*?\*/", "", sql, flags=re.MULTILINE)

    conn = DBConnectorFactory.get_connector()

    out_parts = []
    last = 0
    for m in re.finditer(pattern, response_text, re.IGNORECASE):
        out_parts.append(response_text[last : m.start()])
        original_sql = m.group(1).strip()

        # Reject DDL/DML
        if dml_ddl_pattern.search(strip_comments(original_sql)):
            out_parts.append("```sql\n-- Rejected due to unsafe SQL operation.\n")
            out_parts.append(original_sql)
            out_parts.append("\n```")
            last = m.end()
            continue

        # Attempt fix loops
        fixed_sql = original_sql
        success = False
        for loop_count in range(4):
            try:
                conn.run_transformation(fixed_sql, test_mode=True)
                success = True
                break
            except Exception as e:
                corrected_sql = fix_sql_error(fixed_sql, str(e), loop_count)
                if not corrected_sql:
                    break
                fixed_sql = corrected_sql

        if success:
            out_parts.append("```sql\n")
            out_parts.append(fixed_sql)
            out_parts.append("\n```")
        else:
            failure_message = (
                "Sorry, it seems that I can't get an answer to your question in this case. "
                "Please try to rephrase your question or ask for help if you are not sure.\n "
            )
            out_parts.append(f"{failure_message}\n\n```sql\n-- FAILED TO RUN\n")
            out_parts.append(original_sql)
            out_parts.append("\n```")

        last = m.end()

    out_parts.append(response_text[last:])
    return "".join(out_parts)


async def generate_sql_core(request: ChatRequest, *, use_schema_rag: bool | None = None) -> dict:
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

    if not request.system_prompt:
        user_message = [msg.content for msg in request.messages if msg.role == "user"]
        use_rag = settings.enable_schema_rag if use_schema_rag is None else use_schema_rag
        if use_rag:
            try:
                schema_context = get_schema_rag().run_query(user_message)
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
            4. Always format the SQL blocks following way:
            Query name: <name>
            ```<SQL code>```
            6. Do not use aliases in your SQL.
            7. For each query, provide a brief one-line plain-language explanation of what the query does.
            8. Review how much time the query would take. If it would take several minutes to complete,
            ask the user to simplify their question.
            9. If relevant, offer suggestions for additional queries.

            Relevant Schema Information:
              {schema_context}

            Please generate SQL queries that require no further modifications."""
    else:
        system_prompt = request.system_prompt

    logger.debug("Received chat messages: %s", request.messages)

    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    llm_response = await generate_response(messages, system_prompt)
    logger.debug("LLM response: %s", llm_response)

    fixed_response = validate_and_fix_sql(llm_response)
    logger.debug("Validated and fixed LLM response: %s", fixed_response)

    sql_queries = extract_sql_blocks(fixed_response)

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
