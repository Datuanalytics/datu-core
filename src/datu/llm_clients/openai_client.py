"""LLM client for OpenAI API."""

import json
import re
import textwrap
from typing import Union

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent

from datu.app_config import get_logger, settings
from datu.base.llm_client import BaseLLMClient

logger = get_logger(__name__)

MessageContent = Union[str, list[Union[str, dict]]]


def extract_sql_from_text(text: str) -> str:
    """Extracts SQL code from a code block labeled with 'sql'.
    This function uses a regular expression to find and extract SQL code from the input text.
    It looks for a code block that starts with '```sql' and ends with '```'.
    If no such block is found, it returns the original text.

    Args:
        text (str): The input text containing SQL code.

    Returns:
        str: The extracted SQL code or the original text if no SQL code block is found.
    """
    match = re.search(r"```sql([\s\S]*?)```", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text.strip()


def extract_json_from_text(text: str) -> str:
    """Extracts JSON code from a code block labeled with 'json'.
    This function uses a regular expression to find and extract JSON code from the input text.
    It looks for a code block that starts with '```json' and ends with '```'.
    If no such block is found, it returns the original text.

    Args:
        text (str): The input text containing JSON code.

    Returns:
        str: The extracted JSON code or the original text if no JSON code block is found.
    """
    json_regex = r"```(?:json)?\s*([\s\S]*?)\s*```"
    match = re.search(json_regex, text, re.IGNORECASE)
    if match:
        return match.group(1)
    return text


class OpenAIClient(BaseLLMClient):
    """OpenAIClient class for interacting with the OpenAI API.
    This class provides methods for generating chat completions, fixing SQL errors,
    and generating business glossaries using the OpenAI API.

    Attributes:
        client (ChatOpenAI): The LangChain OpenAI API client.
        model (str): The model to use for generating completions.
    """

    def __init__(self):
        """Initializes the OpenAIClient with the configured model and API key."""
        super().__init__()
        self.model = getattr(settings, "openai_model", "gpt-4o-mini")
        self.client = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=self.model,
            temperature=settings.llm_temperature,
        )
        self.history = ChatMessageHistory()
        self.agent = None
        if settings.enable_mcp:
            if not self.mcp_client:
                raise RuntimeError("MCP is enabled but mcp_client was not initialized. ")
            try:
                self.agent = MCPAgent(
                    llm=self.client,
                    client=self.mcp_client,
                    max_steps=settings.mcp.max_steps,
                    use_server_manager=settings.mcp.use_server_manager,
                )
            except Exception:
                # Prefer failing early so misconfig doesn’t silently degrade behavior
                logger.exception("Failed to construct MCPAgent with provided MCP settings.")
                raise

    async def chat(self, input_text: str) -> str:
        """Sends a chat message to the MCP agent and returns the response.
        Args:
            input_text (str): The input text to send to the agent.
        Returns:
            str: The response from the agent."""

        if not settings.enable_mcp or self.agent is None:
            raise RuntimeError("chat() requires MCP enabled and an initialized agent.")
        response = await self.agent.run(
            input_text,
            max_steps=30,
        )
        return response

    async def chat_completion(self, messages: list[BaseMessage], system_prompt: str | None = None) -> str:
        """Generates a chat completion response based on the provided messages and system prompt.
        Args:
            messages (list[BaseMessage]): A list of messages to send to the LLM.
            system_prompt (str | None): An optional system prompt to guide the LLM's response.
        Returns:
            str: The generated response from the LLM.
        """
        if settings.simulate_llm_response:
            return create_simulated_llm_response()
        if not messages:
            raise ValueError(
                textwrap.dedent(
                    """chat_completion was called with an empty message list. 
            At least one message is required to generate a response.

            Valid inputs: LangChain style HumanMessage, or message dict.

            Example (LangChain message):
                [HumanMessage(content='Hello, what is the weather today?')]        

            Example (OpenAI-style dict):
                [{'role': 'user', 'content': 'Hello, what is the weather today?'}]
            """
                )
            )

        if system_prompt:
            self.history.add_message(SystemMessage(content=system_prompt))

        last_input = messages[-1]
        last_user_message: MessageContent

        if isinstance(last_input, dict):
            if "role" not in last_input or last_input["role"] != "user":
                raise ValueError("The last message dict must have a 'role' key with value 'user'.")
            if "content" not in last_input:
                raise ValueError("The last message dict must contain a 'content' key.")
            last_user_message = last_input["content"]
        elif isinstance(last_input, HumanMessage):
            last_user_message = last_input.content
        else:
            raise TypeError(
                f"Unsupported message type at end of list: {type(last_input).__name__}. "
                "Expected a dict with role='user', or a HumanMessage instance."
            )

        self.history.add_message(HumanMessage(content=last_user_message))
        # Convert entire history messages to plain text for chat()
        # Adjust this if your llm_with_tools expects different format
        input_text = "\n".join(msg.content for msg in self.history.messages if hasattr(msg, "content"))

        if settings.enable_mcp:
            # uses MCP agent
            response = await self.chat(input_text)
        else:
            # direct LLM call without MCP
            response = await self.client.ainvoke(self.history.messages)

        # Assuming response is a BaseMessage or similar with 'content'
        if hasattr(response, "content"):
            self.history.add_message(response)
            return response.content
        else:
            # If response is plain text string
            self.history.add_message(HumanMessage(content=response))
            return response

    def fix_sql_error(self, sql_code: str, error_msg: str, loop_count: int) -> str:
        """Generates a corrected SQL query based on the provided SQL code and error message.

        Args:
            sql_code (str): The SQL code that caused the error.
            error_msg (str): The error message returned by the SQL engine.
            loop_count (int): The number of times this function has been called.

        Returns:
            str: The corrected SQL code.
        """
        prompt = (
            f"The following SQL query caused an error:\n\n{sql_code}\n\n"
            f"Error message:\n{error_msg}\n\n"
            "Please provide a corrected SQL query that addresses the error. "
            "Return only the SQL code in a code block labeled 'sql'."
        )
        response = self.client.invoke(
            [
                SystemMessage(content="You are an SQL expert."),
                HumanMessage(content=prompt),
            ]
        )
        assistant_response = response.content
        # Extract SQL code from the response
        return extract_sql_from_text(assistant_response or "")

    def generate_business_glossary(self, schema_info: dict) -> dict:
        """Generates a business glossary based on the provided schema information.

        Args:
            schema_info (dict): A dictionary containing schema information, including table names and columns.

        Returns:
            dict: A JSON object mapping table names to definitions and columns to descriptions.
        """
        prompt = (
            "You are an expert data catalog curator. For each table in the schema below, "
            "provide a brief business definition for the table and for its key columns. "
            "Here is the schema information:\n"
            f"{schema_info}\n"
            "Return your answer as a JSON object with keys 'definition' and 'columns'."
        )
        response = self.client.invoke(
            [
                SystemMessage(content="You are a data catalog assistant."),
                HumanMessage(content=prompt),
            ]
        )
        # Remove any code block formatting from the response.
        glossary_text = extract_json_from_text(response.content or "")
        glossary = {}
        try:
            glossary = json.loads(glossary_text)
        except json.JSONDecodeError as parse_err:
            logger.error("Error parsing business glossary JSON: %s", parse_err)
            logger.debug("Raw glossary text: %s", glossary_text)
        return glossary


def create_simulated_llm_response() -> str:
    """Simulates a response from the LLM for testing purposes.
    This function returns a hardcoded response that mimics the expected output of the LLM.

    Returns:
        str: A simulated LLM response containing SQL queries and additional information.
    """
    return """
                Validated and fixed LLM response: Here are three separate SQL queries that provide insights into the development of the business over time:

                ### Query name: Report_SalesOrders_Over_Time
                ```sql
                SELECT 
                    "CREATEDAT", 
                    COUNT("SALESORDERID") AS "Total_Sales_Orders", 
                    SUM("GROSSAMOUNT") AS "Total_Gross_Amount", 
                    SUM("NETAMOUNT") AS "Total_Net_Amount"
                FROM 
                    "bronze"."SalesOrders"
                GROUP BY 
                    "CREATEDAT"
                ORDER BY 
                    "CREATEDAT";
                ```
                *This query generates a report showing the total number of sales orders and the total gross and net amounts for each date in the SalesOrders table.*

                ### Query name: Report_BusinessPartners_Over_Time
                ```sql
                SELECT 
                    "CREATEDAT", 
                    COUNT("PARTNERID") AS "Total_Business_Partners"
                FROM 
                    "bronze"."BusinessPartners"
                GROUP BY 
                    "CREATEDAT"
                ORDER BY 
                    "CREATEDAT";
                ```
                *This query provides a report on the total number of business partners created over time, grouped by the creation date.*

                ### Query name: Report_Products_Over_Time
                ```sql
                SELECT 
                    *
                FROM 
                    "bronze"."Products";
                ```
                *This query summarizes the total number of products and their total value created over time, based on the creation date in the Products table.*

                ### Suggestions for Additional Queries:
                - A query to analyze the average order value over time.
                - A query to track changes in the number of different product categories over time.
                - A query to evaluate the growth in revenue by fiscal year.
                """  # noqa: E501
