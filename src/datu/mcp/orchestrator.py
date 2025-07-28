"""Orchestrator for dispatching requests to appropriate tools."""

from typing import Dict, List, Union

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from datu.app_config import get_app_settings, get_logger
from datu.mcp.client import tool_session

settings = get_app_settings()
logger = get_logger(__name__)


async def invoke_tool(tool_name: str, args: dict) -> str:
    async with tool_session(tool_name) as tool:
        return await tool.ainvoke(args)


def dispatch_by_command(input_str: str, tools: Dict[str, BaseTool]) -> tuple[str, dict] | None:
    """
    Dispatches the input string to the appropriate tool based on the command.

    Args:
        input_str (str): Input string like "/echo hello world".
        tools (Dict[str, BaseTool]): A dictionary mapping command names to tools.

    Returns:
        tuple[str, dict] | None: Tool name and input dict, or None if no match.
    """
    if not input_str.startswith("/"):
        return None

    parts = input_str[1:].split(" ", 1)
    print("Parts:", parts)  # Debugging line to check parts
    if len(parts) < 2:
        return None

    tool_key, payload = parts
    if tool_key in tools:
        return tool_key, {"msg": payload}
    return None


def dispatch_by_context(input_data: dict, tools: Dict[str, BaseTool]) -> tuple[str, dict] | None:
    """
    Dispatches input dict to the correct tool using 'tool' and 'input' fields.

    Args:
        input_data (dict): Dict containing keys 'tool' and 'input'.
        tools (Dict[str, BaseTool]): Tool dictionary keyed by tool name.

    Returns:
        tuple[str, dict] | None: Tool name and input dict, or None if not routable.
    """
    tool_key = input_data["tool"]
    if tool_key in tools:
        return tool_key, input_data["input"]
    return None


async def dispatch_with_llm(
    input_messages: List[dict],
    tools: List[BaseTool],
) -> tuple[str, dict] | None:
    """
    Dispatches input using an LLM to select the appropriate tool and arguments.

    Args:
        input_messages (List[dict]): List of chat messages, e.g., [{"role": "user", "content": "..."}].
        tools (List[BaseTool]): List of available LangChain tools.

    Returns:
        tuple[str, dict] | None: Selected tool name and input args, or None if no tool match.
    """
    lc_messages: list[BaseMessage] = []
    for m in input_messages:
        if m["role"] == "user":
            lc_messages.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            lc_messages.append(AIMessage(content=m["content"]))
    system_prompt = (
        "You are an AI assistant that MUST use one of the provided tools to answer every user request. "
        "If no tool is suitable, respond with a clear error message: 'No suitable tool available for this request.' "
        "Never reply directly unless a tool has been explicitly called or no tool applies."
    )
    lc_messages = [SystemMessage(content=system_prompt)] + lc_messages
    model = ChatOpenAI(
        model=settings.openai_model, temperature=settings.llm_temperature, api_key=SecretStr(settings.openai_api_key)
    )

    print("=== Tools available to LLM ===")
    for tool in tools:
        print(f"- {tool.name}: {tool.description}")
    response = await model.bind_tools(tools).ainvoke(lc_messages)
    print("=== Raw LLM response ===")
    print(response)
    print("=== Tool call ===")
    print(getattr(response, "tool_call", None))

    if isinstance(response, AIMessage) and hasattr(response, "tool_calls") and response.tool_calls:
        call = response.tool_calls[0]
        return call["name"], call["args"]
    return None


async def orchestrate_dispatch(
    input_data: Union[str, dict], tools: List[BaseTool], message_history: List[dict]
) -> tuple[str, dict] | None:
    """
    Attempts dispatch using command or context rules, then falls back to LLM-based dispatch.

    Args:
        input_data (str | dict): The raw input, either command string or structured dict.
        tools (List[BaseTool]): Available tools.
        message_history (List[dict]): Message history used for LLM fallback.

    Returns:
        tuple[str, dict] | None: Selected tool and input, or None if dispatch fails.
    """
    tool_map = {tool.name: tool for tool in tools}

    if isinstance(input_data, str):
        result = dispatch_by_command(input_data, tool_map)
        if result:
            return result

    if isinstance(input_data, dict):
        result = dispatch_by_context(input_data, tool_map)
        if result:
            return result

    return await dispatch_with_llm(message_history, tools)
