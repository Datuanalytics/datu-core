from pydantic import Field
from pydantic_settings import BaseSettings


class MCPConfig(BaseSettings):
    """Configuration settings for MCP integration.
    This class uses Pydantic's BaseSettings to manage environment variables
    and provides a structured way to access MCP configuration settings.

    Args:
        max_steps (int): The maximum number of steps for MCP operations.
        use_server_manager (bool): Whether to use the server manager for MCP operations.
        config_file (str): The file path for the MCP configuration file.

    Attributes:
        max_steps (int): The maximum number of steps for MCP operations.
        use_server_manager (bool): Whether to use the server manager for MCP operations.
        config_file (str): The file path for the MCP configuration file.
    """

    max_steps: int = Field(default=30, description="Maximum number of steps MCPAgent can run.")
    use_server_manager: bool = Field(default=True, description="Whether to enable the Server Manager.")
    config_file: str = Field(default="mcp_config.json", description="Path to the MCP configuration file.")
