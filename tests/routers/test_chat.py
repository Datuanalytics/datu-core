# tests/routers/test_chat.py
"""
Simple smoke tests for the chat SQL FastAPI endpoint (self-contained)
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import httpx
import pytest
from fastapi import FastAPI

import src.datu.routers.chat as chat
from src.datu.base.chat_schema import ChatMessage, ChatRequest


def _payload(messages: List[ChatMessage], system_prompt: str | None = None) -> Dict[str, Any]:
    """Serialize a ChatRequest to a plain dict for httpx."""
    req = ChatRequest(messages=messages, system_prompt=system_prompt)
    return json.loads(req.model_dump_json())


def _make_app() -> FastAPI:
    """Create a minimal FastAPI app mounting the router under test."""
    app = FastAPI()
    app.include_router(chat.router, prefix="/chat/sql")
    return app


@pytest.mark.asyncio
async def test_happy_path_single_sql_block(monkeypatch):
    """200 OK with one parsed query when LLM returns a single fenced SQL block."""
    messages = [ChatMessage(role="user", content="daily sales")]
    llm_out = "Query name: Sales\n```sql\nSELECT 1 AS x;\n```"

    async def fake_generate(_msgs, _sys):
        return llm_out

    # Patch the actual call site used by the core the router invokes.
    monkeypatch.setattr(
        "datu.services.sql_generator.core.load_schema_cache",
        lambda *a, **k: [],
        raising=True,
    )
    monkeypatch.setattr(
        "datu.services.sql_generator.core.generate_response",
        fake_generate,
        raising=True,
    )
    monkeypatch.setattr(
        "datu.services.sql_generator.core.estimate_query_complexity",
        lambda _sql: 3,
        raising=True,
    )
    monkeypatch.setattr(
        "datu.services.llm.fix_sql_error",
        lambda sql_code, _err, _loop: sql_code,
        raising=True,
    )
    monkeypatch.setattr(
        "datu.services.sql_generator.core.get_query_execution_time_estimate",
        lambda _c: "Fast (<1s)",
        raising=True,
    )

    app = _make_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/chat/sql/", json=_payload(messages))
    assert r.status_code == 200
    data = r.json()
    assert data["assistant_response"].startswith("Query name: Sales")
    assert isinstance(data["queries"], list) and len(data["queries"]) == 1
    q0 = data["queries"][0]
    assert q0["title"] == "Sales"
    assert "SELECT 1" in q0["sql"]
    assert q0["complexity"] == 3
    assert q0["execution_time_estimate"].startswith("Fast")


@pytest.mark.asyncio
async def test_error_path_llm_raises_500(monkeypatch):
    """Any exception in LLM call returns HTTP 500 with the configured detail."""
    messages = [ChatMessage(role="user", content="daily sales")]

    async def boom(*_args, **_kwargs):
        raise RuntimeError("LLM down")

    # Patch the same call site inside core where the LLM is invoked.
    monkeypatch.setattr(
        "datu.services.sql_generator.core.generate_response",
        boom,
        raising=True,
    )

    app = _make_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/chat/sql/", json=_payload(messages))
    assert r.status_code == 500
    assert r.json()["detail"] == "Internal Server Error in chat endpoint"
