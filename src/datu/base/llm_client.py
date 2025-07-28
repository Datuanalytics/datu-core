"""# BaseLLMClient class to provide a common interface for LLM clients."""

from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    """BaseLLMClient class to provide a common interface for LLM clients.
    This class serves as an abstract base class for all LLM clients,
    providing a common interface and shared functionality.
    """

    @abstractmethod
    def chat_completion(self, messages: list, system_prompt: str | None = None) -> str:
        """Given a conversation (and an optional system prompt), returns the assistant's text response."""

    @abstractmethod
    def fix_sql_error(self, sql_code: str, error_msg: str, loop_count: int) -> str:
        """Given a faulty SQL query and an error message, returns a corrected SQL query."""

    @abstractmethod
    def generate_business_glossary(self, schema_info: dict) -> dict:
        """Given schema information, returns a JSON object mapping table names to definitions and
        columns to descriptions.
        """
