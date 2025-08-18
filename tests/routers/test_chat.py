# tests/routers/test_chat.py
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import datu.routers.chat as chat
from datu.base.chat_schema import ChatMessage, ChatRequest


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(chat.router, prefix="/chat/sql")
    return TestClient(app)


# enable_mcp = True branch


@pytest.mark.asyncio
async def test_happy_path_with_mcp(monkeypatch):
    async def fake_generate_response(_msgs, _sys):
        return "Query name: Sales\n```sql\nSELECT 1;\n```"

    monkeypatch.setattr(chat.settings, "enable_mcp", True, raising=False)
    monkeypatch.setattr(chat, "generate_response", fake_generate_response, raising=True)

    client = _client()
    req = ChatRequest(messages=[ChatMessage(role="user", content="sales")])
    resp = client.post("/chat/sql/", json=req.model_dump())

    assert resp.status_code == 200
    data = resp.json()
    assert data["queries"][0]["title"] == "Sales"
    assert "SELECT 1" in data["queries"][0]["sql"]


@pytest.mark.asyncio
async def test_error_path_with_mcp(monkeypatch):
    async def boom(*_a, **_k):
        raise RuntimeError("LLM down")

    monkeypatch.setattr(chat.settings, "enable_mcp", True, raising=False)
    monkeypatch.setattr(chat, "generate_response", boom, raising=True)

    client = _client()
    req = ChatRequest(messages=[ChatMessage(role="user", content="x")])
    resp = client.post("/chat/sql/", json=req.model_dump())

    assert resp.status_code == 500
    assert "Internal Server Error" in resp.json()["detail"]


# enable_mcp = False branch


@pytest.mark.asyncio
async def test_passthrough_to_generate_sql_core(monkeypatch):
    async def fake_generate_sql_core(request: ChatRequest):
        return {"assistant_response": "core path", "queries": []}

    monkeypatch.setattr(chat.settings, "enable_mcp", False, raising=False)
    monkeypatch.setattr(chat, "generate_sql_core", fake_generate_sql_core, raising=True)

    client = _client()
    req = ChatRequest(messages=[ChatMessage(role="user", content="hi")])
    resp = client.post("/chat/sql/", json=req.model_dump())

    assert resp.status_code == 200
    data = resp.json()
    assert data["assistant_response"] == "core path"
    assert data["queries"] == []
