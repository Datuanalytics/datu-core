from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage
from langchain_core.messages.tool import ToolCall

import datu.mcp.orchestrator as orchestrator
from datu.mcp.orchestrator import dispatch_by_command, dispatch_by_context, dispatch_with_llm


@pytest.fixture(scope="module")
def tools():
    """Mocked tools dictionary."""
    mock_tool = AsyncMock()
    mock_tool.name = "echo"
    mock_tool.ainvoke = AsyncMock(return_value="MCP Echo: mock response")
    return {"echo": mock_tool}


@pytest.mark.asyncio
async def test_dispatch_command(tools):
    input_str = "/echo Hello from command"
    result = dispatch_by_command(input_str, tools)

    assert result is not None
    tool_name, input_data = result
    output = await tools[tool_name].ainvoke(input_data)
    assert "MCP Echo" in output


@pytest.mark.asyncio
async def test_dispatch_context(tools):
    input_data = {"tool": "echo", "input": {"msg": "Hello from context"}}
    result = dispatch_by_context(input_data, tools)

    assert result is not None
    tool_name, input_dict = result
    output = await tools[tool_name].ainvoke(input_dict)
    assert "MCP Echo" in output


@pytest.mark.asyncio
async def test_dispatch_with_llm(tools, monkeypatch):
    mock_response = AIMessage(
        content="", tool_calls=[ToolCall(name="echo", args={"msg": "simulated response"}, id="call-id-123")]
    )

    mock_model_instance = MagicMock()
    mock_bound_model = MagicMock()
    mock_bound_model.ainvoke = AsyncMock(return_value=mock_response)
    mock_model_instance.bind_tools.return_value = mock_bound_model

    monkeypatch.setattr(orchestrator, "ChatOpenAI", MagicMock(return_value=mock_model_instance))

    message_history = [{"role": "user", "content": "echo something"}]
    result = await dispatch_with_llm(message_history, list(tools.values()))

    assert result is not None
    tool_name, tool_input = result
    assert tool_name == "echo"
    assert tool_input["msg"] == "simulated response"
