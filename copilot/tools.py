"""The agent's tools. The LLM reads each docstring to decide when to call a tool,
so the docstrings are written for the model as much as for humans."""
from langchain_core.tools import tool

from . import config, risk
from .knowledge import get_knowledge_base


@tool
def search_governance_knowledge(query: str) -> str:
    """Search the AI governance knowledge base: ISO/IEC 42001, AI risk assessment,
    AI impact assessment, EU AI Act, responsible AI controls, and AI rules in India,
    the UAE/GCC and the USA. Use it for ANY factual governance question.
    Returns passages tagged [source: file.md] that you must cite."""
    hits = get_knowledge_base().search(query, k=config.TOP_K)
    return "\n\n".join(f"[source: {h['source']} > {h['section']}]\n{h['text']}" for h in hits)


@tool
def classify_ai_use_case(description: str) -> str:
    """Screen a described AI system or use case into a risk tier (Prohibited, High risk,
    Limited risk, Minimal risk) modelled on the EU AI Act, with the main obligations.
    Use it when the user describes an AI system and asks how risky it is or what applies."""
    result = risk.classify_use_case(description)
    lines = [f"Tier: {result['tier']}",
             f"Triggers: {', '.join(result['matched'])}",
             "Obligations:"] + [f"- {o}" for o in result["obligations"]] + [f"Note: {result['note']}"]
    return "\n".join(lines)


@tool
def draft_risk_register_entry(system_name: str, risk_description: str,
                              likelihood: int, impact: int) -> str:
    """Draft one ISO/IEC 42001 risk-register row with score, band and treatment.
    likelihood and impact are whole numbers from 1 (lowest) to 5 (highest).
    If the user did not give them, estimate sensibly and say that you estimated."""
    try:
        return risk.draft_risk_entry(system_name, risk_description, likelihood, impact)["markdown"]
    except ValueError as error:
        return f"Could not draft the entry: {error}"


TOOLS = [search_governance_knowledge, classify_ai_use_case, draft_risk_register_entry]
