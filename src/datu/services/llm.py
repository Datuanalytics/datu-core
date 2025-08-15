"""LLM service module.
This module provides functions for interacting with a language model (LLM) to generate responses,
fix SQL errors, and generate business glossaries. It uses a factory pattern to create an LLM client
based on the specified provider in the application settings.
The LLM client is responsible for making API calls to the underlying LLM service.
"""

import time
from typing import Any

from datu.app_config import get_app_settings, get_logger
from datu.factory.llm_client_factory import get_llm_client

logger = get_logger(__name__)
settings = get_app_settings()

llm_client = get_llm_client(provider=settings.llm_provider)


async def generate_response(messages: list[Any], system_prompt: str | None = None) -> str:
    """Generate a response from the LLM based on the provided messages and system prompt.

    Args:
        messages (list): A list of messages to send to the LLM.
        system_prompt (str, optional): An optional system prompt to guide the LLM's response.

    Returns:
        str: The generated response from the LLM. if it fails, returns a default error message.
    """
    logger.debug("LLM conversation payload: messages=%s, system_prompt=%s", messages, system_prompt)
    try:
        start_time = time.time()
        if llm_client is None:
            logger.error("LLM client is not initialized.")
            raise ValueError("LLM client is not initialized.")
        response_text = await llm_client.chat_completion(messages, system_prompt)
        elapsed_time = time.time() - start_time
        logger.debug("LLM response took %.3f seconds", elapsed_time)
        logger.debug("LLM response: %s", response_text)
        return response_text
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Unexpected error generating LLM response: %s", e, exc_info=True)
        return "Sorry, an unexpected error occurred while generating a response."


def fix_sql_error(sql_code: str, error_msg: str, loop_count: int) -> str:
    """Fix a SQL error by generating a corrected SQL query based on the provided SQL code and error message.

    Args:
        sql_code (str): The original SQL code that caused the error.
        error_msg (str): The error message associated with the SQL code.
        loop_count (int): The number of times this function has been called in a loop.

    Returns:
        str: The corrected SQL code.

    Raises:
        ValueError: If the LLM client is not initialized.
    """
    if llm_client is None:
        logger.error("LLM client is not initialized.")
        raise ValueError("LLM client is not initialized.")
    return llm_client.fix_sql_error(sql_code, error_msg, loop_count)


def generate_business_glossary(schema_info: dict) -> dict:
    """Generate a business glossary based on the provided schema information.

    Args:
        schema_info (dict): A dictionary containing schema information, including table names and columns.

    Returns:
        dict: A JSON object mapping table names to definitions and columns to descriptions.

    Raises:
        ValueError: If the LLM client is not initialized.
    """
    if llm_client is None:
        logger.error("LLM client is not initialized.")
        raise ValueError("LLM client is not initialized.")
    return llm_client.generate_business_glossary(schema_info)
