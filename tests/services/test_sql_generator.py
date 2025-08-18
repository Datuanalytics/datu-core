"""
Tests for SQL generator modules using real code paths, with only the LLM and DB
execution mocked to avoid external calls.

- Uses pytest + pytest-asyncio
- Keeps real modules (no wholesale stubbing)
- Mocks datu.services.llm.generate_response and the connector's run_transformation
- Includes Google-style docstrings
"""

from __future__ import annotations

import asyncio
import re

import pytest

# Pull real schema types for request building
from datu.base.chat_schema import ChatMessage, ChatRequest
from src.datu.mcp.tools.sql_generator import sql_generate

# Import the real modules from your codebase
from src.datu.services.sql_generator import core
from src.datu.services.sql_generator.normalizer import normalize_for_preview


@pytest.fixture(autouse=True)
def _reset_db_connector(monkeypatch):
    """Ensure the DB connector does not hit a real database.

    We patch DBConnectorFactory.get_connector().run_transformation to a no-op
    by default; individual tests can override with specific side effects.
    """
    conn = core.DBConnectorFactory.get_connector()

    def no_op(sql: str, test_mode: bool = False):
        return None

    monkeypatch.setattr(conn, "run_transformation", no_op)
    yield


def test_extract_sql_blocks_named_only():
    """When at least one 'Query name:' exists, only those are returned."""
    text = "Intro\nQuery name: A\n```sql\nSELECT 1;\n```\nQuery name: B\n```sql\nSELECT 2;\n```"
    blocks = core.extract_sql_blocks(text)
    assert [b["title"] for b in blocks] == ["A", "B"]
    assert "SELECT 1" in blocks[0]["sql"]
    assert "SELECT 2" in blocks[1]["sql"]


def test_extract_sql_blocks_fallback_only():
    """When no 'Query name:' exists, fallback to generic titles for all fences."""
    text = "x\n```sql\nSELECT 1;\n```\n```sql\nSELECT 2;\n```"
    blocks = core.extract_sql_blocks(text)
    assert len(blocks) == 2
    assert blocks[0]["title"].startswith("Query ")
    assert blocks[1]["title"].startswith("Query ")


def test_get_query_execution_time_estimate_thresholds():
    """Map complexity scores to execution time categories."""
    assert core.get_query_execution_time_estimate(0).startswith("Fast")
    assert core.get_query_execution_time_estimate(6).startswith("Moderate")
    assert core.get_query_execution_time_estimate(15).startswith("Slow")
    assert core.get_query_execution_time_estimate(25).startswith("Very Slow")


def test_validate_and_fix_sql_rejects_ddl():
    """Reject DDL/DML inside fenced SQL."""
    dangerous = "Before\n```sql\nDELETE FROM mytab;\n```\nAfter"
    out = core.validate_and_fix_sql(dangerous)
    assert "Rejected due to unsafe SQL operation" in out
    assert "DELETE FROM" in out


def test_validate_and_fix_sql_fix_loop_success(monkeypatch):
    """Fail once, then succeed after fix."""

    class FakeConn:
        def __init__(self):
            self.fail = True

        def run_transformation(self, sql: str, test_mode: bool = False):
            if self.fail:
                self.fail = False
                raise RuntimeError("syntax error")
            return None

    fake_conn = FakeConn()
    monkeypatch.setattr(core.DBConnectorFactory, "get_connector", lambda: fake_conn)

    def fake_fix(sql: str, err: str, loop_count: int) -> str:
        return sql + " /* fixed */"

    monkeypatch.setattr(core, "fix_sql_error", fake_fix)

    out = core.validate_and_fix_sql("```sql\nSELECT 1\n```")
    assert "FAILED TO RUN" not in out
    assert "/* fixed */" in out


def test_estimate_query_complexity_uses_real_parser():
    """Run complexity on a real-looking query; should be > 0 and stable."""
    q = 'SELECT "id", "amount" FROM public."orders" ORDER BY "id";'
    c = core.estimate_query_complexity(q)
    assert isinstance(c, int) and c >= 1


@pytest.mark.asyncio
async def test_generate_sql_core_happy_path(monkeypatch):
    class SuccessfulConnector:
        """Test connector that always succeeds."""

        def run_transformation(self, sql: str, test_mode: bool = False):
            return None

    # Accept any args because load_schema_cache may call with profile_name, target_name
    monkeypatch.setattr(core.DBConnectorFactory, "get_connector", lambda *a, **k: SuccessfulConnector())

    # Avoid hitting real SchemaExtractor
    monkeypatch.setattr(core, "load_schema_cache", lambda: [{"table": "public.orders", "columns": ["id"]}])

    async def fake_llm(messages, system_prompt):
        return 'Query name: Orders basic\n```sql\nSELECT "id" FROM public."orders" ORDER BY "id";\n```'

    monkeypatch.setattr(core, "generate_response", fake_llm)

    req = ChatRequest(messages=[ChatMessage(role="user", content="show orders")])
    result = await core.generate_sql_core(req, use_schema_rag=False)

    assert "```sql" in result["assistant_response"]
    q = result["queries"][0]
    assert q.title == "Orders basic"
    assert q.complexity >= 1
    assert q.execution_time_estimate in {e.value for e in core.ExecutionTimeCategory}


@pytest.mark.asyncio
async def test_generate_sql_core_failed_fix(monkeypatch):
    """Connector always raises; fix_sql_error returns '', leading to FAILED TO RUN."""

    class FailingConnector:
        """Test connector that always raises."""

        def run_transformation(self, sql: str, test_mode: bool = False):
            raise RuntimeError("Simulated failure")

    monkeypatch.setattr(core.DBConnectorFactory, "get_connector", lambda *a, **k: FailingConnector())

    # Avoid hitting real SchemaExtractor
    monkeypatch.setattr(core, "load_schema_cache", lambda: [{"table": "public.orders", "columns": ["id"]}])

    def fix_returns_empty(sql: str, err: str, loop_count: int) -> str:
        return ""

    monkeypatch.setattr(core, "fix_sql_error", fix_returns_empty)

    async def fake_llm(messages, system_prompt):
        return "Query name: Fails\n```sql\nSELECT broken\n```"

    monkeypatch.setattr(core, "generate_response", fake_llm)

    req = ChatRequest(messages=[ChatMessage(role="user", content="broken")])
    result = await core.generate_sql_core(req, use_schema_rag=False)

    assert "FAILED TO RUN" in result["assistant_response"]
    q = result["queries"][0]
    assert q.complexity == 0
    assert q.execution_time_estimate == "N/A"


def test_normalize_for_preview_headers_bullets_and_spacing():
    """Normalize headings, remove bullets, and collapse blank lines."""
    content = (
        "### Query Name: My Query\n\n"
        "- **Complexity**: 123\n"
        "- **Estimated Execution Time**: Slow\n"
        "\n```sql\nSELECT 1;\n```"
    )
    out = normalize_for_preview(content)
    assert out.startswith("Query name: My Query")
    assert "**Complexity**" not in out
    assert "**Estimated Execution Time**" not in out
    assert re.search(r"Query name:\s*My Query\n```sql", out, flags=re.I)


@pytest.mark.asyncio
async def test_sql_generate_success(monkeypatch):
    """sql_generate returns assistant_response and queries when core succeeds.

    We bypass the internal await by patching asyncio.wait_for to return a canned result.
    """

    async def fake_wait_for(coro, timeout):
        return {
            "assistant_response": "ok",
            "queries": [{"title": "Q1", "sql": "SELECT 1;", "complexity": 1, "execution_time_estimate": "Fast"}],
        }

    monkeypatch.setattr(asyncio, "wait_for", fake_wait_for)

    msgs = [ChatMessage(role="user", content="q")]
    out = await sql_generate(messages=msgs, system_prompt=None, timeout_sec=5, disable_schema_rag=True)
    assert out["assistant_response"] == "ok"
    assert out["queries"][0]["title"] == "Q1"


@pytest.mark.asyncio
async def test_sql_generate_timeout(monkeypatch):
    """sql_generate returns a timeout error when asyncio.wait_for raises TimeoutError."""

    async def boom(*args, **kwargs):
        raise asyncio.TimeoutError()

    monkeypatch.setattr(asyncio, "wait_for", boom)

    msgs = [ChatMessage(role="user", content="q")]
    out = await sql_generate(messages=msgs, timeout_sec=1, disable_schema_rag=True)
    assert out["error"] == "timeout"
    assert "exceeded" in out["details"]


@pytest.mark.asyncio
async def test_sql_generate_invalid_request():
    """Invalid request: messages=None should yield a validation error."""
    out = await sql_generate(messages=None, timeout_sec=1, disable_schema_rag=True)  # type: ignore[arg-type]
    assert out["error"] == "invalid_request"
    assert isinstance(out["details"], list)
