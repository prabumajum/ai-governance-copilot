"""Guardrails: simple, transparent checks around the LLM.

Input guardrail  -> blocks prompt-injection attempts and redacts personal data
                    BEFORE anything reaches the model.
Output guardrail -> redacts personal data, makes sure sources are cited and adds
                    a disclaimer BEFORE the answer reaches the user.

These are rule-based on purpose: easy to read, test and explain. In production you
would add an ML classifier (e.g. Guardrails AI, NeMo Guardrails, Llama Guard).
"""
import re
from dataclasses import dataclass, field

MAX_INPUT_CHARS = 2000
DISCLAIMER = "_General guidance only, not legal advice._"

# Personal data patterns. Order matters: more specific patterns first.
PII_PATTERNS = {
    "EMIRATES_ID": r"\b784-?\d{4}-?\d{7}-?\d\b",
    "EMAIL": r"[\w.+-]+@[\w-]+\.[\w.-]+",
    "CARD_NUMBER": r"\b(?:\d[ -]?){13,16}\b",
    "PHONE": r"\+\d[\d\s-]{7,}\d",
    "INDIAN_PAN": r"\b[A-Z]{5}\d{4}[A-Z]\b",
}

# Phrases typical of prompt-injection / jailbreak attempts.
INJECTION_PATTERNS = [
    r"ignore (all |any |the )?(previous|prior|above|earlier) (instructions|rules|prompts?)",
    r"disregard (all |any |the )?(previous|prior|above|your) (instructions|rules)",
    r"(reveal|show|print|repeat) (me )?(your|the) (system )?(prompt|instructions)",
    r"\bsystem prompt\b",
    r"you are now (?!going)",
    r"\b(jailbreak|developer mode|dan mode)\b",
    r"act as .{0,40}without (any )?(restrictions|rules|limits)",
]

SOURCE_TAG = re.compile(r"\[source: ([\w.-]+\.md)")


@dataclass
class GuardResult:
    allowed: bool
    text: str
    events: list = field(default_factory=list)


def redact_pii(text: str):
    """Replace personal data with placeholders. Returns (new_text, list_of_types_found)."""
    found = []
    for label, pattern in PII_PATTERNS.items():
        text, count = re.subn(pattern, f"[{label} REDACTED]", text)
        if count:
            found.append(label)
    return text, found


def check_input(user_text: str) -> GuardResult:
    """Run every input check. Blocked inputs never reach the LLM."""
    text = (user_text or "").strip()
    if not text:
        return GuardResult(False, "", ["Blocked: empty message"])
    if len(text) > MAX_INPUT_CHARS:
        return GuardResult(False, text, [f"Blocked: message longer than {MAX_INPUT_CHARS} characters"])
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return GuardResult(False, text, ["Blocked: possible prompt-injection attempt"])

    text, pii = redact_pii(text)
    events = [f"Redacted personal data in input: {', '.join(pii)}"] if pii else []
    return GuardResult(True, text, events)


def check_output(answer: str, retrieved_sources: list) -> GuardResult:
    """Clean up the model's answer before showing it."""
    events = []
    text, pii = redact_pii(answer or "")
    if pii:
        events.append(f"Redacted personal data in output: {', '.join(pii)}")

    # Grounding check: if the agent searched the knowledge base, the answer must cite it.
    sources = sorted(set(retrieved_sources))
    if sources and "source:" not in text.lower():
        text += "\n\n**Sources:** " + ", ".join(sources)
        events.append("Added missing source citations")

    if DISCLAIMER not in text:
        text += f"\n\n{DISCLAIMER}"
    return GuardResult(True, text, events)


def sources_in(tool_output: str) -> list:
    """Extract knowledge-base file names from a search tool's output."""
    return SOURCE_TAG.findall(tool_output or "")
