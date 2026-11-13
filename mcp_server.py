"""MCP server: exposes the copilot's tools to any MCP client (Claude Desktop, IDEs, other agents).

MCP (Model Context Protocol) is a standard way for AI apps to discover and call tools.
The same three tools the LangGraph agent uses are published here, so another AI
assistant can use this knowledge base without any of our agent code.

Run it:   python mcp_server.py        (talks over stdio; no API key needed)
"""
from mcp.server.mcpserver import MCPServer

from copilot import config, risk
from copilot.knowledge import get_knowledge_base

mcp = MCPServer(
    name="ai-governance-copilot",
    instructions="Tools for AI governance: search ISO 42001 / EU AI Act guidance, "
                 "screen AI use cases into risk tiers, and draft risk-register entries.",
)


@mcp.tool()
def search_governance_knowledge(query: str) -> str:
    """Search the AI governance knowledge base (ISO/IEC 42001, EU AI Act, risk and
    impact assessment, responsible AI controls, India/UAE/USA rules). Cite the sources."""
    hits = get_knowledge_base().search(query, k=config.TOP_K)
    return "\n\n".join(f"[source: {h['source']} > {h['section']}]\n{h['text']}" for h in hits)


@mcp.tool()
def classify_ai_use_case(description: str) -> dict:
    """Screen an AI use case into an EU AI Act style risk tier with key obligations."""
    return risk.classify_use_case(description)


@mcp.tool()
def draft_risk_register_entry(system_name: str, risk_description: str,
                              likelihood: int, impact: int) -> str:
    """Draft an ISO/IEC 42001 risk-register row. likelihood and impact are 1-5."""
    return risk.draft_risk_entry(system_name, risk_description, likelihood, impact)["markdown"]


if __name__ == "__main__":
    mcp.run()
