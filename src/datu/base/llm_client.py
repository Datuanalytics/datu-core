"""# BaseLLMClient class to provide a common interface for LLM clients."""

from abc import ABC, abstractmethod

from mcp_use import MCPClient

from datu.app_config import settings


class BaseLLMClient(ABC):
    """BaseLLMClient class to provide a common interface for LLM clients.
    This class serves as an abstract base class for all LLM clients,
    providing a common interface and shared functionality.
    """

    def __init__(self):
        """Initializes the BaseLLMClient.
            Sets up the client and MCP client if enabled in the settings.

        Attributes:
            client: The LLM client instance.
            mcp_client: The MCP client instance if MCP is enabled in the settings.
            agent: The agent instance if applicable.
        """
        self.client = None
        self.mcp_client = None
        if settings.enable_mcp:
            self.mcp_client = MCPClient.from_config_file(settings.mcp.config_file)
        self.agent = None

    @abstractmethod
    async def chat_completion(self, messages: list, system_prompt: str | None = None) -> str:
        """Given a conversation (and an optional system prompt), returns the assistant's text response."""

    @abstractmethod
    def fix_sql_error(self, sql_code: str, error_msg: str, loop_count: int) -> str:
        """Given a faulty SQL query and an error message, returns a corrected SQL query."""

    @abstractmethod
    def generate_business_glossary(self, schema_info: dict) -> dict:
        """Given schema information, returns a JSON object mapping table names to definitions and
        columns to descriptions.
        """
