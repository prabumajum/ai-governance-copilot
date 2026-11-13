"""The agent, built as an explicit LangGraph state machine.

    START -> input_guard --(blocked)--> END
                 |
                 v
               agent <-----------+
                 |               |
       (wants a tool?) --yes--> tools
                 |
                 no
                 v
            output_guard -> END

Each box is a plain Python function ("node") that reads the shared state and
returns an update. Drawing the graph explicitly, instead of using a one-line
prebuilt agent, makes every step visible and testable.
"""
import time
import uuid

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from . import config, guardrails
from .tools import TOOLS

SYSTEM_PROMPT = """You are the AI Governance Copilot, an assistant for AI governance,
risk and compliance (GRC) work: ISO/IEC 42001, AI risk and impact assessment,
the EU AI Act, responsible AI controls, and AI rules in India, the UAE/GCC and the USA.

Rules:
1. For any factual governance question, call search_governance_knowledge first and
   answer ONLY from what it returns. Cite each fact like (source: file.md).
   If the knowledge base does not cover it, say so plainly. Never invent articles or dates.
2. When the user describes an AI system and asks how risky it is, call classify_ai_use_case.
3. When the user asks for a risk-register entry, call draft_risk_register_entry.
4. Politely decline anything unrelated to AI governance.
5. Be concise: short paragraphs or bullets, under 250 words.
You give general guidance, not legal advice."""


class State(MessagesState):
    """Shared memory passed between nodes. `messages` comes from MessagesState."""
    guard_events: list
    blocked: bool


def message_text(message) -> str:
    """Gemini can return content as a list of parts; flatten it to plain text."""
    content = message.content
    if isinstance(content, str):
        return content
    return "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content)


def build_graph(model=None):
    """Assemble and compile the graph. Pass a fake `model` in tests to run offline."""
    if model is None:
        from langchain.chat_models import init_chat_model

        def load(name):
            return init_chat_model(name, temperature=0, max_retries=1, timeout=60).bind_tools(TOOLS)

        # Resilience: if the main model is busy (e.g. 503 high demand), try the backups in order.
        model_with_tools = load(config.MODEL).with_fallbacks([load(m) for m in config.FALLBACK_MODELS])
    else:
        model_with_tools = model.bind_tools(TOOLS)

    def input_guard(state: State):
        last = state["messages"][-1]
        result = guardrails.check_input(message_text(last))
        if not result.allowed:
            refusal = ("I can't help with that request. I answer questions on AI governance, "
                       "risk and compliance. Please rephrase your question.")
            return {"messages": [AIMessage(content=refusal)],
                    "guard_events": result.events, "blocked": True}
        update = {"guard_events": result.events, "blocked": False}
        if result.text != message_text(last):
            # Same id = replace the original message, so raw personal data is never stored.
            update["messages"] = [HumanMessage(content=result.text, id=last.id)]
        return update

    def agent(state: State):
        reply = model_with_tools.invoke([SystemMessage(content=SYSTEM_PROMPT)] + state["messages"])
        return {"messages": [reply]}

    def output_guard(state: State):
        messages = state["messages"]
        # Collect the sources retrieved during THIS turn (after the latest user message).
        last_human = max(i for i, m in enumerate(messages) if isinstance(m, HumanMessage))
        sources = []
        for m in messages[last_human:]:
            if isinstance(m, ToolMessage) and m.name == "search_governance_knowledge":
                sources += guardrails.sources_in(message_text(m))
        final = messages[-1]
        result = guardrails.check_output(message_text(final), sources)
        cleaned = final.model_copy(update={"content": result.text})  # same id -> replaces it
        return {"messages": [cleaned], "guard_events": state.get("guard_events", []) + result.events}

    graph = StateGraph(State)
    graph.add_node("input_guard", input_guard)
    graph.add_node("agent", agent)
    graph.add_node("tools", ToolNode(TOOLS))
    graph.add_node("output_guard", output_guard)

    graph.add_edge(START, "input_guard")
    graph.add_conditional_edges("input_guard", lambda s: END if s["blocked"] else "agent")
    graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: "output_guard"})
    graph.add_edge("tools", "agent")
    graph.add_edge("output_guard", END)

    return graph.compile(checkpointer=InMemorySaver())  # checkpointer = conversation memory


def run_turn(graph, question: str, thread_id: str = None) -> dict:
    """Ask one question and return the answer plus a trace for the UI and evals."""
    thread_id = thread_id or str(uuid.uuid4())
    run_config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 12}
    before = len(graph.get_state(run_config).values.get("messages", []))

    start = time.perf_counter()
    state = graph.invoke({"messages": [HumanMessage(content=question)]}, run_config)
    latency = round(time.perf_counter() - start, 2)

    new_messages = state["messages"][before:]
    tools_used, sources = [], []
    for m in new_messages:
        if isinstance(m, AIMessage):
            tools_used += [call["name"] for call in (m.tool_calls or [])]
        if isinstance(m, ToolMessage):
            sources += guardrails.sources_in(message_text(m))

    return {
        "answer": message_text(state["messages"][-1]),
        "tools_used": tools_used,
        "sources": sorted(set(sources)),
        "guard_events": state.get("guard_events", []),
        "blocked": state.get("blocked", False),
        "latency_s": latency,
        "thread_id": thread_id,
    }
