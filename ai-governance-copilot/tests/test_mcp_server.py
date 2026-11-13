"""Check the MCP server publishes the three tools and that they work."""
import asyncio
import json

import pytest

pytest.importorskip("mcp")

import mcp_server  # noqa: E402


def test_lists_three_tools():
    names = {t.name for t in asyncio.run(mcp_server.mcp.list_tools())}
    assert names == {"search_governance_knowledge", "classify_ai_use_case", "draft_risk_register_entry"}


def _text(result):
    """call_tool returns content blocks (and sometimes structured output); get the text."""
    content = result[0] if isinstance(result, tuple) else getattr(result, "content", result)
    return " ".join(getattr(block, "text", str(block)) for block in content)


def test_classify_tool_over_mcp():
    result = asyncio.run(mcp_server.mcp.call_tool(
        "classify_ai_use_case", {"description": "AI that screens CVs for hiring"}))
    assert "High risk" in _text(result)


def test_risk_entry_tool_over_mcp():
    result = asyncio.run(mcp_server.mcp.call_tool(
        "draft_risk_register_entry",
        {"system_name": "Bot", "risk_description": "Wrong answers", "likelihood": 4, "impact": 5}))
    assert "High" in _text(result) and "20" in _text(result)
